'''
PPASTVisitor class. This class visits the elements of the Mini AST produced by
MiniToASTVisitor to build a string representation of the AST. You’ll build on this
file to build the pretty-printer.

This class also performs static semantic analysis.
'''

'''
possible TODO:
- see if i want to move all type checking error reporting into type_of_expr, instead of in visit_binary_expression like i have rn
'''

from miniast import mini_ast, program_ast, type_ast, statement_ast, expression_ast, lvalue_ast
from graphviz import Digraph
import re
import json
import pandas as pd


# pretty_print_ast_visitor.py

from miniast import mini_ast, program_ast, type_ast, statement_ast, expression_ast, lvalue_ast

class PPASTVisitor(mini_ast.ASTVisitor):
   # outputjson={"Types":[],"Top Level Decls":[],"Functions":[]}
    outputjson={}
    
    def __init__(self):
        self.structs={}     #for each struct, the name, fields, linenum where defined
        self.functions={}   #for each func, the name, linenum, params, and return type
        self.globals={}     #all globally declared variables
        self.vars={}      #for each scope--in this case, functions--an entry that points to the parent scope--aka 
                            #the entry in self.functions--. lists all local vars in the local scope, their name, type, etc. 
                            # includes parameters. for ex:
        '''
        [   {parent:"add",
            locals:  [ {name:"g",type:"int",line:3}]},...]                    
        '''
        self.error_count=0
        self._last_tree = None
        self.current_fun=None
        
    def _label(self,s):
        return s if isinstance(s,str) else str(s)
    
    def _to_json(self, node):
        """Convert a ('label', [children...]) tuple tree to a JSON-ish dict."""
        label, kids = node
        return {
        "label": str(label),
        "children": [self._to_json(k) for k in kids]
        }

    def _ensure_tree(self, program):
        if self._last_tree is None:
        # Build it exactly once by running the normal visit
            program.accept(self)   # this sets self._last_tree
        return self._last_tree
    
    def render_json(self, program):
        """Build the same tree your pretty-printer uses, then convert to JSON dict."""
        root = self._ensure_tree(program)   # you already have this
        return self._to_json(root)
    
    def _getlabel(self,possibletuple):
        if isinstance(possibletuple,tuple):
            return possibletuple[0]
        else:
            return str(possibletuple)
    
    def _cleanname(self,name):
        words=name.split(" ")
        if len(words)>1:
            return words[1]
        else:
            return name.replace("Id","",1)
    
    def _node(self,label,*children):    #building a node as a 2 tuple of the label and children
        flat=[]
        for c in children:
            if c is None:
                continue
            if isinstance(c,tuple):
                flat.append(c)
            elif isinstance(c,list):
                temp = []
                for x in c:
                    if x is not None:
                        temp.append(x)
                flat.extend(temp)

        return (self._label(label),flat)
    
    def _render(self,treeroot):
        lines=[]
        def walk(node,prefix="",is_last=True):
            label=node[0]
            kids=node[1]
            connector="└─ " if is_last else "├─ "
            if prefix=="":
                lines.append(label)
            else:
                lines.append(prefix+connector+label)
            if not kids:
                return
            next_prefix=""
            if is_last:
                next_prefix=prefix + " "
            else:
                next_prefix= prefix + "│ "
          
            for i,ch in enumerate(kids):
                walk(ch,next_prefix,i==len(kids)-1)
        walk(treeroot,"",True)
        return "\n".join(lines)
    
    def _op_to_text(self, op):
        try:
            return op.value 
        except AttributeError:
            return str(op)
     
    '''helper functions being added for milestone 1, aka semantic analysis'''
    def report_error(self,msg,line=None):
        ln=-1
        if line is not None:
            ln=line
            print(f"ERROR. {msg}. #{ln}")
        else:
            print(f"ERROR. {msg}")
        self.error_count+=1
    
    def type_to_str(self, t:type_ast.Type | type_ast.ReturnType) -> str:
        if isinstance(t,type_ast.IntType):return "int"
        elif isinstance(t,type_ast.BoolType):return "bool"
        elif isinstance(t,type_ast.StructType):return f"struct {t.name.id}"
        elif isinstance(t,type_ast.ReturnTypeVoid):return "void"
        elif isinstance(t,type_ast.ReturnTypeReal):return self.type_to_str(t.type)
        else:
            return "unknown type"
        
    def is_struct(self,typ):
        return isinstance(typ,str) and typ.startswith("struct ")
    
    def get_struct_name(self,typ):
        words = typ.split(" ")
        if len(words)==1:
            return typ
        return words[1]
     
    def is_same_type(self,a,b): #a and b are both strings representing the type. Null allowed on one side
        if a==b:
            return True
        if self.is_struct(a) and b=="null":
            return True
        if self.is_struct(b) and a=="null":
            return True
        return False
    

    def lookup_var_type(self,varname): #look in self.vars, and self.globals
        currscope=self.vars[self.current_fun]
        if varname in currscope:
            var_entry = currscope[varname]
            return var_entry["type"]
        else:
            g = self.globals.get(varname)
            if g is not None:
                return g["type"]
        return None
 
    
    '''returns the type of a dot field, e.g p.x '''
    def type_of_dot_field(self,structtype,field,linenum):
        if structtype is None:
            return
        structname = self.get_struct_name(structtype)
        struct = self.structs[structname]
        flag = False
        for f in struct["fields"]:
            if f==field:
                flag = True
                return struct["fields"][f]
        if not flag:
            self.report_error(f"'{field}' is not a valid field of type {structtype}",linenum)
            return None
    
    '''returns the type of an lvalue, for ex  "p.x" in p.x=4 would return int or "struct SS ex" would return "struct SS" if it is valid. returns error
        if undefined struct is declared'''
    def type_of_lvalue(self,val:lvalue_ast.LValue):
        if isinstance(val,lvalue_ast.LValueDot):
            stype = self.type_of_lvalue(val.left)
            field = val.id.id
            if self.is_struct(stype):
                sname=self.get_struct_name(stype)
                if sname not in self.structs:
                    self.report_error(f"struct {sname} is not defined, unexpected type for variable '{val.left.id.id}'",val.linenum)
                    return None
                res = self.type_of_dot_field(stype,field,val.linenum)
            
            #print(f"this was a dot. passing in stype {stype} and field {field}. res: {res}. on line {val.linenum} ")
                return res
            else:
                if stype is not None:
                    self.report_error(f"Invalid reference: dot operator cannot be used on value of type {stype}",val.linenum)
                return None
        else:
            lookup = self.lookup_var_type(val.id.id)    #if it not an lvalue dot
            if lookup is not None:
                return lookup
            else:
                self.report_error(f"Undefined variable '{val.id.id }'",val.linenum)
    
    '''returns the type of whatever is on one side of an expression. for ex, returns int when evaluating expr "x+3" if x is an int'''
    def type_of_expr(self,e:expression_ast.Expression):
        if isinstance(e,expression_ast.IdentifierExpression):
            lookup = self.lookup_var_type(e.id)
            if lookup is not None:
                return lookup
            else:
                if e.id in self.structs:
                    return f"struct {e.id}"
                else:
                    self.report_error(f"Name '{e.id}' is not defined",e.linenum)
                    return None
        
        elif isinstance(e,expression_ast.DotExpression):
            left = self.type_of_expr(e.left)
            fieldname=e.id.id
            if self.is_struct(left):
                sname = self.get_struct_name(left)
                if sname not in self.structs:
                    self.report_error(f"struct {sname} is not defined, unexpected type for variable '{e.left.id.id}'",e.linenum)
                    return None
                return self.type_of_dot_field(left,fieldname,e.linenum)
            else:
                if left is not None:
                    self.report_error(f"Invalid reference: dot operator cannot be used on value of type {left}",e.linenum)
                return None #im going to see what happens now. if no error is thrown, then this is prob the right place for
                            #adding an error about triyng to get the dot field of something that isn't a struct. but i think i also
                            #need to add a similar error printing in type_of_lvalue, bc this has to do with line 16/17, not 15. 15 passed?
            
        elif isinstance(e,expression_ast.FalseExpression) or isinstance(e,expression_ast.TrueExpression):
            return "bool"

        elif isinstance(e,expression_ast.NewExpression):
            sname=e.id.id
            return f"struct {sname}"
    
        elif isinstance(e,expression_ast.NullExpression):
            return "null"
        
        elif isinstance(e,expression_ast.ReadExpression) or isinstance(e,expression_ast.IntegerExpression):
            return "int"

        elif isinstance(e,expression_ast.InvocationExpression):
            if e.name.id not in self.functions:
                return "error"
            calledfunc=self.functions[e.name.id]
            rettype = calledfunc["return"]
            #want to make sure that the return type of the function called, matches the return type of the function whose escope we r in
            #but for rn, i think we just want to return the RETURN TYPE of the function called
            return rettype
        
        elif isinstance(e,expression_ast.BinaryExpression):
            op = e.operator.value if hasattr(e.operator, "value") else str(e.operator)
            lt = self.type_of_expr(e.left)
            rt = self.type_of_expr(e.right)
            equalityops=['==','!='] #these require require operands of integer or structure type. The operands must have matching type. Structs can be null.
            arithops=['+','-','*','/']    #these require integers only. 
            relationalops=['<','>','<=','>='] #these require integers only
            booleanops=['||','&&'] #these require boolean only
            if lt is not None and rt is not None: #if either was not defined, type_of_expr() would have already reported the error
                if op in arithops:
                    if lt == "int" and rt=="int":
                        return "int"
                elif (op in booleanops):
                    if lt == "bool" and rt=="bool":
                        return "bool"
                elif op in relationalops:
                    if lt=="int" and rt=="int":
                        return "bool"
                elif op in equalityops:
                    if lt==rt and (lt.split()[0]=="struct" and rt.split()[0]=="struct") or (lt=="int" and rt=="int"):
                        return "bool"
                else:
                    print(f"error???")

            return None #bc error would've already been handled/printed
        elif isinstance(e,expression_ast.UnaryExpression):
            op = self._op_to_text(e.operator)
            operand = e.operand
            t = self.type_of_expr(operand)
            if t is not None:
                if op == "!":    #can only be performed on boolean operands. returns a boolean
                    if t != "bool":
                        self.report_error(f"Cannot perform operation '{op}' with operand of type {t}", e.linenum)
                        return None
                    else:       #if it was a valid bool, will evaluate to bool
                        return "bool"
                if op =="-": #can only be performed on integer operands. returns an int
                    if t!="int":
                        self.report_error(f"Cannot perform operation '{op}' with operand of type {t}",e.linenum)
                        return None
                    else:
                        return "int"        
                return None
        else:
            print(f"error???")
            return None

   
    
    '''adds all type declarations to types symbol table'''
    def collect_type_decl(self, td:program_ast.TypeDeclaration):
        name = td.name.id
        if name in self.structs:
            self.report_error(f"Redeclaration of Struct '{name}'",td.linenum)
        line=td.linenum
        fields={}
        for decl in td.fields:
            name1 = decl.name.id
            if name1 in fields:
                self.report_error(f"Redeclaration of struct field '{name1}'",td.linenum)
            ftype=self.type_to_str(decl.type)
            fields[name1]=ftype
            
            if ftype.startswith("struct "):     #type of the struct field, if it is a "struct" type
                structname=self.get_struct_name(ftype)   #the name of the struct type
                if structname != name and structname not in self.structs:             #it can only be the name of the struct itself, OR a previously declared struct
                    self.report_error(f"Unexpected field in 'struct {name}': 'struct {structname}' is not defined",decl.linenum)
        self.structs[name]={"line":line,"fields":fields}
    
    '''adds all global declarations to globals symbol table'''
    def collect_global_decl(self,td:program_ast.Declaration):
        name = td.name.id
        dtype = self.type_to_str(td.type)
        linenum=td.linenum
        if name in self.globals:
            self.report_error(f"Redeclaration of global variable '{name}'",td.linenum)
        self.globals[name]={"line":linenum,"type":dtype}

    '''adds all function signatures to functions symbol table'''
    def collect_function_signature(self,td:program_ast.Function):
        name=td.name.id
        if name in self.functions:
            self.report_error(f"Redeclaration of function name '{name}",td.linenum)
        linenum=td.linenum
        params=[]
        seen=[]
        for p in td.params:
            pname=p.name.id
            if pname in seen:
                self.report_error(f"Duplicate function parameter names: '{pname}",td.linenum)
            else:
                seen.append(pname)
            params.append(self.type_to_str(p.type))
        ret = self.type_to_str(td.ret_type)
        
        self.functions[name]={
            "line":linenum,
            "params":params,
            "return":ret
        }
    
    def visit_program(self, program: program_ast.Program):
        types=[]
        decls=[]
        funcs=[]
        for t in getattr(program,"types",[]):
            self.collect_type_decl(t)
        for t in getattr(program,"types",[]):
            types.append(t.accept(self))
        for d in getattr(program,"declarations",[]):
            self.collect_global_decl(d)
            decls.append(d.accept(self))
        for f in getattr(program,"functions",[]):
            self.collect_function_signature(f)
        if "main" not in self.functions:
            self.report_error("No main function found")
        for f in getattr(program,"functions",[]):
            funcs.append(f.accept(self))
        
        root = self._node("Program",
                          self._node("Types",types),
                          self._node("Top Level Decls",decls),
                          self._node("Functions",funcs))
        self.outputjson["Types"]=[types]
        self.outputjson["Top_Decls"]=[decls]
        self.outputjson["Functions"]=[funcs]
        
        self._last_tree=root
        print(f"ERRORS FOUND {self.error_count}\n")
        return self._render(root)
        
    def visit_declaration(self,declaration:program_ast.Declaration):
        thetype=declaration.type.accept(self)       #the type, like 'int'
        name = declaration.name.accept(self)
        typelabel=self._getlabel(thetype)
        namelabel=self._cleanname(self._getlabel(name))
        ret = f"Decl {typelabel}{namelabel}"       
        return self._node(ret)
    
    def visit_type_declaration(self, type_declaration: program_ast.TypeDeclaration):

        name = type_declaration.name.accept(self)
        namelabel=self._cleanname(self._getlabel(name))
        fields=[]
        for f in getattr(type_declaration,"fields",[]):
            fields.append(f.accept(self))
        
        return self._node(f"Struct {namelabel}",fields)

    '''here, we will want to add all locally declared variables to a locals symbol table in self.vars'''
    '''    [   {parent:"add",
            locals:  [ {name:"g",type:"int",line:3}]},...]  '''  
    def visit_function(self, function: program_ast.Function):
        fname=function.name.id
        self.current_fun=fname
        sig = self.functions[fname]
        ret = sig["return"]
        name=self._cleanname(self._getlabel(function.name.accept(self)))
        self.vars[fname]={}
        locals=[{}]
       # entry["parent"]=name
        retnode=function.ret_type.accept(self)
       # ret = self._getlabel(function.ret_type.accept(self))
        params=[]
        localvars=[]
        body=[]
        seenparams=[]
        seenlocals=[]
        for p in getattr(function,"params",[]):
            pname = p.name.id
            ptype = self.type_to_str(p.type)
            if pname in seenparams:
                self.report_error(f"Duplicate function parameter names: '{pname}",function.linenum)
            else:
                seenparams.append(pname)
            self.vars[fname][pname]={"type":ptype,"line":p.linenum}
  
        for p in getattr(function,"params",[]):
            params.append(p.accept(self))
            
        for l in getattr(function,"locals",[]):
            lname=l.name.id
            ltype=self.type_to_str(l.type)
            if lname in seenlocals:
                self.report_error(f"Duplicate local '{lname}' in '{fname}'",l.linenum)
            if lname in seenparams:
                self.report_error(f"Parameter '{lname}' redeclared in '{fname}'", l.linenum)
            else:
                seenlocals.append(lname)
            self.vars[fname][lname]={"type":ltype,"line":l.linenum}

            
        for l in getattr(function,"locals",[]):
            localvars.append(l.accept(self))
            
        for s in getattr(function,"body",[]):
            body.append(s.accept(self))
        label = f"fun{name}"
        
        if not function.body:
            if ret != "void":
                self.report_error(f"Non-void function is missing return statement: '{fname}'",sig["line"])
            return
        last_stmt = function.body[-1]
        if ret=="void":
            if isinstance(last_stmt,statement_ast.ReturnStatement):
                self.report_error(f"Void function '{fname}' must not return a value",last_stmt.linenum)
        elif isinstance(last_stmt,statement_ast.ReturnEmptyStatement):
                self.report_error(f"Non-void function is missing return statement of type {ret}: '{fname}'", sig["line"])
        elif isinstance(last_stmt,statement_ast.ReturnStatement):
            exprtype = self.type_of_expr(last_stmt.expression)
            if exprtype is None:
                pass
            elif exprtype!=ret:
                self.report_error(f"Function '{fname}' must return a value of type '{ret}'",last_stmt.linenum)
        
        self.current_fun=None
        return self._node(label, 
                          self._node("Params", params),
                          self._node("Locals", localvars),
                          self._node("Return Type",retnode),
                          self._node("Body", body))
    
    
    def visit_type(self, type_: type_ast.Type): #leave blank on purpose?
        pass

    def visit_int_type(self, int_type: type_ast.IntType):
        return self._node("int")
        
    def visit_bool_type(self, bool_type: type_ast.BoolType):
        return self._node("bool")

    def visit_struct_type(self, struct_type: type_ast.StructType):
        #we probs want to make sure that the name of the struct whose type is being 'declared', is a defined one
        name = self.get_struct_name(struct_type.name.id)
       # name = self._cleanname(self._getlabel(struct_type.name.accept(self)))
        if name not in self.structs:
            self.report_error(f"struct {name} is not defined",struct_type.linenum)
        return self._node(f"struct {name}")
    
    
    
    def visit_return_type_real(self, return_type_real: type_ast.ReturnTypeReal):
        inner = getattr(return_type_real,"type",None)
        if inner is not None:
            return inner.accept(self)
        return self._node("<return-type>")
        
    
    def visit_return_type_void(self, return_type_void) -> mini_ast.Any:
        return self._node("void")

    def visit_statement(self, statement: statement_ast.Statement): #leave blank on purpose?
        pass
        
     #type of dot field used in type_of_expr, under isinstance  dot expression. and used in type_of_lvalue. type_of_lvalue used in itself and in 
     #visit_assignment_statement. 
        
    def visit_assignment_statement(self, s: statement_ast.AssignmentStatement):
        #checking if the type of right matches the type of left. 
        #calling self.accept on left and right expressions
        #target is an lvalue (dot or id)
        #if either target or source is none, dont send an error? bc error for why it is none, was alr sent
        target = getattr(s,"target",[]).accept(self) #this is an LVALUE
        source = getattr(s,"source",[]).accept(self) #this is an EXPRESSIOn
        ttype = self.type_of_lvalue(s.target)
        stype=self.type_of_expr(s.source)
        #print(f"target: {ttype}. source: {stype}. #{s.linenum} ")
        if ttype is not None and stype is not None: #if one was None, error would have alr been sent, inside type_of_expr
            if ttype != stype:
                self.report_error(f"Invalid assignment: type '{stype}' assigned to variable of type {ttype}: '{s.target.id.id}'",s.linenum)
        return self._node("Assign",
                          self._node("Target",target),
                          self._node("Source",source))


    def visit_block_statement(self, block_statement: statement_ast.BlockStatement):
        stmnts=[]
        for s in block_statement.statements:
            stmnts.append(s.accept(self))
        return self._node("Block",stmnts)

    def visit_conditional_statement(self, conditional_statement: statement_ast.ConditionalStatement):
        gtype = self.type_of_expr(conditional_statement.guard)
        if gtype != "bool":
            self.report_error(f"Unexpected expression: conditional expression must evaluate to bool; found {gtype}",conditional_statement.linenum)
        name = conditional_statement.guard.accept(self)
        thenblockstmts = []
        thenblockst = conditional_statement.then_block
        for s in thenblockst.statements:
            thenblockstmts.append(s.accept(self))
        elseblocksmts=[]
        if(getattr(conditional_statement,"else_block") is not None):
            elseblock=conditional_statement.else_block
            for s in elseblock.statements:
                elseblocksmts.append(s.accept(self)) 
        else:
            elseblocksmts=None    
        return self._node(f"Branch",self._node("Condition",name),self._node("then-body",thenblockstmts),self._node("else-body",elseblocksmts))

    def visit_while_statement(self, while_statement: statement_ast.WhileStatement):
        gtype = self.type_of_expr(while_statement.guard)
        if gtype!="bool":
            self.report_error(f"Unexpected expression: conditional expression must evaluate to bool; found {gtype}",while_statement.linenum)
        cond = while_statement.guard.accept(self)
        body = while_statement.body.accept(self)
        return self._node("While",self._node("Condition",cond),self._node("Body",body))

    def visit_delete_statement(self, delete_statement: statement_ast.DeleteStatement):
        etype = self.type_of_expr(delete_statement.expression)
        if not self.is_struct(etype):
            self.report_error(f"Expected struct argument for delete, got '{etype}'",delete_statement.linenum)
        expr = delete_statement.expression.accept(self)
        return self._node("Delete",self._node("Expression",expr))

    #no error checking needs to be done here, since it routes to visit_invocation_expression
    def visit_invocation_statement(self, invocation_statement: statement_ast.InvocationStatement):
        callee=invocation_statement.expression.accept(self)
        return self._node("Invocation",callee)

    def visit_println_statement(self, println_statement: statement_ast.PrintLnStatement):
        etype = self.type_of_expr(println_statement.expression)
        if etype != "int":
            self.report_error(f"Expected integer argument for print statement, got '{etype}'",println_statement.linenum)
        expr = println_statement.expression.accept(self)
        return self._node("Print endl",self._node("Expression",expr))

    def visit_print_statement(self, print_statement: statement_ast.PrintStatement):
        etype=self.type_of_expr(print_statement.expression)
        if etype != "int":
            self.report_error(f"Expected integer argument for print statement, got'{etype}'",print_statement.linenum)
        expr = print_statement.expression.accept(self)
        return self._node("Print",self._node("Expression",expr))
        
    def visit_return_empty_statement(self, return_empty_statement: statement_ast.ReturnEmptyStatement):
        return self._node("Return")

    def visit_return_statement(self, return_statement: statement_ast.ReturnStatement):
        expr = None
        if (hasattr(return_statement,"expression")) and return_statement.expression is not None:
            expr = getattr(return_statement,"expression").accept(self)
        label=f"Return"
        return self._node(label,expr)

    def visit_expression(self, expression: expression_ast.Expression):
        pass

    def visit_dot_expression(self, dot_expression: expression_ast.DotExpression): 
        left = dot_expression.left.accept(self)
        name = dot_expression.id.accept(self)
        namelabel = self._cleanname(self._getlabel(name))
      #  print(f"in visit dot expression for {namelabel} at {dot_expression.linenum}")
        return self._node(f"Dot field={namelabel}",left)
      
    def visit_false_expression(self, false_expression: expression_ast.FalseExpression):
        return self._node("false")

    def visit_true_expression(self, true_expression: expression_ast.TrueExpression):
        return self._node("true")

    def visit_identifier_expression(self, identifier_expression: expression_ast.IdentifierExpression):
        name = getattr(identifier_expression,"id")
        return self._node(f"Id {name}")

    def visit_new_expression(self, new_expression: expression_ast.NewExpression):
        name = new_expression.id.accept(self)
        return self._node(f"new",name)

    def visit_null_expression(self, null_expression: expression_ast.NullExpression):
        return self._node("null")

    def visit_read_expression(self, read_expression: expression_ast.ReadExpression):
        return self._node("read")
    
    def visit_integer_expression(self, integer_expression: expression_ast.IntegerExpression):
        return self._node(f"{integer_expression.value}")

    def visit_invocation_expression(self, expr: expression_ast.InvocationExpression):
        name = self._cleanname(self._getlabel(expr.name.accept(self)))
        callee=name
        args=expr.arguments
        if callee not in self.functions:
            self.report_error(f"Call to unknown function '{callee}'",expr.linenum)
        else:
            calleefunc = self.functions[callee]
            caller_linenum = self.functions[self.current_fun]["line"]
            callee_linenum=calleefunc["line"]
            if callee_linenum>caller_linenum: #the function being called is declared AFTER the function calling it. so it shouldn't have access
                self.report_error(f"Call to unknown function '{callee}'",expr.linenum)
            
            numparams=len(calleefunc["params"])
            numargs=len(args)
            if numparams != numargs:
                self.report_error(f"Expected {numparams} positional arguments and got {numargs} for fun '{callee}'",expr.linenum)
            elif numparams==1 and numargs==1:
                typeofarg=self.type_of_expr(args[0])
                typeofparam=calleefunc["params"][0]
                if typeofparam.split(" ")[0] == "struct": #if the param is asking for a struct, we will allow 'null' to be passed in
                    if typeofarg!=typeofparam and typeofarg!="null":
                        self.report_error(f"Unexpected argument in call to fun '{callee}'. expected {typeofparam}, found {typeofarg}",expr.linenum)
                elif typeofparam != typeofarg:
                    self.report_error(f"Unexpected argument in call to fun '{callee}'. expected {typeofparam}, found {typeofarg}",expr.linenum)
            else:
                for i in range(0,numparams):
                    p = calleefunc["params"][i]
                    a = args[i]
                    typeofarg=self.type_of_expr(a)
                    if p.split(" ")[0]=="struct":
                        #allowed: typeofarg==p OR typeofarg=="null". not allowed: typeofarg!=p AND typeofarg!=null
                        if typeofarg!=p and typeofarg!="null":
                            self.report_error(f"Unexpected argument [{i}] in call to fun '{callee}'. expected {p}, found {typeofarg}",expr.linenum)
                    elif typeofarg != p:
                        self.report_error(f"Unexpected argument [{i}] in call to fun '{callee}'. expected {p}, found {typeofarg}",expr.linenum)
                    
   
        arguments = []
        for arg in expr.arguments:
            arguments.append(arg.accept(self))
     #   args = invocation_expression.arguments.accept(self)
        return self._node(f"call {name}",self._node("Args",arguments))

    
    def visit_unary_expression(self, unary_expression: expression_ast.UnaryExpression):
        op=self._op_to_text(unary_expression.operator)
        operand=unary_expression.operand.accept(self)
        return self._node(f"Op {op}",operand)

    def visit_binary_expression(self, e: expression_ast.BinaryExpression):
       # print(f"on linenum {e.linenum}")
        '''it is possible that i will do the type_of_expr calls and stuff in other places. so if i have time i should come back and
            move the error messages into type_of_expr, and call type_of_expr here rather than doing the checking and error reporting here (for consistency)'''
        equalityops=['==','!='] #these require require operands of integer or structure type. The operands must have matching type. Structs can be null.
        arithops=['+','-','*','/']    #these require integers only. 
        relationalops=['<','>','<=','>='] #these require integers only
        booleanops=['||','&&'] #these require boolean only
        op=self._op_to_text(e.operator)
        left=e.left
        right=e.right
        lt = self.type_of_expr(left)
        rt=self.type_of_expr(right)
       # print(f"BINARY EXPR: type of left is {lt}.  type of right is {rt}. op is {op}")
        
        if lt is not None and rt is not None: #if either was not defined, type_of_expr() would have already reported the error
            if op in arithops or op in relationalops:
                if lt != "int":
                    self.report_error(f"Cannot perform operation '{op}' with operand of type {lt}",e.linenum)
                if rt != "int":
                    self.report_error(f"Cannot perform operation '{op}' with operand of type {rt}",e.linenum)
            if op in booleanops:
                 if lt != "bool":
                    self.report_error(f"Cannot perform operation '{op}' with operand of type {lt}",e.linenum)
                 if rt != "bool":
                    self.report_error(f"Cannot perform operation '{op}' with operand of type {rt}",e.linenum)
            if op in equalityops:
                if lt != rt:
                    self.report_error(f"Cannot perform operation '{op}' with mismatching types: '{lt}' and '{rt}'",e.linenum)
                elif lt==rt:
                    words=lt.split()
                    if words[0]!="struct" and lt!="int":
                        self.report_error(f"Cannot perform equality operation with type {lt}",e.linenum)
      
        l=left.accept(self)
        r=right.accept(self)
        return self._node(f"Op {op}",l,r)
 
    def visit_lvalue(self, lvalue: lvalue_ast.LValue):
        pass
        
    def visit_lvalue_dot(self, lvalue_dot: lvalue_ast.LValueDot):
        left = lvalue_dot.left.accept(self) #an lvalue?
        field = lvalue_dot.id.accept(self)
        fieldlabel = self._cleanname(self._getlabel(field))
        return self._node(f"LValueDot field={fieldlabel}", left)

    def visit_lvalue_id(self, lvalue_id: lvalue_ast.LValueID):
        name = lvalue_id.id.accept(self)
        namelabel = self._cleanname(self._getlabel(name))
        return self._node(f"LValueID " + namelabel)
    
    '''  def make_tree(self, program: program_ast.Program):
        #run the visitor to get the 'label',children tree, that can be passed into the render_graphviz function.
        #calling types, decls, funcs since they are the three top level nodes after 'program'.
        types = [t.accept(self) for t in getattr(program, "types", [])]
        decls = [d.accept(self) for d in getattr(program, "declarations", [])]
        funcs = [f.accept(self) for f in getattr(program, "functions", [])]
        return self._node("Program",
                          self._node("Types", types),
                          self._node("Top Level Decls", decls),
                          self._node("Functions", funcs))'''


    def render_graphviz(self, program, outfile="mini_ast", fmt="png"):
    
        root = self._ensure_tree(program)  

        node_defaults = {
            "shape": "box",
            "style": "rounded,filled",
            "fontname": "Courier",
            "fontsize": "10",
            "color": "#424242",
            "fillcolor": "#FFFFFF",
            "penwidth": "1.0",
        }
        edge_defaults = {
            "color": "#757575",
            "arrowsize": "0.7",
        }

        KIND_STYLE = {
            "structural": {"fillcolor": "#F5F5F5", "shape": "box"},
            "type":       {"fillcolor": "#E3F2FD", "shape": "box"},
            "operator":   {"fillcolor": "#FFE0B2", "shape": "diamond"},
            "identifier": {"fillcolor": "#E8F5E9", "shape": "ellipse"},
            "literal":    {"fillcolor": "#FFF8E1", "shape": "ellipse"},
            "lvalue":     {"fillcolor": "#F3E5F5", "shape": "ellipse"},
            "decl":       {"fillcolor":"#f3e5f5","shape":"ellipse"},
            "lvalue-dot": {"fillcolor":"#ffe0b2","shape":"ellipse"}
        }

        def kind_from_label(label: str) -> str:
            s = label.strip()
            if s in {"int", "bool", "void", "null", "true", "false", "read", "new"}:
                return "literal"
            if re.fullmatch(r"\d+", s):
                return "literal"

            if s.startswith("Id "):
                return "identifier"
            if s.startswith("LValueID") :
                return "lvalue"
            if s.startswith("LValueDot"):
                return "lvalue-dot"

            if s.startswith("Op "):
                return "operator"
            if s.startswith("Dot "):
                return "operator"

            if s.startswith("struct "):
                return "type"
            
            if s.startswith("Decl"):
                return "decl"

            if s in {
                "Program", "Types", "Top Level Decls", "Functions",
                "Params", "Locals", "Body", "Return", "Return Type",
                "Assign", "Target", "Source", "Print", "Print endl",
                "Invocation", "Args", "While", "Branch", "then-body",
                "else-body", "Block"
            }:
                return "structural"
            if  s.startswith("fun ") or s.startswith("Struct "):
                return "structural"

            return "structural"

        dot = Digraph("mini_ast", format=fmt)
        dot.node_attr.update(node_defaults)
        dot.edge_attr.update(edge_defaults)

        counter = 0
        def add(node):
            nonlocal counter
            label, kids = node
            nid = f"n{counter}"; counter += 1

            k = kind_from_label(str(label))
            attrs = dict(node_defaults)
            attrs.update(KIND_STYLE.get(k, {}))

            dot.node(nid, label=str(label), **attrs)

            for ch in kids:
                cid = add(ch)
                dot.edge(nid, cid)
            return nid

        add(root)
        return dot.render(outfile, cleanup=True)


    def _coerce_scalar(self, v):
        if isinstance(v, set):
            return next(iter(v)) if v else None
        return v
    
    def convert_to_dataframe(self):
        structsdf=pd.DataFrame(
            [{"name":n,"line":v["line"],"num_fields":len(v["fields"])} for n,v in self.structs.items()]
        ).sort_values(["name"]).reset_index(drop=True)
        
        df_struct_fields = pd.DataFrame(
            [{"struct": n, "field": fname, "type": ftype}
             for n, v in self.structs.items()
             for fname, ftype in v["fields"].items()]
        ).sort_values(["struct", "field"]).reset_index(drop=True)

        df_funcs = pd.DataFrame(
            [{"name": n, "line": v["line"],
              "params": ", ".join(v["params"]), "ret": v["return"]}
             for n, v in self.functions.items()]
        ).sort_values(["name"]).reset_index(drop=True)

        df_globals = pd.DataFrame(
            [{"name": n, "line": v["line"], "type": v["type"]}
             for n, v in self.globals.items()]
        ).sort_values(["name"]).reset_index(drop=True)
        
        rows = []
        for fun, table in self.vars.items():
            for name, meta in table.items():
                rows.append({
                    "function": fun,
                    "name": name,
                    "type": meta.get("type"),
                    "kind": meta.get("kind", ""),
                    "line": meta.get("line"),
                })
        df_locals = pd.DataFrame(rows, columns=["function", "name", "type", "kind", "line"])
        if not df_locals.empty:
            df_locals = df_locals.sort_values(["function", "name"]).reset_index(drop=True)

        return structsdf, df_struct_fields, df_funcs, df_globals,df_locals

    def print_tables(self):
        titles=["Structs","Struct Fields","Functions","Globals","Locals"]
        for title, df in zip(titles,self.convert_to_dataframe()):
            print(f"\n{title}")
            if df.empty:print("(none)")
            else:
               # print(df.to_string(index=False))  
                print(df.to_markdown(index=False))  # needs tabulate >=0.8.7
        print("\n")

   
        


    
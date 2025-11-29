'''does ast traversal and produces JSON representation'''

from miniast import mini_ast, program_ast, type_ast, statement_ast, expression_ast, lvalue_ast

class ASTtoJSON(mini_ast.ASTVisitor):
    
    def _getlabel(self,possibletuple):
        if isinstance(possibletuple,tuple):
            return possibletuple[0]
        else:
            return str(possibletuple)
    
    def _cleanname(self,name):
        return name.replace("Id","",1)

    def line(self,node):
        return getattr(node, "linennum",None)
    
    def _op_to_text(self, op):
        try:
            return op.value 
        except AttributeError:
            return str(op)
    
    def _id_text(self,id_node):
        return getattr(id_node,"id",None) if id_node else None
    
    def visit_program(self,program:program_ast.Program):
        types=[]
        decls=[]
        funcs=[]
        for t in getattr(program,"types",[]):
            types.append(t.accept(self))
        for d in getattr(program,"declarations",[]):
            decls.append(d.accept(self))
        for f in getattr(program,"functions",[]):
            funcs.append(f.accept(self))
        
        return{
            "node":"Program",
            "types":types,
            "declarations":decls,
            "functions":funcs
        }
    
    def visit_declaration(self,declaration:program_ast.Declaration):
        thetype=declaration.type.accept(self)       #the type, like 'int'
        name = declaration.name.accept(self)
        typelabel=self._getlabel(thetype)
        namelabel=self._cleanname(self._getlabel(name))
        return{
            "node":"Decl",
            "line":self.line(declaration),
            "name": self._id_text(declaration.name)  ,    
            "type":thetype
        }

    
    def visit_type_declaration(self, type_declaration: program_ast.TypeDeclaration):
        name = type_declaration.name.accept(self)
        namelabel=self._cleanname(self._getlabel(name))
        fields=[]
        for f in getattr(type_declaration,"fields",[]):
            fields.append(f.accept(self))
        
        return{
            "node":"TypeDecl",
            "line":self.line(type_declaration),
             "name": self._id_text(type_declaration.name),
            "fields":fields
        }
        
    def visit_function(self, function: program_ast.Function):
        name=self._cleanname(self._getlabel(function.name.accept(self)))
        retnode=function.ret_type.accept(self)
        params=[]
        localvars=[]
        body=[]
        for p in getattr(function,"params",[]):
            params.append(p.accept(self))
        for l in getattr(function,"locals",[]):
            localvars.append(l.accept(self))
        for s in getattr(function,"body",[]):
            body.append(s.accept(self))
        return{
            "node":"Function",
            "line":self.line(function),
            "name":self._id_text(function.name),
            "params":params,
            "locals":localvars,
            "return type":retnode,
            "body":body
        }
    
    def visit_type(self, type_: type_ast.Type): #leave blank on purpose?
        return {"node": "Type", "kind": "unknown"}


    def visit_int_type(self, int_type: type_ast.IntType):
        return{
            "node":"Type",
            "type":"int"
        }      
    def visit_bool_type(self, bool_type: type_ast.BoolType):
                return{
            "node":"Type",
            "type":"bool"
        }

    def visit_struct_type(self, struct_type: type_ast.StructType):
        name = self._cleanname(self._getlabel(struct_type.name.accept(self)))
        return{
            "node":"Type",
            "type":"struct",
            "name":self._id_text(struct_type.name)
        }
    
    def visit_return_type_real(self, return_type_real: type_ast.ReturnTypeReal): #NOT SURE AB THIS ONE
        inner = getattr(return_type_real,"type",None)
        if inner is not None:
            return inner.accept(self)
        return inner.type.accept(self)
            
    def visit_return_type_void(self, return_type_void) -> mini_ast.Any:
        return {"node":"Type","kind":"void"}

    def visit_statement(self, statement: statement_ast.Statement): #leave blank on purpose?
        return{"node":"Statement"}
        
    def visit_assignment_statement(self, assignment_statement: statement_ast.AssignmentStatement):
        target = getattr(assignment_statement,"target",[]).accept(self) #this is an LVALUE
        source = getattr(assignment_statement,"source",[]).accept(self) #this is an EXPRESSIOn
        return{
            "node":"Assign",
            "line":self.line(assignment_statement),
            "target":target,
            "source":source
        }

    def visit_block_statement(self, block_statement: statement_ast.BlockStatement):
        stmnts=[]
        for s in block_statement.statements:
            stmnts.append(s.accept(self))
        return{
            "node":"Block",
            "line":self.line(block_statement),
            "statements":stmnts
        }

    def visit_conditional_statement(self, conditional_statement: statement_ast.ConditionalStatement):
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
        return{
            "node":"If/Branch",
            "line":self.line(conditional_statement),
            "condition":name,
            "then-body":thenblockstmts,
            "else-body":elseblocksmts 
        }

    def visit_while_statement(self, while_statement: statement_ast.WhileStatement):
        cond = while_statement.guard.accept(self)
        body = while_statement.body.accept(self)
        return{
            "node":"While",
            "line":self.line(while_statement),
            "condition":cond,
            "body":body
        }

    def visit_delete_statement(self, delete_statement: statement_ast.DeleteStatement):
        expr = delete_statement.expression.accept(self)
        return{
            "node":"Delete",
            "line":self.line(delete_statement),
            "expression":expr
        }

    def visit_invocation_statement(self, invocation_statement: statement_ast.InvocationStatement):
        callee=invocation_statement.expression.accept(self)
        return{
            "node":"Invocation/CallSmt",
            "line":self.line(invocation_statement),
            "callee":callee
        }

    def visit_println_statement(self, println_statement: statement_ast.PrintLnStatement):
        expr = println_statement.expression.accept(self)
        return{
            "node":"Print endl",
            "line":self.line(println_statement),
            "expression":expr
        }

    def visit_print_statement(self, print_statement: statement_ast.PrintStatement):
        expr = print_statement.expression.accept(self)
        return{
            "node":"Print",
            "line":self.line(print_statement),
            "expression":expr
        }
        
    def visit_return_empty_statement(self, return_empty_statement: statement_ast.ReturnEmptyStatement):
        return{
            "node":"Return",
            "line":self.line(return_empty_statement),
            "expression":None
        }

    def visit_return_statement(self, return_statement: statement_ast.ReturnStatement):
        expr = None
        if (hasattr(return_statement,"expression")) and return_statement.expression is not None:
            expr = getattr(return_statement,"expression").accept(self)
        label=f"Return"
        return{
            "node":"Return",
            "line":self.line(return_statement),
            "expression":expr
        }

    def visit_expression(self, expression: expression_ast.Expression):
        return{"node":"Expression"}

    def visit_dot_expression(self, dot_expression: expression_ast.DotExpression):
        left = dot_expression.left.accept(self)
        name = dot_expression.id.accept(self)
        namelabel = self._cleanname(self._getlabel(name))
        return{
            "node":"Dot",
            "line":self.line(dot_expression),
            "left expression":left,
            "field":self._id_text(dot_expression.id)
        }
      
    def visit_false_expression(self, false_expression: expression_ast.FalseExpression):
        return{
            "node":"False",
            "line":self.line(false_expression)
        }

    def visit_true_expression(self, true_expression: expression_ast.TrueExpression):
        return{
            "node":"True",
            "line":self.line(true_expression)
        }

    def visit_identifier_expression(self, identifier_expression: expression_ast.IdentifierExpression):
        name = getattr(identifier_expression,"id")
        return{
            "node":"Id",
            "line":self.line(identifier_expression),
            "name":name
            }
        
    def visit_new_expression(self, new_expression: expression_ast.NewExpression): #NOT SURE AB THIS ONE
        name = new_expression.id.accept(self)
        return{
            "node":"New",
            "line":self.line(new_expression),
            "type":name
        }

    def visit_null_expression(self, null_expression: expression_ast.NullExpression):
        return{
            "node":"Null",
            "line":self.line(null_expression)
        }

    def visit_read_expression(self, read_expression: expression_ast.ReadExpression):
        return{
            "node":"Read",
            "line":self.line(read_expression)
        }
    
    def visit_integer_expression(self, integer_expression: expression_ast.IntegerExpression):
        return{
            "node":"Int",
            "line":self.line(integer_expression),
            "value":integer_expression.value
        }
       

    def visit_invocation_expression(self, invocation_expression: expression_ast.InvocationExpression):
        name = self._cleanname(self._getlabel(invocation_expression.name.accept(self)))
        args = []
        for arg in invocation_expression.arguments:
            args.append(arg.accept(self))
     #   args = invocation_expression.arguments.accept(self)
        return{
            "node":"Invocation/CallExpr",
            "line":self.line(invocation_expression),
            "name":self._id_text(invocation_expression.name),
            "args":args
        }

    def visit_unary_expression(self, unary_expression: expression_ast.UnaryExpression):
        op=self._op_to_text(unary_expression.operator)
        operand=unary_expression.operand.accept(self)
        return{
            "node":"Unary",
            "line":self.line(unary_expression),
            "Op":op,
            "expression":operand
        }

    def visit_binary_expression(self, binary_expression: expression_ast.BinaryExpression):
        op=self._op_to_text(binary_expression.operator)
        left = binary_expression.left.accept(self)
        right = binary_expression.right.accept(self)
        return{
            "node":"Binary",
            "line":self.line(binary_expression),
            "Op":op,
            "left expression":left,
            "right expression":right
        }
 
    def visit_lvalue(self, lvalue: lvalue_ast.LValue):
        return{"node":"Lvalue"}
        
    def visit_lvalue_dot(self, lvalue_dot: lvalue_ast.LValueDot):
        left = lvalue_dot.left.accept(self) #an lvalue?
        field = lvalue_dot.id.accept(self)
        fieldlabel = self._cleanname(self._getlabel(field))
        return{"node":"LValueDot",
               "line":self.line(lvalue_dot),
               "field":self._id_text(lvalue_dot.id),
               "left expression":left
               }

    def visit_lvalue_id(self, lvalue_id: lvalue_ast.LValueID):
        name = lvalue_id.id.accept(self)
        namelabel = self._cleanname(self._getlabel(name))
        return{"node":"LValueId",
               "line":self.line(lvalue_id),
               "name":self._id_text(lvalue_id.id)
               }

from miniast import mini_ast, program_ast, type_ast, statement_ast, expression_ast, lvalue_ast
from ir.helpers import GlobalsFrame,Frame,StructLayout
from ir.emitter import Emitter
from ir.ir_module import ModuleIR, FunctionIR, ProcedureIR, write_module

#next: implement printing and reading to make it easier to test everything
#then, try nested function calls
#then, think about blocks and loop

NEWLINE_ASCII='0x0A'
SPACE_ASCII='0x20'

END_PROCS_PATH=r"./ir/asm_chunks/end_procs.txt"
STORE_INPUT_PATH_PATH=r"./ir/asm_chunks/store_input_path.txt"
#/Users/avikumar/Desktop/fall-2025/COMP 520/milestones/ir/end_procs.txt

class CodeGenerator(mini_ast.ASTVisitor):
    def __init__(self,structs,funcs,glbls,variables,filename):
        self.structs=structs
        self.funcs=funcs
        self.globals=glbls 
        self.vars=variables
        self.globalsFrame=GlobalsFrame(self.structs,self.globals)
        self.em=None
        self.frames={}
        self.struct_layouts={}
        filestem=filename.split(".")[0]
        self.output_file=f"{filestem}-first-pass.s"
        self.oplines=[]
        self.globals_map = self.globalsFrame.globals_map
        self.frame=None         #the Frame object for the currently active frame
        self._label_n  = 0
        self.proc_label_counter=0
        self.if_counter=0
        self.loop_counter=0
        self.read_needed=False
        self.module=None
        
        for f in self.funcs:
            frame=Frame(variables=self.vars,fname=f)
            self.frames[f]=(frame)
        for s in self.structs:
            stlayout=StructLayout(self.structs[s],s)
            self.struct_layouts[s]=stlayout
            
        
    def fresh_label(self,prefix="L"):
        self._label_n+=1
        return f"{prefix}{self._label_n}"
    
    def load_global(self,name):
        tcurr=self.frame.new_temp()
        tcurr1=self.frame.new_temp()
        lines=[]
        self.em.emit(f"la {tcurr} {name}")
        self.em.emit(f"lw {tcurr1} 0({tcurr})")     #now, the value of the global variable is stored in register tcurr1. 
        return tcurr1   #returns reg where global has been loaded
    
    def store_global(self,name,reg):
        tcurr=self.frame.new_temp()
        self.em.emit(f"la {tcurr} {name}")
        self.em.emit(f"sw {reg} 0({tcurr})")
    
    def is_var_local(self,name):
        if name not in self.frame.register_map and name in self.globals_map:
            return False
        else:
            return True

    def get_struct_type(self,struct_name):
         if self.is_var_local(struct_name):
             fname=self.frame.fname
             ans=self.vars[fname][struct_name]["type"]
             ans=ans.split(" ")[1]
         #(f"type is {ans}")
             return ans
         else:
             ans=self.globals_map[struct_name]["Type"]
             if len(ans.split(" "))>1:
                 ans=ans.split(" ")[1]
         #    print(f"type is {ans}")
             return ans

    def op_to_text(self, op):
        try:
            return op.value 
        except AttributeError:
            return str(op)

    def check_for_immediates(self, expr):   
        '''checks if the passed in Expression is an Integer, False, or True expression. if so, returns the value of the expression.
            if not, returns None.
        '''
        if isinstance(expr,expression_ast.IntegerExpression):
            ans=expr.value
            return ans
        elif isinstance(expr,expression_ast.TrueExpression):
            return 1
        elif isinstance(expr,expression_ast.FalseExpression):
            return 0
        else:
            return None
    
    def emit_precall(self):
        num_to_decrement=self.frame.num_locals*4 #...say that it is 20, bc 5 locals *4=20
        num_to_decrement=num_to_decrement+4 #bc saving ra...so now 24
        self.em.emit(f"addi sp sp -{num_to_decrement}") #sp = sp-24
        self.em.emit(f"sw ra 0(sp)")
        for local in self.frame.register_map:
            local_reg=self.frame.register_map[local]
            local_offset=self.frame.local_offset[local] * -1
            line=f"sw {local_reg} {local_offset}(sp)"
            self.em.emit(line)

    def emit_precall_new(self): #in the new one, not concerned ab saving locals. just ra
        num_to_decrement=4 #...say that it is 20, bc 5 locals *4=20
        self.em.emit(f"addi sp sp -{num_to_decrement}") #sp = sp-24
        self.em.emit(f"sw ra 0(sp)")
    
    def emit_postreturn_new(self):
        num_to_decrement=4 #...say that it is 20, bc 5 locals *4=20
        self.em.emit(f"#start of postreturn")
        self.em.emit(f"lw ra 0(sp) ")
        self.em.emit(f"addi sp sp {num_to_decrement}")

    
    def emit_postreturn(self):
        num_to_decrement=self.frame.num_locals*4 #...say that it is 20, bc 5 locals *4=20
        num_to_decrement=num_to_decrement+4 #bc saving ra...so now 24
        self.em.emit(f"lw ra 0(sp)")
        for local in self.frame.register_map:
            local_reg=self.frame.register_map[local]
            local_offset=self.frame.local_offset[local]*-1
            line=f"lw {local_reg} {local_offset}(sp)"   #brings everything back into registers
            self.em.emit(line)
        self.em.emit(f"addi sp sp {num_to_decrement}")

        
    def visit_program(self, program: program_ast.Program):
        self.module=ModuleIR(setup_lines=self.setup_file())
        for f in program.functions:
            if f.name.id!="main":
                proc_ir=f.accept(self)
                self._attach_procedure(proc_ir)
        for f in program.functions:
            if f.name.id=="main":
                proc_ir=f.accept(self)
                self._attach_procedure(proc_ir)
        return self.module
                
    def visit_declaration(self, decl: program_ast.Declaration):
        pass
    def visit_type_declaration(self, type_declaration: program_ast.TypeDeclaration):
        pass

    def visit_function(self, function: program_ast.Function):
        self.em=Emitter()
        # carry label counters across procedures so labels stay globally unique
        self.em.if_block_label_counter=self.if_counter
        self.em.loop_label_counter=self.loop_counter
        fname=function.name.id
        self.frame=self.frames[fname]
        self.em.emit(f"{fname}:")
        if fname=="main":
            #add the standard code for reading in the filepath given as a command line argument:
            if self.read_needed:
                with open(STORE_INPUT_PATH_PATH,"r") as f:
                    cont=f.read()
                    for line in cont.split("\n"):
                        self.em.emit(line)
            sp_offset=self.frame.num_locals*4*-1
            self.em.emit(f"addi sp sp {sp_offset}")
            for var in self.frame.local_offset:
                self.em.emit(f"sw zero {self.frame.local_offset[var]}(sp) #this holds var {var}")
            self.em.emit(f"#start of body")

            for s in function.body:
                s.accept(self)
            self.em.emit(f"addi a0 zero 0")
            self.em.emit(f"jal zero exit")
            self.frame=None
            proc_ir=self._build_procedure_ir(fname,self.em.lines)
            self.if_counter=self.em.if_block_label_counter
            self.loop_counter=self.em.loop_label_counter
            return proc_ir
        else:
            #prologue
       #     print(f"adding prologue for {fname}")
            numtooffset=52+(4*self.frame.num_locals)
            self.em.emit("#start of prologue")
            self.em.emit(f"addi sp sp -{numtooffset} ") #-64
            for var in self.frame.local_offset:
                self.em.emit(f"sw zero {self.frame.local_offset[var]}(sp) #this holds var {var}") #0,4,8
            #next one, aka ra, will be at numlocals*4. cuz if there were 4 locals, they were placed at 0, 4,8,12. next is 4*4=16
            next_offset=self.frame.num_locals*4 #12
            self.em.emit(f"sw ra {next_offset}(sp)") #ra is at 12
            ctr=next_offset+4 #16
            for i in range(0,12):
                self.em.emit(f"sw s{i} {ctr}(sp)") #16, 20, 24, 28, 32, 36, 40, 44, 48, 52, 56, 60
                ctr+=4
            #currently, sp is at -64. 60(sp) holds s12. 12(sp) holds ra
            for p in function.params:
                pname=p.name.id
            for i in range(0,len(function.params)):
                param=function.params[i]
                pname=param.name.id
                reg_to_store_param=self.frame.register_map[pname]
                offset_to_store_param=self.frame.local_offset[pname]
                #self.em.emit(f"addi {reg_to_store_param} a{i} 0")
                self.em.emit(f"sw a{i} {offset_to_store_param}(sp) #storing param at offset instead of in reg")
            self.em.emit(f"#end of prologue")
            '''
            1. decrement sp by 13*4=52
            2. save ra. sw ra 0(sp)
            3. save s0-s11 onto the stack. x8,x9,x18-x27. for each:
                    sw s{x} 4(sp)
                    sw s{x1} 8(sp)
                    ...
            4. for each local that is a param (for i in frame.variables: frame.variables[i][kind]=="param"), 
                or alternatively, for each param arg, get its name. look it up and ensure that in frame.variables[argname][kind]="param".
                just for my own sanity.
                then, for each param, get its name. look it up in the register map to get the reg where it should be stored.
                then, for i in range (0,len(params)): addi {params_local_reg} a{i} 0...moving the params from a-registers to their assigned ones
            '''
            #body:
            self.em.emit(f"#start of body")
            for i in range(0,len(function.body)-1):
                s=function.body[i]
                s.accept(self)
            self.em.emit(f"#end of body")
            
            #epilogue:
                #return stmt:
            self.em.emit(f"#start of epilogue")
            num_stmts=len(function.body)
            ret_stmt=function.body[num_stmts-1]
            ret_reg=ret_stmt.accept(self) #wait, i think the storing of a0 in the LHS of assignment statement w invocation will be done
            #automatically, since i account for it in visit_return_statement and visit_invocation_expression
            destroy_locals_offset=self.frame.num_locals*4
            self.em.emit(f"addi sp sp {destroy_locals_offset}")
            self.em.emit(f"lw ra 0(sp)")
            ctr=4
            for i in range(0,12):
                self.em.emit(f"lw s{i} {ctr}(sp)")
                ctr+=4
            self.em.emit(f"addi sp sp 52")
            self.em.emit("ret")
            self.proc_label_counter+=1
            self.em.emit(f"#end of epilogue")
            #epilogue
            '''
            1. the return_statement/expression thingy's accept method will return the register where return val is stored. so, 
                if i dont already do it there, i should copy this value into a0
                    - check if the function is meant to return something. if so, it would have had visit_return_stmt
                    - if it doesnt return anything (void), dont have to load anything anywhere
            2. lw ra 0(sp)
            3. then, for each of s0-s11:
                lw s{x} 4(sp)
                lw s{x1} 8(sp)
                ...
            4. increment sp by 13*4=52
            5. ret
            '''

            self.frame=None
            proc_ir=self._build_procedure_ir(fname,self.em.lines)
            self.if_counter=self.em.if_block_label_counter
            self.loop_counter=self.em.loop_label_counter
            return proc_ir
        proc_ir=self._build_procedure_ir(fname,self.em.lines)
        self.if_counter=self.em.if_block_label_counter
        self.loop_counter=self.em.loop_label_counter
        return proc_ir


    def visit_type(self, type_: type_ast.Type):
        pass

    def visit_int_type(self, int_type: type_ast.IntType):
        pass

    def visit_bool_type(self, bool_type: type_ast.BoolType):
        pass

    def visit_struct_type(self, struct_type: type_ast.StructType):
        pass
    
    def visit_return_type_real(self, return_type_real: type_ast.ReturnTypeReal):
        pass
    
    def visit_return_type_void(self, return_type_void) -> mini_ast.Any:
        pass

    def visit_statement(self, statement: statement_ast.Statement):
        pass
        
    def visit_assignment_statement(self, s: statement_ast.AssignmentStatement):
        #IF IT IS A NEW!!!! we should, in the visit_new_expr, do the malloc. and return the register that contains the pointer that we want to store as p's value
        target=s.target
        source=s.source
        rhs_reg=source.accept(self)
        if isinstance(target,lvalue_ast.LValueID):
            tname=s.target.id.id
            #print(f"target is lvalueid: name={tname}")
            if tname not in self.frame.register_map and tname in self.globals_map:    #not in the local map. if it is in the local map, we default to referencing the local var's namespace
                self.store_global(name=tname,reg=rhs_reg)
            else:
                dst_offset=self.frame.local_offset[tname]
                dstreg=self.frame.register_map[tname]
              #  self.em.addi(dstreg,rhs_reg,"0x0")  
                self.em.emit(f"sw {rhs_reg} {dst_offset}(sp) #placing local's value in stack rather than reg")              
        else: #LValue Dot (structs)...implement later
            if isinstance(target,lvalue_ast.LValueDot):
                left=target.left
                name=target.id.id
                addr_reg=target.accept(self)   #returns reg that contains addr to write to. rhs_reg contains val we want to write
                self.em.emit(f"sw {rhs_reg} 0({addr_reg})")
                
           
            '''
            structname=target.left.id.id    #eg p
            structfield=target.id.id        #eg x
            structtype=""
            is_local=self.is_var_local(structname)
            if is_local:
                structtype=self.frame.types[structname]
                structtype=structtype.split(" ")[1]
            else:
                structtype=self.globals_map[structname]["Type"]
            print(f"name:{structname}. type: {structtype}. field:{structfield}") 
           # fieldoffset=self.struct_layouts[]
            if (self.is_var_local(structname)):       #we get the pointer from the register
                reg_w_struct_ptr=self.frame.register_map[structname]   #tells us which register holds the pointer to heap
                #now, add offset to this value. then, SW 'source' at 0(addr+offset)
                field_offset = self.struct_layouts[structtype].struct_fields[structfield]["offset"]
                print(f"offset for field {structfield} is {field_offset}")
                curr=self.frame.new_temp()
                self.em.emit(f"addi {curr} {reg_w_struct_ptr} {field_offset}")  #curr now holds pointer to where we want to store 'rhs_reg'
                self.em.emit(f"sw {rhs_reg} 0({curr})")
            '''   

    def visit_block_statement(self, block_statement: statement_ast.BlockStatement):
        
        pass

    def visit_conditional_statement(self, conditional_statement: statement_ast.ConditionalStatement):
        evaluated_condition_reg = conditional_statement.guard.accept(self) #name will store the register that holds the value of the evaluated expression
        #so i guess Rd[eval_cond_reg] will either be zero or one?? wait this makes this so much easier
        #all we have to do is check whether it is one or zero. "beq {eval_cond_reg} zero cont"...if it evaluated to zero aka false, then
        #we go to cont. if it was one, we can enter the if-
        thenblockcode = []
        thenblock = conditional_statement.then_block
        curr_num_lines=len(self.em.lines)
        for s in thenblock.statements:
            s.accept(self)
          # thenblockstmts.append(s.accept(self))
        new_num_lines=len(self.em.lines)
        thenblocklines=self.restore_emitter_lines(curr_num_lines,new_num_lines)
        
        elseblockstatements=conditional_statement.else_block.statements
        if elseblockstatements is None or len(elseblockstatements)==0: #aka just an if statement
            self.em.if_block(op1=evaluated_condition_reg,op2="zero",comp_inst="beq",ifblock=thenblocklines)
            return None
        else:
            currnumlines=len(self.em.lines)
            for s in elseblockstatements:
                s.accept(self)
            newnumlines=len(self.em.lines)
            #numtoremove=newnumlines-currnumlines
            elseblocklines=self.restore_emitter_lines(currnumlines,newnumlines)
            self.em.if_else_block(op1=evaluated_condition_reg,op2="zero",comp_inst="beq",ifblock=thenblocklines,elseblock=elseblocklines)
            return None

    def restore_emitter_lines(self,oldnumlines,newnumlines):
        ret=[]
        numtoremove=newnumlines-oldnumlines
        ret=self.em.lines[-numtoremove:]
        self.em.lines=self.em.lines[:-numtoremove]
        return ret

    def visit_while_statement(self, while_statement: statement_ast.WhileStatement):
        currlines=len(self.em.lines)
        eval_reg=while_statement.guard.accept(self)
        newlines=len(self.em.lines) 
        guard_lines=self.restore_emitter_lines(currlines,newlines)
        currlines=len(self.em.lines)
        whileblock=while_statement.body
        for stmt in whileblock.statements:
            stmt.accept(self)
        newlines=len(self.em.lines)
        whileblock_lines=self.restore_emitter_lines(currlines,newlines)
    #    print(f"block lines")
    #    for l2 in whileblock_lines:
    #        print(l2)
        self.em.while_block(eval_reg,guard_lines,whileblock_lines)
        pass

    def visit_delete_statement(self, delete_statement: statement_ast.DeleteStatement):
        #the statement will always ultimately evaluate to a variable of type struct. could be nested though. eg q.coords being a 'struct Pair'
        #accept the statement to load it into a register
        var_reg=delete_statement.expression.accept(self)
        self.em.emit(f"addi a0 {var_reg} 0 #start of precall")
        self.emit_precall_new()
        self.em.emit("jal free")
        self.emit_postreturn_new()
        return None

    def visit_invocation_statement(self, invocation_statement: statement_ast.InvocationStatement):
      #  print(f"in visit invocation stmt for {self.frame.fname}: {invocation_statement.expression.name.id}")
        expr=invocation_statement.expression
        expr.accept(self)
        #eg sub(x,y)

    #possible optimization: when i am simply trying to get a value specifically for placing into an argument register, eg before a proc call
    #then i can find some way to pass in the 'reg_to_store' as a parameter to the visit_assignment_statemnet, for example.
    #so that, instead of storing the evaluated result, in this case the number that the user wants to print, in a wasted reg before moving it to a0, i can just store
    #it directly in a0
    #alternatively....i think simple local register allocation would probably be able to fix this tbh. 
    def visit_println_statement(self, println_statement: statement_ast.PrintLnStatement):
        immtoprint=self.check_for_immediates(println_statement.expression)
        if immtoprint is not None:
            self.em.emit(f"addi a0 zero {immtoprint}")
        else:
            expr_reg = println_statement.expression.accept(self)
            self.em.emit(f"addi a0 {expr_reg} 0")
        self.em.emit(f"jal print_int")
        self.em.emit(f"li a0 {NEWLINE_ASCII}")
        self.em.emit(f"jal print_char")
        return None

    def visit_print_statement(self, print_statement: statement_ast.PrintStatement):
        immtoprint=self.check_for_immediates(print_statement.expression)
        if immtoprint is not None:
            self.em.emit(f"addi a0 zero {immtoprint}")
        else:
            expr_reg = print_statement.expression.accept(self)
            self.em.emit(f"addi a0 {expr_reg} 0")
        self.em.emit(f"jal print_int")
        self.em.emit(f"li a0 {SPACE_ASCII}")
        self.em.emit(f"jal print_char")
        return None
       

    def visit_return_empty_statement(self, return_empty_statement: statement_ast.ReturnEmptyStatement):
        return None #nothing stored in a reg so

    def visit_return_statement(self, return_statement: statement_ast.ReturnStatement):
        fname=self.frame.fname
        if fname!="main":
       #    print(f"calling visit return statement for {return_statement.expression}")
            expr_reg=return_statement.expression.accept(self)
       #     print(f"expr reg is {expr_reg}")
            self.em.emit(f"addi a0 {expr_reg} 0")
            return "a0"
        elif fname=="main":
            return None
        

    def visit_expression(self, expression: expression_ast.Expression):
        pass
    '''
    so as long as {left} is a dotExpression, we want to keep recursing to find the root. when {left} is an IdentifierExpression, we have found the root variable.
at that point, we also know the type from get_struct_type. now, we can search our STs to find a)where the var is located. then, when left is identifier expr, 
we look up ST to find out the offset at which {name} resides in struct {left}. add this to the address stored for {left}'s pointer. then, lw at this address.
the value that we load in, is the address/pointer stored for 'coords'. return this address. go up a level. 
    '''
    
    #returns the register that holds the ADDRESS representing the base address of the left side of a dot expression (aka the struct whose field is being referenced)
    #for dot expression nodes, this can be used by adding the field's offset, and loading in the value at that address.
    #for lvalue dot nodes, this can be used by adding the field's offset, and using this computed address as the destination for sw
    def compute_dot_expr_addr(self,expr):   #q.coords.x .......  now q.coords ...... now q!
        if isinstance(expr,expression_ast.DotExpression) or isinstance(expr,lvalue_ast.LValueDot):
            left=expr.left  #left=q.coords .........  now q
            name=expr.id.id #right=x    ............  now coords
         #   print(f"in compute, found dot expr: left={left} and name={name}")
            left_base_addr,left_type=self.compute_dot_expr_addr(left) #gives us reg storing base address of {left}. and struct type of {left}
            left_stlayout=self.struct_layouts[left_type]
            field_offset=left_stlayout.field_offsets[name]  #offset of field {right} for struct {left}
            field_type=left_stlayout.field_types[name]
            words=field_type.split(" ")
            if len(words)>1:
                field_type=words[1]
            #add field_offset to value at base_reg to get pointer to q.coords
            curr=self.frame.new_temp()
            self.em.emit(f"addi {curr} {left_base_addr} {field_offset}")  #curr now holds pointer to q.coords
            curr1=self.frame.new_temp()
            self.em.emit(f"lw {curr1} 0({curr})") #curr1 now holds base address of the entire q.coords.x??
            return curr1,field_type
 
        elif isinstance(expr,expression_ast.IdentifierExpression):   #now q.
            #    print(f"in compute, found identifier expr: {expr.id}")
                #we know the name of the struct variable. if we know what register holds q, we have the base pointer. so find that out
                #we know the type of the struct. if we know what offset the {name} is placed at, we can add that to the base pointer. so find that out
                base_name=expr.id
                base_type=self.get_struct_type(base_name)
                base_reg=None
               
                if self.is_var_local(base_name):
                   base_reg=self.frame.new_temp()
                   # base_reg=self.frame.register_map[base_name]
                   local_offset=self.frame.local_offset[base_name]
                   self.em.emit(f"lw {base_reg} {local_offset}(sp)")
                    
                else:   #eg global variable
                    base_reg=self.load_global(base_name)
                return base_reg,base_type
            
        elif isinstance(expr,lvalue_ast.LValueID):
            base_name=expr.id.id
        #    print(f"in compute, found lvalue id expr: {base_name}")
            base_type=self.get_struct_type(base_name)
            base_reg=None
            if self.is_var_local(base_name):
                base_reg=self.frame.new_temp()
                local_offset=self.frame.local_offset[base_name]
                self.em.emit(f"lw {base_reg} {local_offset}(sp)")
               # base_reg=self.frame.register_map[base_name]
            else:   #eg global variable
                base_reg=self.load_global(base_name)
            return base_reg,base_type
        else:
            print(f"in compute, found type which is none of the above")
               
    
    def visit_dot_expression(self, expr: expression_ast.DotExpression):    #q.coords.x    
        left = expr.left    #q.coords
        name = expr.id.id   #q.x
   #     print(f"entered visit_dot_expression for left={left} and name={name}. \n")
        base_ptr,base_type=self.compute_dot_expr_addr(expr.left)   #for q.coords.x, this would return reg holding pointer to base of 'coords'??
        #base_ptr: register that holds value x, where x=the base pointer to the struct that has {name} as a field. 
                                                # aka in q.coords.x, x=base ptr to the instance of 'coords'. numerical value of address where this
                                                #Pair struct instance is existing in memory
        
        #next: get value of offset from struct {left} to field {name}. base_type=the struct type
        stlayout=self.struct_layouts[base_type]
        field_offset=stlayout.field_offsets[name]
        curr=self.frame.new_temp()
        self.em.emit(f"addi {curr} {base_ptr} {field_offset}") #now, curr=pointer to the entire dot expression. e.g. pointer to q.coords.x
        self.em.emit(f"lw {curr} 0({curr})")        #now, curr = value
        return curr
        
        

    def visit_false_expression(self, expr: expression_ast.FalseExpression):
        curr=self.frame.new_temp()
        #self.em.li(curr,"0x0")
        self.em.emit(f"li {curr} 0x0")
        return curr      

    def visit_true_expression(self, expr: expression_ast.TrueExpression):
        curr=self.frame.new_temp()
        self.em.emit(f"li {curr} 0x1")
        return curr

    def visit_identifier_expression(self, expr: expression_ast.IdentifierExpression):
        curr=self.frame.new_temp()
    #    print(f"in identifier expression for {expr.id}. rn next temp is {curr}")
        srcid=expr.id
        if srcid in self.frame.register_map:
            srcreg = self.frame.register_map[srcid]
            src_offset=self.frame.local_offset[srcid]
            self.em.emit(f"lw {curr} {src_offset}(sp)")
            #print(f"adding addi for dstreg={curr},rhsreg={srcreg}")
            #self.em.emit(f"addi {curr} {srcreg} 0x0") #its possible that this step is not necessary. need t go back and think about it
            #return curr
            #attempting to return just the srcreg straight up itself, instead of a new temp that loads in its value. thus commenting out the
            # self.em.emit above. we will see if this breaks it:
            return curr
            #return srcreg
        elif srcid in self.globals_map:
            globalreg=self.load_global(srcid)   #returns reg where global was loaded. in this case setting x=g where g is a global
            return globalreg


    def visit_new_expression(self, expr: expression_ast.NewExpression):
        type1=expr.id.id
        size=self.struct_layouts[type1].size
        self.em.emit(f"li a0 {size}")   #a0 holds amount of bytes to allocate
        self.em.emit(f"jal malloc")
            #now, store returned value for p
        return "a0"

    def visit_null_expression(self, expr: expression_ast.NullExpression): #just going to set whatever was set to null to 0. i think idk
        curr=self.frame.new_temp()
        val=0
        self.em.emit(f"li {curr} {val}")
        return curr

    def visit_read_expression(self, expr: expression_ast.ReadExpression):
        self.read_needed=True
        self.em.emit(f"lw a0 filepath_ptr #start of precall")
        self.emit_precall_new()
        self.em.emit("jal ra read_int")
        self.emit_postreturn_new()
        self.em.emit("bne a1 zero read_err1")
        self.proc_label_counter+=1
        return "a0"
    

    def visit_integer_expression(self, expr: expression_ast.IntegerExpression):
        curr=self.frame.new_temp()
        val=expr.value
        self.em.emit(f"li {curr} {val}")
        return curr


    def visit_invocation_expression(self, expr: expression_ast.InvocationExpression): #here, we must return the register where the return value is stored
        args=expr.arguments
        arguments=[]
        for arg in args:
        #   print(f"calling accept for {arg}")
            arguments.append(arg.accept(self))  #for each arg, the reg where it is stored is in arguments[] list
        for i in range(0,len(arguments)):
            arg_reg=arguments[i] #eg t20
            if i==0:
                line=f"addi a{i} {arg_reg} 0x0 #start of precall"
            else:
                line=f"addi a{i} {arg_reg} 0x0"
            self.em.emit(line)
        callee=expr.name.id
        num_to_decrement=self.frame.num_locals*4 #...say that it is 20, bc 5 locals *4=20
        num_to_decrement=num_to_decrement+4 #bc saving ra...so now 24
        self.emit_precall_new()
        self.em.emit(f"jal {callee}")
        self.emit_postreturn_new()
        self.proc_label_counter+=1
        return "a0" #return val will be saved in a0. if it was an invocation_statement, it doesnt rlly matter
        #
        #precall:
            #save temp registers in stack
            #save params in param registers a0-a-7
            #save ra??
            #s0-s1 and s2-s11 are SAFE. dont necessarily need to be saved on stack. aka 8,9, and 18-27
        #eg sub(x,y) in a=sub(x,y)
        #postreturn: return values will be in a0 and a1

    def visit_unary_expression(self, expr: expression_ast.UnaryExpression):
        op=expr.operator.value
        operand_reg=expr.operand.accept(self)    #returns the register where operand is stored. if operand was just a value/variable, visit_identifier_expression takes care of this
        curr=self.frame.new_temp()
        if op=="-":
            self.em.emit(f"sub {curr} zero {operand_reg}")
            return curr
        elif op=="!":
            ifblock=[f"li {curr} 0x0"]
            elseblock=[f"li {curr} 0x1"]
            self.em.if_else_block(operand_reg,"zero","beq",ifblock,elseblock)
            return curr

    def visit_binary_expression(self, expr: expression_ast.BinaryExpression):
        #1. match the op to its name in RISCV syntax
        #2. 'rd' will be a new temp
        #3. if either of the operands is an instance of an INTEGER... also. using sll  . 
        binaryops={
            "+":"add",
            "-":"sub",
            "*":"mul",
            "||":"or",
            "&&":"and"
        }
        #ones with imm versions: add, and, or, 
        #ones without: sub,mul
        
        equalityops=['==','!='] #   ----DONE
        arithops=['+','-','*','/']    #these require integers only.  ------DONE
        relationalops=['<','>','<=','>='] #these require integers only -----DONE
        booleanops=['||','&&'] #these require boolean only ------DONE

        op=self.op_to_text(expr.operator)
        leftreg=None
        rightreg=None
        leftimm=self.check_for_immediates(expr.left)
        rightimm=self.check_for_immediates(expr.right)

        tcurr=self.frame.new_temp()

        if op in binaryops:
            if op=="-" or op=="*": #no logic with immediates is necessary here. bc sub and mul don't have i-type counterparts
                leftreg=expr.left.accept(self)
                rightreg=expr.right.accept(self)
                ans=f"{binaryops[op]} {tcurr} {leftreg} {rightreg}"
                self.em.emit(ans)
                return tcurr
            #left imm none, right imm none....accept both
            #left imm none, right imm yes...only accept left
            #left imm yes, right imm none...only accept right
            #left imm yes, right imm yes...wouldnt happen
            else:
                if leftimm is None and rightimm is not None:
                    leftreg=expr.left.accept(self)
                    ans=f"{binaryops[op]}i {tcurr} {leftreg} {rightimm}"
                    self.em.emit(ans)
                    return tcurr
                elif rightimm is None and leftimm is not None:
                    rightreg=expr.right.accept(self)
                    ans=f"{binaryops[op]}i {tcurr} {rightreg} {leftimm}"
                    self.em.emit(ans)
                    return tcurr
                elif rightimm is None and leftimm is None:
                    leftreg=expr.left.accept(self)
                    rightreg=expr.right.accept(self)
                    ans=f"{binaryops[op]} {tcurr} {leftreg} {rightreg}"
                    self.em.emit(ans)
                    return tcurr     
        else:
            leftreg=expr.left.accept(self)
            rightreg=expr.right.accept(self)
            if op=="/":
                self.em.emit(f"li {tcurr} 0x0")    #the quotient, aka the ans
                while_block_lines=[]
                while_block_lines.append(f"sub {leftreg} {leftreg} {rightreg}")
                while_block_lines.append(f"addi {tcurr} {tcurr} 0x1")
                self.em.while_block_for_division(leftreg,rightreg,"blt",while_block_lines)
                return tcurr
            
            if op=="<":
                self.em.emit(f"slt {tcurr} {leftreg} {rightreg}")
                return tcurr
            if op==">":
                self.em.emit(f"slt {tcurr} {rightreg} {leftreg}")
                return tcurr
            if op==">=":
                self.em.emit(f"slt {tcurr} {leftreg} {rightreg}")
                self.em.not_op(destreg=tcurr)   #sets R[tcurr] = !(R[tcurr])
                return tcurr
            if op=="<=":
                #print(f"visiting binary expression on line {expr.linenum}")
                self.em.emit(f"slt {tcurr} {rightreg} {leftreg}")
                self.em.not_op(destreg=tcurr)
                return tcurr
            if op=="==":
                ifblock=[f"li {tcurr} 0x1"]
                elseblock=[f"li {tcurr} 0x0"]
                self.em.if_else_block(op1=leftreg,op2=rightreg,comp_inst="bne",ifblock=ifblock,elseblock=elseblock)
                return tcurr
            if op=="!=":
                ifblock=[f"li {tcurr} 0x1"]
                elseblock=[f"li {tcurr} 0x0"]
                self.em.if_else_block(leftreg,rightreg,"beq",ifblock,elseblock)
                return tcurr

    def visit_lvalue(self, lvalue: lvalue_ast.LValue):
        pass
        
    def visit_lvalue_dot(self, lv: lvalue_ast.LValueDot):
        left=lv.left
        name=lv.id.id
    #    print(f"visiting lvalue dot: left={left} and name={name}")
        base_ptr,base_type=self.compute_dot_expr_addr(left) #gives us reg storing base address of {left}. and struct type of {left}
        stlayout=self.struct_layouts[base_type]
        field_offset=stlayout.field_offsets[name]
        curr=self.frame.new_temp()
        self.em.emit(f"addi {curr} {base_ptr} {field_offset}") 
        #now, curr=pointer to the entire dot expression. e.g. pointer to q.coords.x. this would be the address at which we'd want to 'sw'
        return curr


    def visit_lvalue_id(self, lvalue_id: lvalue_ast.LValueID):
        name=lvalue_id.id
   #     print(f"visiting lvalue id. name is {name}")
        pass
    
    
    def setup_file(self):
        lines=[]
        lines.append(".globl main\n .import berkeley_utils.s # the ecall utilities")
        lines.append(".import read_int.s # the file read wrapper")
        lines.append(" ")
        lines.append(" ")
        lines.append(".data")
        lines.append("filepath_ptr: .word")
        lines.append('error_string1: .string "read_int returned an error\\n"')
        lines.append('error_string2: .string "incorrect number of arguments\\n"')
        for g in self.globals:
            str_ = f"{g}: .word 0x0"
            lines.append(str_)
        lines.append(" ")
        lines.append(".text")
        return lines

            
    def write_file(self):
        if self.module is None:
            raise ValueError("No module IR has been generated yet.")
        print(f"writing to file {self.output_file}")
        return write_module(self.module, self.output_file, END_PROCS_PATH)

    def _build_procedure_ir(self,fname,lines):
        label = lines[0] if lines and lines[0].endswith(":") else f"{fname}:"
        prologue=[]
        body=[]
        epilogue=[]
        section=body
        body_started=True
        remaining_lines=lines[1:] if lines and lines[0]==label else lines
        for line in remaining_lines:
            stripped=line.strip()
            if stripped.startswith("#start of prologue"):
                section=prologue
                body_started=False
                continue
            if stripped.startswith("#start of body"):
                section=body
                body_started=True
                continue
            if stripped.startswith("#start of epilogue"):
                section=epilogue
                continue
            if stripped.startswith("#end of"):
                continue
            if not body_started:
                prologue.append(line)
                continue
            section.append(line)
        return ProcedureIR(name=fname,label=label,prologue=prologue,body=body,epilogue=epilogue)

    def _attach_procedure(self,proc_ir:ProcedureIR):
        if self.module is None:
            self.module=ModuleIR(setup_lines=self.setup_file())
        existing=None
        for fn in self.module.functions:
            if fn.name==proc_ir.name:
                existing=fn
                break
        if existing is None:
            existing=FunctionIR(name=proc_ir.name)
            self.module.functions.append(existing)
        existing.procedures.append(proc_ir)

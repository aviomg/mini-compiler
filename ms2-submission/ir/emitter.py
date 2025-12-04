from enum import Enum

class LabelType(Enum):
    IF_START = 1
    IF_END = 2
    IF_ELSE = 3
    IF_IF=4
    WHILE_START=5
    WHILE_END=6

# class ConditionalStatement():
#     def __init__(self,op1,op2,comp_inst):
#         self.has_else_block=False
#         self.op1=op1
#         self.op2=op2
#         self.comp_inst=comp_inst
    
#     def if_block_start():
        
    

class Emitter():
    def __init__(self):
        self.lines=[]
        self.loop_label_counter=0    #use this for if/else blocks, while blocks, etc.
        self.if_block_label_counter=0
    
    def emit(self,s):
        self.lines.append(s)
    
    def emit_lines(self,lines_):
        for l in lines_:
            self.lines.append(l)
    
    def label(self,s):
        self.emit(f"{s}:")
    
    def get_fresh_label(self,type:LabelType,counterval):
        match type:
            case LabelType.IF_START:
                return f"ifBlockStart{counterval}"
            case LabelType.IF_END:
                return f"endIfBlock{counterval}"
            case LabelType.IF_ELSE:
                return f"else{counterval}"
            case LabelType.IF_IF:
                return f"if{counterval}"
            case LabelType.WHILE_START:
                return f"whileStart{counterval}"
            case LabelType.WHILE_END:
                return f"endWhile{counterval}"
    
    def li(self,rd,imm):self.emit(f"li {rd} {imm}")
    def mv(self,rd,rs):self.emit(f"mv {rd} {rs}") #sets R[rd] = R[rs]. same as addi rd rs 0
    def add(self,rd,rs,rt):self.emit(f"add {rd} {rs} {rt}")
    def addi(self,rd,rs,imm):self.emit(f"addi {rd} {rs} {imm}")
    def sub(self,rd,rs,rt):self.emit(f"sub {rd} {rs} {rt}")
    def mul(self,rd,rs,rt):self.emit(f"mul {rd} {rs} {rt}")
    def la(self,rd,label):self.emit(f"la {rd} {label}")
    def lw(self,rd,offset,rs): self.emit(f"lw {rd} {offset}({rs})")
    def sw(self,rd,offset,rs): self.emit(f"sw {rd} {offset}({rs})")
    
        
    def if_block(self,op1:str,op2:str,comp_inst:str,ifblock:list[str]):
       # self.emit(" ")
        stlabel=self.get_fresh_label(LabelType.IF_START,self.if_block_label_counter)
        iflabel=self.get_fresh_label(LabelType.IF_IF,self.if_block_label_counter)
        contlabel=self.get_fresh_label(LabelType.IF_END,self.if_block_label_counter)
        self.emit(f"{stlabel}:")
        self.emit(f"{comp_inst} {op1} {op2} {contlabel}")
        self.emit(f"{iflabel}:")
        for line in ifblock:
            self.emit(line)
        #self.emit(" ")
        self.emit(f"{contlabel}:")
        self.if_block_label_counter+=1
    
    def if_else_block(self,op1:str,op2:str,comp_inst:str,ifblock:list[str],elseblock:list[str]):
       # self.emit(" ")
        stlabel=self.get_fresh_label(LabelType.IF_START,self.if_block_label_counter)
        iflabel=self.get_fresh_label(LabelType.IF_IF,self.if_block_label_counter)
        elselabel=self.get_fresh_label(LabelType.IF_ELSE,self.if_block_label_counter)
        contlabel=self.get_fresh_label(LabelType.IF_END,self.if_block_label_counter)
        self.emit(f"{stlabel}:")
        self.emit(f"{comp_inst} {op1} {op2} {elselabel}")  #eg beq t1 t2 else0
        self.emit(f"{iflabel}:")
        for line in ifblock:
            self.emit(line)
        self.emit(f"jal zero {contlabel}")
        self.emit(f"{elselabel}:")
        for line1 in elseblock:
            self.emit(line1)
       # self.emit(f" ")
        self.emit(f"{contlabel}:")
        self.if_block_label_counter+=1

    def while_block(self,eval_reg,guard_body,while_body):
        stlabel=self.get_fresh_label(LabelType.WHILE_START,self.loop_label_counter)
        endlabel=self.get_fresh_label(LabelType.WHILE_END,self.loop_label_counter)
      #  self.emit(" ")
        self.emit(f"{stlabel}:")
        for line in guard_body:
            self.emit(line)
        self.emit(f"beq {eval_reg} zero {endlabel}")
        for line2 in while_body:
            self.emit(line2)
        self.emit(f"j {stlabel}")
      #  self.emit(" ")
        self.emit(f"{endlabel}:")
        self.loop_label_counter+=1
        

    '''handling negative division: need to follow this template, assuming:
        x23=the dividend (thing being divided)
        x27=the divisor (num to divide by)
        x22=the quotient(where we r storing the ans)
        template:
        bge x23 zero whileStart0 #if positive, go to normal division

        negative_division:
        neg x23 x23
        whileStart1:
        blt x23 x27 endWhile1
        sub x23 x23 x27
        addi x22 x22 1
        j whileStart1
        endWhile1:
        neg x22 x22
        j endWhile0

        whileStart0: 
        blt x23 x27 endWhile0
        sub x23 x23 x27
        addi x22 x22 0x1
        j whileStart0
        endWhile0:
        '''

    def while_block_for_division(self,exit_op1,exit_op2,exit_inst,loop_body):
        '''
        exit_op1: the first operand to use in the condition that is used to check whether the while loop should terminate
        exit_op2: the second operand to use in the exit checking condition
        exit_inst: the operation with which to compare exit_op1 and exit_op2, eg beq, bne, blt, etc.
        loop_body: a list of instructions to put in the body of the while loop
        '''
        startlabel=self.get_fresh_label(LabelType.WHILE_START,self.loop_label_counter)
        endlabel=self.get_fresh_label(LabelType.WHILE_END,self.loop_label_counter)
     #   self.emit(" ")
        self.emit(f"{startlabel}:")
        self.emit(f"{exit_inst} {exit_op1} {exit_op2} {endlabel}")
        self.emit_lines(loop_body)
        self.emit(f"j {startlabel}")
     #   self.emit(" ")
        self.emit(f"{endlabel}:")
        self.loop_label_counter+=1
    
    def not_op(self,destreg):
        '''
        destreg: the operand which will be negated. only applies to boolean variables. e.g. !(0)=1 and !(1)=0
        ''' 
        startlabel=self.get_fresh_label(LabelType.IF_START,self.if_block_label_counter)
        elselabel=self.get_fresh_label(LabelType.IF_ELSE,self.if_block_label_counter)
        contlabel=self.get_fresh_label(LabelType.IF_END,self.if_block_label_counter)
    #    self.emit(" ")
        self.emit(f"{startlabel}:")
        self.emit(f"beqz {destreg} {elselabel}")
        self.emit(f"li {destreg} 0x0")
        self.emit(f"jal zero {contlabel}")
        self.emit(f"{elselabel}:")
        self.emit(f"li {destreg} 0x1")
    #    self.emit(f" ")
        self.emit(f"{contlabel}:")        

        self.if_block_label_counter+=1
        


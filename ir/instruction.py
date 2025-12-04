from enum import Enum

class InstType(Enum):
    R_TYPE=1
    I_TYPE=2
    STORE=3
    BRANCH=4
    JUMP=5
    LONG_IMMS=6
    OTHER=7

LOAD_OPS=["lb","lbu","lh","lhu","lw","la"]
OTHER_I_OPS=["li","mv","nop","not","jalr"]
OTHER_OPS=["ebreak","ecall","neg"]
STORE_OPS=["sb","sh","sw"]
BRANCH_OPS=["beq","bne","blt","bltu","bge","bgeu","beqz","bnez"]
JUMP_OPS=["jal","j","jr","ret"]
U_OPS=["auipc","lui"]
RESTRICTED_OPS=["x0","x1","x2","x3","x4","x10","x11","zero","a0","a1","sp","ra"]


class Procedure():
    def __init__(self,procname, blocks,instructions,regused,vr,regranges,call_live_reg,no_call_reg,body_inst,prebody_inst,postbody_inst):
        self.name=procname
        self.blocks=blocks
        self.instructions=instructions
        self.registers_used=regused
        self.virtual_registers=vr
        self.register_ranges=regranges
        self.call_live_reg=call_live_reg
        self.no_call_reg=no_call_reg
        self.prologue_inst=[]
        self.body_inst=body_inst
        self.epilogue_inst=[]
        self.pre_prologue=[]
        self.post_epilogue=[]
        self.prebody_inst=prebody_inst
        self.postbody_inst=postbody_inst
    
    
    
        '''

        all_lines=[]
        for block in self.blocks:
            for line in block.lines:
                all_lines.append(line)

        inprologue=False
        inbody=False
        inepilogue=False
        inpreprologue=True
        current_section="pre-prologue"
        for line in all_lines:
            if "#start of prologue" in line:
                inprologue=True
                inpreprologue=False
            if "#start of body" in line:
                inbody=True
                inprologue=False
            if "#start of epilogue" in line:
                inepilogue=True
                inbody=False
            if inpreprologue:
                self.pre_prologue.append(line)
            elif inprologue:
                self.prologue_inst.append(line)
            elif inbody:
                self.body_inst.append(line)
            elif inepilogue:
                self.epilogue_inst.append(line)
          '''  
                
            


class Instruction():
    #the main thing that matters is the rd and the registers that are used.
    def __init__(self, instruction):
        self.inst=instruction.split(" ")
        self.type=None
        self.rd=None #all except store type will have these. for store, this will be set to "Mem"
        self.rs1=None #all except j, jal, la, li, ret will have these
        self.rs2=None #only store and branch and r-type will have these
        self.imm=None #only i-type, store type, j-type will have these
        self.label=None #only pseudo instructions, branch type, jump type, and la would have these
        self.op=self.inst[0]
        self.index_in_proc=None
        self.owner_proc=None
        self.defs=[]
        self.uses=[]
        self.section=""
        flag=False #for when to default to r-type
        
        if (self.is_standard_i_type()):   #aka, i-type ops 
            flag=True
            #eg addi x1 x2 imm
            self.type=InstType.I_TYPE
            self.rd=self.inst[1]
            self.rs1=self.inst[2]
            self.imm=self.inst[3]
        else:
            if self.op in OTHER_I_OPS:
                self.handle_i_inst()
            elif self.op in LOAD_OPS:
                self.type=InstType.I_TYPE
                if self.op=="la":
                    self.rd=self.inst[1]
                    self.label=self.inst[2]
                else:
                    self.rd=self.inst[1]
                    if "(" in self.inst[2]:
                        p2=self.inst[2].split("(") #p2[0] is "imm" and p2[1] is "rs1)"
                        self.rs1=p2[1][:-1]
                        self.imm=p2[0]
                    else:
                        # handle label loads like "lw a0 filepath_ptr"
                        self.label=self.inst[2]
            elif self.op in STORE_OPS:
                self.type=InstType.STORE
                self.rd="Mem"
                self.rs2=self.inst[1]
                p2=self.inst[2].split("(")
                self.imm=p2[0]
                self.rs1=p2[1][:-1]
            elif self.op in OTHER_OPS:
                self.type=InstType.OTHER
                if self.op=="neg":
                    self.rd=self.inst[1]
                    self.rs1=self.inst[2]
                    self.type=InstType.R_TYPE
            elif self.op in BRANCH_OPS:
                self.type=InstType.BRANCH
                self.rs1=self.inst[1]
                self.rs2=self.inst[2]
                if self.op=="beqz" or self.op=="bnez":
                    self.label=self.inst[2]
                    self.rs2="x0"
                else:
                    self.label=self.inst[3]
            elif self.op in JUMP_OPS:
                self.type=InstType.JUMP
                if self.op=="jal":
                    if len(self.inst)>2:
                        self.rd=self.inst[1] #jal rd label
                        self.label=self.inst[2]
                    else:
                        self.label=self.inst[1]
                elif self.op=="j":
                    self.label=self.inst[1]
                elif self.op=="jr":
                    self.rs1=self.inst[1]    
            elif self.op in U_OPS:
                self.type=InstType.LONG_IMMS
                if self.op=="auipc":
                    self.rd=self.inst[1]
                    self.imm=self.inst[2]
                elif self.op=="lui":
                    self.rd=self.inst[1]
                    self.imm=self.inst[2]                 
            else:
                self.handle_r_inst()
        self.calculate_uses()
        self.calculate_defs()
    
    def calculate_uses(self):
        if self.rs1 is not None and self.rs1 not in RESTRICTED_OPS:
            self.uses.append(self.rs1)
        if self.rs2 is not None and self.rs2 not in RESTRICTED_OPS:
            self.uses.append(self.rs2)
    
    def calculate_defs(self):
        if self.rd is not None and self.rd !="Mem" and self.rd not in RESTRICTED_OPS:
            self.defs.append(self.rd)
        
    def is_standard_i_type(self):
        len_of_op_name=len(self.op)
        last_letter=self.op[len_of_op_name-1]
        if last_letter=="i" and self.op!="lui":
            if self.op not in OTHER_I_OPS:
                return True
        if self.op=="sltiu":
            return True

        return False

    def handle_i_inst(self):
        self.type=InstType.I_TYPE
        if self.op=="lui":
            self.rd=self.inst[1]
            self.imm=self.inst[2]
        if self.op=="li": #li x10 30 = addi x10 zero 30
            self.rd=self.inst[1]
            self.rs1="x0"
            self.imm=self.inst[2]
        if self.op=="mv":
            self.rd=self.inst[1]
            self.rs1=self.inst[2]
            self.imm="0"
        if self.op=="not":
            self.rd=self.inst[1]
            self.rs1=self.inst[2]
            self.imm="-1"
        if self.op=="jalr":
            self.rd=self.inst[1]
            self.rs1=self.inst[2]
            self.imm=self.inst[3]
            
    
    def handle_r_inst(self):
        self.type=InstType.R_TYPE
        self.rd=self.inst[1]
        self.rs1=self.inst[2]
        self.rs2=self.inst[3]
        

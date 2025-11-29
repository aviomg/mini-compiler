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
        flag=False #for when to default to r-type
        
        if (self.is_standard_i_type()):   #aka, i-type ops 
            print(f"processing op {self.op}")
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
                    p2=self.inst[2].split("(") #p2[0] is "imm" and p2[1] is "rs1)"
                    self.rs1=p2[1][:-1]
                    self.imm=p2[0]
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
        print(f"inst: {self.inst}")
        self.type=InstType.R_TYPE
        self.rd=self.inst[1]
        self.rs1=self.inst[2]
        self.rs2=self.inst[3]
        

#for each line of assembly, convert all register names/referrals to a standardized formt
#so either all in terms of their real names, e.g. x1,x2,x3..x31
#or all in terms of their ABI Mnemonic, e.g. ra, sp, gp, tp, t0, t1...t6
from ir.instruction import Instruction
import re
import json



REG_MAP_PATH=r"./ir/reg_map.json"
REG_NUM_PATTERN=re.compile(r'(?<=\s)x(\d{1,2})(?=\s|$)')
REG_MNEMONIC_PATTERN=re.compile(r'(?<=\s)(?:zero|ra|sp|gp|tp|t[0-6]|s(?:[0-9]|1[01])|a[0-7])(?=\s|$)|(?<=\()(?:zero|ra|sp|gp|tp|t[0-6]|s(?:[0-9]|1[01])|a[0-7])(?=\))')
#im allowing read_err1 and cmd_err2. ill just skip them later
LABEL_PATTERN= re.compile(
    r'''^
        (?!\s*(?:if\d+|else\d+|precall\d+|postreturn\d+):\s*$)    # exclude lines like "if3:" or "else10:"
        \s*([A-Za-z_]\w*)\s*:\s*         # label: (capture the label name)
        $
    ''',
    re.VERBOSE,
)
BLOCK_LABEL_PATTERN=re.compile(r'^\s*(B\d+):\s*$')
OPS=ops = [
    "add", "sub", "and", "or", "xor",
    "sll", "srl", "sra", "slt", "sltu",
    "addi", "andi", "ori", "xori",
    "slli", "srli", "srai", "slti", "sltiu",
    "lb", "lbu", "lh", "lhu", "lw",
    "sb", "sh", "sw",
    "beq", "bne", "blt", "bltu", "bge", "bgeu",
    "jal", "jalr", "auipc", "lui",
    "ebreak", "ecall",
    "mul",
    "beqz", "bnez", "j", "jr",
    "la", "li", "mv", "neg", "nop", "not", "ret"
]
BRANCH_OPS=["beq","bne","blt","bltu","bge","bgeu","beqz","bnez"]
JUMP_OPS=["jal","j","jr","ret"]
CONVERT_MNEMONIC_TO_NUM=True


class RegisterAllocation():
    def __init__(self, asm_file_path):
        self.path=asm_file_path
        self.normalized_asm_path=self.path.split(".")[0] + "-norm" + ".s"
        self.normalized_lines=[]
        self.map_nums=None  #key is num, e.g. x10. value is mnemonic name, eg a0
        self.map_mnemonics=None #key is mnemonic name. value is num, e.g. x10
        self.blocks={}
        self.block_counter=0
        self.modified_lines=[]

        with open(REG_MAP_PATH,'r',encoding='utf-8') as jsonmap:
            self.map_nums=json.load(jsonmap)
        self.map_mnemonics={value:key for key,value in self.map_nums.items()}
        print(self.map_mnemonics)
    
        with open(self.path,"r") as f:
            with open(self.normalized_asm_path,"w") as fout:    #converts all mneumonic register names into their actual ones, e.g. x1,x2,x3..
                
                print(f"reading path")
                cont=f.read()
                for line in cont.split("\n"):
                    if CONVERT_MNEMONIC_TO_NUM:
                        newline=REG_MNEMONIC_PATTERN.sub(self.normalize_reg,line)
                    else:
                        newline=REG_NUM_PATTERN.sub(self.normalize_reg,line)
                    #print(newline)
                    fout.write(newline)
                    fout.write("\n")
        startoftext=False
        with open(self.normalized_asm_path,"r") as normfile:
            cont=normfile.read()
            lines=cont.split("\n")
            for line in lines:
                if ".text" in line.split():
                   # print(f"found .text thing")
                    startoftext=True
                    self.modified_lines.append(line)
                    self.modified_lines.append(" ")
                    self.modified_lines.append(self.fresh_block())
                    continue
                if not startoftext:
                    self.modified_lines.append(line)
                else: #everything after start of text
                    split=line.split()
                    lenofsplit=(len(split))
                    if (lenofsplit==1 and split[0]=="ret") or (lenofsplit>1 and (split[0] in BRANCH_OPS or split[0] in JUMP_OPS)):
                        self.modified_lines.append(line)
                        self.modified_lines.append(" ")
                        self.modified_lines.append(self.fresh_block())
                        continue
                    else:
                        self.modified_lines.append(line)
                    
        print(f"modified lines")          
        for line in self.modified_lines:
            print(line)
        with open(self.normalized_asm_path,"w") as normfile2:
            for line in self.modified_lines:
                normfile2.write(line + "\n")
    
    
    def fresh_block(self):
        ret=f"B{self.block_counter}:"
        self.block_counter+=1
        return ret
    
    def normalize_reg(self,match:re.Match): #the function passed into re.sub() which converts all menumonic names into real ones
        reg=match.group(0)
        if CONVERT_MNEMONIC_TO_NUM:
            num=self.map_mnemonics[reg]
        else:
            regnum=int(reg[1:])
            if regnum<=31:
                num=self.map_nums[reg]
            else:
                num=reg
        #st=f"{reg}->{num}"
        return num
    
    def create_blocks(self):
        print(f"labels:")
        currblocklines=[]
        currlabel=None
        with open(self.normalized_asm_path,"r") as f:
            cont=f.read()
            for line in cont.split("\n"):
                m=BLOCK_LABEL_PATTERN.match(line)
              #  m=LABEL_PATTERN.match(line)
                if m is not None:   #we have found a new block
                    lname=m.group(1)
                    print(lname) #e.g. "whileBlock0:" or "main:"
                    if currblocklines:  #if we alr had a block started. clear out currblocklines
                        self.blocks[currlabel]=currblocklines
                        currblocklines=[]
                 #set label, begin appending to currblocklines
                    currlabel=lname
                    currblocklines.append(line)
                else:
                    if currblocklines:
                        currblocklines.append(line)
                    else:
                        continue
        if currblocklines:
            self.blocks[currlabel]=currblocklines
        
     #   print("BLOCKS:\n")
     #   for b in self.blocks:
     #       lines=self.blocks[b]
     #       for line in lines:
     #           print(line)
     #       print("\n--------------------------------------\n")
                        
         
    
    def run(self):
        self.create_blocks() #now we have all the blocks
        
        
        
      
    
    



'''
ok, i think that all i have left is reg allocation???? idk ... idk. should probably test it a bit more. but its kind of hard without the reg allocation




Still have to handle:
- null expressions, setting things to null , etc.--done
    - setting a struct to null. Probably just means that we set the ptr to be 0??? i actually have no idea
    - "addi t0, x0, 0   # Set register t0 to 0 (null)", possibly, according to AI
- block statements--done
- conditional statements--done
- while statements--done
- reg allocation LOL


conditionals and whiles:
- have a ConditionalStatement class that has a global 'label counter'. every time a class object is initialized, the counter is incremented. but 
    - the object has a unique, constant (after being set) 'label counter'
    - fields: op1, op2, comp inst, 
    - has  if_start, if_end methods, if_else_start, if_else_middle, if_else_end
    - Emitter also has 


ALTERNATIVELY:
- record length of self.em.lines BEFORE calling accept(self) on each statement in the block
- do the accept(self) call
- record length now. subtracting that tells us how many lines were just added to self.em.lines. call this num i
- remove the last i elements of self.em.lines. place them in new array. pass THIS ARRAY into my original if_else method that i was going to have in Emitter


to mention in design doc:
- how i handled the block statements
- shortcuts when it comes to doing immediate mathematics. by having helper check_for_immediate methods that i call in visit_binary_expression



PLAN:
- figure out regex for each "x{num}" aka reference to a register
- write to a new file. for each line, modify the line so that:
    - for each match m to the regex expression, find the value of x=register_mapping[m]. replace m with x. 
    - write this updated line to the new file. so in lines without any reg references, same line will be written
    
    
patterns like this:
"lw x17 4(sp)
addi a0 x17 0
jal print_int"
aka one line that defines a reg X, second line directly defines a0 by setting it equal to X, third line makes a proc call...
can be transformed into this:
"lw a0 4(sp)
jal print_int"
thus freeing up the register x17

- maybe make a pass where i free up registers. then make a pass where i convert all VRs to PRs --eg ones over 31--by using this set of freed up registers
- ideally, our local vars in main should be able to live on s0-s11, in which case they already get saved to the stack. this would eliminate a lot of load and store words
- maybe, each time a local is loaded for USAGE, not definition,  i set self.frame.in_reg[localname]=regNum. for all others, in_reg[localname]=None
    -i would know if it is loaded for USAGE, this would be all cases except cases where it is the 'source' in an assignment statement
- then, each following time it needs to be used for USAGE, i check if self.frame.in_reg[localname] is not None. if so, rather than doing a store word,
    i can just use the register.
- when locals are being updated, we can initially ignore all of this register functionality, and after updating the value, 'free' the register and set
    in_reg to false, since it now contains a stale value
- doing this would also mean keeping somehow track of a list of 'free registers'


-ok, the only times that registers are alive across blocks is when there are while and if blocks involved. e.g., a counter that is first defined before
    a while loop, and then incremented inside the while loop, and then stored somewhere after the loop is over.
    -OR, a register holding a value that is used in the branch condition of a while loop, and modified inside the while loop
    
    
- after computing LR intervals for a block (traversing blocks bottom-up), for each LR whose end-value in the interval, e.g. y in [x,y] is inf, we
    - iterate through each following block to see if it is used--see if used_again=true. by used, meaning:
    used_again=False
    for each subsequent block (top down from the curr block):
            for each inst:
                if reg gets redefined:
                    set used_again=False
                    return
                if reg gets used aka rs1 or rs2 (and loop hasn't alr returned, meaning reg hasn't yet been redefined):
                    set used_again=True
                    return
    now, for each one that DOES get used again, we know to spill. for each that doesn't , we can update its y in [x,y] to be equal to x???

'''
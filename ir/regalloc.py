#for each line of assembly, convert all register names/referrals to a standardized formt
#so either all in terms of their real names, e.g. x1,x2,x3..x31
#or all in terms of their ABI Mnemonic, e.g. ra, sp, gp, tp, t0, t1...t6
from typing import List, Optional
from ir.instruction import Instruction,Procedure
import re
import json
import math
from collections import defaultdict


class RegStack(): #for a given block, for all blocks whose free registers we are allowed to use, create a regstack object with the prevBlock's free registers list
    #then, each time i want to make a replacement, i will refer to the list in this object. each time i make a replacement, i will pop that val off the stack.
    def __init__(self, free_registers_list):
        self.free_registers=free_registers_list
    
    def pop_reg(self):
        return self.free_registers.pop()
    

class Block():
    def __init__(self,idx,label,lines,instructions):
        self.index:int=idx
        self.label:str=label
        self.lines:List[str]=lines
        self.instructions:List[Instruction]=instructions
        self.proc_name:Optional[str]=None
        self.free_registers=[] #this has all registers which are free to be used once the given block is done executing.
        self.is_reg_free={} #for each reg used in the block, is_reg_free[regnum]=True means that the register is free to be used after this block. if false, means that this same LR/reg is used in subsequent blocks

class VR():
    def __init__(self,regnum):
        self.vr=regnum
        self.lr=None
        self.vrtolr=None
        self.nu=None
        self.prevuse=math.inf
        self.defined_at=None
        

REG_MAP_PATH=r"./ir/reg_map.json"
END_PROCS_PATH=r"./ir/asm_chunks/end_procs.txt"

REG_NUM_PATTERN=re.compile(r'(?<=\s)x(\d{1,2})(?=\s|$)|(?<=\()x(\d{1,2})(?=\))')
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
OTHER_LABELS=["endWhile","ifBlockStart","whileStart","else","endIfBlock","if"]
CONVERT_MNEMONIC_TO_NUM=True
RESTRICTED_OPS=["x0","x1","x2","x3","x4","x10","x11","zero","a0","a1","sp","ra"]


class RegisterAllocation():
    def __init__(self, asm_file_path,setuplines,filename):
        self.path=asm_file_path
        self.normalized_asm_path=self.path.split(".")[0] + "-norm" + ".s"
        self.normalized_lines=[]
        self.map_nums=None  #key is num, e.g. x10. value is mnemonic name, eg a0
        self.map_mnemonics=None #key is mnemonic name. value is num, e.g. x10
        #self.blocks=[]
        self.blocks:List[Block]=[]
        self.procs:dict[str,List[Block]]={}
        self.instrutions_per_proc:dict[str,List[Instruction]]={}
        self.block_counter=0
        self.modified_lines=[]
        self.num_blocks=0
        self.reg_to_exclude=[]
        self.procObjects=[]
        self.setuplines=setuplines
        self.output_filename=filename.split(".")[0] +  ".s"
        if CONVERT_MNEMONIC_TO_NUM:
            self.reg_to_exclude=["x0","x1","x2","x3","x4","x10","x11"]
        else:
            self.reg_to_exclude=["zero","x0","x1","x2","x3","x4","x10","x11","a0","a1","sp","ra"]

        with open(REG_MAP_PATH,'r',encoding='utf-8') as jsonmap:
            self.map_nums=json.load(jsonmap)
        self.map_mnemonics={value:key for key,value in self.map_nums.items()}
    
        with open(self.path,"r") as f:
            with open(self.normalized_asm_path,"w") as fout:    #converts all mneumonic register names into their actual ones, e.g. x1,x2,x3..
                
                print(f"\n----------------------------------\n")
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
        self.blocks=[]
        curr_lines=[]
        curr_label=None
        #self.blocks=[[] for _ in range(self.block_counter-1)]
        #self.instructions_by_block=[[] for _ in range(self.block_counter-1)]
        #print(f"size of blocks list is {len(self.blocks)}")
        #currblocklines=[]
        currlabel=None
        
        
        '''
                if m is not None:   #we have found a new block
                    lname=m.group(1)
                    print(lname) #e.g. "whileBlock0:" or "main:"
                    blockindex=int(lname[1:])
                    if currblocklines:  #if we alr had a block started. clear out currblocklines
                        self.blocks[blockindex-1]=currblocklines
                        currblocklines=[]
                 #set label, begin appending to currblocklines
                    currlabel=lname
                    currblocklines.append(line)
                else:
                    if currblocklines:
                        currblocklines.append(line)
                
                    else:
                        continue
        '''

        with open(self.normalized_asm_path,"r") as f:
            cont=f.read()
            for line in cont.split("\n"):
                m=BLOCK_LABEL_PATTERN.match(line) #if we found an line like 'B0:'
              #  m=LABEL_PATTERN.match(line)
                if m is not None:   #we found a match indicating a new block
                    lname=m.group(1)
                  #  print(f"lname:{lname}")
                    blockindex=len(self.blocks)
                    if len(curr_lines)>0: #if we alr had block started, clear out currblocklines
                        label=curr_label
                        instructions=self.generate_instruction_list(curr_lines)
                        block=Block(blockindex,label, curr_lines,instructions)
                        self.blocks.append(block)
                        curr_lines=[]
                  #  if curr_lines is not None:  #finalize previous block
                  #      idx=len(self.blocks) #0
                  #      label=curr_label  
                  #      instructions=self.generate_instruction_list(curr_lines)
                  #      block=Block(idx,label,curr_lines,instructions)
                  #      self.blocks.append(block)
                    
                    #if curr lines WAS none, we start a new block. or even if it wasnt:
                    curr_label=m.group(1)+":"
                    curr_lines.append(line)
                else:
                    #just a normal line
                    if len(curr_lines)>0:
                        curr_lines.append(line)
            if len(curr_lines)>0:
                idx=len(self.blocks)
                label=curr_label
                instructions=self.generate_instruction_list(curr_lines)
                block=Block(idx,label,curr_lines,instructions)
                self.blocks.append(block)
            
        self.num_blocks=len(self.blocks)
       # print(f"BLOCKS (total of {self.num_blocks}):\n")
       # for block in self.blocks:
       #     print(f"block at index {block.index}:")
       #     print(("\n").join(block.lines))
      #     for line in lines:
      #         print(line)
       #     print("--------------------------------------")
        
    def assign_procedures(self):
        currproc = None

        for block in self.blocks:
            proc_label = None

            for line in block.lines:
                s = line.strip()
                # Only care about labels of the form "foo:"
                if not s.endswith(":"):
                    continue

                # Skip basic block labels like "B0:", "B1:", etc.
                if BLOCK_LABEL_PATTERN.match(s):
                    continue

                # Strip the trailing ':'
                lname = s[:-1]

                # Skip structural / control-flow labels such as:
                # endWhile0, ifBlockStart0, whileStart0, else0, endIfBlock0, if0, ...
                is_proc_label = True
                for prefix in OTHER_LABELS:
                    if lname.startswith(prefix):
                        is_proc_label = False
                        break
                if not is_proc_label:
                    continue

                # Anything that gets here is a "procedure" label
                proc_label = lname
                break

            # If we found a new procedure label in this block, update currproc
            if proc_label is not None:
                currproc = proc_label

            block.proc_name = currproc
        '''
        currproc=None
        for block in self.blocks:
            
            lines=block.lines
            if len(lines)>1:
                secondline=lines[1].strip()
                if secondline.endswith(":"):
                        is_proc_label=True
                        for label in OTHER_LABELS:
                            if label in secondline:
                                is_proc_label=False
                                break
                        if is_proc_label:
                            currproc=secondline[:-1]
            print(f"curr proc is {currproc}")
            block.proc_name=currproc
        '''
        
    
    def build_proc_map(self):
        procs=defaultdict(list)
        for block in self.blocks:
            if block.proc_name is not None:
                procs[block.proc_name].append(block)
        self.procs=procs
                    

                        
    def get_proc_indexes(self): #we needed this when the lists were maintained separately
        proc_indexes=[]
        for i in range(0,len(self.blocks)):
            block=self.blocks[i]
            if len(block)>1:
                secondline=block[1].strip()
                if len(secondline)>1:
                    if secondline[len(secondline)-1]==":":
                        is_proc_label=True
                        for label in OTHER_LABELS:
                            if label in secondline:
                                is_proc_label=False
                                break
                        if is_proc_label:
                            proc_indexes.append(i)
        return proc_indexes

    def has_rd(self,inst:Instruction):
        if inst.rd is None or inst.rd=="Mem" or inst.rd in self.reg_to_exclude:
            return False   
        return True
    def has_rs1(self,inst:Instruction):
        if inst.rs1 is None or inst.rs1 in self.reg_to_exclude:
            return False
        return True
    def has_rs2(self,inst:Instruction):
        if inst.rs2 is None or inst.rs2 in self.reg_to_exclude:
            return False
        return True 

    def compute_live_ranges(self,instructions):
        '''
        instructions: a list of Instruction objects that represent each instruction in a given basic block. 
        
        - creates VR objects for each VR/LR and returns a dict mapping each VR name to its VR object
        '''
        virtual_registers={}
        LRcounter=0
        currline=len(instructions)
        for inst in reversed(instructions):
            currline-=1
            if (self.has_rd(inst)):
                if inst.rd not in virtual_registers:
                    vr=VR(inst.rd)
                    virtual_registers[inst.rd]=vr
                vr=virtual_registers[inst.rd]
                if vr.vrtolr is None:
                    vr.vrtolr=LRcounter
                    LRcounter+=1
                vr.lr=vr.vrtolr    
                vr.nu=vr.prevuse
                vr.prevuse=math.inf
                vr.vrtolr=None
                vr.defined_at=currline
            if self.has_rs1(inst):
                if inst.rs1 not in virtual_registers:
                    vr=VR(inst.rs1)
                    virtual_registers[inst.rs1]=vr
                vr=virtual_registers[inst.rs1]
                if vr.vrtolr is None:
                    vr.vrtolr=LRcounter
                    LRcounter+=1
                vr.lr=vr.vrtolr
                vr.nu=vr.prevuse
                vr.prevuse=currline
            if self.has_rs2(inst):
                if inst.rs2 not in virtual_registers:
                    vr=VR(inst.rs2)
                    virtual_registers[inst.rs2]=vr
                vr=virtual_registers[inst.rs2]
                if vr.vrtolr is None:
                    vr.vrtolr=LRcounter
                    LRcounter+=1
                vr.lr=vr.vrtolr
                vr.nu=vr.prevuse
                vr.prevuse=currline
        return virtual_registers

    def generate_instruction_list(self,block): #given a block, returns a list of Instruction Objects
        instructions=[]
        for line in block:
            if len(line)<=1:
                continue
            if line[-1]!=":" and line.split(" ")[0] in OPS:
                inst=Instruction(line)
                instructions.append(inst)
        return instructions
    
    def scan_blocks_for_reg(self,key,block_indexes_to_check): 
        #returns True if the register is not used in any subsequent blocks. returns false otherwise
        #if none of the if statements enter execution, the register was not even mentioned, so return true
        
        for block_to_check in block_indexes_to_check:
            instruction_list=block_to_check.instructions
        
       # for ind in block_indexes_to_check:
       #     block_to_check=self.blocks[ind]
            #now, checking ONE SINGLE BLOCK. e.g., if we are currently processing B14, the first iter of the loop defined above is for B15. the loop below will iterate through each inst in B15
       #     instruction_list=self.instructions_by_block[ind]
            for inst in instruction_list:
                rd=inst.rd
                rs1=inst.rs1
                rs2=inst.rs2
                if rd==key: #register was redefined before a single use. we can return true
                    if rs1==key or rs2==key:
                        return False
                    else:
                        return True
                if rs1==key or rs2==key:
                    return False
        return True
                    
                
                    
                
        
    def process_blocks(self,procblocks,fun): #procblocks=list of blocks for proc "fun"
       # print(f"processing blocks for proc {fun}:")
        #for each procedure. for each block in that procedure, call compute_live_ranges to get virtual registers
        #then, for each block, figure out all subsequent blocks that are in the same procedure. also figure out keyslist of all reg
        # used in that block. and create is_reg_free dict using keyslist
        #for each key in keys list, call scan blocks and pass in blocks to check
        #procblocks= a list of lists. each list is a BLOCK. aka every element is one line of the assembly inside that block. and it is all the blocks for a given proc
        free_registers={}   #usage example: free_registers[22]=[1,2,3] means that registers x1,x2,and x3 are free to be used AFTER block 22 executes
        for b in procblocks: #b = block being analyzed
            virtual_registers=self.compute_live_ranges(b.instructions)
            #print(f"virtual registers for block B{b.index}:")
            #for v in virtual_registers:
             #   obj=virtual_registers[v]
              #  print(f"{v}:\t lr:{obj.lr}\t nu:{obj.nu}\t pu:{obj.prevuse}\t def_at:{obj.defined_at}")  
            blocks_to_check_by_index=[]
            #for a given block, add all other blocks in procblocks for which index is higher
            b_index=b.index
            for other_block in procblocks:
                if other_block.index>b_index:
                    blocks_to_check_by_index.append(other_block) #ohh, so blocks to check by index alr contains a list of BLOCK objects
          #  print(f"blocks to check, by index, for block B{b.index}:")
          #  for check in blocks_to_check_by_index:
          #      print(f"B{check.index}") 
            keyslist=[]
            for v in virtual_registers:
                keyslist.append(v)
            reg_is_free=dict.fromkeys(keyslist,True)
            for key in keyslist:
                is_reg_free=self.scan_blocks_for_reg(key,blocks_to_check_by_index)  
                reg_is_free[key]=is_reg_free #maps each reg to true or false
            free_reg_after_block=[]
            for el in reg_is_free:  #each el is a regnum
                b.is_reg_free[el]=reg_is_free[el]
                if reg_is_free[el]==True: #reg is free!
                    free_reg_after_block.append(el)
            #now, free_reg_after_block tells us all registers free to be used after curr block. so all reg not used in any subsequent block
            b.free_registers=free_reg_after_block
         #   print(f"free-to-use registers after block {b_index}:")
        #    for reg in b.free_registers:
        #        print(reg)
         #   for reg in b.is_reg_free:
          #      print(f"{reg}:{b.is_reg_free[reg]}")
  
                
        '''
        - we must exclude x0-x4 inclusive from this processing. and exclude x10 and x11
        keep running list of lists. for each block, list[blocknum]= list of free registers at the end of block{blocknum}
        1. bottom up. for each block:...wait i guess it doesnt have to be bottom-up
            - initialize list of free_registers at end of that block, to empty.
            -for every reg used:
                -is_free=True
                - iterate through each block AFTER that block. for each block:
                    -look for a USE (not redefinition) of that register number. if it exists, is_free=False and return.
                    - if we see a redefinition at any point and we haven't yet seen a use...is_free=True and return.
                    - wait no. imagine a redefinition that ALSO uses the register. any other redefinition would be fine tho i think.
                    for each inst:
                        -if rd is key:
                            if rs1 is not key and rs2 is not key:
                                return True
                        -if rs is key:
                            if redefined=false, return False
                            else: print smthn bc idk if this would even happen
                    
                - if is_free, append reg to list of free registers at end of block
        2. top down. for each block:
            -get the list of free registers at the end of the previous block
            -
        - better to just iterate throuh blocks and keep an is_free hashmap (mapping registers to true/false), for determining this
        - anotherrr possible way to do this, is to do it for each reg. for each reg, identify all blocks where it is used and/or defined. idk
        
        '''

        '''          
                #we can now follow the algorith, simply checking if rd, rs1, rs2 are 'None'. or if 'rd' is "Mem". and that none of them r in
                #reg_to_exclude
        #    vr_width=max(len(virtual_registers[vr].vr) for vr in virtual_registers)
        #    lr_width=max(len(virtual_registers[vr].lr) for vr in virtual_registers)
        #    nu_width=max(len(virtual_registers[vr].nu) for vr in virtual_registers)
        #    pu_width=max(len(virtual_registers[vr].pu) for vr in virtual_registers)
        #    defat_width=max(len(virtual_registers[vr].defined_at) for vr in virtual_registers)
        
            vr_width=max(0,len("VR"))
            nu_width=max(0,len("NU"))
            pu_width=max(0,len("PU"))
            defat_width=max(0,len("Defined At"))
            lr_width=max(0,len("LR"))
            header_format = f"{{:<{vr_width}}} {{:<{lr_width}}} {{:<{nu_width}}} {{:<{pu_width}}} {{:<{defat_width}}}"
            print(header_format.format("VR", "LR", "NU","PU","Defined At"))
            print("-" * (vr_width + lr_width + nu_width + + pu_width+defat_width+6)) # Separator
            for v in virtual_registers:
                vreg = virtual_registers[v]
                print(header_format.format(vreg.vr,vreg.lr,vreg.nu,vreg.prevuse,vreg.defined_at))
        '''
    def reassign_registers(self,block):
        proc=block.proc_name
        free_registers=[]
        for b in self.procs[proc]:
            if b.index<block.index: #blocks that have alr executed
                for reg in b.free_registers:
                    if reg not in free_registers:
                        if int(reg[1:])<=31:
                            free_registers.append(reg)
        print(f"free registers to be used for B{block.index}: {free_registers}")
            
        
            #for each block in same proc w lower index, create RegStack object.
            #or...create concatenated list of free registers, cuz they could overlap?
        # look for registers numbered above 31. 
                    #  i think the best way to do this is a while loop, incrementing i each time (i starts at 32)
                    #and simultaneously using a boolean value as the while loop's condition. e.g., if we get to a certain i, for ex i=40, and we find NO registers in the block,
                    #then we are done. and can terminate loop
        # for each instance of this (invalid reg num) found:
            #grab the first RegStack object with a list that is not empty
            #pop a register that we can use
            #in the curr block, textually replace all instances of the invalid reg with this valid one?
        
        # if we find them, then grab list of all blocks in the same proc, with a lower index.
        #for each of these, starting with the one farthest from us (?): create a regstack object.
     
     #for each reg, find first index that defines  it is start. last index that uses it -1 is end
     
    def compute_reg_ranges(self,inst_list,reg_used):
        first_dict=dict.fromkeys(reg_used,None) #for each reg, first line where it is used/defined/mentioned (currently)
        last_dict=dict.fromkeys(reg_used,None)  #for each reg, last line where it is used/defined
        for inst in inst_list:
            index=inst.index_in_proc
            for reg in inst.uses: 
            #    if first_dict[reg] is None:
            #        first_dict[reg]=index
                last_dict[reg]=index-1
            for reg in inst.defs:
                if first_dict[reg] is None:
                    first_dict[reg]=index
                    last_dict[reg]=index-1
       # for reg in reg_used:
       #     print(f"{reg}: first use={first_dict[reg]}\t\t last use={last_dict[reg]}")
        
        ranges={}
        for reg in reg_used:
            firstuse=first_dict[reg]
            lastuse=last_dict[reg]
            ranges[reg]=(firstuse,lastuse)
        return ranges                                
        #for each inst, 
            #for each reg in inst.uses, if 
            
    
    def process_instructions_per_proc(self,proc):
        print(f"in proc {proc}")
        '''
        For each proc:
            - create a concatenated list of all instructions in that procedure (by looping through all blocks in the procedure and appending the instructions)-->all_inst
            - assign each instruction an index relative to the entire proc, saved at Instruction.index_in_proc
            - assign each instruction the name of the procedure it lives in, saved at Instruction.owner_proc
            - iterate through each instruction to create a list of every register used and/or defined inside the proc (outside of the reserved/special ones)-->registers_used
            - returns all_inst and registers_used
        '''
        list_of_inst=[]
        list_of_body_inst=[]
        list_of_prebody_inst=[]
        list_of_postbody_inst=[]
        in_block_index=0
        instcounter=0
        registers_used=[]
       # if proc=="main":
       #     currsection="body"
       # else:
        currsection=None
        for block in self.procs[proc]:
            lines=block.lines
            in_block_index=0
            for line1 in lines:
                line=line1.strip()
                if "#start of prologue" in line:
                    currsection="prologue"
                    continue
                if "#end of prologue" in line:
                    currsection=None
                    continue
                if "#start of body" in line:
                    currsection="body"
                    continue
                if "#end of body" in line:
                    currsection=None
                    continue
                if "#start of epilogue" in line:
                    currsection="epilogue"
                    continue
                if line.endswith(":"):
                    continue
                if line.split(" ")[0] not in OPS:
                    continue
                print(f"checking block.instructions at index {in_block_index}, for block {block.index}")
                inst=block.instructions[in_block_index]
                in_block_index+=1
                inst.owner_proc=proc
                inst.index_in_proc=instcounter
                instcounter+=1
                inst.section=currsection
                list_of_inst.append(inst)
        bodyinstcounter=0
        body_seen=False
        for block in self.procs[proc]:
            for inst in block.instructions:
                section=inst.section
                if section !="body":
                    if body_seen:
                        list_of_postbody_inst.append(inst)
                    else:
                        list_of_prebody_inst.append(inst)
                    continue
                body_seen=True
                inst.index_in_body=bodyinstcounter
                bodyinstcounter+=1
                list_of_body_inst.append(inst)
                for use in inst.uses:
                    if use not in registers_used:
                        registers_used.append(use)
                for defn in inst.defs:
                    if defn not in registers_used:
                        registers_used.append(defn)
        return list_of_inst,list_of_body_inst,registers_used,list_of_prebody_inst,list_of_postbody_inst
                
       # print(f"for proc {proc}, processed isntructions:")
       # for instru in list_of_inst:
       #     print(f"{(" ").join(instru.inst)}\t\t\t {instru.section}")
            
                    
            
        '''
            for inst in block.instructions:
                inst.owner_proc=proc
                inst.index_in_proc=instcounter
                instcounter+=1
                #    print(f"{inst.index_in_proc}" + ":" + " ".join(inst.inst))
                list_of_inst.append(inst)
                for use in inst.uses:
                    if use not in registers_used:
                        registers_used.append(use)
                for defn in inst.defs:
                    if defn not in registers_used:
                        registers_used.append(defn)
        '''
        
    def compute_call_sites(self,list_of_inst,register_ranges):
        #register_ranges is a dict where each entry reg_ranges[regnum]=(first_use_index, last_use_index)
        call_site_indexes=[]
        call_live_regs=[]
        no_call_regs=[]
        for i in list_of_inst:
            if i.op=="jal":
                call_site_indexes.append(i.index_in_proc)
        for r in register_ranges:
            interval=register_ranges[r]
            for c in call_site_indexes:
                if interval[0] < c and interval[1]>c:
                    call_live_regs.append(r)
                else:
                    no_call_regs.append(r)
        return call_live_regs,no_call_regs    
    
    def linear_scan(self,proc):
        print(f"lines to analyze for {proc.name}")
        for inst in proc.body_inst:
            print((" ").join(inst.inst))
        print(f"reg ranges for {proc.name}")
        for r in proc.register_ranges:
            print(f"{r}: {proc.register_ranges[r]}")
        print(f"call live registers for {proc.name}")
        for r in proc.call_live_reg:
            print(r)
        '''
        TODO: first separate inst into prologue, body, epilogue inst. then only perform linear scan on body
        '''
       # if proc.name=="main":
       #     return
        og_freecall=["s0","s1","s2","s3","s4","s5","s6","s7","s8","s9","s10","s11"]
        og_freenocall=["t0","t1","t2","t3","t4","t5","t6"]#"a2","a3","a4","a5","a6","a7"]
        #sort VRs by increasing start interval:
        free_call=["s0","s1","s2","s3","s4","s5","s6","s7","s8","s9","s10","s11"]
        free_nocall=["t0","t1","t2","t3","t4","t5","t6"]#"a2","a3","a4","a5","a6","a7"]
        free_nocall.reverse()
        active={} #form: each element active[regnum]={physreg:"t0","end":21}
        assign={}
        print(f"sorted intervals for {proc.name}")
        sorted_intervals=sorted(proc.register_ranges.items(),key=lambda item: item[1][0])
       # for reg in sorted_intervals:
       #     print(reg)
        for reg, (start, end) in sorted_intervals:
            is_call_live = True if reg in proc.call_live_reg else False
           # is_call_live = False if reg in proc.no_call_reg else True
            print(f"{reg}: {start}-{end}...call live? {is_call_live}")
            newactive={}
            for activevr in active:
                newactive[activevr]=active[activevr]
            for activevr in active:  
                preg=active[activevr]["physreg"]
                activeend=active[activevr]["end"]
                if activeend<start:
                    if preg in og_freecall:
                        free_call.append(preg)
                    elif preg in og_freenocall:
                        free_nocall.append(preg)
                    del newactive[activevr]
            active=newactive
            if not is_call_live:
                if len(free_call)>0:#pool isn't empty
                    assign[reg]=free_call.pop()
                    active[reg]={"physreg":assign[reg],"end":end}
            elif is_call_live:
                if len(free_call)>0:
                    assign[reg]=free_call.pop()
                    active[reg]={"physreg":assign[reg],"end":end}
            print(f"current state after processing reg {reg}:")
            print(f"assign:{assign}")
            print(f"active: {active}")
            print(f"remaining no call reg:{free_nocall} ")
            print(f"remaining call reg: {free_call}")
        
        for inst in proc.body_inst:
            def remap(reg):
                if reg is None:
                    return None
                return assign.get(reg,reg)
            
            if inst.rd is not None:
                inst.rd=remap(inst.rd)
            if inst.rs1 is not None:
                inst.rs1 = remap(inst.rs1)
            if inst.rs2 is not None:
                inst.rs2 = remap(inst.rs2)
            
            if hasattr(inst, "uses") and inst.uses is not None:
                inst.uses = [remap(r) for r in inst.uses]
            if hasattr(inst, "defs") and inst.defs is not None:
                inst.defs = [remap(r) for r in inst.defs]
            
            newtokens=[]
            for tok in inst.inst:
                if tok in assign:
                    newtokens.append(assign[tok])
                    continue
                m=re.match(r"(-?\d+)\(([^)]+)\)", tok)
                if m:
                    offset, base = m.groups()
                    base = remap(base)
                    newtokens.append(f"{offset}({base})")
                    continue
                newtokens.append(tok)
            
            inst.inst=newtokens
        print(f"fixed instructions for proc {proc.name}:")
        for inst in proc.body_inst:
                line=" ".join(inst.inst)
                print(line)

        '''
            if inst.rd is not None and inst.rd in assign:
                print(f"fixing {inst.rd} to be {assign[inst.rd]}")
                inst.rd=assign[inst.rd]
                print(f"inst.rd is now {inst.rd}")
            if inst.rs1 is not None and inst.rs1 in assign:
                inst.rs1=assign[inst.rs1]
            if inst.rs2 is not None and inst.rs2 in assign:
                inst.rs2 = assign[inst.rs2]
        
       
                    
        '''      
          #  for entry in active:
                
    def write_final_asm(self,filename):
        #for each procedure object in self.procObjects, write a line for every isnt in prebody
        #then each line in body
        #then each line in post body
        alllines=[]
      #  with open(filename,"w") as f:
        for proc in self.procObjects:
            alllines.append(f"{proc.name}:")
            for inst in proc.prebody_inst:
                    line=" ".join(inst.inst)
                    alllines.append(line)
            for inst in proc.body_inst:
                    line=" ".join(inst.inst)
                    alllines.append(line)
            for inst in proc.postbody_inst:
                    line=" ".join(inst.inst)
                    alllines.append(line)
        with open(filename,"w") as f:
            for line in self.setuplines:
                f.write(line +"\n")
            
            for line2 in alllines:
                f.write(line2 + "\n")
                
            with open(END_PROCS_PATH,"r") as f2:
                cont=f2.read()
                lines=cont.split("\n")
                for l in lines:
                    f.write(l + "\n")
            
        
    
    def write_final_asm2(self,filename):
        """
        Rebuilds the assembly file after allocation:
             - copy everything before the first basic-block label unchanged
            - for each block, re-emit its lines, but for instruction lines
            use the updated Instruction.inst tokens.
        """
        # 1) Read the normalized file so we can keep the header (.data, .globl, .text, etc.)
        with open(self.normalized_asm_path,"r") as f:
            
            all_lines = f.read().splitlines()

        # Find the first basic-block label line (e.g. "B0:")
        first_block_idx = None
        for i, line in enumerate(all_lines):
            if BLOCK_LABEL_PATTERN.match(line.strip()):
                first_block_idx = i
                break

        with open(filename, "w") as out:
            # 2) Write everything before B0: unchanged
            if first_block_idx is None:
                # no blocks? just dump file
                for line in all_lines:
                    out.write(line + "\n")
                return

            for i in range(first_block_idx):
                out.write(all_lines[i] + "\n")

            # 3) Now write all code from our Block objects
            for block in self.blocks:
                inst_idx = 0  # index into block.instructions

                for line in block.lines:
                    stripped = line.strip()

                    # Keep labels and non-op lines exactly as they were
                    parts = stripped.split()
                    if not parts:
                        out.write(line + "\n")
                        continue

                    op = parts[0]

                    # If this line is an instruction (op in OPS), replace with updated inst.inst
                    if op in OPS and not stripped.endswith(":"):
                        inst = block.instructions[inst_idx]
                        inst_idx += 1
                        out.write(" ".join(inst.inst) + "\n")
                    else:
                        # labels, directives, comments, markers like #start of body etc.
                        out.write(line + "\n")         
    
    def run(self):
        self.create_blocks() #now we have all the block objects. each has the instructions. 
        #and associated procedures will become known once we run assign_procedures and build_proc_map. so dont need to do the indexing anymore?
        self.assign_procedures()    #obtains the name of each procedure. for each block in the procedure, sets block.proc_name to the proc name
        self.build_proc_map()       #for each entry in the self.procs dict, which is keyed by proc name, appends all blocks that are in that proc.
        for proc in self.procs:
            procblocks=self.procs[proc]
            procname=proc
            self.process_blocks(procblocks,procname) #this is done once for each procedure. processes blocks and instructions in blocks
            #first it will probably get called for SUB
        for proc in self.procs:
            if proc=="read_err1" or proc=="cmd_err2":
                continue
            #list of inst is indexed list of all instructions in a proc. registers_used is list of all registers used/defined in the proc:
            list_of_inst, list_of_body_inst, registers_used,prebody_inst,postbody_inst=self.process_instructions_per_proc(proc)  
            virtual_registers=self.compute_live_ranges(list_of_body_inst)
            print(f"call live registers for proc {proc}:")
            register_ranges=self.compute_reg_ranges(list_of_body_inst,registers_used)
            #NOW: call a function that checks for call sites and 'live across call' registers
            call_live_regs,no_call_regs=self.compute_call_sites(list_of_body_inst,register_ranges)
           # for r in call_live_regs:
           #     print(r)
            
            blocks0=self.procs[proc]
            inst0=list_of_inst
            regused0=registers_used
            vr0=virtual_registers
            regranges0=register_ranges
            procobj=Procedure(
                    procname=proc, blocks=blocks0,instructions=inst0,regused=regused0,vr=vr0,
                    regranges=regranges0,call_live_reg=call_live_regs,no_call_reg=no_call_regs,body_inst=list_of_body_inst,
                    prebody_inst=prebody_inst,postbody_inst=postbody_inst)
            self.procObjects.append(procobj)
        
        for obj in self.procObjects:
            self.linear_scan(obj)
        self.write_final_asm(self.output_filename)
        
        
          
      #  if proc=="main":
      #          with open("temp.s","w") as filee:
      #              for inst in list_of_inst:
      #                  filee.write(f"{inst.index_in_proc}: {" ".join(inst.inst)}" + "\n")
          

        '''
        all_uses={} #dict mapping regnum to uses. e.g. uses[x9]=list of lines where x9 was used
        all_defs={}  #same idea as above but for defs. also, for each 'def list' for each register, the first element will be negative infinity and
                #the last element will be infinity. (not showing the code to implement this rn because its trivial)
        for each instruction index i from 0 to N-1:
            for each r in uses(i) (aka rs1, rs2 if they exist):
                uses=all_uses[r] if it already exists (aka have seen this reg before), else uses=[]
                uses.append(i)  #append the line num where reg was used
                all_uses[r]=uses   #update the overal uses list for that regnum
            for each r in defs(i) (aka rd if it exists):
                defs = all_defs[r] if it alr exists, else defs=[]
                defs.append(i) #append line num where reg was defined
                all_defs[r]=defs #update overall defs list for that regnum
        
        #NOW: logic to calculate live range intervals. 
        for each register used/defined in the proc:
            realintervals=[]
            for each element at index i in the 'defs' list for this register: (each defs[i] is a linnum indicating a line where reg was defined)
                temp_interval=[defs[i],defs[i+1]]
                actual_interval=[defs[i],None]
                for each use (a line num aka an integer) in the 'uses' list for this register:
                    if use is numerically within the interval defined by 'temp_interval':
                        actual_interval[1]= use #the interval goes from the line of definition to the line of the use
                if actual_interval[1] is not None: #if it was None, that means that the reg was never used in this 'defined interval', so we don't need to add this LR interval to our final set
                    realintervals.append(actual_interval)
     
        # for this part, my logic seems to be pretty straightforward. however
        #i am not sure whether i am doing this 'live range' computation correctly bc i might have implemented it wrong.
        #the idea behind doing it this way is to be able to be more optimal, e.g., how in the example above for x8 in sub, the algorithm you described
        #would have computed its 'live range' as [5,24]. but this algorithm would compute two live ranges: [negative inf,5] and [23,24]. i think that this 
        #is ultimately helpful because it means that a different register can be used in one of the LRs? is this information that im calculating even
        #helpful? i am not sure. i just wanted to try it out before resorting to doing the 'overestimated ranges' felt like 
                
                

                
                
        '''

        '''
        proc_indexes=self.get_proc_indexes()
        intervals=[[] for _ in range(len(proc_indexes))]
        for i in range(1,len(proc_indexes)):
            intervals[i-1]=[proc_indexes[i-1],proc_indexes[i]-1]
        intervals[len(proc_indexes)-1]=[proc_indexes[len(proc_indexes)-1],self.num_blocks-1]
        print(f"num blocks: {self.num_blocks}")
        print(f"intervals:")
        for inter in intervals:
            print(inter)
        proc_names={}
        for ind in proc_indexes:
            block=self.blocks[ind]
            secondline=block[1]
            procname=secondline.strip()[:-1]
            proc_names[ind]=procname
        print(f"proc names:")

        for i in range(0,len(proc_names)):
            name=proc_names[i]
            interval=intervals[i]
            print(f"block {i}:{name}")
            print(f"proc block interval: {interval}")
            proc_sublist=self.blocks[interval[0]:interval[1]+1]
            self.proc_blocks[name]=proc_sublist
            print(f"proc sub blocks:")
        '''
        '''    
        for block in self.blocks:
            must_reassign=False
            for inst in block.instructions:
                rd_as_int=int(inst.rd[1:]) if inst.rd is not None and inst.rd != "Mem" else None
                rs1_as_inst=int(inst.rs1[1:]) if inst.rs1 is not None else None
                rs2_as_inst=int(inst.rs2[1:]) if inst.rs2 is not None else None
                if rd_as_int is not None:
                    if rd_as_int>31:
                        must_reassign=True
                        break
                if rs1_as_inst is not None:
                    if rs1_as_inst>31:
                        must_reassign=True
                        break
                if rs2_as_inst is not None:
                    if rs2_as_inst>31:
                        must_reassign=True
                        break
            if must_reassign:
                print(f"reassignment must occur for block B{block.index}")
                self.reassign_registers(block)
        '''
        #self.reassign_registers()
            
             
            
        
        
        
      
    
    



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
    
- ok also, another option would be to implement some sort of free_temp functionality in my first pass. and then in cases where i know a reg is only going to be
used for something very temporary, i can call free_temp after emitting.
- but this cant necessarily be used in tandem with what im doing rn with the bottom-up reg searching. so lemme try the bottom-up thing first and see if
that is enough


- ok CURRENTLY am caught up!!! for each block, i know the registers that are free to be used after it.
- wait, i have to account for the saving and restoring of s0-11...dont want to 'reuse free registers' in the prologue and epilogue

- uhhhh... i forgot to account for cases where the registers that we dont want to touch--e.g., those which are live across blocks--are numbered above 31
- i also dont think my current impl accounts for registers which are live past the end of a given block. if they are, we do NOT want to reassign them. 
    and if they r numbered above 31 we prob still dont want to reassign them, and want to wait until an additional pass
    -so maybe, for each block, also keep a list of fixed_registers. calculate this how?
        - for each reg we can't free, we put it in this list.
- at that point, if i am only modifying registers that are ONLY USED in their currnet block scope, and are known to not be reused later (aka registers not in the 
    fixed register list), ...i can create RegStack objects for each block rather than globally. bc the free registers from block 3, for ex, could easily be used
    in both block 4 and block 5
    
- left off in reassign_registers

'''
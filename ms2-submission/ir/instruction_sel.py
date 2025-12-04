from ir.helpers import Frame,GlobalsFrame,StructLayout
import json

class InstructionSelector():
    def __init__(self,ASTJSON,structs,funcs,glbls,variables,filename):
        self.ast_json=ASTJSON
        self.structs=structs
        self.funcs=funcs
        self.globals=glbls 
        self.vars=variables
        self.globalsFrame=GlobalsFrame(self.structs,self.globals)
        self.globals_map=None
        self.frames={}
        self.struct_layouts=[]
        self.output_file=filename.split(".")[0] + ".s"
        self.oplines=[]
        
        
    
        for f in self.funcs:
            frame=Frame(variables=self.vars,fname=f)
            self.frames[f] = frame
            print(f"Frame {f} (size {frame.frame_size}):")
            print("ra @ 0(fp)")
            print("s0 @ -4(fp)")
            for v in frame.local_offset:
                print(f"{v} @ {frame.local_offset[v]}(fp) ---------> {frame.register_map[v]}")
            print("\n")
            
        print(f"\n\n")
        self.globals_map = self.globalsFrame.globals_map
        print("Globals:")
        for e in self.globals_map:
            print(f"{e} -> Label({self.globals_map[e]["Label"]}) ... Initialized={self.globals_map[e]["Initialized"]}")

        
        for s in self.structs:
            stlayout = StructLayout(self.structs[s],s)
            self.struct_layouts.append(stlayout)
        
        with open(self.ast_json, "r") as j:
            data = json.load(j)
            for f in data["functions"]:
                self.process_function(f)
                
        self.write_file()        
        
        
        
    def process_function(self,root):
        fname = root["name"]
        frame = self.frames[fname]
        frame.next_temp=frame.num_locals
        curr_reg = frame.num_locals
        self.oplines.append(f"{fname}:")
            
        #if in BOTH global and register map. use local. if only in global, use global    
            
        #addi [targetreg] [srcreg] zero
        for stmt in root["body"]:   
            if stmt["node"]=="Assign": #for every assignment statement
                target = stmt["target"]["name"]
                print(f"processing assignment statement for {target}")
                rhslines,rhsreg=self.process_expression(stmt["source"],frame)
                if rhslines==0:
                    continue
                for l in rhslines:
                    self.oplines.append(l)
                if target not in frame.register_map and target in self.globals_map:    #not in the local map. if it is in the local map, we default to referencing the local var's namespace
                        print(f"var {target} not in the reg map")
                        addr_reg=frame.new_temp()
                        l1 = f"la {addr_reg} {self.globals_map[target]["Label"]}"
                        l2 = f"sw {rhsreg} 0({addr_reg})"
                        self.oplines.append(l1)
                        self.oplines.append(l2)
                        continue
                else:
                    treg = self.get_regnum(target,frame)  #the register where the variable who is on LHS of assignment stmt is stored
                    print(f"treg for {target} is {treg}")
                    print(f"stmt at source is {stmt["source"]}. frame is {frame}. curreg is {curr_reg}")
                    t = f"addi {treg} {rhsreg} 0x0"          #saving the value on RHS to register on LHS
                    self.oplines.append(t)    
                            
        
    def process_expression(self,root,frame): #RETURNS the new current register, after incrementations were done
            '''
            root = the 'source' section of an assignment stmt node. aka stmt["source"]
            '''
            lines=[]
            exprtype = root["node"]
            match exprtype:
                case "Dot":
                    return 0,None
                case "False":
                    curr=frame.new_temp()
                    l = f"li {curr} 0x0"
                    sreg = f"{curr}" #the register where the result of the expression is saved
                    lines.append(l)
                    return lines,sreg

                case "True":
                    curr=frame.new_temp()
                    l=f"li {curr} 0x1"
                    sreg=f"{curr}"
                    lines.append(l)
                    return lines,sreg
                case "Id":
                    return self.process_id(root,frame)
                case "New":
                    return 0,None
                case "Null":
                    return 0,None
                case "Read":
                    return 0,None
                case "Int":
                    curr=frame.new_temp()
                    val = root["value"]
                    l=f"li {curr} {val}"
                    sreg= f"{curr}"
                    lines.append(l)
                    return lines,sreg
                case "Invocation/CallExpr":
                    return 0,None
                case "Unary":
                    return self.process_unary(root,frame)
                case "Binary":
                    return self.process_binary(root,frame)
                
    
    def load_global(self,name,frame):    #emits code to load a global var into a register, and returns the code as well as the name of the reg where global's val is stored
        tcurr=frame.new_temp()
        tcurr1=frame.new_temp()
        lines=[]
        lines.append(f"la {tcurr} {name}")
        lines.append(f"lw {tcurr1} 0({tcurr})")     #now, the value of the global variable is stored in register tcurr1. 
        return lines, tcurr1
            
    def process_id(self,node,frame):
        '''
        node = the 'source' section of an assignment stmt node. aka stmt["source"]
        '''
        lines=[]
        sourceid=node["name"]
        if sourceid in frame.register_map:  #source is a local var
            curr=frame.new_temp()
            srcreg = frame.register_map[sourceid]
            l=f"addi {curr} {srcreg} 0x0"
            lines.append(l)
            return lines,curr
        elif sourceid in self.globals_map:
            loadlines,global_val_reg = self.load_global(sourceid,frame)
            [lines.append(l) for l in loadlines]
            tcurr2=frame.new_temp()
            lines.append(f"addi {tcurr2} {global_val_reg} 0x0")
            return lines,tcurr2
    
    def process_binary(self,node,frame):
        return 0,None
    
    def process_unary(self,node,frame):
        '''
        node = the 'source' section of an assignment stmt node. aka stmt["source"]
        NOTE: RN THIS ONLY WORKS IN CASES WHERE THE OPERAND IS AN ID!!!! NEED TO FIGURE OUT OTHER CASES
        '''
        lines=[]
        source_op=node["expression"]
        if source_op["node"] != "Id":
            return 0,None   #not yet implemented
        if source_op["node"] == "Id":
            srcvar = source_op["name"] #aka 'r' for r=-r
            if srcvar in frame.register_map:
                pass
                
            
        return 0,None
    
    def get_regnum(self,vname,frame):
        return frame.register_map[vname]
        
    
    def write_file(self):
        with open(self.output_file,"w") as f:
            f.write(".globl main\n .import berkeley_utils.s # the ecall utilities\n .import read_int.s # the file read wrapper\n\n")
            f.write("\n")
            f.write(".data\n")
            for g in self.globals:
                str = f"{g}: .word 0x0"
                f.write(str + "\n")
            f.write("\n.text\n")
            for l in self.oplines:
                f.write(l + "\n")
        
        
        
    
    
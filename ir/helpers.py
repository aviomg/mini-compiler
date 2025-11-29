
templates={}
templates['prologue'] = "addi sp sp -4\n sw ra 0(sp)\n addi sp sp -4\n sw s0 0(sp)"

'''
Possible impl:
at the start of a function, emit the prologue template, followed by saving all of the locals (defined in the Frame) class on the stack
at the specified offset. e.g. , for each local:
    addi sp sp -4
    addi t0 zero 0
    sw t0 0(sp)

then, whenever the values get assigned/used, look up their offset and retrieve them into a register, e.g. if we then have the line g=3, and localoffset[g]=-12:
    for sub, we know size of frame is 20, meaning the last thing gets stored at (-1 * sizeofframe-4) =  -16. and currently our sp = this var = -16.
    if we know that localoffset[g]=-12, then we know how to move sp up by computing the difference (-12) - (-16) = 4. so we do:
        addi sp sp 4 #now it points to g
        addi t0 zero 3 
        sw t0 0(sp) #g = 3
        
        
1. if any params, load them FROM the param registers--a0-a2?--into registers at the regnum given by the Frame object.
2. then do execution
3. for calls, copy values into the param registers


- wait also, i COULD be using .space for the structs? works for almsot everything except a nested struct.
    - do a pass to find ALL declarations of structs. for each, assign a label and a .space and save this in the ST. 
    - so basically, keeping all structs in the static data area? ok maybe not a good idea.
    - but i can def do this for globally declared structs
    
'''

class GlobalsFrame():
    def __init__(self,structs,glbls):
        self.globals_map={} #maps globals names to their labels
        for g in glbls:
            self.globals_map[g]={"Label":glbls[g]["label"],"Initialized":False,"Type":glbls[g]["type"]}

    def setInitialized(self,varname):
        if varname not in self.globals_map:
            print(f"the variable {varname} does not exist or is not a global variable. setInitialized call failed.")
            return
        self.globals_map[varname]["Initialized"]=True
        
#0,1,2,3,4: metas (zero, ra, sp, gp, thread pointer)
#5-7: temporaries (t0-t2)(must be saved by caller before making function call; can be used by callee)
#8-9: callee-saved (s0,s1) 
#                  (must be saved by callee at beginning of function call, then restored before function return; can be used by caller without having to worry about overwrites)
#10-11: argument and return val registers (a0,a1): should not use these as temporaries since return vals wil be placed here
#12-17: argument registers (a2-a7): must be saved by caller before making function call (esp since args need to be placed here); can be used by callee
#18-27: callee-saved (s2-s11)
#28-31: temporaries (t3-t6)
#ok so ban 10 and 11, for now.
            
class Frame():
    #a table to keep track, for each local, whether it is currently in a register or not. when we load something into memory, we will set 'in reg' to false
    def __init__(self,variables,fname):
        self.fname=fname
        self.variables=variables
        self.frame_size=(len(variables[fname]) * 4) + 8
        self.local_offset = {}
        self.register_map={}
        self.num_locals=len(variables[fname])
        self.types={}
        self.kinds={}
        regcounter=5
        for l in variables[fname]:
            self.local_offset[l]=variables[fname][l]["offset"]
            self.register_map[l]="x"+str(regcounter)
            self.types[l]=variables[fname][l]["type"]
            self.kinds[l]=variables[fname][l]["kind"]
            print(f"var: {l}.......reg:{self.register_map[l]}")
          #  regcounter+=1
   
        print("\n")
        
       # if self.num_locals+5==10 or self.num_locals+5==11:
       #     self.next_temp=12
       # else:
       #     self.next_temp=self.num_locals+5
        self.next_temp=5
  
        
    def addr_of_local(self,name): #eg in sub, g
        ans = self.local_offset[name]
        return ans
    
    def new_temp(self):
        if self.next_temp==10:
            reg=f"x{self.next_temp+2}"
            self.next_temp+=3
            return reg
        if self.next_temp==11:
            reg=f"x{self.next_temp+1}"
            self.next_temp+=2
        else:
            reg=f"x{self.next_temp}"
            self.next_temp+=1
            return reg
    

class StructLayout():
    def __init__(self,struct,structname):
        self.struct=struct
        self.name=structname
        self.struct_fields=self.struct["fields"]
        self.size=0
        self.field_offsets={}
        self.field_types={}
      #  print(f"struct name is {self.name}")
        for f in self.struct_fields:
            self.field_offsets[f]=self.struct_fields[f]["offset"]
        for f in self.struct_fields:
            ft=self.struct_fields[f]["type"]
            words=ft.split(" ")
            if len(words)>1:
                ft=words[1]
            self.field_types[f]=ft
        for f in self.struct_fields:
            print(f"{f} with offset {self.field_offsets[f]} and type {self.field_types[f]}")
        
            
        
        
        
        
        #so far we have each field and its offset. now need to compute size
        for f in self.struct_fields:
            if self.struct_fields[f]["type"] == "int" or self.struct_fields[f]["type"] == "bool":
                self.size+=4
            else:
                self.size+=4
        
       # print(f"size of struct {self.name} is {self.size}")
       
        
        '''
        for this: struct Quad{
                        int width;
                        int height;
                        bool isSquare;
                        struct Pair coords;
                        };
            1. allocate 16 bytes of space. for the fourth block in the allocated heap, just call malloc? and store the pointer?
            2. yeah, i guess the size does not necessarily have to be dynamic
            
            so then if i do: 
            struct Quad q;
            ....
            q.coords.x=10
            
            then...i have to go to the offset that 'coords' is stored at. get the pointer. follow the pointer. get offset that x is stored at. store the new value.
            ok i guess it isnt that hard. just have to figure out how to use malloc ????? the assembly version
        '''
        
        
        '''
        SUB: frame size = 12.
        x -> 0
        g -> 4
        hello -> 8
        '''
    
 
        
        
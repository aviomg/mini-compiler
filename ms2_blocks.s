.globl main
 .import berkeley_utils.s # the ecall utilities
.import read_int.s # the file read wrapper
 
 
.data
filepath_ptr: .word
error_string1: .string "read_int returned an error\n"
error_string2: .string "incorrect number of arguments\n"
g: .word 0x0
h: .word 0x0
 
.text
 
B0:
iftest:
#start of prologue
addi x2 x2 -60 
sw x0 0(x2) #this holds var readnum
sw x0 4(x2) #this holds var ans
sw x1 8(x2)
sw x8 12(x2)
sw x9 16(x2)
sw x18 20(x2)
sw x19 24(x2)
sw x20 28(x2)
sw x21 32(x2)
sw x22 36(x2)
sw x23 40(x2)
sw x24 44(x2)
sw x25 48(x2)
sw x26 52(x2)
sw x27 56(x2)
sw x10 0(x2) #storing param at offset instead of in reg
#end of prologue
#start of body
li x5 50
sw x5 4(x2) #placing local's value in stack rather than reg
lw x7 0(x2)
li x8 4
slt x6 x8 x7
ifBlockStart0:
beqz x6 else0
 
B1:
li x6 0x0
jal x0 endIfBlock0
 
B2:
else0:
li x6 0x1
endIfBlock0:
ifBlockStart1:
beq x6 x0 else1
 
B3:
if1:
lw x12 4(x2)
addi x9 x12 200
sw x9 4(x2) #placing local's value in stack rather than reg
jal x0 endIfBlock1
 
B4:
else1:
lw x14 4(x2)
addi x13 x14 100
sw x13 4(x2) #placing local's value in stack rather than reg
endIfBlock1:
#end of body
#start of epilogue
lw x15 4(x2)
addi x10 x15 0
addi x2 x2 8
lw x1 0(x2)
lw x8 4(x2)
lw x9 8(x2)
lw x18 12(x2)
lw x19 16(x2)
lw x20 20(x2)
lw x21 24(x2)
lw x22 28(x2)
lw x23 32(x2)
lw x24 36(x2)
lw x25 40(x2)
lw x26 44(x2)
lw x27 48(x2)
addi x2 x2 52
ret
 
B5:
#end of epilogue
main:
#start of body
addi s11 x0 2      # check for correct number of command line arguments
bne x10 s11 cmd_err2
 
B6:
lw x10 4(x11)         # load the filepath 
la x11 filepath_ptr  # load address of filepath home location 
sw x10 0(x11)         # save the filepath to its home location
addi x2 x2 -12
sw x0 0(x2) #this holds var ex
sw x0 4(x2) #this holds var r
sw x0 8(x2) #this holds var readnum
li s11 10
sw s11 0(x2) #placing local's value in stack rather than reg
li s11 5
lw s10 0(x2)
mul s10 s11 s10
sw s10 4(x2) #placing local's value in stack rather than reg
whileStart0:
lw s10 0(x2)
li s11 12
slt s11 s10 s11
beq s11 x0 endWhile0
 
B7:
lw x10 filepath_ptr #start of precall
addi x2 x2 -4
sw x1 0(x2)
jal x1 read_int
 
B8:
#start of postreturn
lw x1 0(x2) 
addi x2 x2 4
bne x11 x0 read_err1
 
B9:
sw x10 8(x2) #placing local's value in stack rather than reg
lw s11 8(x2)
li s10 4
slt s10 s10 s11
ifBlockStart2:
beqz s10 else2
 
B10:
li s10 0x0
jal x0 endIfBlock2
 
B11:
else2:
li s10 0x1
endIfBlock2:
ifBlockStart3:
beq s10 x0 else3
 
B12:
if3:
lw s10 4(x2)
addi s10 s10 200
sw s10 4(x2) #placing local's value in stack rather than reg
jal x0 endIfBlock3
 
B13:
else3:
lw s10 4(x2)
addi s10 s10 100
sw s10 4(x2) #placing local's value in stack rather than reg
endIfBlock3:
lw s10 4(x2)
addi x10 s10 0
jal print_int
 
B14:
li x10 0x0A
jal print_char
 
B15:
lw s10 0(x2)
addi s10 s10 1
sw s10 0(x2) #placing local's value in stack rather than reg
j whileStart0
 
B16:
endWhile0:
addi x10 x0 0
jal x0 exit
 
B17:
#end of body
read_err1:
    la x10 error_string1
    jal print_str
 
B18:
    li x10 1
    jal exit
 
B19:
cmd_err2:
    la x10 error_string2
    jal print_str
 
B20:
    li x10 1
    jal exit
 
B21:




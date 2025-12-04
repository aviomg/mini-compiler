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
iftest:
#start of prologue
addi sp sp -60 
sw zero 0(sp) #this holds var readnum
sw zero 4(sp) #this holds var ans
sw ra 8(sp)
sw s0 12(sp)
sw s1 16(sp)
sw s2 20(sp)
sw s3 24(sp)
sw s4 28(sp)
sw s5 32(sp)
sw s6 36(sp)
sw s7 40(sp)
sw s8 44(sp)
sw s9 48(sp)
sw s10 52(sp)
sw s11 56(sp)
sw a0 0(sp) #storing param at offset instead of in reg
#end of prologue
#start of body
li x5 50
sw x5 4(sp) #placing local's value in stack rather than reg
lw x7 0(sp)
li x8 4
slt x6 x8 x7
ifBlockStart0:
beqz x6 else0
li x6 0x0
jal zero endIfBlock0
else0:
li x6 0x1
endIfBlock0:
ifBlockStart1:
beq x6 zero else1
if1:
lw x12 4(sp)
addi x9 x12 200
sw x9 4(sp) #placing local's value in stack rather than reg
jal zero endIfBlock1
else1:
lw x14 4(sp)
addi x13 x14 100
sw x13 4(sp) #placing local's value in stack rather than reg
endIfBlock1:
#end of body
#start of epilogue
lw x15 4(sp)
addi a0 x15 0
addi sp sp 8
lw ra 0(sp)
lw s0 4(sp)
lw s1 8(sp)
lw s2 12(sp)
lw s3 16(sp)
lw s4 20(sp)
lw s5 24(sp)
lw s6 28(sp)
lw s7 32(sp)
lw s8 36(sp)
lw s9 40(sp)
lw s10 44(sp)
lw s11 48(sp)
addi sp sp 52
ret
#end of epilogue
main:
#start of body
addi t0 zero 2      # check for correct number of command line arguments
bne a0 t0 cmd_err2
lw a0 4(a1)         # load the filepath 
la a1 filepath_ptr  # load address of filepath home location 
sw a0 0(a1)         # save the filepath to its home location
addi sp sp -12
sw zero 0(sp) #this holds var ex
sw zero 4(sp) #this holds var r
sw zero 8(sp) #this holds var readnum
li x5 10
sw x5 0(sp) #placing local's value in stack rather than reg
li x7 5
lw x8 0(sp)
mul x6 x7 x8
sw x6 4(sp) #placing local's value in stack rather than reg
whileStart0:
lw x12 0(sp)
li x13 12
slt x9 x12 x13
beq x9 zero endWhile0
lw a0 filepath_ptr #start of precall
addi sp sp -4
sw ra 0(sp)
jal ra read_int
#start of postreturn
lw ra 0(sp) 
addi sp sp 4
bne a1 zero read_err1
sw a0 8(sp) #placing local's value in stack rather than reg
lw x15 8(sp)
li x16 4
slt x14 x16 x15
ifBlockStart2:
beqz x14 else2
li x14 0x0
jal zero endIfBlock2
else2:
li x14 0x1
endIfBlock2:
ifBlockStart3:
beq x14 zero else3
if3:
lw x18 4(sp)
addi x17 x18 200
sw x17 4(sp) #placing local's value in stack rather than reg
jal zero endIfBlock3
else3:
lw x20 4(sp)
addi x19 x20 100
sw x19 4(sp) #placing local's value in stack rather than reg
endIfBlock3:
lw x21 4(sp)
addi a0 x21 0
jal print_int
li a0 0x0A
jal print_char
lw x23 0(sp)
addi x22 x23 1
sw x22 0(sp) #placing local's value in stack rather than reg
j whileStart0
endWhile0:
addi a0 zero 0
jal zero exit
#end of body
read_err1:
    la a0 error_string1
    jal print_str
    li a0 1
    jal exit
cmd_err2:
    la a0 error_string2
    jal print_str
    li a0 1
    jal exit

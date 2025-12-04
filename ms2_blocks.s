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
addi sp sp -52
sw ra 0(sp)
sw s0 4(sp)
sw s1 8(sp)
sw s2 12(sp)
sw s3 16(sp)
sw s4 20(sp)
sw s5 24(sp)
sw s6 28(sp)
sw s7 32(sp)
sw s8 36(sp)
sw s9 40(sp)
sw s10 44(sp)
sw s11 48(sp)
addi x5 a0 0
li x7 50
addi x6 x7 0x0
addi x9 x5 0x0
li x12 4
slt x8 x12 x9
 
conditionalBlockStart0:
beqz x8 else0
li x8 0x0
jal zero endConditionalBlock0
else0:
li x8 0x1
endConditionalBlock0:
 
conditionalBlockStart1:
beq x8 zero else1
if1:
addi x14 x6 0x0
addi x15 x6 0x0
addi x13 x15 200
addi x6 x13 0x0
jal zero endConditionalBlock1
else1:
addi x17 x6 0x0
addi x18 x6 0x0
addi x16 x18 100
addi x6 x16 0x0
endConditionalBlock1:
 
addi x19 x6 0x0
addi a0 x19 0
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


main:
addi t0 zero 2      # check for correct number of command line arguments
bne a0 t0 cmd_err2
lw a0 4(a1)         # load the filepath 
la a1 filepath_ptr  # load address of filepath home location 
sw a0 0(a1)         # save the filepath to its home location
li x8 10
addi x5 x8 0x0
li x12 5
addi x13 x5 0x0
mul x9 x12 x13
addi x6 x9 0x0
 
whileStart0:
addi x15 x5 0x0
li x16 12
slt x14 x15 x16
beq x14 zero endWhile0
lw a0 filepath_ptr
precall0:
addi sp sp -16
sw ra 0(sp)
sw x5 4(sp)
sw x6 8(sp)
sw x7 12(sp)
jal ra read_int
postreturn0:
lw ra 0(sp)
lw x5 4(sp)
lw x6 8(sp)
lw x7 12(sp)
addi sp sp 16
bne a1 zero read_err1
addi x7 a0 0x0
addi x18 x7 0x0
li x19 4
slt x17 x19 x18
 
conditionalBlockStart2:
beqz x17 else2
li x17 0x0
jal zero endConditionalBlock2
else2:
li x17 0x1
endConditionalBlock2:
 
conditionalBlockStart3:
beq x17 zero else3
if3:
addi x21 x6 0x0
addi x22 x6 0x0
addi x20 x22 200
addi x6 x20 0x0
jal zero endConditionalBlock3
else3:
addi x24 x6 0x0
addi x25 x6 0x0
addi x23 x25 100
addi x6 x23 0x0
endConditionalBlock3:
 
addi x26 x6 0x0
addi a0 x26 0
jal print_int
li a0 0x0A
jal print_char
addi x28 x5 0x0
addi x29 x5 0x0
addi x27 x29 1
addi x5 x27 0x0
j whileStart0
endWhile0:
 
addi a0 zero 0
jal zero exit


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

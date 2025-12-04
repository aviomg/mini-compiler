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
sub:
#start of prologue
addi sp sp -64 
sw zero 0(sp) #this holds var a
sw zero 4(sp) #this holds var b
sw zero 8(sp) #this holds var ans
sw ra 12(sp)
sw s0 16(sp)
sw s1 20(sp)
sw s2 24(sp)
sw s3 28(sp)
sw s4 32(sp)
sw s5 36(sp)
sw s6 40(sp)
sw s7 44(sp)
sw s8 48(sp)
sw s9 52(sp)
sw s10 56(sp)
sw s11 60(sp)
sw a0 0(sp) #storing param at offset instead of in reg
sw a1 4(sp) #storing param at offset instead of in reg
#end of prologue
#start of body
lw x6 0(sp)
lw x7 4(sp)
sub x5 x6 x7
sw x5 8(sp) #placing local's value in stack rather than reg
#end of body
#start of epilogue
lw x8 8(sp)
addi a0 x8 0
addi sp sp 12
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
addxy:
#start of prologue
addi sp sp -60 
sw zero 0(sp) #this holds var pair
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
lw x6 0(sp)
addi x7 x6 0
lw x7 0(x7)
lw x8 0(sp)
addi x9 x8 4
lw x9 0(x9)
add x5 x7 x9
sw x5 4(sp) #placing local's value in stack rather than reg
lw x12 4(sp)
lw x13 0(sp)
addi x14 x13 0
sw x12 0(x14)
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
addi sp sp -24
sw zero 0(sp) #this holds var ex
sw zero 4(sp) #this holds var r
sw zero 8(sp) #this holds var b
sw zero 12(sp) #this holds var readnum
sw zero 16(sp) #this holds var z
sw zero 20(sp) #this holds var p
li a0 8
jal malloc
sw a0 20(sp) #placing local's value in stack rather than reg
li x5 75
lw x6 20(sp)
addi x7 x6 4
sw x5 0(x7)
li x8 25
lw x9 20(sp)
addi x12 x9 0
sw x8 0(x12)
lw x13 20(sp)
addi x14 x13 0
lw x14 0(x14)
lw x15 20(sp)
addi x16 x15 4
lw x16 0(x16)
addi a0 x14 0x0 #start of precall
addi a1 x16 0x0
addi sp sp -4
sw ra 0(sp)
jal sub
#start of postreturn
lw ra 0(sp) 
addi sp sp 4
sw a0 4(sp) #placing local's value in stack rather than reg
lw x17 4(sp)
addi a0 x17 0
jal print_int
li a0 0x0A
jal print_char
lw x18 20(sp)
addi a0 x18 0x0 #start of precall
addi sp sp -4
sw ra 0(sp)
jal addxy
#start of postreturn
lw ra 0(sp) 
addi sp sp 4
lw x19 20(sp)
addi x20 x19 0
lw x20 0(x20)
addi a0 x20 0
jal print_int
li a0 0x0A
jal print_char
li x21 10
sw x21 0(sp) #placing local's value in stack rather than reg
lw x22 4(sp)
sub x23 zero x22
sw x23 4(sp) #placing local's value in stack rather than reg
lw x27 4(sp)
addi x26 x27 2
li x28 3
mul x25 x26 x28
lw x29 0(sp)
li x24 0x0
whileStart0:
blt x25 x29 endWhile0
sub x25 x25 x29
addi x24 x24 0x1
j whileStart0
endWhile0:
sw x24 16(sp) #placing local's value in stack rather than reg
lw x30 16(sp)
addi a0 x30 0
jal print_int
li a0 0x0A
jal print_char
lw x32 4(sp)
lw x33 0(sp)
slt x31 x33 x32
ifBlockStart0:
beqz x31 else0
li x31 0x0
jal zero endIfBlock0
else0:
li x31 0x1
endIfBlock0:
sw x31 8(sp) #placing local's value in stack rather than reg
lw x35 4(sp)
lw x36 20(sp)
addi a0 x36 0x0 #start of precall
addi sp sp -4
sw ra 0(sp)
jal addxy
#start of postreturn
lw ra 0(sp) 
addi sp sp 4
add x34 x35 a0
sw x34 0(sp) #placing local's value in stack rather than reg
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

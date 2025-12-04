.globl main
 .import berkeley_utils.s # the ecall utilities
.import read_int.s # the file read wrapper
 
 
.data
filepath_ptr: .word
error_string1: .string "read_int returned an error\n"
error_string2: .string "incorrect number of arguments\n"
g: .word 0x0
h: .word 0x0
shapes1: .word 0x0
 
.text
main:
#start of body
addi sp sp -20
sw zero 0(sp) #this holds var x
sw zero 4(sp) #this holds var ex
sw zero 8(sp) #this holds var r
sw zero 12(sp) #this holds var b
sw zero 16(sp) #this holds var c1
li a0 8
jal malloc
sw a0 16(sp) #placing local's value in stack rather than reg
li x5 15
lw x6 16(sp)
addi x7 x6 0
sw x5 0(x7)
li x8 2
lw x9 16(sp)
addi x12 x9 4
sw x8 0(x12)
li x13 20
sw x13 8(sp) #placing local's value in stack rather than reg
li x14 3
la x15 g
sw x14 0(x15)
li x16 5
sw x16 0(sp) #placing local's value in stack rather than reg
sw zero 4(sp) #placing local's value in stack rather than reg
li x18 0x0
sw x18 12(sp) #placing local's value in stack rather than reg
la x20 g
lw x21 0(x20)
sw x21 0(sp) #placing local's value in stack rather than reg
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

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
 
B0:
main:
#start of body
addi x2 x2 -20
sw x0 0(x2) #this holds var x
sw x0 4(x2) #this holds var ex
sw x0 8(x2) #this holds var r
sw x0 12(x2) #this holds var b
sw x0 16(x2) #this holds var c1
li x10 8
jal malloc
 
B1:
sw x10 16(x2) #placing local's value in stack rather than reg
li x5 15
lw x6 16(x2)
addi x7 x6 0
sw x5 0(x7)
li x8 2
lw x9 16(x2)
addi x12 x9 4
sw x8 0(x12)
li x13 20
sw x13 8(x2) #placing local's value in stack rather than reg
li x14 3
la x15 g
sw x14 0(x15)
li x16 5
sw x16 0(x2) #placing local's value in stack rather than reg
sw x0 4(x2) #placing local's value in stack rather than reg
li x18 0x0
sw x18 12(x2) #placing local's value in stack rather than reg
la x20 g
lw x21 0(x20)
sw x21 0(x2) #placing local's value in stack rather than reg
addi x10 x0 0
jal x0 exit
 
B2:
#end of body
read_err1:
    la x10 error_string1
    jal print_str
 
B3:
    li x10 1
    jal exit
 
B4:
cmd_err2:
    la x10 error_string2
    jal print_str
 
B5:
    li x10 1
    jal exit
 
B6:



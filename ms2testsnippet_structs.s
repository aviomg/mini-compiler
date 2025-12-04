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
li s11 15
lw s10 16(x2)
addi s10 s10 0
sw s11 0(s10)
li s10 2
lw s11 16(x2)
addi s11 s11 4
sw s10 0(s11)
li s11 20
sw s11 8(x2) #placing local's value in stack rather than reg
li s11 3
la s10 g
sw s11 0(s10)
li s10 5
sw s10 0(x2) #placing local's value in stack rather than reg
sw x0 4(x2) #placing local's value in stack rather than reg
li s10 0x0
sw s10 12(x2) #placing local's value in stack rather than reg
la s10 g
lw s10 0(s10)
sw s10 0(x2) #placing local's value in stack rather than reg
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




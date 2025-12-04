.globl main
 .import berkeley_utils.s # the ecall utilities
.import read_int.s # the file read wrapper
 
 
.data
g: .word 0x0
h: .word 0x0
 
.text
main:
li x8 20
addi x7 x8 0x0
li x9 3
la x10 g
sw x9 0(x10)
li x11 5
addi x5 x11 0x0
addi x13 x5 0x0
addi x15 x7 0x0
la x16 g
lw x17 0(x16)
mul x14 x15 x17
sub x12 x13 x14
addi x5 x12 0x0
li x18 11
addi x6 x18 0x0
sub:
li x8 0x0
addi x7 x8 0x0
li x9 3
addi x6 x9 0x0
add:
addi x7 x5 0x0
li x8 1
sub x6 x7 x8
addi x5 x6 0x0

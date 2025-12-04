.globl main
 .import berkeley_utils.s # the ecall utilities
.import read_int.s # the file read wrapper
 
 #this snippet can be used for testing nested dot and lvaluedot nodes. but first need to make the reg count go down lol
.data
g: .word 0x0
h: .word 0x0
s: .word 0x0
 
.text
main:
li a0 8
jal malloc
addi x7 a0 0x0
li a0 8
jal malloc
addi x8 a0 0x0
li a0 16
jal malloc
addi x9 a0 0x0
li x11 10
addi x12 x7 4
sw x11 0(x12)
li x13 2
addi x14 x7 0
sw x13 0(x14)
li x15 25
addi x16 x8 0
sw x15 0(x16)
li x17 75
addi x18 x8 4
sw x17 0(x18)
li x19 10
addi x20 x9 0
sw x19 0(x20)
li x21 12
addi x22 x9 4
sw x21 0(x22)
li x23 0x0
addi x24 x9 8
sw x23 0(x24)
addi x25 x8 0x0
addi x26 x9 12
sw x25 0(x26)
li a0 16
jal malloc
la x27 s
sw a0 0(x27)
li x28 0x0
la x29 s
lw x30 0(x29)
addi x31 x30 0
sw x28 0(x31)
la x32 s
lw x33 0(x32)
addi x34 x33 0
lw x34 0(x34)
addi x6 x34 0x0
addi x35 x8 0x0
la x36 s
lw x37 0(x36)
addi x38 x37 4
sw x35 0(x38)
addi x39 x9 0x0
la x40 s
lw x41 0(x40)
addi x42 x41 8
sw x39 0(x42)
addi x43 x9 0x0
la x44 s
lw x45 0(x44)
addi x46 x45 12
sw x43 0(x46)
la x47 s
lw x48 0(x47)
addi x49 x48 8
lw x50 0(x49)
addi x51 x50 12
lw x52 0(x51)
addi x53 x52 0
lw x53 0(x53)
addi x5 x53 0x0

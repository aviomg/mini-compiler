sub:
addi x2 x2 -52
sw x1 0(sp)
sw x8 4(sp)
sw x9 8(sp)
sw x18 12(sp)
sw x19 16(sp)
sw x20 20(sp)
sw x21 24(sp)
sw x22 28(sp)
sw x23 32(sp)
sw x24 36(sp)
sw x25 40(sp)
sw x26 44(sp)
sw x27 48(sp)
addi x5 x10 0
addi x6 x11 0
addi x9 x5 0x0
addi x12 x6 0x0
sub x8 x9 x12
addi x7 x8 0x0
addi x13 x7 0x0
addi x10 x13 0
lw x1 0(sp)
lw x8 4(sp)
lw x9 8(sp)
lw x18 12(sp)
lw x19 16(sp)
lw x20 20(sp)
lw x21 24(sp)
lw x22 28(sp)
lw x23 32(sp)
lw x24 36(sp)
lw x25 40(sp)
lw x26 44(sp)
lw x27 48(sp)
addi x2 x2 52
ret



--------------------------------------

addxy:
addi x2 x2 -52
sw x1 0(sp)
sw x8 4(sp)
sw x9 8(sp)
sw x18 12(sp)
sw x19 16(sp)
sw x20 20(sp)
sw x21 24(sp)
sw x22 28(sp)
sw x23 32(sp)
sw x24 36(sp)
sw x25 40(sp)
sw x26 44(sp)
sw x27 48(sp)
addi x5 x10 0
addi x8 x5 0
lw x8 0(x8)
addi x9 x5 4
lw x9 0(x9)
add x7 x8 x9
addi x6 x7 0x0
addi x12 x6 0x0
addi x13 x5 0
sw x12 0(x13)
addi x14 x6 0x0
addi x10 x14 0
lw x1 0(sp)
lw x8 4(sp)
lw x9 8(sp)
lw x18 12(sp)
lw x19 16(sp)
lw x20 20(sp)
lw x21 24(sp)
lw x22 28(sp)
lw x23 32(sp)
lw x24 36(sp)
lw x25 40(sp)
lw x26 44(sp)
lw x27 48(sp)
addi x2 x2 52
ret



--------------------------------------

main:
addi x5 x0 2      # check for correct number of command line arguments
bne x10 x5 cmd_err2
lw x10 4(a1)         # load the filepath 
la x11 filepath_ptr  # load address of filepath home location 
sw x10 0(a1)         # save the filepath to its home location
li x10 8
jal malloc
addi x10 x10 0x0
li x12 75
addi x13 x10 4
sw x12 0(x13)
li x14 25
addi x15 x10 0
sw x14 0(x15)
precall0:
addi x16 x10 0
lw x16 0(x16)
addi x17 x10 4
lw x17 0(x17)
addi x10 x16 0x0
addi x11 x17 0x0
addi x2 x2 -28
sw x1 0(sp)
sw x5 4(sp)
sw x6 8(sp)
sw x7 12(sp)
sw x8 16(sp)
sw x9 20(sp)
sw x10 24(sp)
jal sub
postreturn0:
lw x1 0(sp)
lw x5 4(sp)
lw x6 8(sp)
lw x7 12(sp)
lw x8 16(sp)
lw x9 20(sp)
lw x10 24(sp)
addi x2 x2 28
addi x6 x10 0x0
addi x18 x6 0x0
addi x10 x18 0
jal print_int
li x10 0x0A
jal print_char
precall1:
addi x19 x10 0x0
addi x10 x19 0x0
addi x2 x2 -28
sw x1 0(sp)
sw x5 4(sp)
sw x6 8(sp)
sw x7 12(sp)
sw x8 16(sp)
sw x9 20(sp)
sw x10 24(sp)
jal addxy
postreturn1:
lw x1 0(sp)
lw x5 4(sp)
lw x6 8(sp)
lw x7 12(sp)
lw x8 16(sp)
lw x9 20(sp)
lw x10 24(sp)
addi x2 x2 28
addi x20 x10 0
lw x20 0(x20)
addi x10 x20 0
jal print_int
li x10 0x0A
jal print_char
li x21 10
addi x5 x21 0x0
addi x25 x6 0x0
addi x26 x6 0x0
addi x24 x26 2
li x27 3
mul x23 x24 x27
addi x28 x5 0x0
li x22 0x0
 

--------------------------------------

whileStart0:
blt x23 x28 endWhile0
sub x23 x23 x28
addi x22 x22 0x1
j whileStart0
 

--------------------------------------

endWhile0:
addi x9 x22 0x0
addi x29 x9 0x0
addi x10 x29 0
jal print_int
li x10 0x0A
jal print_char
lw x10 filepath_ptr
precall2:
addi x2 x2 -28
sw x1 0(sp)
sw x5 4(sp)
sw x6 8(sp)
sw x7 12(sp)
sw x8 16(sp)
sw x9 20(sp)
sw x10 24(sp)
jal x1 read_int
postreturn2:
lw x1 0(sp)
lw x5 4(sp)
lw x6 8(sp)
lw x7 12(sp)
lw x8 16(sp)
lw x9 20(sp)
lw x10 24(sp)
addi x2 x2 28
bne x11 x0 read_err1
addi x8 x10 0x0
addi x31 x8 0x0
li x32 4
slt x30 x32 x31
 

--------------------------------------

conditionalBlockStart0:
beqz x30 else0
li x30 0x0
jal x0 endConditionalBlock0
else0:
li x30 0x1
 

--------------------------------------

endConditionalBlock0:
 

--------------------------------------

conditionalBlockStart1:
beq x30 x0 else1
if1:
addi x34 x6 0x0
addi x35 x6 0x0
addi x33 x35 200
addi x6 x33 0x0
jal x0 endConditionalBlock1
else1:
addi x37 x6 0x0
addi x38 x6 0x0
addi x36 x38 100
addi x6 x36 0x0
 

--------------------------------------

endConditionalBlock1:
addi x40 x10 4
lw x40 0(x40)
li x41 50
slt x39 x41 x40
 

--------------------------------------

conditionalBlockStart2:
beq x39 x0 endConditionalBlock2
if2:
li x42 20
addi x5 x42 0x0
addi x43 x5 0x0
addi x10 x43 0
jal print_int
li x10 0x0A
jal print_char
 

--------------------------------------

endConditionalBlock2:
li x44 2
addi x6 x44 0x0
addi x46 x6 0x0
addi x47 x5 0x0
slt x45 x47 x46
 

--------------------------------------

conditionalBlockStart3:
beqz x45 else3
li x45 0x0
jal x0 endConditionalBlock3
else3:
li x45 0x1
 

--------------------------------------

endConditionalBlock3:
addi x7 x45 0x0
addi x48 x7 0x0
 

--------------------------------------

conditionalBlockStart4:
beq x48 x0 else4
if4:
addi x49 x9 0x0
addi x10 x49 0
jal print_int
li x10 0x0A
jal print_char
jal x0 endConditionalBlock4
else4:
li x50 0
addi x10 x50 0
jal print_int
li x10 0x0A
jal print_char
 

--------------------------------------

endConditionalBlock4:
addi x10 x0 0
jal x0 exit



--------------------------------------

read_err1:
    la x10 error_string1
    jal print_str
    li x10 1
    jal exit


--------------------------------------

cmd_err2:
    la x10 error_string2
    jal print_str
    li x10 1
    jal exit



--------------------------------------
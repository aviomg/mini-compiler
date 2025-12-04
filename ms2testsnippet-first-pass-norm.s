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
sub:
#start of prologue
addi x2 x2 -64 
sw x0 0(x2) #this holds var a
sw x0 4(x2) #this holds var b
sw x0 8(x2) #this holds var ans
sw x1 12(x2)
sw x8 16(x2)
sw x9 20(x2)
sw x18 24(x2)
sw x19 28(x2)
sw x20 32(x2)
sw x21 36(x2)
sw x22 40(x2)
sw x23 44(x2)
sw x24 48(x2)
sw x25 52(x2)
sw x26 56(x2)
sw x27 60(x2)
sw x10 0(x2) #storing param at offset instead of in reg
sw x11 4(x2) #storing param at offset instead of in reg
#end of prologue
#start of body
lw x6 0(x2)
lw x7 4(x2)
sub x5 x6 x7
sw x5 8(x2) #placing local's value in stack rather than reg
#end of body
#start of epilogue
lw x8 8(x2)
addi x10 x8 0
addi x2 x2 12
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
 
B1:
#end of epilogue
addxy:
#start of prologue
addi x2 x2 -60 
sw x0 0(x2) #this holds var pair
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
lw x6 0(x2)
addi x7 x6 0
lw x7 0(x7)
lw x8 0(x2)
addi x9 x8 4
lw x9 0(x9)
add x5 x7 x9
sw x5 4(x2) #placing local's value in stack rather than reg
lw x12 4(x2)
lw x13 0(x2)
addi x14 x13 0
sw x12 0(x14)
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
 
B2:
#end of epilogue
main:
#start of body
addi x5 x0 2      # check for correct number of command line arguments
bne x10 x5 cmd_err2
 
B3:
lw x10 4(x11)         # load the filepath 
la x11 filepath_ptr  # load address of filepath home location 
sw x10 0(x11)         # save the filepath to its home location
addi x2 x2 -24
sw x0 0(x2) #this holds var ex
sw x0 4(x2) #this holds var r
sw x0 8(x2) #this holds var b
sw x0 12(x2) #this holds var readnum
sw x0 16(x2) #this holds var z
sw x0 20(x2) #this holds var p
li x10 8
jal malloc
 
B4:
sw x10 20(x2) #placing local's value in stack rather than reg
li x5 75
lw x6 20(x2)
addi x7 x6 4
sw x5 0(x7)
li x8 25
lw x9 20(x2)
addi x12 x9 0
sw x8 0(x12)
lw x13 20(x2)
addi x14 x13 0
lw x14 0(x14)
lw x15 20(x2)
addi x16 x15 4
lw x16 0(x16)
addi x10 x14 0x0 #start of precall
addi x11 x16 0x0
addi x2 x2 -4
sw x1 0(x2)
jal sub
 
B5:
#start of postreturn
lw x1 0(x2) 
addi x2 x2 4
sw x10 4(x2) #placing local's value in stack rather than reg
lw x17 4(x2)
addi x10 x17 0
jal print_int
 
B6:
li x10 0x0A
jal print_char
 
B7:
lw x18 20(x2)
addi x10 x18 0x0 #start of precall
addi x2 x2 -4
sw x1 0(x2)
jal addxy
 
B8:
#start of postreturn
lw x1 0(x2) 
addi x2 x2 4
lw x19 20(x2)
addi x20 x19 0
lw x20 0(x20)
addi x10 x20 0
jal print_int
 
B9:
li x10 0x0A
jal print_char
 
B10:
li x21 10
sw x21 0(x2) #placing local's value in stack rather than reg
lw x22 4(x2)
sub x23 x0 x22
sw x23 4(x2) #placing local's value in stack rather than reg
lw x27 4(x2)
addi x26 x27 2
li x28 3
mul x25 x26 x28
lw x29 0(x2)
li x24 0x0
whileStart0:
blt x25 x29 endWhile0
 
B11:
sub x25 x25 x29
addi x24 x24 0x1
j whileStart0
 
B12:
endWhile0:
sw x24 16(x2) #placing local's value in stack rather than reg
lw x30 16(x2)
addi x10 x30 0
jal print_int
 
B13:
li x10 0x0A
jal print_char
 
B14:
lw x32 4(x2)
lw x33 0(x2)
slt x31 x33 x32
ifBlockStart0:
beqz x31 else0
 
B15:
li x31 0x0
jal x0 endIfBlock0
 
B16:
else0:
li x31 0x1
endIfBlock0:
sw x31 8(x2) #placing local's value in stack rather than reg
lw x35 4(x2)
lw x36 20(x2)
addi x10 x36 0x0 #start of precall
addi x2 x2 -4
sw x1 0(x2)
jal addxy
 
B17:
#start of postreturn
lw x1 0(x2) 
addi x2 x2 4
add x34 x35 x10
sw x34 0(x2) #placing local's value in stack rather than reg
addi x10 x0 0
jal x0 exit
 
B18:
#end of body
read_err1:
    la x10 error_string1
    jal print_str
 
B19:
    li x10 1
    jal exit
 
B20:
cmd_err2:
    la x10 error_string2
    jal print_str
 
B21:
    li x10 1
    jal exit
 
B22:



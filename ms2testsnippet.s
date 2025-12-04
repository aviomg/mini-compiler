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
#end of prologue
#start of body
lw s11 0(x2)
lw s10 4(x2)
sub s10 s11 s10
sw s10 8(x2) #placing local's value in stack rather than reg
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
lw s11 0(x2)
addi s11 s11 0
lw s11 0(s11)
lw s10 0(x2)
addi s10 s10 4
lw s10 0(s10)
add s10 s11 s10
sw s10 4(x2) #placing local's value in stack rather than reg
lw s10 4(x2)
lw s11 0(x2)
addi s11 s11 0
sw s10 0(s11)
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
addi x2 x2 -24
sw x0 0(x2) #this holds var ex
sw x0 4(x2) #this holds var r
sw x0 8(x2) #this holds var b
sw x0 12(x2) #this holds var readnum
sw x0 16(x2) #this holds var z
sw x0 20(x2) #this holds var p
li x10 8
jal malloc
 
B3:
sw x10 20(x2) #placing local's value in stack rather than reg
li s11 75
lw s10 20(x2)
addi s10 s10 4
sw s11 0(s10)
li s10 25
lw s11 20(x2)
addi s11 s11 0
sw s10 0(s11)
lw s11 20(x2)
addi s11 s11 0
lw s11 0(s11)
lw s10 20(x2)
addi s10 s10 4
lw s10 0(s10)
addi x10 s11 0x0 #start of precall
addi x11 s10 0x0
addi x2 x2 -4
sw x1 0(x2)
jal sub
 
B4:
lw x1 0(x2) 
addi x2 x2 4
sw x10 4(x2) #placing local's value in stack rather than reg
lw s10 4(x2)
addi x10 s10 0
jal print_int
 
B5:
li x10 0x0A
jal print_char
 
B6:
lw s10 20(x2)
addi x10 s10 0x0 #start of precall
addi x2 x2 -4
sw x1 0(x2)
jal addxy
 
B7:
lw x1 0(x2) 
addi x2 x2 4
lw s10 20(x2)
addi s10 s10 0
lw s10 0(s10)
addi x10 s10 0
jal print_int
 
B8:
li x10 0x0A
jal print_char
 
B9:
li s10 10
sw s10 0(x2) #placing local's value in stack rather than reg
lw s10 4(x2)
sub s10 x0 s10
sw s10 4(x2) #placing local's value in stack rather than reg
lw s10 4(x2)
addi s10 s10 2
li s11 3
mul s11 s10 s11
lw s10 0(x2)
li s9 0x0
whileStart0:
blt s11 s10 endWhile0
 
B10:
sub s11 s11 s10
addi s9 s9 0x1
j whileStart0
 
B11:
endWhile0:
sw s9 16(x2) #placing local's value in stack rather than reg
lw s9 16(x2)
addi x10 s9 0
jal print_int
 
B12:
li x10 0x0A
jal print_char
 
B13:
lw s9 4(x2)
lw s10 0(x2)
slt s10 s10 s9
ifBlockStart0:
beqz s10 else0
 
B14:
li s10 0x0
jal x0 endIfBlock0
 
B15:
else0:
li s10 0x1
endIfBlock0:
sw s10 8(x2) #placing local's value in stack rather than reg
lw s10 4(x2)
lw s9 20(x2)
addi x10 s9 0x0 #start of precall
addi x2 x2 -4
sw x1 0(x2)
jal addxy
 
B16:
lw x1 0(x2) 
addi x2 x2 4
add s9 s10 x10
sw s9 0(x2) #placing local's value in stack rather than reg
addi x10 x0 0
jal x0 exit
 
B17:
#end of body
read_err1:
    la x10 error_string1
    jal print_str
 
B18:
    li x10 1
    jal exit
 
B19:
cmd_err2:
    la x10 error_string2
    jal print_str
 
B20:
    li x10 1
    jal exit
 
B21:




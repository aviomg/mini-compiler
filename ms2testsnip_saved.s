.globl main
 .import berkeley_utils.s # the ecall utilities
 .import read_int.s # the file read wrapper


.data
g: .word 0x0
h: .word 0x0

.text
main:
li t5 20
addi t2 t5 0x0
li t6 3
la t7 g
sw t6 0(t7)
li t8 5
addi t0 t8 0x0
li t9 0x0
addi t4 t9 0x0
la t10 g
lw t11 0(t10)
addi t12 t11 0x0
addi t0 t12 0x0
addi t13 t2 0x0
addi t0 t13 0x0
addi t14 t2 0x0
la t15 g
sw t14 0(t15)
addi t16 t1 0x0
addi t3 t16 0x0

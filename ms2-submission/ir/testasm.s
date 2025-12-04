add x1 x2 x3
or x3 x4 x5
sltu x1 x2 x3
addi x1 x2 20
slli x1 x2 20
sltiu x1 x2 20
lb x1 4(x2)
lbu x1 4(x2)
lw x1 4(x2)
sb x1 4(x2)
sw x1 4(x2)
beq x1 x2 label1
bne x1 x2 label1
bgeu x1 x2 label1
jal x1 label1
jalr x1 x2 20
auipc x1 200
lui x1 200
mul x1 x2 x3
beqz x1 label1
bnez x1 label1
j label1
jal label1
jr x1
la x2 label1
li x2 20
mv x2 x3
neg x2 x3
not x2 x3

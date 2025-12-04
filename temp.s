0: addi x5 x0 2      # check for correct number of command line arguments
1: bne x10 x5 cmd_err2
2: lw x10 4(x11)         # load the filepath 
3: la x11 filepath_ptr  # load address of filepath home location 
4: sw x10 0(x11)         # save the filepath to its home location
5: addi x2 x2 -24
6: sw x0 0(x2) #this holds var ex
7: sw x0 4(x2) #this holds var r
8: sw x0 8(x2) #this holds var b
9: sw x0 12(x2) #this holds var readnum
10: sw x0 16(x2) #this holds var z
11: sw x0 20(x2) #this holds var p
12: li x10 8
13: jal malloc
14: sw x10 20(x2) #placing local's value in stack rather than reg
15: li x5 75
16: lw x6 20(x2)
17: addi x7 x6 4
18: sw x5 0(x7)
19: li x8 25
20: lw x9 20(x2)
21: addi x12 x9 0
22: sw x8 0(x12)
23: lw x13 20(x2)
24: addi x14 x13 0
25: lw x14 0(x14)
26: lw x15 20(x2)
27: addi x16 x15 4
28: lw x16 0(x16)
29: addi x10 x14 0x0 #start of precall
30: addi x11 x16 0x0
31: addi x2 x2 -4
32: sw x1 0(x2)
33: jal sub
34: lw x1 0(x2) #start of postreturn
35: addi x2 x2 4
36: sw x10 4(x2) #placing local's value in stack rather than reg
37: lw x17 4(x2)
38: addi x10 x17 0
39: jal print_int
40: li x10 0x0A
41: jal print_char
42: lw x18 20(x2)
43: addi x10 x18 0x0 #start of precall
44: addi x2 x2 -4
45: sw x1 0(x2)
46: jal addxy
47: lw x1 0(x2) #start of postreturn
48: addi x2 x2 4
49: lw x19 20(x2)
50: addi x20 x19 0
51: lw x20 0(x20)
52: addi x10 x20 0
53: jal print_int
54: li x10 0x0A
55: jal print_char
56: li x21 10
57: sw x21 0(x2) #placing local's value in stack rather than reg
58: lw x22 4(x2)
59: sub x23 x0 x22
60: sw x23 4(x2) #placing local's value in stack rather than reg
61: lw x27 4(x2)
62: addi x26 x27 2
63: li x28 3
64: mul x25 x26 x28
65: lw x29 0(x2)
66: li x24 0x0
67: blt x25 x29 endWhile0
68: sub x25 x25 x29
69: addi x24 x24 0x1
70: j whileStart0
71: sw x24 16(x2) #placing local's value in stack rather than reg
72: lw x30 16(x2)
73: addi x10 x30 0
74: jal print_int
75: li x10 0x0A
76: jal print_char
77: lw x32 4(x2)
78: lw x33 0(x2)
79: slt x31 x33 x32
80: beqz x31 else0
81: li x31 0x0
82: jal x0 endIfBlock0
83: li x31 0x1
84: sw x31 8(x2) #placing local's value in stack rather than reg
85: lw x35 4(x2)
86: lw x36 20(x2)
87: addi x10 x36 0x0 #start of precall
88: addi x2 x2 -4
89: sw x1 0(x2)
90: jal addxy
91: lw x1 0(x2) #start of postreturn
92: addi x2 x2 4
93: add x34 x35 x10
94: sw x34 0(x2) #placing local's value in stack rather than reg
95: addi x10 x0 0
96: jal x0 exit

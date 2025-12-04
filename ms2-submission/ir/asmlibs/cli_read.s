# Testing the use of read_int to treat a file like standard in.
# Despite the existence of error checking here, read_int does
# not return if it encounters an error. Instead, it exits. 
# Run this with: $ java -jar <path/to/venus>/venus-jvm-latest.jar ./cli_read.s -- ./testinput.txt

.globl main
.import berkeley_utils.s
.import read_int.s

.data 
    filepath_ptr: .word
    error_string1: .string "read_int returned an error\n"
    error_string2: .string "incorrect number of arguments\n"

.text
main:
    # read a value from a file and print the value
    # filename is passed in as command line argument
    # a0 = argc
    # a1 = argv
    # argv+0 will contain a pointer to venus cmd
    # argv+4 will contain a pointer to filepath

    addi t0 zero 2      # check for correct number of command line arguments
    bne a0 t0 cmd_err2

    lw a0 4(a1)         # load the filepath 
    la a1 filepath_ptr  # load address of filepath home location 
    sw a0 0(a1)         # save the filepath to its home location

    # try reading an int
    lw a0 filepath_ptr      # load pointer to filepath in a0
    jal ra read_int         # integer will be in a0 after call
    bne a1 zero read_err1   # check the error code
    jal ra print_int        # now print the int to standard out
    li a0 0x0A              # ascii for newline
    jal print_char          # note the non-standard format. Venus translates this to 'jal ra read_int' 

    # try reading another int
    lw a0 filepath_ptr
    jal read_int           
    bne a1 zero read_err1
    jal print_int
    li a0 '\n'
    jal print_char

    # exit nicely
    addi a0 zero 0
    jal exit

read_err1:
    la a0 error_string1
    jal print_str
    li a0 1
    jal exit

cmd_err2:
    la a0 error_string2
    jal print_str
    li a0 1
    jal exit

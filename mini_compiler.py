'''driver'''

import sys
from antlr4 import *
from MiniLexer import MiniLexer
from MiniParser import MiniParser
from mini_ast_visitor import MiniToASTVisitor
from pretty_print_ast_visitor import PPASTVisitor
from parse_tree_to_json import PTtoJSON
from ir.codegen import CodeGenerator, END_PROCS_PATH
import json
import argparse
from ast_to_json import ASTtoJSON
from ir.regalloc import RegisterAllocation
from ir.ir_module import write_module




def main(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument("mini_file", help="the .mini file to be compiled")
    parser.add_argument("-p","--ast_prettyprint", help="pretty print the AST for your source file", action="store_true")
    parser.add_argument("-of","--out_file",help="save the pretty printed AST in a text file rather than to the terminal",action="store_true")
    parser.add_argument("-gg", "--generate_ast_graph",help="generate a GraphViz AST graph for your source file", action="store_true")
    parser.add_argument("-gp", "--generate_parse_tree",help="generate a JSON file representing the parse tree for your source file", action="store_true")
    parser.add_argument("-s", "--symbol_table",help="print out the symbol tables", action="store_true")
    parser.add_argument("-j","--ast_json",help="save the AST as a JSON file at ast.json",action="store_true")
    args = parser.parse_args()    
    input_stream = FileStream(argv[1])  # create a stream of characters from the input file (e.g., test.mini)
    lexer = MiniLexer(input_stream)     # create a lexer for the input stream...turn characters → tokens using Mini.g4's lexer rules
    stream = CommonTokenStream(lexer)   # buffer tokens so the parser can look ahead efficiently
    parser = MiniParser(stream)         # create a parser for the stream of tokens
    program_ctx = parser.program()      # recursively parse, starting with the top-level 'program' construct of Mini.g4. returns a parse-tree node
    
    #print(input_stream)
    
    if args.generate_parse_tree:
            filename="out.json"
   # if len(argv)>2:
   #     if argv[2]=="generate-json":
            ptjson = PTtoJSON().visitProgram(program_ctx)
            with open(filename, "w") as f:
                json.dump(ptjson, f, indent=2)
            print(f"JSON representation of parse tree saved to {filename}")


    if parser.getNumberOfSyntaxErrors() > 0:
        print("Syntax errors.")
    else:
        print("Parse successful.\n")
        """Create AST."""
        mini_ast_visitor = MiniToASTVisitor()
        mini_ast = mini_ast_visitor.visitProgram(program_ctx)

        """Pretty print AST.
        Milestone 0: Implement this visitor"""
        pp_visitor = PPASTVisitor()
        pp_str = mini_ast.accept(pp_visitor)
        
        if args.symbol_table:
            pp_visitor.print_tables()
        
        if args.ast_prettyprint:
            outfile="out.txt"
            print("AST:\n")
            if args.out_file:
                with open(outfile,"w") as f:
                    f.write(pp_str)
                print(f"Pretty print AST written to {outfile}")
            else:
                print(pp_str)
        
        jsonvisitor=ASTtoJSON()
        astjson=mini_ast.accept(jsonvisitor)
        if args.ast_json:
            outfile="ast.json"
            with open(outfile,"w") as f:
                json.dump(astjson,f,indent=2)
            print(f"Structured AST JSON saved to {outfile}")
        
        structs,funcs,glbls,variables=pp_visitor.get_symbol_table_vals()
        if pp_visitor.error_count!=0:
            print(f"Assembly file not generated due to syntax errors.")
            return
            
        
            #instruction_selector = InstructionSelector(ASTJSON="ast.json",structs=structs,funcs=funcs,glbls=glbls,variables=variables,filename=args.mini_file)
        codegen=CodeGenerator(structs,funcs,glbls,variables,filename=args.mini_file)
        module_ir=mini_ast.accept(codegen)
        if module_ir is None:
            module_ir=codegen.module
        op_file=codegen.output_file
        setuplines=write_module(module_ir, op_file, END_PROCS_PATH)
        regalloc=RegisterAllocation(op_file,setuplines,filename=args.mini_file)
        regalloc.run()
        
            
       # if args.sem_analysis:
       #     collector = SemanticAnalyzer()
       #     collector.visit_program(mini_ast)
       #     collector.print_tables()
            
            
       # with open(pp_output,"w") as f:
        #    f.write(pp_str)
        if args.generate_ast_graph:
            graphviz_outfile="out"
            try:
                outfile=graphviz_outfile
                outpath = pp_visitor.render_graphviz(mini_ast, outfile=outfile, fmt="svg")
                print("Graphviz AST written to "+ outfile+".svg")
            except Exception as e:
                print("error rendering graphviz. please check if it is properly installed:", e) 
        #with open("output.json","w") as f:
        #    data = pp_visitor.render_json(mini_ast)
        #    json.dump(data,f,indent=4)
if __name__ == '__main__':
    main(sys.argv)


from typing import Any
from MiniVisitor import MiniVisitor
from MiniParser import MiniParser

def node(kind, ctx, fields=None, children=None):
    return {
        "kind": kind,
        "line": getattr(ctx.start, "line", None) if ctx else None,
        "fields": fields or {},
        "children": children or []
    }

class PTtoJSON(MiniVisitor):
    def visitProgram(self, ctx: MiniParser.ProgramContext):
        return node("Program", ctx, children=[
            self.visit(ctx.types()),
            self.visit(ctx.declarations()),
            self.visit(ctx.functions()),
        ])

    # types: (typeDeclaration)*    -> return list node
    def visitTypes(self, ctx: MiniParser.TypesContext):
        items=[]
        for t in ctx.typeDeclaration():
            items.append(self.visit(t))
        return node("Types", ctx, children=items)

    # typeDeclaration: 'struct' ID '{' nestedDecl '}' ';'
    def visitTypeDeclaration(self, ctx: MiniParser.TypeDeclarationContext):
        name = ctx.ID().getText() #
        return node("Struct (TypeDeclaration)", ctx,
                    fields={"name": name},
                    children=[ self.visit(ctx.nestedDecl()) ])

    # nestedDecl: (decl ';')+       e.g., declaration fields inside a struct?
    def visitNestedDecl(self, ctx: MiniParser.NestedDeclContext):
        items=[]
        for d in ctx.decl():
            items.append(self.visit(d))
        return node("Nested Decl", ctx, children=items)

    # decl: type ID                 e.g., param arguments like function fun(int x, int y)
    def visitDecl(self, ctx: MiniParser.DeclContext):  
        ty = self.visit(ctx.type_())
        identity = ctx.ID().getText()
        return node("Decl", ctx, fields={"name": identity}, children=[ty])

    # type: 'int' | 'bool' | 'struct' ID
    def visitIntType(self, ctx: MiniParser.IntTypeContext):
        return node("Int", ctx)

    def visitBoolType(self, ctx: MiniParser.BoolTypeContext):
        return node("Bool", ctx)

    def visitStructType(self, ctx: MiniParser.StructTypeContext):
        return node("Struct", ctx, fields={"name": ctx.ID().getText()})

    # declarations: (declaration)*          e.g., int x = 4;
    def visitDeclarations(self, ctx: MiniParser.DeclarationsContext):
        decls = []
        for d in ctx.declaration():
            decls.append(self.visit(d))
        return node("Declarations", ctx, children=decls)


    # declaration: type ID (',' ID)* ';'
    def visitDeclaration(self, ctx: MiniParser.DeclarationContext):
        ty = self.visit(ctx.type_())
        ids=[]
        for tok in ctx.ID():
            ids.append(tok.getText())
        decls=[]
        for i in ids:
            decls.append(node("Declaration", ctx, fields={"name": i}, children=[ty]))  
        return node("Declaration Group", ctx, children=decls)

    # functions: (function)*
    def visitFunctions(self, ctx: MiniParser.FunctionsContext):
        funcs=[]
        for f in ctx.function():
            funcs.append(self.visit(f))
        return node("Functions", ctx, children=funcs)

    # function: 'fun' ID parameters returnType '{' declarations statementList '}'
    def visitFunction(self, ctx: MiniParser.FunctionContext):
        params = [] 
        for d in ctx.parameters().decl():
            params.append(self.visit(d))
        return node("Function", ctx,
            fields={"name": ctx.ID().getText()},
            children=[
                node("Parameters", ctx, children=params),
                self.visit(ctx.returnType()),
                self.visit(ctx.declarations()),
                self.visit(ctx.statementList()),
            ])
    
    def visitReturnTypeReal(self,ctx:MiniParser.ReturnTypeRealContext):
        return node("ReturnType Real",ctx,children=[self.visit(ctx.type_())])
    def visitReturnTypeVoid(self,ctx:MiniParser.ReturnTypeVoidContext):
        return node("ReturnType Void",ctx)
    
    
    def visitStatementList(self,ctx:MiniParser.StatementListContext):
        statements = []
        for s in ctx.statement():
            statements.append(self.visit(s))
        return node("Statement List",ctx,children=statements)
    
    def visitBlock(self,ctx:MiniParser.BlockContext):
        return node("Block", ctx,children=[self.visit(ctx.statementList())])    
        
    def visitNestedBlock(self, ctx: MiniParser.NestedBlockContext):
        return self.visit(ctx.block())
    
    # assignment: lvalue '=' (expression | 'read') ';'
    def visitAssignment(self,ctx:MiniParser.AssignmentContext):
        src: Any 
        if (ctx.expression()):
            src=self.visit(ctx.expression())
        else:
            src=node("Read", ctx)
        return node ("Assignment",ctx,children=[self.visit(ctx.lvalue()),src])
    
        # lvalue: ID ('.' ID)*
    def visitLvalueId(self, ctx: MiniParser.LvalueIdContext):
        return node("LValueId", ctx, fields={"name": ctx.ID().getText()})

    #e.g, p.x = 4; .... 'l value' is x, with field being p?
    def visitLvalueDot(self, ctx: MiniParser.LvalueDotContext):
        # left-recursive rule; this visit will return nested dots
        left = self.visit(ctx.lvalue())
        field = ctx.ID().getText()
        return node("LValueDot", ctx, fields={"field": field}, children=[ left ])
    
    def visitExpression(self, ctx: MiniParser.ExpressionContext):
        child = self.visitChildren(ctx)
        return node("Expr", ctx, children=[child])
    
    def visitArguments(self,ctx:MiniParser.ArgumentsContext):
        exprs=[]
        for e in ctx.expression():
            exprs.append(self.visit(e))
        return node("Args",ctx,children=exprs)        
    
    #ID '(' arguments ')'           e.g., a node that represents a func call. like sum(a,b)
    def visitInvocationExpr(self,ctx:MiniParser.InvocationExprContext):
        identifier = ctx.ID().getText()
        args = self.visit(ctx.arguments())
        return node("Invocation Expr", ctx,fields={"name":identifier},children=[args])
    
    def visitDotExpr(self,ctx:MiniParser.DotExprContext):
        base = self.visit(ctx.expression())
        return node("Dot Expr",ctx,fields={"field":ctx.ID().getText()},children=[base])
    
    def visitUnaryExpr(self,ctx:MiniParser.UnaryExprContext):
        # ('-' | '!') expression
        return node("Unary Expr",ctx,fields={"op":ctx.op.text},children=[self.visit(ctx.expression())]) #child is the 'base expression' to the left of the dot.?
        pass
    
    def visitBinaryExpr(self,ctx:MiniParser.BinaryExprContext):
        op = ctx.op.text
        leftside = self.visit(ctx.lft)  #this will be an expression context
        rightside = self.visit(ctx.rht) #this will be an expression context
        return node("Binary Expr",ctx,fields={"op":op,},children=[leftside,rightside])
    
    def visitIdentifierExpr(self,ctx:MiniParser.IdentifierExprContext):
        return node("Identifier Expr",ctx,fields={"name":ctx.ID().getText()})
    
    def visitIntegerExpr(self, ctx:MiniParser.IntegerExprContext):
        return node("Integer Expr",ctx,fields={"value":ctx.INTEGER().getText()})
    
    def visitTrueExpr(self,ctx:MiniParser.TrueExprContext):
        return node("Boolean Expr",ctx,fields={"value":True})
    
    def visitFalseExpr(self,ctx:MiniParser.FalseExprContext):
        return node("Boolean Expr",ctx,fields={"value":False})
    
    def visitNewExpr(self,ctx:MiniParser.NewExprContext):
        return node("New Expr",ctx,fields={"name":ctx.ID().getText()})
    
    def visitNullExpr(self,ctx:MiniParser.NullExprContext):
        return node("Null Expr",ctx,fields={"value":"null"})
    
    def visitNestedExpr(self,ctx:MiniParser.NestedExprContext):
        return node("Nested Expr",ctx,fields={},children=[self.visit(ctx.expression())])
    
    def visitPrint(self, ctx: MiniParser.PrintContext):
        return node("Print", ctx, children=[ self.visit(ctx.expression()) ])
    
    def visitPrintLn(self, ctx: MiniParser.PrintLnContext):
        return node("PrintLn", ctx, children=[ self.visit(ctx.expression()) ])
    
    def visitConditional(self,ctx:MiniParser.ConditionalContext):
        thenblock = self.visit(ctx.thenBlock)
        elseblock:Any
        if(ctx.elseBlock):
            elseblock=self.visit(ctx.elseBlock)
        else:
            elseblock=None
        ifexpr=self.visit(ctx.expression())
        chdrn = [ifexpr,thenblock]
        if elseblock:
            chdrn.append(elseblock)
        return node("Conditional",ctx,children=chdrn)
    
    def visitWhile(self,ctx:MiniParser.WhileContext):
        return node("While",ctx,children=[self.visit(ctx.expression()),self.visit(ctx.block())])
    
    def visitDelete(self,ctx:MiniParser.DeleteContext):
        return node("Delete",ctx,children=[self.visit(ctx.expression())])
    
    def visitReturn(self,ctx:MiniParser.ReturnContext):
        if ctx.expression() is not None:
            return node("Return",ctx,children=[self.visit(ctx.expression())])
        else:
            return node("Return",ctx)
    
    def visitInvocation(self,ctx:MiniParser.InvocationContext):
        call = node("Call", ctx, fields={"name": ctx.ID().getText()},
                children=[ self.visit(ctx.arguments()) ])
        return node("Invocation", ctx, children=[call])
        
    
    

        
        
                




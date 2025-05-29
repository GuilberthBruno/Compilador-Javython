# Generated from MyG.g4 by ANTLR 4.13.2
from antlr4 import *
if "." in __name__:
    from .MyGParser import MyGParser
else:
    from MyGParser import MyGParser

# This class defines a complete generic visitor for a parse tree produced by MyGParser.

class MyGVisitor(ParseTreeVisitor):

    # Visit a parse tree produced by MyGParser#prog.
    def visitProg(self, ctx:MyGParser.ProgContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by MyGParser#stmnt.
    def visitStmnt(self, ctx:MyGParser.StmntContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by MyGParser#declar.
    def visitDeclar(self, ctx:MyGParser.DeclarContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by MyGParser#assign.
    def visitAssign(self, ctx:MyGParser.AssignContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by MyGParser#parens.
    def visitParens(self, ctx:MyGParser.ParensContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by MyGParser#unaryPlus.
    def visitUnaryPlus(self, ctx:MyGParser.UnaryPlusContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by MyGParser#intValue.
    def visitIntValue(self, ctx:MyGParser.IntValueContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by MyGParser#unaryMinus.
    def visitUnaryMinus(self, ctx:MyGParser.UnaryMinusContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by MyGParser#addSub.
    def visitAddSub(self, ctx:MyGParser.AddSubContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by MyGParser#varRef.
    def visitVarRef(self, ctx:MyGParser.VarRefContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by MyGParser#mulDiv.
    def visitMulDiv(self, ctx:MyGParser.MulDivContext):
        return self.visitChildren(ctx)



del MyGParser
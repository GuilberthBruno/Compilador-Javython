# Generated from MyG.g4 by ANTLR 4.13.2
from antlr4 import *
if "." in __name__:
    from .MyGParser import MyGParser
else:
    from MyGParser import MyGParser

# This class defines a complete listener for a parse tree produced by MyGParser.
class MyGListener(ParseTreeListener):

    # Enter a parse tree produced by MyGParser#prog.
    def enterProg(self, ctx:MyGParser.ProgContext):
        pass

    # Exit a parse tree produced by MyGParser#prog.
    def exitProg(self, ctx:MyGParser.ProgContext):
        pass


    # Enter a parse tree produced by MyGParser#stmnt.
    def enterStmnt(self, ctx:MyGParser.StmntContext):
        pass

    # Exit a parse tree produced by MyGParser#stmnt.
    def exitStmnt(self, ctx:MyGParser.StmntContext):
        pass


    # Enter a parse tree produced by MyGParser#declar.
    def enterDeclar(self, ctx:MyGParser.DeclarContext):
        pass

    # Exit a parse tree produced by MyGParser#declar.
    def exitDeclar(self, ctx:MyGParser.DeclarContext):
        pass


    # Enter a parse tree produced by MyGParser#assign.
    def enterAssign(self, ctx:MyGParser.AssignContext):
        pass

    # Exit a parse tree produced by MyGParser#assign.
    def exitAssign(self, ctx:MyGParser.AssignContext):
        pass


    # Enter a parse tree produced by MyGParser#parens.
    def enterParens(self, ctx:MyGParser.ParensContext):
        pass

    # Exit a parse tree produced by MyGParser#parens.
    def exitParens(self, ctx:MyGParser.ParensContext):
        pass


    # Enter a parse tree produced by MyGParser#unaryPlus.
    def enterUnaryPlus(self, ctx:MyGParser.UnaryPlusContext):
        pass

    # Exit a parse tree produced by MyGParser#unaryPlus.
    def exitUnaryPlus(self, ctx:MyGParser.UnaryPlusContext):
        pass


    # Enter a parse tree produced by MyGParser#intValue.
    def enterIntValue(self, ctx:MyGParser.IntValueContext):
        pass

    # Exit a parse tree produced by MyGParser#intValue.
    def exitIntValue(self, ctx:MyGParser.IntValueContext):
        pass


    # Enter a parse tree produced by MyGParser#unaryMinus.
    def enterUnaryMinus(self, ctx:MyGParser.UnaryMinusContext):
        pass

    # Exit a parse tree produced by MyGParser#unaryMinus.
    def exitUnaryMinus(self, ctx:MyGParser.UnaryMinusContext):
        pass


    # Enter a parse tree produced by MyGParser#addSub.
    def enterAddSub(self, ctx:MyGParser.AddSubContext):
        pass

    # Exit a parse tree produced by MyGParser#addSub.
    def exitAddSub(self, ctx:MyGParser.AddSubContext):
        pass


    # Enter a parse tree produced by MyGParser#varRef.
    def enterVarRef(self, ctx:MyGParser.VarRefContext):
        pass

    # Exit a parse tree produced by MyGParser#varRef.
    def exitVarRef(self, ctx:MyGParser.VarRefContext):
        pass


    # Enter a parse tree produced by MyGParser#mulDiv.
    def enterMulDiv(self, ctx:MyGParser.MulDivContext):
        pass

    # Exit a parse tree produced by MyGParser#mulDiv.
    def exitMulDiv(self, ctx:MyGParser.MulDivContext):
        pass



del MyGParser
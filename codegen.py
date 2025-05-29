from MyGVisitor import MyGVisitor

class ErroSemantico(Exception):
    """Exceção lançada para erros semânticos."""
    pass

class CodeGenerator(MyGVisitor):
    def __init__(self):
        self.temp_count = 0
        self.code = []
        self.symbol_table = {}  
        self.semantic_errors = [] 
        self.in_assignment_rhs = False  # Flag para indicar se estamos no lado direito de uma atribuição

    def new_temp(self):
        self.temp_count +=1
        return f"t{self.temp_count}"

    def reportar_erro(self, mensagem):
        """Reporta um erro e interrompe a execução."""
        print(f"ERRO: {mensagem}")
        raise ErroSemantico(mensagem)

    def visitProg(self, ctx):
        try:
            for stmt in ctx.stmnt():
                self.visit(stmt)
            
            return self.code
        except ErroSemantico as e:
            print(f"Compilação interrompida: {e}")
            return []

    def visitStmnt(self, ctx):
        return self.visitChildren(ctx)

    def visitDeclar(self, ctx):
        var_name = ctx.ID().getText()
        
        if var_name in self.symbol_table:
            self.reportar_erro(f"Variável '{var_name}' já declarada anteriormente")
        else:
            self.symbol_table[var_name] = {"declared": True, "initialized": False}
            self.code.append(f"declr {var_name}")
        
        return None

    def visitAssign(self, ctx):
        var_name = ctx.ID().getText()
        
        if var_name not in self.symbol_table:
            self.reportar_erro(f"Variável '{var_name}' usada sem declaração prévia")
        
        # Marque que estamos avaliando o lado direito de uma atribuição
        self.in_assignment_rhs = True
        value = self.visit(ctx.expr())
        self.in_assignment_rhs = False
        
        # Após avaliar a expressão, marcamos a variável como inicializada
        self.symbol_table[var_name]["initialized"] = True
        
        self.code.append(f"{var_name} = {value}")
        return None

    def visitExpr(self, ctx):
        # Identificar o tipo de expressão pelo número de filhos
        child_count = ctx.getChildCount()

        # Expressão com operador unário '-'
        if child_count == 2 and ctx.getChild(0).getText() == '-':
            value = self.visit(ctx.expr(0))
            temp = self.new_temp()
            self.code.append(f"{temp} = -{value}")
            return temp
            
        # Expressão com operador unário '+'
        elif child_count == 2 and ctx.getChild(0).getText() == '+':
            return self.visit(ctx.expr(0))
            
        # Expressão com operador binário (multiplicação/divisão)
        elif child_count == 3 and ctx.children[1].getText() in ['*', '/']:
            left = self.visit(ctx.expr(0))
            right = self.visit(ctx.expr(1))
            op = ctx.children[1].getText()
            
            if op == '/' and right == '0':
                self.reportar_erro("Divisão por zero detectada")
                
            temp = self.new_temp()
            self.code.append(f"{temp} = {left} {op} {right}")
            return temp
            
        # Expressão com operador binário (soma/subtração)
        elif child_count == 3 and ctx.children[1].getText() in ['+', '-']:
            left = self.visit(ctx.expr(0))
            right = self.visit(ctx.expr(1))
            op = ctx.children[1].getText()
            temp = self.new_temp()
            self.code.append(f"{temp} = {left} {op} {right}")
            return temp
            
        # Expressão entre parênteses
        elif child_count == 3 and ctx.getChild(0).getText() == '(' and ctx.getChild(2).getText() == ')':
            return self.visit(ctx.expr(0))
            
        # Expressão literal (INT)
        elif ctx.INT() is not None:
            return ctx.INT().getText()
            
        # Expressão variável (ID)
        elif ctx.ID() is not None:
            var_name = ctx.ID().getText()
            # Verificar se a variável foi declarada
            if var_name not in self.symbol_table:
                self.reportar_erro(f"Variável '{var_name}' usada sem declaração prévia")
            # Verificar se a variável foi inicializada (apenas se não estamos no lado direito de uma atribuição)
            elif not self.symbol_table[var_name]["initialized"] and not self.in_assignment_rhs:
                print(f"AVISO: Variável '{var_name}' pode não ter sido inicializada")
            
            return var_name
            
        # Caso padrão
        print(f"Tipo de expressão não reconhecido: {ctx.getText()}")
        return self.visitChildren(ctx)

    def visitVar(self, ctx):
        var_name = ctx.ID().getText()
        
        if var_name not in self.symbol_table:
            self.reportar_erro(f"Variável '{var_name}' usada sem declaração prévia")
        
        return var_name

    def visitParens(self, ctx):
        return self.visit(ctx.expr())

    def visitAddSub(self, ctx):
        left = self.visit(ctx.expr(0))
        right = self.visit(ctx.expr(1))
        op = ctx.op.text
        temp = self.new_temp()
        self.code.append(f"{temp} = {left} {op} {right}")
        return temp

    def visitMulDiv(self, ctx):
        left = self.visit(ctx.expr(0))
        right = self.visit(ctx.expr(1))
        op = ctx.op.text
        
        if op == '/' and right == '0':
            self.reportar_erro("Divisão por zero detectada")
            
        temp = self.new_temp()
        self.code.append(f"{temp} = {left} {op} {right}")
        return temp

    def visitUnaryMinus(self, ctx):
        value = self.visit(ctx.expr())
        temp = self.new_temp()
        self.code.append(f"{temp} = -{value}")
        return temp

    def visitUnaryPlus(self, ctx):
        return self.visit(ctx.expr())

    def visitIntValue(self, ctx):
        return ctx.INT().getText()

    def visitVarRef(self, ctx):
        var_name = ctx.ID().getText()
        
        if var_name not in self.symbol_table:
            self.reportar_erro(f"Variável '{var_name}' usada sem declaração prévia")
        # Apenas exibir aviso se não estamos no lado direito de uma atribuição
        elif not self.symbol_table[var_name]["initialized"] and not self.in_assignment_rhs:
            print(f"AVISO: Variável '{var_name}' pode não ter sido inicializada")
            
        return var_name
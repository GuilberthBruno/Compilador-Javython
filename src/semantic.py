from collections import defaultdict

class SemanticAnalyzer:
    def __init__(self):
        self.symbol_table = defaultdict(dict)
        self.current_scope = "global"
        self.functions = {}
        self.errors = []
    
    def analyze(self, ast):
        """Método principal para iniciar a análise semântica"""
        if ast is None:
            self.add_error("AST está vazio")
            return False
        
        if ast[0] != 'program':
            self.add_error("Estrutura do programa inválida")
            return False
        
        # Nome do programa
        program_name = ast[1]
        
        # Conteúdo do programa (declarações, métodos, main)
        program_content = ast[2]
        
        # Analisa declarações globais
        declarations = program_content[0]
        self.analyze_declarations(declarations)
        
        # Analisa métodos/funções
        methods = program_content[1]
        self.analyze_methods(methods)
        
        # Analisa bloco main
        main_method = program_content[2]
        self.analyze_main(main_method)
        
        return len(self.errors) == 0
    
    def analyze_declarations(self, declarations):
        """Analisa declarações de variáveis globais"""
        if declarations[0] != 'declarations':
            return
            
        for decl in declarations[1]:
            if decl[0] == 'declare_group':
                var_type = decl[2]
                for var_name in decl[1]:
                    self.add_symbol(var_name, var_type, "global")
            elif decl[0] == 'declare':
                var_type = decl[1]
                var_name = decl[2]
                self.add_symbol(var_name, var_type, "global")
            elif decl[0] == 'const_assign':
                var_name = decl[1]
                # Para constantes, inferimos o tipo do valor
                value = decl[2]
                if isinstance(value, bool):
                    var_type = 'bool'
                elif isinstance(value, int):
                    var_type = 'int'
                elif isinstance(value, float):
                    var_type = 'float'
                elif isinstance(value, str):
                    var_type = 'str'
                else:
                    var_type = 'unknown'
                self.add_symbol(var_name, var_type, "global", is_const=True)
    
    def analyze_methods(self, methods):
        """Analisa declarações de métodos/funções"""
        for method in methods:
            if method[0] != 'method':
                continue
                
            return_type = method[1]
            method_name = method[2]
            params = method[3]
            body = method[4]
            
            # Adiciona função à tabela de símbolos
            self.functions[method_name] = {
                'return_type': return_type,
                'params': params,
                'scope': method_name
            }
            
            # Entra no escopo da função
            self.current_scope = method_name
            
            # Adiciona parâmetros à tabela de símbolos
            for param in params:
                param_type, param_name = param
                self.add_symbol(param_name, param_type, method_name)
            
            # Analisa o corpo da função
            self.analyze_block(body)
            
            # Volta ao escopo global
            self.current_scope = "global"
    
    def analyze_main(self, main):
        """Analisa o bloco main"""
        if main[0] != 'main':
            return
            
        self.current_scope = "main"
        self.analyze_block(main[1])
        self.current_scope = "global"
    
    def analyze_block(self, block):
        """Analisa um bloco de código (declarações e statements)"""
        declarations = block[0]
        statements = block[1]
        
        # Analisa declarações locais
        if declarations and declarations[0] == 'declarations':
            for decl in declarations[1]:
                if decl[0] == 'declare_group':
                    var_type = decl[2]
                    for var_name in decl[1]:
                        self.add_symbol(var_name, var_type, self.current_scope)
                elif decl[0] == 'declare':
                    var_type = decl[1]
                    var_name = decl[2]
                    self.add_symbol(var_name, var_type, self.current_scope)
                elif decl[0] == 'const_assign':
                    var_name = decl[1]
                    value = decl[2]
                    if isinstance(value, bool):
                        var_type = 'bool'
                    elif isinstance(value, int):
                        var_type = 'int'
                    elif isinstance(value, float):
                        var_type = 'float'
                    elif isinstance(value, str):
                        var_type = 'str'
                    else:
                        var_type = 'unknown'
                    self.add_symbol(var_name, var_type, self.current_scope, is_const=True)
        
        # Analisa statements
        for stmt in statements:
            self.analyze_statement(stmt)
    
    def analyze_statement(self, stmt):
        """Analisa um statement individual"""
        if not stmt:
            return
            
        stmt_type = stmt[0]
        
        if stmt_type == 'assign':
            var_name = stmt[1]
            expr = stmt[2]
            
            # Verifica se a variável foi declarada
            if not self.is_symbol_defined(var_name):
                self.add_error(f"Variável '{var_name}' não declarada")
            else:
                # Verifica se é constante
                symbol = self.get_symbol(var_name)
                if symbol.get('is_const', False):
                    self.add_error(f"Não é possível modificar a constante '{var_name}'")
                
                # Verifica compatibilidade de tipos
                expr_type = self.analyze_expression(expr)
                var_type = symbol['type']
                
                if expr_type and var_type != expr_type:
                    self.add_error(f"Tipo incompatível na atribuição: '{var_name}' é do tipo '{var_type}' mas recebeu '{expr_type}'")
        
        elif stmt_type == 'increment' or stmt_type == 'decrement':
            var_name = stmt[1]
            
            if not self.is_symbol_defined(var_name):
                self.add_error(f"Variável '{var_name}' não declarada")
                return
                
            symbol = self.get_symbol(var_name)
            if symbol['type'] not in ('int', 'float'):
                self.add_error(f"Operação {stmt_type} inválida para variável do tipo '{symbol['type']}'")
        
        elif stmt_type == 'if':
            condition = stmt[1]
            if_block = stmt[2]
            
            self.analyze_condition(condition)
            self.analyze_block(if_block)
            
            # Verifica se tem else
            if len(stmt) > 3:
                else_block = stmt[3]
                self.analyze_block(else_block)
        
        elif stmt_type == 'while':
            condition = stmt[1]
            block = stmt[2]
            
            self.analyze_condition(condition)
            self.analyze_block(block)
        
        elif stmt_type == 'for':
            init = stmt[1]
            condition = stmt[2]
            update = stmt[3]
            block = stmt[4]
            
            self.analyze_statement(init)
            self.analyze_condition(condition)
            self.analyze_statement(update)
            self.analyze_block(block)
        
        elif stmt_type == 'print':
            for item in stmt[1]:
                if isinstance(item, tuple) and item[0] == 'string_literal':
                    continue  # Ignora strings literais
                self.analyze_expression(item)
        
        elif stmt_type == 'input':
            variables = stmt[1]
            for var_name in variables:
                if not self.is_symbol_defined(var_name):
                    self.add_error(f"Variável '{var_name}' não declarada")
        
        elif stmt_type == 'return':
            expr = stmt[1]
            expr_type = self.analyze_expression(expr)
            
            if self.current_scope in self.functions:
                expected_type = self.functions[self.current_scope]['return_type']
                if expr_type != expected_type:
                    self.add_error(f"Tipo de retorno incompatível: esperado '{expected_type}', obtido '{expr_type}'")
            elif self.current_scope == "main":
                self.add_error("O método main não deve retornar valores")
        
        elif stmt_type == 'break':
            # Verifica se está dentro de um loop
            # (Implementação simplificada - seria necessário rastrear contexto de loops)
            pass
        
        elif stmt_type == 'block':
            self.analyze_block(stmt[1])
        
        elif stmt_type == 'call':
            func_name = stmt[1]
            args = stmt[2]
            
            if func_name not in self.functions:
                self.add_error(f"Função '{func_name}' não declarada")
                return
                
            # Verifica parâmetros
            expected_params = self.functions[func_name]['params']
            if len(args) != len(expected_params):
                self.add_error(f"Número incorreto de argumentos para '{func_name}'. Esperado: {len(expected_params)}, Obtido: {len(args)}")
                return
                
            for i, (arg, param) in enumerate(zip(args, expected_params)):
                arg_type = self.analyze_expression(arg)
                param_type = param[0]
                
                if arg_type != param_type:
                    self.add_error(f"Tipo incorreto para argumento {i+1} de '{func_name}'. Esperado: '{param_type}', Obtido: '{arg_type}'")
    
    def analyze_condition(self, condition):
        """Analisa uma condição (if, while, etc.)"""
        if condition[0] == 'condition':
            op = condition[1]
            left = condition[2]
            right = condition[3]
            
            left_type = self.analyze_expression(left)
            right_type = self.analyze_expression(right)
            
            if left_type != right_type:
                self.add_error(f"Tipos incompatíveis na condição: '{left_type}' e '{right_type}'")
        
        elif condition[0] == 'not':
            expr = condition[1]
            expr_type = self.analyze_expression(expr)
            
            if expr_type != 'bool':
                self.add_error(f"Operador NOT aplicado a tipo não booleano: '{expr_type}'")
    
    def analyze_expression(self, expr):
        """Analisa uma expressão e retorna seu tipo"""
        if isinstance(expr, tuple):
            if expr[0] == 'binop':
                op = expr[1]
                left = expr[2]
                right = expr[3]
                
                left_type = self.analyze_expression(left)
                right_type = self.analyze_expression(right)
                
                # Verifica compatibilidade de tipos
                if left_type != right_type:
                    # Permite operações entre int e float (promove int para float)
                    if {left_type, right_type} == {'int', 'float'}:
                        # Para operações aritméticas, o resultado é float
                        if op in ('+', '-', '*', '/'):
                            return 'float'
                        # Para comparações, o resultado é bool
                        elif op in ('==', '!=', '>', '<'):
                            return 'bool'
                    else:
                        self.add_error(f"Tipos incompatíveis na operação '{op}': '{left_type}' e '{right_type}'")
                        return None
                
                # Operações aritméticas
                if op in ('+', '-', '*', '/'):
                    if left_type not in ('int', 'float'):
                        self.add_error(f"Operação '{op}' inválida para tipo '{left_type}'")
                        return None
                    
                    # Divisão sempre retorna float
                    if op == '/':
                        return 'float'
                    return left_type
                
                # Operações de comparação
                elif op in ('==', '!=', '>', '<'):
                    return 'bool'
                
                # Operações com strings
                elif op == '+':
                    if left_type == 'str' and right_type == 'str':
                        return 'str'
            
            elif expr[0] == 'uminus':
                operand_type = self.analyze_expression(expr[1])
                if operand_type not in ('int', 'float'):
                    self.add_error(f"Operador unário '-' inválido para tipo '{operand_type}'")
                    return None
                return operand_type
            
            elif expr[0] == 'call':
                func_name = expr[1]
                if func_name not in self.functions:
                    self.add_error(f"Função '{func_name}' não declarada")
                    return None
                return self.functions[func_name]['return_type']
            
            elif expr[0] == 'string_literal':
                return 'str'
            
            elif expr[0] == 'condition':
                # Já tratado em analyze_condition
                return 'bool'
        
        elif isinstance(expr, str):
            # Verifica se é uma string literal (entre aspas)
            if expr.startswith('"') and expr.endswith('"'):
                return 'str'
            # Verifica se é um booleano literal
            elif expr.lower() in ('true', 'false'):
                return 'bool'
            # Caso contrário, é uma variável
            elif self.is_symbol_defined(expr):
                return self.get_symbol(expr)['type']
            else:
                self.add_error(f"Variável '{expr}' não declarada")
                return None
        
        elif isinstance(expr, bool):
            return 'bool'
        
        elif isinstance(expr, int):
            return 'int'
        
        elif isinstance(expr, float):
            return 'float'
        
        return None
    
    def add_symbol(self, name, type, scope, is_const=False):
        """Adiciona um símbolo à tabela de símbolos"""
        if name in self.symbol_table[scope]:
            self.add_error(f"'{name}' já declarado no escopo '{scope}'")
            return
            
        self.symbol_table[scope][name] = {
            'type': type,
            'scope': scope,
            'is_const': is_const
        }
    
    def is_symbol_defined(self, name):
        """Verifica se um símbolo está definido no escopo atual ou global"""
        if name in self.symbol_table[self.current_scope]:
            return True
        if name in self.symbol_table["global"]:
            return True
        return False
    
    def get_symbol(self, name):
        """Obtém informações de um símbolo"""
        if name in self.symbol_table[self.current_scope]:
            return self.symbol_table[self.current_scope][name]
        if name in self.symbol_table["global"]:
            return self.symbol_table["global"][name]
        return None
    
    def add_error(self, message):
        """Adiciona um erro semântico"""
        self.errors.append(message)
    
    def get_errors(self):
        """Retorna a lista de erros semânticos"""
        return self.errors
from llvmlite import ir

class LLVMGenerator:
    def __init__(self):
        self.module = ir.Module(name="main_module")
        # Configurar target triple e data layout corretos
        self.module.triple = "x86_64-pc-linux-gnu"
        self.module.data_layout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-f80:128-n8:16:32:64-S128"
        self.builder = None
        self.symbol_table = {}
        self.functions = {}
        self.current_function = None
        self.return_type = None
        self.string_cache = {}  # Cache para strings globais

    def generate(self, ast):
        """Gera LLVM IR a partir da AST"""
        self.visit(ast)
        return str(self.module)

    def _map_type(self, type_str):
        """Mapeia tipos da linguagem para tipos LLVM"""
        type_map = {
            'int': ir.IntType(32),
            'float': ir.DoubleType(),
            'bool': ir.IntType(1),
            'str': ir.PointerType(ir.IntType(8)),
            'void': ir.VoidType()
        }
        return type_map.get(type_str.lower(), ir.IntType(32))  # Default para int

    def visit(self, node):
        if node is None:
            return None

        # Se o node é um valor primitivo (int, float, bool, str)
        if isinstance(node, (int, float, str, bool)):
            if isinstance(node, int):
                return ir.Constant(ir.IntType(32), node)
            elif isinstance(node, float):
                return ir.Constant(ir.DoubleType(), node)
            elif isinstance(node, bool):
                return ir.Constant(ir.IntType(1), int(node))
            elif isinstance(node, str):
                # Tentar detectar se é um número como string
                try:
                    if '.' in node:
                        return ir.Constant(ir.DoubleType(), float(node))
                    else:
                        return ir.Constant(ir.IntType(32), int(node))
                except ValueError:
                    # É uma string literal ou identificador
                    if node.startswith('"') and node.endswith('"'):
                        return self.visit_string_literal(node[1:-1])
                    else:
                        # É um identificador - fazer load se existir
                        if node in self.symbol_table:
                            ptr = self.symbol_table[node]
                            return self.builder.load(ptr, name=f"{node}.load")
                        else:
                            raise ValueError(f"Identificador '{node}' não encontrado na tabela de símbolos")
            return node

        # Se o node é uma lista, processar cada elemento
        if isinstance(node, list):
            for item in node:
                self.visit(item)
            return None

        # Se o node é uma tupla, processa normalmente
        if isinstance(node, tuple) and len(node) > 0:
            node_type = node[0]
            # Corrigir nomes de métodos que têm hífen
            if node_type == 'if-else':
                node_type = 'if_else'
            visitor = getattr(self, f'visit_{node_type}', None)
            if visitor:
                return visitor(node)
        
        return None

    def visit_program(self, node):
        _, program_name, content = node
        self.module.name = f"program_{program_name}"
        
        declarations, methods, main = content
        self.visit(declarations)
        
        for method in methods:
            self.visit(method)
        
        self.visit(main)

    def visit_declarations(self, node):
        _, declarations = node
        for decl in declarations:
            self.visit(decl)

    def visit_declare_group(self, node):
        _, var_list, var_type = node
        llvm_type = self._map_type(var_type)
        for var_name in var_list:
            if self.current_function:
                # Variável local
                ptr = self.builder.alloca(llvm_type, name=var_name)
                self.symbol_table[var_name] = ptr
            else:
                # Variável global
                var = ir.GlobalVariable(self.module, llvm_type, var_name)
                var.initializer = llvm_type(0)
                self.symbol_table[var_name] = var

    def visit_declare(self, node):
        _, var_type, var_name = node
        llvm_type = self._map_type(var_type)
        if self.current_function:
            ptr = self.builder.alloca(llvm_type, name=var_name)
            self.symbol_table[var_name] = ptr
        else:
            var = ir.GlobalVariable(self.module, llvm_type, var_name)
            # Inicializar com valor padrão baseado no tipo
            if llvm_type == ir.IntType(32):
                var.initializer = ir.Constant(llvm_type, 0)
            elif llvm_type == ir.IntType(1):
                var.initializer = ir.Constant(llvm_type, False)
            elif llvm_type == ir.DoubleType():
                var.initializer = ir.Constant(llvm_type, 0.0)
            elif isinstance(llvm_type, ir.PointerType):
                var.initializer = ir.Constant(llvm_type, None)  # null pointer
            else:
                var.initializer = llvm_type(0)
            self.symbol_table[var_name] = var

    def visit_const_assign(self, node):
        _, var_name, value = node
        if isinstance(value, bool):
            llvm_type = ir.IntType(1)
            const = ir.Constant(llvm_type, int(value))
        elif isinstance(value, int):
            llvm_type = ir.IntType(32)
            const = ir.Constant(llvm_type, value)
        elif isinstance(value, float):
            llvm_type = ir.DoubleType()
            const = ir.Constant(llvm_type, value)
        else:  # string
            llvm_type = ir.PointerType(ir.IntType(8))
            const = ir.GlobalVariable(self.module, llvm_type, name=f"str.{var_name}")
            const.initializer = ir.Constant(ir.ArrayType(ir.IntType(8), len(value)), bytearray(value.encode()))
        
        var = ir.GlobalVariable(self.module, llvm_type, var_name)
        var.initializer = const
        self.symbol_table[var_name] = var

    def visit_method(self, node):
        _, return_type, method_name, params, body = node
        llvm_return_type = self._map_type(return_type)
        
        # Cria tipos dos parâmetros - ajustado para a estrutura correta
        param_types = [self._map_type(p[0]) for p in params]  # p[0] é o tipo, p[1] é o nome
        func_type = ir.FunctionType(llvm_return_type, param_types)
        
        # Adiciona função ao módulo
        func = ir.Function(self.module, func_type, name=method_name)
        self.functions[method_name] = func
        
        # Cria bloco de entrada
        entry_block = func.append_basic_block(name="entry")
        self.builder = ir.IRBuilder(entry_block)
        self.current_function = func
        self.return_type = llvm_return_type
        
        # Salvar estado anterior da tabela de símbolos
        old_symbol_table = self.symbol_table.copy()
        
        # Adiciona parâmetros à tabela de símbolos - ajustado para a estrutura correta
        for i, (param_type, param_name) in enumerate(params):
            ptr = self.builder.alloca(self._map_type(param_type), name=param_name)
            self.builder.store(func.args[i], ptr)
            self.symbol_table[param_name] = ptr
        
        # Processar o corpo da função
        # Garantir que processamos todos os statements na ordem correta
        all_statements = []
        for stmt in body:
            if isinstance(stmt, list):
                all_statements.extend(stmt)
            else:
                all_statements.append(stmt)
        
        # Separar statements por tipo para processar em ordem correta
        declarations = []
        assigns = []
        returns = []
        others = []
        
        for s in all_statements:
            if isinstance(s, tuple) and len(s) > 0:
                if s[0] == 'declarations':
                    declarations.append(s)
                elif s[0] == 'assign':
                    assigns.append(s)
                elif s[0] == 'return':
                    returns.append(s)
                else:
                    others.append(s)
            else:
                others.append(s)
        
        # Processar em ordem: declarations, others, assigns, returns
        for s in declarations + others + assigns + returns:
            self.visit(s)
        
        # Adiciona retorno padrão se necessário
        if not self.builder.block.is_terminated:
            if llvm_return_type == ir.VoidType():
                self.builder.ret_void()
            else:
                # Retorno padrão baseado no tipo
                if llvm_return_type == ir.IntType(32):
                    self.builder.ret(ir.Constant(ir.IntType(32), 0))
                elif llvm_return_type == ir.IntType(1):
                    self.builder.ret(ir.Constant(ir.IntType(1), 0))
                elif llvm_return_type == ir.DoubleType():
                    self.builder.ret(ir.Constant(ir.DoubleType(), 0.0))
        
        # Restaurar estado
        self.symbol_table = old_symbol_table
        self.current_function = None
        self.return_type = None
        self.builder = None

    def visit_main(self, node):
        # Estrutura: ('main', (declarações, statements))
        _, content = node
        declarations, statements = content
        
        func_type = ir.FunctionType(ir.VoidType(), [])
        func = ir.Function(self.module, func_type, name="main")
        
        # Criar bloco de entrada
        entry_block = func.append_basic_block(name="entry")
        self.builder = ir.IRBuilder(entry_block)
        self.current_function = func
        
        # Salvar estado anterior da tabela de símbolos
        old_symbol_table = self.symbol_table.copy()
        
        # Processar declarações locais
        self.visit(declarations)
        
        # Processar statements - manter ordem original a menos que haja dependências problemáticas
        # Reorganizar quando há if seguido de assigns de variáveis usadas na condição
        should_reorder = False
        
        # Verificar se há padrão if + assign que precisa ser reordenado
        for i, stmt in enumerate(statements):
            if (isinstance(stmt, tuple) and len(stmt) > 0 and 
                stmt[0] == 'if'):
                # Verificar se há assigns de variáveis booleanas depois
                for j in range(i + 1, len(statements)):
                    next_stmt = statements[j]
                    if (isinstance(next_stmt, tuple) and len(next_stmt) > 0 and
                        next_stmt[0] == 'assign' and len(next_stmt) > 2 and
                        next_stmt[2] in ('true', 'false')):  # Atribuição booleana
                        should_reorder = True
                        break
                if should_reorder:
                    break
        
        if should_reorder:
            # Separar statements por tipo para processar em ordem correta
            assigns = []
            conditions = []
            others = []
            
            for stmt in statements:
                if isinstance(stmt, tuple) and len(stmt) > 0:
                    if stmt[0] == 'assign':
                        assigns.append(stmt)
                    elif stmt[0] in ('if', 'if_else', 'while', 'for'):
                        conditions.append(stmt)
                    else:
                        others.append(stmt)
                else:
                    others.append(stmt)
            
            # Processar em ordem: assigns, outros, conditions
            for stmt in assigns + others + conditions:
                self.visit(stmt)
        else:
            # Processar statements na ordem original
            for stmt in statements:
                self.visit(stmt)
        
        # Adicionar retorno void se não houver retorno explícito
        if not self.builder.block.is_terminated:
            self.builder.ret_void()
        
        # Restaurar estado
        self.symbol_table = old_symbol_table
        self.current_function = None
        self.builder = None

    def visit_block(self, node):
        """Processa um bloco de instruções"""
        _, content = node
        
        # Se content é uma tupla com (declarations, statements)
        if isinstance(content, tuple) and len(content) == 2:
            declarations, statements = content
            
            # Processar declarações se existirem
            if declarations:
                for decl in declarations:
                    self.visit(decl)
            
            # Processar statements
            if statements:
                for stmt in statements:
                    self.visit(stmt)
        else:
            # Se content é uma lista simples de statements
            for stmt in content:
                self.visit(stmt)

    def visit_assign(self, node):
        _, var_name, expr = node
        
        # Processar expressão
        if expr == 'true':
            value = ir.Constant(ir.IntType(1), 1)
        elif expr == 'false':
            value = ir.Constant(ir.IntType(1), 0)
        else:
            value = self.visit(expr)
        
        # Buscar a variável na tabela de símbolos
        if var_name in self.symbol_table:
            ptr = self.symbol_table[var_name]
            
            # Verificar se os tipos são compatíveis
            if isinstance(ptr, ir.GlobalVariable):
                target_type = ptr.type.pointee
            else:
                target_type = ptr.type.pointee
            
            # Converter tipos se necessário
            if target_type != value.type:
                # Conversões básicas
                if target_type == ir.IntType(1) and value.type == ir.IntType(32):
                    # int para bool
                    value = self.builder.icmp_signed('!=', value, ir.Constant(ir.IntType(32), 0))
                elif target_type == ir.IntType(32) and value.type == ir.IntType(1):
                    # bool para int
                    value = self.builder.zext(value, ir.IntType(32))
                elif target_type == ir.DoubleType() and value.type == ir.IntType(32):
                    # int para float
                    value = self.builder.sitofp(value, ir.DoubleType())
                elif target_type == ir.IntType(32) and value.type == ir.DoubleType():
                    # float para int
                    value = self.builder.fptosi(value, ir.IntType(32))
            
            self.builder.store(value, ptr)
        else:
            # Se não existe, criar variável local
            if self.current_function:
                # Inferir tipo do valor
                var_type = value.type
                ptr = self.builder.alloca(var_type, name=var_name)
                self.symbol_table[var_name] = ptr
                self.builder.store(value, ptr)
            else:
                raise ValueError(f"Variável '{var_name}' não declarada")

    def visit_binop(self, node):
        _, op, left, right = node
        left_val = self.visit(left)
        right_val = self.visit(right)
        
        # Verificar se os valores são válidos
        if left_val is None or right_val is None:
            raise ValueError("Operandos inválidos na operação binária")
        
        # Determinar se precisamos de conversão de tipos
        left_type = left_val.type
        right_type = right_val.type
        
        # Promover tipos se necessário (int para float)
        if left_type == ir.IntType(32) and right_type == ir.DoubleType():
            left_val = self.builder.sitofp(left_val, ir.DoubleType(), name="int_to_float")
            left_type = ir.DoubleType()
        elif left_type == ir.DoubleType() and right_type == ir.IntType(32):
            right_val = self.builder.sitofp(right_val, ir.DoubleType(), name="int_to_float")
            right_type = ir.DoubleType()
        
        # Operações aritméticas
        if op == '+':
            if left_type == ir.DoubleType():
                return self.builder.fadd(left_val, right_val, name="fadd")
            else:
                return self.builder.add(left_val, right_val, name="add")
        elif op == '-':
            if left_type == ir.DoubleType():
                return self.builder.fsub(left_val, right_val, name="fsub")
            else:
                return self.builder.sub(left_val, right_val, name="sub")
        elif op == '*':
            if left_type == ir.DoubleType():
                return self.builder.fmul(left_val, right_val, name="fmul")
            else:
                return self.builder.mul(left_val, right_val, name="mul")
        elif op == '/':
            if left_type == ir.DoubleType():
                return self.builder.fdiv(left_val, right_val, name="fdiv")
            else:
                return self.builder.sdiv(left_val, right_val, name="sdiv")
        # Operações de comparação
        elif op == '==':
            if left_type == ir.DoubleType():
                return self.builder.fcmp_ordered('==', left_val, right_val, name="fcmp_eq")
            else:
                return self.builder.icmp_signed('==', left_val, right_val, name="icmp_eq")
        elif op in ('>', '<', '!=', '>=', '<='):
            if left_type == ir.DoubleType():
                return self.builder.fcmp_ordered(op, left_val, right_val, name="fcmp")
            else:
                return self.builder.icmp_signed(op, left_val, right_val, name="icmp")
        else:
            raise ValueError(f"Operação '{op}' não suportada")

    def visit_if(self, node):
        _, condition, if_block = node
        
        # Avaliar condição
        if isinstance(condition, str):
            # Se é uma string, procurar na tabela de símbolos
            if condition in self.symbol_table:
                ptr = self.symbol_table[condition]
                cond_val = self.builder.load(ptr, name=f"{condition}.load")
            else:
                raise ValueError(f"Variável '{condition}' não encontrada")
        else:
            cond_val = self.visit(condition)
        
        # Criar blocos
        if_block_llvm = self.current_function.append_basic_block(name="if_block")
        merge_block = self.current_function.append_basic_block(name="merge")
        
        # Branch condicional
        self.builder.cbranch(cond_val, if_block_llvm, merge_block)
        
        # Gera código para o bloco if
        self.builder.position_at_end(if_block_llvm)
        self.visit(if_block)
        if not self.builder.block.is_terminated:
            self.builder.branch(merge_block)
        
        # Continua no bloco merge
        self.builder.position_at_end(merge_block)

    def visit_if_else(self, node):
        _, condition, if_block, else_block = node
        cond_val = self.visit(condition)
        
        if_block_llvm = self.current_function.append_basic_block(name="if_block")
        else_block_llvm = self.current_function.append_basic_block(name="else_block")
        merge_block = self.current_function.append_basic_block(name="merge")
        
        self.builder.cbranch(cond_val, if_block_llvm, else_block_llvm)
        
        # Gera código para o bloco if
        self.builder.position_at_end(if_block_llvm)
        self.visit(if_block)
        self.builder.branch(merge_block)
        
        # Gera código para o bloco else
        self.builder.position_at_end(else_block_llvm)
        self.visit(else_block)
        self.builder.branch(merge_block)
        
        # Continua no bloco merge
        self.builder.position_at_end(merge_block)

    def visit_while(self, node):
        _, condition, block = node
        cond_block = self.current_function.append_basic_block(name="while_cond")
        body_block = self.current_function.append_basic_block(name="while_body")
        end_block = self.current_function.append_basic_block(name="while_end")
        
        # Salta para o bloco de condição
        self.builder.branch(cond_block)
        
        # Bloco de condição
        self.builder.position_at_end(cond_block)
        cond_val = self.visit(condition)
        self.builder.cbranch(cond_val, body_block, end_block)
        
        # Bloco do corpo
        self.builder.position_at_end(body_block)
        self.visit(block)
        self.builder.branch(cond_block)  # Loop
        
        # Bloco de saída
        self.builder.position_at_end(end_block)

    def visit_for(self, node):
        _, init, condition, update, block = node
        cond_block = self.current_function.append_basic_block(name="for_cond")
        body_block = self.current_function.append_basic_block(name="for_body")
        update_block = self.current_function.append_basic_block(name="for_update")
        end_block = self.current_function.append_basic_block(name="for_end")
        
        # Inicialização
        self.visit(init)
        self.builder.branch(cond_block)
        
        # Condição
        self.builder.position_at_end(cond_block)
        cond_val = self.visit(condition)
        self.builder.cbranch(cond_val, body_block, end_block)
        
        # Corpo
        self.builder.position_at_end(body_block)
        self.visit(block)
        self.builder.branch(update_block)
        
        # Atualização
        self.builder.position_at_end(update_block)
        self.visit(update)
        self.builder.branch(cond_block)
        
        # Fim
        self.builder.position_at_end(end_block)

    def visit_print(self, node):
        _, items = node
        
        # Declara funções de formatação padrão se não existirem
        self._declare_print_functions()
        
        for item in items:
            if isinstance(item, tuple) and item[0] == 'string_literal':
                # Caso para strings literais
                self._print_string_literal(item[1])
            elif isinstance(item, str):
                # Verificar se é uma string literal (entre aspas)
                if item.startswith('"') and item.endswith('"'):
                    # É uma string literal - remover as aspas
                    text = item[1:-1]  # Remove aspas do início e fim
                    self._print_string_literal(text)
                elif item in self.symbol_table:
                    # É um identificador de variável
                    ptr = self.symbol_table[item]
                    value = self.builder.load(ptr, name=f"{item}.load")
                    
                    if value.type == ir.IntType(1):  # bool
                        self._print_bool(value)
                    elif value.type == ir.IntType(32):  # int
                        self._print_int(value)
                    elif value.type == ir.DoubleType():  # float
                        self._print_float(value)
                    else:
                        self._print_unknown()
                else:
                    raise ValueError(f"Variável '{item}' não encontrada")
            else:
                # Caso para expressões/variáveis
                value = self.visit(item)
                if value.type == ir.IntType(1):  # bool
                    self._print_bool(value)
                elif value.type == ir.IntType(32):  # int
                    self._print_int(value)
                elif value.type == ir.DoubleType():  # float
                    self._print_float(value)
                elif isinstance(value.type, ir.PointerType) and \
                     isinstance(value.type.pointee, ir.IntType):  # string
                    self._print_string(value)
                else:
                    # Tipo não suportado
                    self._print_unknown()

    def _declare_print_functions(self):
        """Declara funções de I/O padrão necessárias"""
        if 'printf' not in self.module.globals:
            # Declara printf
            printf_ty = ir.FunctionType(ir.IntType(32), [ir.PointerType(ir.IntType(8))], var_arg=True)
            printf = ir.Function(self.module, printf_ty, name="printf")
            printf.attributes.add('noinline')
            
        if 'puts' not in self.module.globals:
            # Declara puts para strings simples
            puts_ty = ir.FunctionType(ir.IntType(32), [ir.PointerType(ir.IntType(8))])
            puts = ir.Function(self.module, puts_ty, name="puts")
            puts.attributes.add('noinline')

    def _print_string_literal(self, text):
        """Gera código para imprimir string literal"""
        # Cria constante global para a string
        text_bytes = text.encode('utf-8')
        str_type = ir.ArrayType(ir.IntType(8), len(text_bytes)+1)
        str_const = ir.Constant(str_type, bytearray(text_bytes + b'\0'))
        
        # Cria variável global para a string
        global_name = f".str.{abs(hash(text))}"
        global_var = ir.GlobalVariable(self.module, str_type, global_name)
        global_var.linkage = 'private'
        global_var.global_constant = True
        global_var.initializer = str_const
        
        # Obtém ponteiro para o primeiro caractere
        ptr = self.builder.gep(global_var, [ir.Constant(ir.IntType(32), 0), ir.Constant(ir.IntType(32), 0)], inbounds=True)
        
        # Chama puts (mais eficiente para strings sem formatação)
        puts = self.module.get_global('puts')
        self.builder.call(puts, [ptr])

    def _print_int(self, value):
        """Gera código para imprimir inteiro"""
        fmt_str = self._get_or_create_global_string("%d\n", "int_fmt")
        printf = self.module.get_global('printf')
        # Garantir que fmt_str é um ponteiro i8*
        if isinstance(fmt_str.type, ir.PointerType) and isinstance(fmt_str.type.pointee, ir.ArrayType):
            fmt_str = self.builder.bitcast(fmt_str, ir.PointerType(ir.IntType(8)))
        self.builder.call(printf, [fmt_str, value])

    def _print_float(self, value):
        """Gera código para imprimir float"""
        fmt_str = self._get_or_create_global_string("%.2f\n", "float_fmt")
        printf = self.module.get_global('printf')
        # Garantir que fmt_str é um ponteiro i8*
        if isinstance(fmt_str.type, ir.PointerType) and isinstance(fmt_str.type.pointee, ir.ArrayType):
            fmt_str = self.builder.bitcast(fmt_str, ir.PointerType(ir.IntType(8)))
        self.builder.call(printf, [fmt_str, value])

    def _print_bool(self, value):
        """Gera código para imprimir booleano"""
        # Primeiro converte para string "true" ou "false"
        true_str = self._get_or_create_global_string("true\n", ".true_str")
        false_str = self._get_or_create_global_string("false\n", ".false_str")
        
        # Garantir que são ponteiros i8*
        if isinstance(true_str.type, ir.PointerType) and isinstance(true_str.type.pointee, ir.ArrayType):
            true_str = self.builder.bitcast(true_str, ir.PointerType(ir.IntType(8)))
        if isinstance(false_str.type, ir.PointerType) and isinstance(false_str.type.pointee, ir.ArrayType):
            false_str = self.builder.bitcast(false_str, ir.PointerType(ir.IntType(8)))
        
        # Seleciona a string apropriada
        str_ptr = self.builder.select(value, true_str, false_str)
        
        # Imprime usando puts
        puts = self.module.get_global('puts')
        self.builder.call(puts, [str_ptr])

    def _print_string(self, value):
        """Gera código para imprimir string (ponteiro para char)"""
        puts = self.module.get_global('puts')
        self.builder.call(puts, [value])

    def _print_unknown(self):
        """Gera código para tipo desconhecido"""
        fmt_str = self._get_or_create_global_string("<unknown type>\n", ".unk_fmt")
        puts = self.module.get_global('puts')
        # Garantir que fmt_str é um ponteiro i8*
        if isinstance(fmt_str.type, ir.PointerType) and isinstance(fmt_str.type.pointee, ir.ArrayType):
            fmt_str = self.builder.bitcast(fmt_str, ir.PointerType(ir.IntType(8)))
        self.builder.call(puts, [fmt_str])

    def _get_or_create_global_string(self, text, name_prefix=""):
        """Cria ou retorna uma string global constante"""
        # Usar cache para evitar duplicatas
        cache_key = f"{name_prefix}:{text}"
        if cache_key in self.string_cache:
            return self.string_cache[cache_key]
        
        text_bytes = text.encode('utf-8')
        str_type = ir.ArrayType(ir.IntType(8), len(text_bytes)+1)
        
        # Criar nome único usando um contador simples
        import time
        global_name = f"{name_prefix}_{abs(hash(text))}_{int(time.time() * 1000000) % 1000000}"
        
        str_const = ir.Constant(str_type, bytearray(text_bytes + b'\0'))
        global_var = ir.GlobalVariable(self.module, str_type, global_name)
        global_var.linkage = 'private'
        global_var.global_constant = True
        global_var.initializer = str_const
        
        # Criar ponteiro para a string
        ptr = self.builder.gep(global_var, [ir.Constant(ir.IntType(32), 0), ir.Constant(ir.IntType(32), 0)], inbounds=True)
        
        # Salvar no cache
        self.string_cache[cache_key] = ptr
        
        return ptr

    def visit_return(self, node):
        if len(node) == 1:
            # return sem valor
            self.builder.ret_void()
        else:
            # return com valor
            _, expr = node
            value = self.visit(expr)
            self.builder.ret(value)

    def visit_call(self, node):
        _, func_name, args = node
        
        # Buscar função na tabela de funções
        if func_name in self.functions:
            func = self.functions[func_name]
        else:
            raise ValueError(f"Função '{func_name}' não encontrada")
        
        # Avaliar argumentos
        arg_values = []
        for arg in args:
            if isinstance(arg, str) and arg in self.symbol_table:
                # É uma variável - fazer load
                ptr = self.symbol_table[arg]
                value = self.builder.load(ptr, name=f"{arg}.load")
                arg_values.append(value)
            else:
                # É uma expressão
                value = self.visit(arg)
                arg_values.append(value)
        
        # Chamar função
        return self.builder.call(func, arg_values, name="call_result")

    def visit_uminus(self, node):
        _, expr = node
        value = self.visit(expr)
        if isinstance(value.type, ir.DoubleType):
            return self.builder.fneg(value, name="neg")
        else:
            return self.builder.neg(value, name="neg")

    def visit_not(self, node):
        _, expr = node
        value = self.visit(expr)
        return self.builder.not_(value, name="not")

    def visit_condition(self, node):
        _, op, left, right = node
        left_val = self.visit(left)
        right_val = self.visit(right)
        
        if isinstance(left_val.type, ir.DoubleType):
            return self.builder.fcmp_ordered(op, left_val, right_val, name="cmp")
        else:
            return self.builder.icmp_signed(op, left_val, right_val, name="cmp")

    def visit_number(self, node):
        """Processa números literais"""
        if isinstance(node, tuple) and len(node) == 2:
            _, value = node
        else:
            value = node
            
        if isinstance(value, int):
            return ir.Constant(ir.IntType(32), value)
        elif isinstance(value, float):
            return ir.Constant(ir.DoubleType(), value)
        else:
            # Caso seja um valor direto (não tuple)
            if isinstance(node, int):
                return ir.Constant(ir.IntType(32), node)
            elif isinstance(node, float):
                return ir.Constant(ir.DoubleType(), node)
            elif isinstance(node, bool):
                return ir.Constant(ir.IntType(1), int(node))
            elif isinstance(node, str):
                # Tentar converter string para número
                try:
                    if '.' in node:
                        return ir.Constant(ir.DoubleType(), float(node))
                    else:
                        return ir.Constant(ir.IntType(32), int(node))
                except ValueError:
                    # Não é um número, retornar None
                    return None

    def visit_id(self, node):
        """Processa identificadores (variáveis)"""
        if isinstance(node, tuple):
            _, var_name = node
        else:
            var_name = node
            
        if var_name in self.symbol_table:
            var_ptr = self.symbol_table[var_name]
            # Fazer load da variável
            return self.builder.load(var_ptr, name=f"{var_name}.load")
        else:
            raise ValueError(f"Variável '{var_name}' não declarada")

    def visit_true(self, node):
        """Processa valor booleano true"""
        return ir.Constant(ir.IntType(1), 1)
    
    def visit_false(self, node):
        """Processa valor booleano false"""
        return ir.Constant(ir.IntType(1), 0)

    def visit_string_literal(self, node):
        """Processa strings literais"""
        if isinstance(node, tuple):
            _, text = node
        else:
            text = node
            
        # Cria string global
        text_bytes = text.encode('utf-8')
        str_type = ir.ArrayType(ir.IntType(8), len(text_bytes) + 1)
        str_const = ir.Constant(str_type, bytearray(text_bytes + b'\0'))
        
        global_name = f".str.{abs(hash(text))}"
        global_var = ir.GlobalVariable(self.module, str_type, global_name)
        global_var.linkage = 'private'
        global_var.global_constant = True
        global_var.initializer = str_const
        
        # Retorna ponteiro para o primeiro caractere
        return self.builder.gep(global_var, [ir.Constant(ir.IntType(32), 0)], inbounds=True)

    def debug_ast(self, node, indent=0):
        """Debug: imprime estrutura da AST"""
        prefix = "  " * indent
        if isinstance(node, tuple):
            print(f"{prefix}TUPLE: {node[0] if len(node) > 0 else 'empty'}")
            for i, child in enumerate(node[1:], 1):
                print(f"{prefix}  [{i}]:")
                self.debug_ast(child, indent + 2)
        else:
            print(f"{prefix}VALUE: {node} (type: {type(node).__name__})")

    def visit_input(self, node):
        """Processa instruções de input"""
        _, variables = node
        
        # Declarar scanf se não existir
        if 'scanf' not in self.module.globals:
            scanf_type = ir.FunctionType(ir.IntType(32), [ir.PointerType(ir.IntType(8))], var_arg=True)
            scanf_func = ir.Function(self.module, scanf_type, name="scanf")
            scanf_func.attributes.add('noinline')
        
        scanf = self.module.get_global('scanf')
        
        for var_name in variables:
            if var_name in self.symbol_table:
                ptr = self.symbol_table[var_name]
                
                # Determinar tipo da variável
                if isinstance(ptr, ir.GlobalVariable):
                    var_type = ptr.type.pointee
                else:
                    var_type = ptr.type.pointee
                
                # Criar format string baseado no tipo
                if var_type == ir.IntType(32):
                    fmt_str = self._get_or_create_global_string("%d", "scanf_int_fmt")
                elif var_type == ir.DoubleType():
                    fmt_str = self._get_or_create_global_string("%lf", "scanf_float_fmt")
                else:
                    # Tipo não suportado para input
                    continue
                
                # Garantir que fmt_str é um ponteiro i8*
                if isinstance(fmt_str.type, ir.PointerType) and isinstance(fmt_str.type.pointee, ir.ArrayType):
                    fmt_str = self.builder.bitcast(fmt_str, ir.PointerType(ir.IntType(8)))
                
                # Chamar scanf
                self.builder.call(scanf, [fmt_str, ptr])
            else:
                raise ValueError(f"Variável '{var_name}' não declarada")

from llvmlite import ir

class LLVMGenerator:
    def __init__(self):
        self.module = ir.Module(name="main_module")
        self.builder = None
        self.symbol_table = {}
        self.functions = {}
        self.current_function = None
        self.return_type = None

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

        node_type = node[0]
        visitor = getattr(self, f'visit_{node_type}', None)
        if visitor:
            return visitor(node)
        elif isinstance(node, (int, float, str, bool)):
            return node
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
        
        # Cria tipos dos parâmetros
        param_types = [self._map_type(p[0]) for p in params]
        func_type = ir.FunctionType(llvm_return_type, param_types)
        
        # Adiciona função ao módulo
        func = ir.Function(self.module, func_type, name=method_name)
        self.functions[method_name] = func
        
        # Cria bloco de entrada
        entry_block = func.append_basic_block(name="entry")
        self.builder = ir.IRBuilder(entry_block)
        self.current_function = func
        self.return_type = llvm_return_type
        
        # Adiciona parâmetros à tabela de símbolos
        for i, (param_type, param_name) in enumerate(params):
            ptr = self.builder.alloca(self._map_type(param_type), name=param_name)
            self.builder.store(func.args[i], ptr)
            self.symbol_table[param_name] = ptr
        
        self.visit(body)
        
        # Adiciona retorno padrão se necessário
        if not any(inst.opname == 'ret' for inst in entry_block.instructions):
            if llvm_return_type == ir.VoidType():
                self.builder.ret_void()
            else:
                self.builder.ret(ir.Constant(llvm_return_type, 0))
        
        self.current_function = None
        self.return_type = None

    def visit_main(self, node):
        _, body = node
        func_type = ir.FunctionType(ir.VoidType(), [])
        func = ir.Function(self.module, func_type, name="main")
        
        entry_block = func.append_basic_block(name="entry")
        self.builder = ir.IRBuilder(entry_block)
        self.current_function = func
        self.return_type = ir.VoidType()
        
        self.visit(body)
        
        if not any(isinstance(inst, ir.Return) for inst in entry_block.instructions):
            self.builder.ret_void()
        
        self.current_function = None
        self.return_type = None

    def visit_assign(self, node):
        _, var_name, expr = node
        value = self.visit(expr)
        ptr = self.symbol_table.get(var_name)
        if ptr:
            self.builder.store(value, ptr)

    def visit_binop(self, node):
        _, op, left, right = node
        left_val = self.visit(left)
        right_val = self.visit(right)
        
        if op == '+':
            if isinstance(left_val.type, ir.DoubleType):
                return self.builder.fadd(left_val, right_val, name="tmp")
            else:
                return self.builder.add(left_val, right_val, name="tmp")
        elif op == '-':
            if isinstance(left_val.type, ir.DoubleType):
                return self.builder.fsub(left_val, right_val, name="tmp")
            else:
                return self.builder.sub(left_val, right_val, name="tmp")
        elif op == '*':
            if isinstance(left_val.type, ir.DoubleType):
                return self.builder.fmul(left_val, right_val, name="tmp")
            else:
                return self.builder.mul(left_val, right_val, name="tmp")
        elif op == '/':
            if isinstance(left_val.type, ir.DoubleType):
                return self.builder.fdiv(left_val, right_val, name="tmp")
            else:
                return self.builder.sdiv(left_val, right_val, name="tmp")
        elif op == '==':
            if isinstance(left_val.type, ir.DoubleType):
                return self.builder.fcmp_ordered('==', left_val, right_val, name="cmp")
            else:
                return self.builder.icmp_signed('==', left_val, right_val, name="cmp")
        elif op in ('>', '<', '!=', '>=', '<='):
            if isinstance(left_val.type, ir.DoubleType):
                return self.builder.fcmp_ordered(op, left_val, right_val, name="cmp")
            else:
                return self.builder.icmp_signed(op, left_val, right_val, name="cmp")

    def visit_if(self, node):
        _, condition, if_block = node
        cond_val = self.visit(condition)
        
        if_block_llvm = self.current_function.append_basic_block(name="if_block")
        merge_block = self.current_function.append_basic_block(name="merge")
        
        self.builder.cbranch(cond_val, if_block_llvm, merge_block)
        
        # Gera código para o bloco if
        self.builder.position_at_end(if_block_llvm)
        self.visit(if_block)
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
            else:
                # Caso para expressões/variáveis
                value = self.visit(item)
                if isinstance(value.type, ir.IntType(1)):  # bool
                    self._print_bool(value)
                elif isinstance(value.type, ir.IntType(32)):  # int
                    self._print_int(value)
                elif isinstance(value.type, ir.DoubleType):  # float
                    self._print_float(value)
                elif isinstance(value.type, ir.PointerType) and \
                     isinstance(value.type.pointee, ir.IntType(8)):  # string
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
        ptr = self.builder.gep(global_var, [ir.Constant(ir.IntType(32), 0)], inbounds=True)
        
        # Chama puts (mais eficiente para strings sem formatação)
        puts = self.module.get_global('puts')
        self.builder.call(puts, [ptr])

    def _print_int(self, value):
        """Gera código para imprimir inteiro"""
        fmt_str = self._get_or_create_global_string("%d\n", ".int_fmt")
        printf = self.module.get_global('printf')
        self.builder.call(printf, [fmt_str, value])

    def _print_float(self, value):
        """Gera código para imprimir float"""
        fmt_str = self._get_or_create_global_string("%f\n", ".float_fmt")
        printf = self.module.get_global('printf')
        self.builder.call(printf, [fmt_str, value])

    def _print_bool(self, value):
        """Gera código para imprimir booleano"""
        # Primeiro converte para string "true" ou "false"
        true_str = self._get_or_create_global_string("true\n", ".true_str")
        false_str = self._get_or_create_global_string("false\n", ".false_str")
        
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
        self.builder.call(puts, [fmt_str])

    def _get_or_create_global_string(self, text, name_prefix=""):
        """Cria ou retorna uma string global constante"""
        text_bytes = text.encode('utf-8')
        str_type = ir.ArrayType(ir.IntType(8), len(text_bytes)+1)
        
        # Verifica se já existe uma string igual
        for global_var in self.module.globals:
            if isinstance(global_var, ir.GlobalVariable) and \
               isinstance(global_var.type, str_type) and \
               global_var.initializer is not None and \
               global_var.initializer == bytearray(text_bytes + b'\0'):
                return self.builder.gep(global_var, [ir.Constant(ir.IntType(32), 0)], inbounds=True)
        
        # Cria nova string global
        global_name = f"{name_prefix}.{abs(hash(text))}"
        str_const = ir.Constant(str_type, bytearray(text_bytes + b'\0'))
        global_var = ir.GlobalVariable(self.module, str_type, global_name)
        global_var.linkage = 'private'
        global_var.global_constant = True
        global_var.initializer = str_const
        
        return self.builder.gep(global_var, [ir.Constant(ir.IntType(32), 0)], inbounds=True)

    def visit_return(self, node):
        _, expr = node
        if expr is None:
            self.builder.ret_void()
        else:
            value = self.visit(expr)
            self.builder.ret(value)

    def visit_call(self, node):
        _, func_name, args = node
        func = self.functions.get(func_name)
        if not func:
            # Se não encontrada, assume função intrínseca
            arg_types = [self.visit(arg).type for arg in args]
            func = self.module.declare_intrinsic(func_name, [], arg_types)
        
        arg_values = [self.visit(arg) for arg in args]
        return self.builder.call(func, arg_values)

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
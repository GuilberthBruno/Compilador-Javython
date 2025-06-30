import ply.yacc as yacc
import lexer
from pprint import pprint

# --- Tabela de Símbolos e Contexto Semântico ---
symbol_table_stack = [{}]
current_scope_type = "global"
loop_depth = 0
current_method_return_type = None

def enter_scope():
    symbol_table_stack.append({})

def exit_scope():
    if len(symbol_table_stack) > 1:
        symbol_table_stack.pop()
    else:
        raise SemanticError("Attempted to exit global scope.")

def add_symbol(name, attributes, lineno):
    current_scope = symbol_table_stack[-1]
    if name.lower() in lexer.reserved.keys():
        raise SemanticError(f"Erro semântico: '{name}' é uma palavra reservada e não pode ser usada como identificador na linha {lineno}.")
    if name in current_scope:
        raise SemanticError(f"Erro semântico: Identificador '{name}' já declarado neste escopo na linha {lineno}.")
    if len(symbol_table_stack) == 1:
        for scope in symbol_table_stack:
            for existing_symbol_name, existing_symbol_attrs in scope.items():
                if existing_symbol_name == name and existing_symbol_attrs.get('kind') == 'method':
                     raise SemanticError(f"Erro semântico: Identificador '{name}' já é o nome de um método global na linha {lineno}.")
    current_scope[name] = attributes

def lookup_symbol(name):
    for scope in reversed(symbol_table_stack):
        if name in scope:
            return scope[name]
    return None

class SemanticError(Exception):
    pass

# --- Regras de Gramática e Análise Semântica ---

def p_program(p):
    '''program : PROGRAM COLON ID SEMICOLON program_content END'''
    exit_scope()
    p[0] = ('program', p[3], p[5], p.lineno(1))

def p_program_content(p):
    '''program_content : declarations methods_list main_method'''
    p[0] = (p[1], p[2], p[3])

def p_declarations(p):
    '''declarations : DECIDS COLON vars_and_consts_declarations
                    | empty'''
    if len(p) > 2:
        p[0] = ('declarations', p[3], p.lineno(1))
    else:
        p[0] = ('declarations', [], p.lineno(1) if p.slice[0].type == 'DECIDS' else 0)

def p_vars_and_consts_declarations(p):
    '''vars_and_consts_declarations : var_declaration
                                    | var_declaration vars_and_consts_declarations'''
    if len(p) == 2:
        p[0] = [p[1]]
    else:
        p[0] = [p[1]] + p[2]

def p_var_declaration(p):
    '''var_declaration : ID COMMA ID_list COLON type SEMICOLON
                       | ID COLON type SEMICOLON
                       | ID ASSIGN expression SEMICOLON'''
    lineno = p.lineno(1)
    if len(p) == 7: # Group declaration
        var_type = p[5]
        ids = [p[1]] + p[3]
        for var_id in ids:
            add_symbol(var_id, {'kind': 'variable', 'type': var_type, 'initialized': False, 'lineno': lineno}, lineno)
        p[0] = ('declare_group', ids, var_type, lineno)
    elif len(p) == 5:
        if p[2] == ':': # Single variable declaration
            var_type = p[3]
            var_id = p[1]
            add_symbol(var_id, {'kind': 'variable', 'type': var_type, 'initialized': False, 'lineno': lineno}, lineno)
            p[0] = ('declare', var_type, var_id, lineno)
        else: # Constant declaration/initialization
            var_id = p[1]
            expr_node = p[3]
            actual_type = get_expression_type(expr_node, lineno)
            existing_symbol = lookup_symbol(var_id)

            if existing_symbol:
                 if existing_symbol.get('kind') == 'constant':
                     raise SemanticError(f"Erro semântico: Constante '{var_id}' não pode ser reatribuída na linha {lineno}.")
                 elif existing_symbol.get('kind') == 'method':
                     raise SemanticError(f"Erro semântico: Identificador '{var_id}' já é um nome de método na linha {lineno}.")
                 if existing_symbol.get('kind') == 'variable':
                     if not is_type_compatible(existing_symbol['type'], actual_type):
                         raise SemanticError(f"Erro semântico: Incompatibilidade de tipos na atribuição para '{var_id}'. Esperado '{existing_symbol['type']}', mas recebeu '{actual_type}' na linha {lineno}.")
                     existing_symbol['initialized'] = True
                     p[0] = ('assign', var_id, expr_node, lineno)
                     return
            else:
                add_symbol(var_id, {'kind': 'constant', 'type': actual_type, 'value': expr_node, 'lineno': lineno}, lineno)
            p[0] = ('const_assign', var_id, expr_node, lineno)

def p_ID_list(p):
    '''ID_list : ID
               | ID COMMA ID_list'''
    if len(p) == 2:
        p[0] = [p[1]]
    else:
        p[0] = [p[1]] + p[3]

def p_type(p):
    '''type : INT
            | FLOAT
            | BOOL
            | STR'''
    p[0] = p[1]

def p_methods_list(p):
    '''methods_list : method_declaration methods_list
                    | empty'''
    if len(p) == 3:
        p[0] = [p[1]] + p[2]
    else:
        p[0] = []

def p_method_declaration(p):
    '''method_declaration : type_or_void ID LPAREN parameters_list RPAREN LBRACE block_content RBRACE'''
    global current_method_return_type
    method_type = p[1]
    method_name = p[2]
    params = p[4]
    block = p[7]
    lineno = p.lineno(2)

    for scope in symbol_table_stack:
        if method_name in scope:
            raise SemanticError(f"Erro semântico: O nome '{method_name}' já está em uso como {scope[method_name].get('kind')} na linha {lineno}.")

    add_symbol(method_name, {'kind': 'method', 'type': method_type, 'parameters': params, 'lineno': lineno}, lineno)

    enter_scope()
    global current_scope_type
    current_scope_type = "method"
    current_method_return_type = method_type

    for param_type, param_name in params:
        add_symbol(param_name, {'kind': 'parameter', 'type': param_type, 'lineno': lineno}, lineno)

    p[0] = ('method', method_type, method_name, params, block, lineno)

    exit_scope()
    current_scope_type = "global"
    current_method_return_type = None

def p_type_or_void(p):
    '''type_or_void : type
                    | VOID'''
    p[0] = p[1]

def p_parameters_list(p):
    '''parameters_list : parameter_list
                       | empty'''
    if len(p) == 2 and p[1] is not None:
        p[0] = p[1]
    else:
        p[0] = []

def p_parameter_list(p):
    '''parameter_list : parameter
                      | parameter COMMA parameter_list'''
    if len(p) == 2:
        p[0] = [p[1]]
    else:
        p[0] = [p[1]] + p[3]

def p_parameter(p):
    '''parameter : type ID'''
    p[0] = (p[1], p[2])

def p_main_method(p):
    '''main_method : MAIN COLON block_content'''
    lineno = p.lineno(1)
    enter_scope()
    global current_scope_type
    current_scope_type = "main"

    p[0] = ('main', p[3], lineno)

    exit_scope()
    current_scope_type = "global"

def p_empty(p):
    'empty :'
    p[0] = []

def p_statements(p):
    '''statements : statement
                  | statement statements'''
    if len(p) == 2:
        p[0] = [p[1]]
    else:
        p[0] = [p[1]] + p[2]

def p_statement(p):
    '''statement : assignment_statement
                 | if_statement
                 | while_statement
                 | for_statement
                 | print_statement
                 | input_statement
                 | return_statement
                 | break_statement
                 | block_statement
                 | function_call_statement'''
    p[0] = p[1]

def p_assignment_statement(p):
    '''assignment_statement : assignment SEMICOLON'''
    p[0] = p[1]

def p_print_statement(p):
    '''print_statement : PRINT LPAREN expression_list RPAREN SEMICOLON'''
    lineno = p.lineno(1)
    p[0] = ('print', p[3], lineno)

def p_input_statement(p):
    '''input_statement : INPUT LPAREN variable_list RPAREN SEMICOLON'''
    lineno = p.lineno(1)
    for var_id in p[3]:
        sym = lookup_symbol(var_id)
        if not sym:
            raise SemanticError(f"Erro semântico: Variável '{var_id}' não declarada para input na linha {lineno}.")
        if sym.get('kind') == 'constant':
            raise SemanticError(f"Erro semântico: Constante '{var_id}' não pode ser modificada por input na linha {lineno}.")
        sym['initialized'] = True
    p[0] = ('input', p[3], lineno)

def p_return_statement(p):
    '''return_statement : RETURN expression SEMICOLON'''
    lineno = p.lineno(1)

    if current_method_return_type is None:
        raise SemanticError(f"Erro semântico: 'return' fora de um método na linha {lineno}.")

    returned_expr_type = get_expression_type(p[2], lineno)

    if current_method_return_type == 'void':
        if returned_expr_type != 'void' and p[2] != []:
            raise SemanticError(f"Erro semântico: Método 'void' não deve retornar um valor. Retornou '{returned_expr_type}' na linha {lineno}.")
    else:
        if not is_type_compatible(current_method_return_type, returned_expr_type):
            raise SemanticError(f"Erro semântico: Tipo de retorno incompatível para o método. Esperado '{current_method_return_type}', mas retornou '{returned_expr_type}' na linha {lineno}.")

    p[0] = ('return', p[2], lineno)

def p_expression_list(p):
    '''expression_list : expression
                       | expression COMMA expression_list'''
    if len(p) == 2:
        p[0] = [p[1]]
    else:
        p[0] = [p[1]] + p[3]

def p_variable_list(p):
    '''variable_list : ID
                     | ID COMMA variable_list'''
    if len(p) == 2:
        p[0] = [p[1]]
    else:
        p[0] = [p[1]] + p[3]

def p_block_statement(p):
    '''block_statement : LBRACE block_content RBRACE'''
    lineno = p.lineno(1)
    p[0] = ('block', p[2], lineno)

def p_block_content(p):
    '''block_content : declarations statements
                     | declarations
                     | statements
                     | empty'''
    decls_node = ('declarations', [], 0)
    stmts_list = []

    if len(p) == 3:
        decls_node = p[1]
        stmts_list = p[2]
    elif len(p) == 2:
        if isinstance(p[1], tuple) and p[1][0] == 'declarations':
            decls_node = p[1]
        elif isinstance(p[1], list):
            stmts_list = p[1]
    p[0] = (decls_node, stmts_list)

def p_assignment(p):
    '''assignment : ID ASSIGN expression'''
    var_id = p[1]
    expr_node = p[3]
    lineno = p.lineno(1)

    sym = lookup_symbol(var_id)
    if not sym:
        raise SemanticError(f"Erro semântico: Variável '{var_id}' não declarada na linha {lineno}.")
    if sym.get('kind') == 'constant':
        raise SemanticError(f"Erro semântico: Constante '{var_id}' não pode ser reatribuída na linha {lineno}.")

    expected_type = sym['type']
    actual_type = get_expression_type(expr_node, lineno)

    if not is_type_compatible(expected_type, actual_type):
        raise SemanticError(f"Erro semântico: Incompatibilidade de tipos na atribuição para '{var_id}'. Esperado '{expected_type}', mas recebeu '{actual_type}' na linha {lineno}.")

    sym['initialized'] = True
    p[0] = ('assign', var_id, expr_node, lineno)

def p_assignment_inc_dec(p):
    '''assignment : ID INCREMENT
                  | ID DECREMENT'''
    var_id = p[1]
    op = p[2]
    lineno = p.lineno(1)

    sym = lookup_symbol(var_id)
    if not sym:
        raise SemanticError(f"Erro semântico: Variável '{var_id}' não declarada na linha {lineno}.")
    if sym.get('kind') == 'constant':
        raise SemanticError(f"Erro semântico: Constante '{var_id}' não pode ser incrementada/decrementada na linha {lineno}.")
    if sym['type'] not in ['int', 'float']:
        raise SemanticError(f"Erro semântico: Operador '{op}' só pode ser aplicado a tipos 'int' ou 'float', mas recebeu '{sym['type']}' para '{var_id}' na linha {lineno}.")

    p[0] = ('increment' if op == '++' else 'decrement', var_id, lineno)

def p_if_statement(p):
    '''if_statement : IF LPAREN condition RPAREN block_statement
                    | IF LPAREN condition RPAREN block_statement ELSE block_statement'''
    lineno = p.lineno(1)
    condition_node = p[3]
    if_block = p[5]

    cond_type = get_expression_type(condition_node, lineno)
    if cond_type != 'bool':
        raise SemanticError(f"Erro semântico: Condição do IF deve ser booleana, mas recebeu '{cond_type}' na linha {lineno}.")

    if len(p) == 6:
        p[0] = ('if', condition_node, if_block, lineno)
    else:
        else_block = p[7]
        p[0] = ('if-else', condition_node, if_block, else_block, lineno)

def p_while_statement(p):
    '''while_statement : WHILE LPAREN condition RPAREN block_statement'''
    global loop_depth
    lineno = p.lineno(1)
    condition_node = p[3]
    while_block = p[5]

    cond_type = get_expression_type(condition_node, lineno)
    if cond_type != 'bool':
        raise SemanticError(f"Erro semântico: Condição do WHILE deve ser booleana, mas recebeu '{cond_type}' na linha {lineno}.")

    loop_depth += 1
    p[0] = ('while', condition_node, while_block, lineno)
    loop_depth -= 1

def p_for_statement(p):
    '''for_statement : FOR LPAREN assignment_statement condition SEMICOLON assignment RPAREN block_statement'''
    global loop_depth
    lineno = p.lineno(1)

    cond_type = get_expression_type(p[4], lineno)
    if cond_type != 'bool':
        raise SemanticError(f"Erro semântico: Condição do FOR deve ser booleana, mas recebeu '{cond_type}' na linha {lineno}.")

    loop_depth += 1
    p[0] = ('for', p[3], p[4], p[6], p[8], lineno)
    loop_depth -= 1

def p_break_statement(p):
    '''break_statement : BREAK SEMICOLON'''
    lineno = p.lineno(1)
    if loop_depth == 0:
        raise SemanticError(f"Erro semântico: 'break' usado fora de um loop na linha {lineno}.")
    p[0] = ('break', lineno)

def p_condition(p):
    '''condition : expression comparison expression
                 | NOT expression'''
    lineno = p.lineno(1)

    if len(p) == 4:
        left_expr = p[1]
        op = p[2]
        right_expr = p[3]

        left_type = get_expression_type(left_expr, lineno)
        right_type = get_expression_type(right_expr, lineno)

        if op in ['==', '!=']:
            if not is_comparable_equality(left_type, right_type):
                raise SemanticError(f"Erro semântico: Tipos incompatíveis para comparação '{op}': '{left_type}' e '{right_type}' na linha {lineno}.")
        elif op in ['>', '<']:
            if not is_comparable_order(left_type, right_type):
                raise SemanticError(f"Erro semântico: Tipos incompatíveis para comparação '{op}': '{left_type}' e '{right_type}' na linha {lineno}.")

        p[0] = ('bool', 'condition', op, left_expr, right_expr, lineno)
    else:
        expr_node = p[2]
        expr_type = get_expression_type(expr_node, lineno)
        if expr_type != 'bool':
            raise SemanticError(f"Erro semântico: Operador '!' só pode ser aplicado a expressões booleanas, mas recebeu '{expr_type}' na linha {lineno}.")
        p[0] = ('bool', 'not', expr_node, lineno)

def p_comparison(p):
    '''comparison : EQUALS
                  | NEQUALS
                  | GT
                  | LT'''
    p[0] = p[1]

def p_expression(p):
    '''expression : term
                  | expression PLUS term
                  | expression MINUS term'''
    if len(p) == 2:
        p[0] = p[1]
    else:
        op = p[2]
        left_expr = p[1]
        right_expr = p[3]
        lineno = p.lineno(2)

        left_type = get_expression_type(left_expr, lineno)
        right_type = get_expression_type(right_expr, lineno)

        if op == '+':
            if (left_type == 'str' or right_type == 'str'):
                result_type = 'str'
                if not (left_type == 'str' or right_type == 'str' or (left_type in ['int', 'float'] and right_type in ['int', 'float'])):
                     raise SemanticError(f"Erro semântico: Tipos incompatíveis para concatenação ou soma: '{left_type}' e '{right_type}' na linha {lineno}.")
            elif (left_type in ['int', 'float'] and right_type in ['int', 'float']):
                result_type = 'float' if 'float' in [left_type, right_type] else 'int'
            else:
                 raise SemanticError(f"Erro semântico: Operador '{op}' só pode ser aplicado a 'int', 'float' ou 'str' (para '+') mas recebeu '{left_type}' e '{right_type}' na linha {lineno}.")
        elif op == '-':
            if not (left_type in ['int', 'float'] and right_type in ['int', 'float']):
                raise SemanticError(f"Erro semântico: Operador '{op}' só pode ser aplicado a 'int' ou 'float', mas recebeu '{left_type}' e '{right_type}' na linha {lineno}.")
            result_type = 'float' if 'float' in [left_type, right_type] else 'int'

        p[0] = (result_type, 'binop', op, left_expr, right_expr, lineno)

def p_term(p):
    '''term : factor
            | term TIMES factor
            | term DIVIDE factor'''
    if len(p) == 2:
        p[0] = p[1]
    else:
        op = p[2]
        left_term = p[1]
        right_factor = p[3]
        lineno = p.lineno(2)

        left_type = get_expression_type(left_term, lineno)
        right_type = get_expression_type(right_factor, lineno)

        if not (left_type in ['int', 'float'] and right_type in ['int', 'float']):
            raise SemanticError(f"Erro semântico: Operadores '{op}' só podem ser aplicados a 'int' ou 'float', mas recebeu '{left_type}' e '{right_type}' na linha {lineno}.")

        result_type = 'float' if 'float' in [left_type, right_type] else 'int'
        p[0] = (result_type, 'binop', op, left_term, right_factor, lineno)

def p_factor(p):
    '''factor : ID
              | NUMBER
              | STRING_LITERAL
              | BOOLEAN_LITERAL
              | LPAREN expression RPAREN
              | function_call'''
    lineno = p.lineno(1)

    if len(p) == 2:
        val = p[1]
        if isinstance(val, str):
            if val.lower() == 'true' or val.lower() == 'false':
                p[0] = ('bool_literal', bool(val.lower() == 'true'), 'bool', lineno)
            elif val.startswith('"') and val.endswith('"'):
                p[0] = ('str_literal', val, 'str', lineno)
            else: # ID
                sym = lookup_symbol(val)
                if not sym:
                    raise SemanticError(f"Erro semântico: Variável '{val}' não declarada na linha {lineno}.")
                p[0] = ('ID', val, sym['type'], lineno)
        elif isinstance(val, int):
            p[0] = ('int_literal', val, 'int', lineno)
        elif isinstance(val, float):
            p[0] = ('float_literal', val, 'float', lineno)
        elif isinstance(val, tuple) and val[0] == 'call':
            p[0] = val
    else: # LPAREN expression RPAREN
        expr_internal_type = get_expression_type(p[2], lineno)
        p[0] = (expr_internal_type, 'parenthesized_expr', p[2], lineno)

def p_factor_uminus(p):
    '''factor : MINUS factor %prec UMINUS'''
    expr_node = p[2]
    lineno = p.lineno(1)

    expr_type = get_expression_type(expr_node, lineno)
    if expr_type not in ['int', 'float']:
        raise SemanticError(f"Erro semântico: Operador unário '-' só pode ser aplicado a tipos 'int' ou 'float', mas recebeu '{expr_type}' na linha {lineno}.")

    p[0] = (expr_type, 'uminus', expr_node, lineno)

def p_function_call(p):
    '''function_call : ID LPAREN expression_list RPAREN'''
    func_name = p[1]
    args = p[3]
    lineno = p.lineno(1)

    sym = lookup_symbol(func_name)
    if not sym or sym.get('kind') != 'method':
        raise SemanticError(f"Erro semântico: Função '{func_name}' não declarada ou não é uma função na linha {lineno}.")

    declared_params = sym['parameters']
    if len(args) != len(declared_params):
        raise SemanticError(f"Erro semântico: Número incorreto de argumentos para a função '{func_name}'. Esperado {len(declared_params)}, mas recebeu {len(args)} na linha {lineno}.")

    for i, arg_expr in enumerate(args):
        expected_param_type = declared_params[i][0]
        actual_arg_type = get_expression_type(arg_expr, lineno)

        if not is_type_compatible(expected_param_type, actual_arg_type):
            raise SemanticError(f"Erro semântico: Tipo de argumento incompatível para o parâmetro {i+1} ('{declared_params[i][1]}') da função '{func_name}'. Esperado '{expected_param_type}', mas recebeu '{actual_arg_type}' na linha {lineno}.")

    p[0] = (sym['type'], 'call', func_name, args, lineno)

def p_function_call_statement(p):
    '''function_call_statement : function_call SEMICOLON'''
    p[0] = p[1]

def p_error(p):
    error_msg = ""
    if p:
        error_msg = f"Erro de sintaxe na entrada: '{p.value}' na linha {p.lineno}"
        print(error_msg)
    else:
        error_msg = "Erro de sintaxe na entrada: EOF inesperado"
        print(error_msg)
    raise ParserError(error_msg)

# --- Funções Auxiliares de Análise Semântica ---

def get_expression_type(expr_node, lineno):
    if isinstance(expr_node, tuple):
        node_type = expr_node[0]
        if node_type in ['int_literal', 'float_literal', 'str_literal', 'bool_literal', 'ID']:
            return expr_node[2]
        elif node_type == 'parenthesized_expr':
            return get_expression_type(expr_node[2], lineno)
        elif node_type in ['int', 'float', 'str', 'bool', 'void']:
            return node_type
        elif node_type == 'condition':
            return 'bool'
        raise SemanticError(f"Erro semântico: Não foi possível inferir o tipo da expressão na linha {lineno}. Nó: {expr_node[0]}")
    elif isinstance(expr_node, list) and not expr_node:
        return 'void'
    return 'unknown'

def is_type_compatible(expected, actual):
    if expected == actual:
        return True
    if expected == 'float' and actual == 'int':
        return True
    return False

def is_comparable_equality(type1, type2):
    if type1 == type2:
        return True
    if type1 in ['int', 'float'] and type2 in ['int', 'float']:
        return True
    return False

def is_comparable_order(type1, type2):
    if type1 in ['int', 'float'] and type2 in ['int', 'float']:
        return True
    return False

# --- Configuração do Parser ---

tokens = lexer.tokens

precedence = (
    ('left', 'PLUS', 'MINUS'),
    ('left', 'TIMES', 'DIVIDE'),
    ('right', 'UMINUS'),
)

parser = yacc.yacc(debug=True)

class ParserError(Exception):
    pass

def parse(data):
    global symbol_table_stack, current_scope_type, loop_depth, current_method_return_type
    symbol_table_stack = [{}]
    current_scope_type = "global"
    loop_depth = 0
    current_method_return_type = None
    try:
        return parser.parse(data, lexer=lexer.lexer)
    except SemanticError as e:
        print(f"Erro semântico: {e}")
        raise e
    except Exception as e:
        print(f"Erro durante o parsing: {e}")
        raise e

# --- Funções de Impressão da AST (sem comentários) ---

def tuplas_para_listas(obj):
    if isinstance(obj, tuple):
        return [tuplas_para_listas(item) for item in obj]
    elif isinstance(obj, list):
        return [tuplas_para_listas(item) for item in obj]
    elif isinstance(obj, dict):
        return {k: tuplas_para_listas(v) for k, v in obj.items()}
    else:
        return obj

def print_arvore(node, prefix="", is_last=True):
    if isinstance(node, (list, tuple)):
        label = ""
        children = node
        if isinstance(node, tuple) and len(node) > 0:
            if isinstance(node[0], str):
                if node[0] in ['int', 'float', 'str', 'bool', 'void']:
                    if len(node) > 1 and isinstance(node[1], str):
                        label = f"({node[0]}) {node[1]}"
                        children = node[2:]
                    else:
                        label = f"({node[0]}) {node[0]}"
                        children = node[1:]
                else:
                    label = node[0]
                    children = node[1:]

        node_str = str(label)
        if isinstance(node, tuple) and len(node) > 0 and isinstance(node[-1], int) and node[-1] > 0:
            node_str += f" (L{node[-1]})"

        print(prefix + ("└── " if is_last else "├── ") + node_str)

        for i, child in enumerate(children):
            is_last_child = (i == len(children) - 1)
            print_arvore(child, prefix + ("    " if is_last else "│   "), is_last_child)
    elif isinstance(node, dict):
        print(prefix + ("└── " if is_last else "├── ") + "{dict}")
        for i, (k, v) in enumerate(node.items()):
            is_last_child = (i == len(node) - 1)
            print(prefix + ("    " if is_last else "│   ") + ("└── " if is_last_child else "├── ") + str(k))
            print_arvore(v, prefix + ("    " if is_last else "│   ") + ("    " if is_last_child else "│   "), True)
    else:
        node_str = str(node)
        print(prefix + ("└── " if is_last else "├── ") + node_str)

# --- Testes ---
if __name__ == "__main__":
    test_code = """
    program: TesteMetodosNativos;
decIds:
    nome: str;
    idade: int;
    altura: float;
    isEstudante: bool;
    PI = 3.14159;
    saudacao = "Olá, Javython!";
    MAX_SIZE = 100;
main:
    print("Olá, bem-vindo ao teste de métodos nativos!");
    print("Por favor, digite suas informações:");

    print("Qual é o seu nome?");
    input(nome);

    print("Qual é a sua idade?");
    input(idade);

    print("Qual é a sua altura em metros (ex: 1.75)?");
    input(altura);

    print("Seu nome é:", nome);
    print("Sua idade é:", idade, "anos.");
    print("Sua altura é:", altura, "metros.");

    isEstudante = true;
    print("Você é estudante?", isEstudante);

    print("Sua idade em meses é:", idade * 12);
    print("Sua altura em centímetros é:", altura * 100);

    novaIdade = idade + 5;
    novaAltura = altura / 2.0;
    nomeCompleto = nome + " " + "Sobrenome";
    ehMaior = idade > 18;
    ehDiferente = nome != "João";

    print("Nova idade:", novaIdade);
    print("Nova altura:", novaAltura);
    print("Nome completo:", nomeCompleto);
    print("É maior de idade?", ehMaior);
    print("Nome é diferente de João?", ehDiferente);
    print("PI é:", PI);
    print("Saudação:", saudacao);
    print("Tamanho máximo:", MAX_SIZE);

    if (idade > 20) {
        print("Você tem mais de 20 anos.");
    } else {
        print("Você tem 20 anos ou menos.");
    }

    count = 0;
    while (count < 3) {
        print("Contagem:", count);
        count++;
        if (count == 2) {
            break;
        }
    }

    for (i = 0; i < 2; i++) {
        print("Loop for, i:", i);
        if (i == 1) {
            break;
        }
    }
end
    """
    test_error_code = """
    program: TesteErrosSemanticos;
decIds:
    minhaVariavel: int;
    minhavariavel: float;
    PI = 3.14;
    print = 5;
main:
    minhaConstante = 10;
    minhaConstante = 20;
    input(minhaConstante);
    outraVariavel = "texto";
    minhaVariavel = "cinco";
    boolVar: bool;
    boolVar = 10;
    if ("string") {
        print("Erro");
    }
    resultado = 10 + "string";
    return 10;

    void teste() {
        return;
    }
    minhaVarNaoDeclarada = 1;
    break;

end
    """

    test_method_return_error = """
    program: TesteRetorno;
    int meuMetodoInt() {
        return "string";
    }
    void meuMetodoVoid() {
        return 5;
    }
    main:
        print("Testando retornos.");
    end
    """

    print("\n--- Testando código SEM ERROS semânticos ---")
    try:
        result = parse(test_code)
        print("\n--- Parsing e Análise Semântica Concluídos com Sucesso! ---")
        print("\n--- AST EM FORMATO DE ÁRVORE ---")
        print_arvore(result)
    except SemanticError as e:
        print(f"\n--- Erro Semântico Inesperado: {e} ---")
    except Exception as e:
        print(f"\n--- Outro Erro Capturado: {e} ---")

    print("\n\n--- Testando código com ERROS SEMÂNTICOS esperados (gerais) ---")
    try:
        parse(test_error_code)
    except SemanticError as e:
        print(f"\n--- Erro Semântico Capturado (Esperado): {e} ---")
    except Exception as e:
        print(f"\n--- Outro Erro Capturado: {e} ---")

    print("\n\n--- Testando código com ERROS SEMÂNTICOS esperados (retorno de método) ---")
    try:
        parse(test_method_return_error)
    except SemanticError as e:
        print(f"\n--- Erro Semântico Capturado (Esperado): {e} ---")
    except Exception as e:
        print(f"\n--- Outro Erro Capturado: {e} ---")
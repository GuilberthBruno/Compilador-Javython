import ply.yacc as yacc
from lexer import tokens

# Dicionário para armazenar variáveis (tabela de símbolos simples)
symbol_table = {}

# Classe de erro personalizada
class ParserError(Exception):
    pass

# Regras de gramática para o parser
def p_program(p):
    '''program : PROGRAM COLON ID SEMICOLON program_content END'''
    p[0] = ('program', p[3], p[5])

# Conteúdo principal do programa: declarações globais, métodos e o método main
def p_program_content(p):
    '''program_content : declarations methods_list main_method'''
    p[0] = (p[1], p[2], p[3])

# Declarações de variáveis e constantes (globais)
def p_declarations(p):
    '''declarations : DECIDS COLON vars_and_consts_declarations
                    | empty'''
    if len(p) > 2:
        p[0] = ('declarations', p[3])
    else:
        p[0] = ('declarations', [])

# Regra para repetição de declarações
def p_vars_and_consts_declarations(p):
    '''vars_and_consts_declarations : var_or_const_declaration
                                    | var_or_const_declaration vars_and_consts_declarations'''
    if len(p) == 2:
        p[0] = [p[1]]
    else:
        p[0] = [p[1]] + p[2]

# Declaração de variáveis ou constantes (grupo ou individual)
def p_var_or_const_declaration_group(p):
    '''var_or_const_declaration : ID COMMA ID_list COLON type SEMICOLON'''
    p[0] = ('declare_group', [p[1]] + p[3], p[5])
    for var_id in [p[1]] + p[3]:
        symbol_table[var_id] = {'type': p[5], 'value': None}

def p_var_or_const_declaration_single(p):
    '''var_or_const_declaration : ID COLON type SEMICOLON
                                | ID ASSIGN expression SEMICOLON'''
    if len(p) == 5:
        if p[2] == ':':
            p[0] = ('declare', p[3], p[1])
            symbol_table[p[1]] = {'type': p[3], 'value': None}
        else:
            p[0] = ('const_assign', p[1], p[3])
            symbol_table[p[1]] = {'type': 'const', 'value': p[3]}

def p_ID_list(p):
    '''ID_list : ID
               | ID COMMA ID_list'''
    if len(p) == 2:
        p[0] = [p[1]]
    else:
        p[0] = [p[1]] + p[3]

# Tipos de dados
def p_type(p):
    '''type : INT
            | FLOAT
            | BOOL
            | STR'''
    p[0] = p[1]

# Declaração de métodos (zero ou mais)
def p_methods_list(p):
    '''methods_list : method_declaration methods_list
                    | empty'''
    if len(p) == 3:
        p[0] = [p[1]] + p[2]
    else:
        p[0] = []

def p_method_declaration(p):
    '''method_declaration : type_or_void ID LPAREN parameters_list RPAREN LBRACE block_content RBRACE'''
    p[0] = ('method', p[1], p[2], p[4], p[7])
    
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

# Método main, de acordo com a sintaxe do exemplo no PDF
def p_main_method(p):
    '''main_method : MAIN COLON main_body'''
    p[0] = ('main', p[3])

def p_main_body(p):
    '''main_body : declarations statements
                 | statements
                 | empty'''
    if len(p) == 3:
        p[0] = (p[1], p[2])
    elif len(p) == 2:
        if p[1][0] == 'declarations':
            p[0] = (p[1], [])
        else:
            p[0] = (('declarations', []), p[1])
    else:
        p[0] = (('declarations', []), [])
    

# Bloco de declarações vazias
def p_empty(p):
    'empty :'
    pass

# Bloco de statements
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
                 | block_statement'''
    p[0] = p[1]

# Statements que terminam com ponto e vírgula
def p_assignment_statement(p):
    '''assignment_statement : assignment SEMICOLON'''
    p[0] = p[1]

def p_print_statement(p):
    '''print_statement : PRINT LPAREN expression_list RPAREN SEMICOLON'''
    p[0] = ('print', p[3])

def p_input_statement(p):
    '''input_statement : INPUT LPAREN variable_list RPAREN SEMICOLON'''
    p[0] = ('input', p[3])

def p_return_statement(p):
    '''return_statement : RETURN expression SEMICOLON'''
    p[0] = ('return', p[2])

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

# Bloco de código
def p_block_statement(p):
    '''block_statement : LBRACE block_content RBRACE'''
    p[0] = ('block', p[2])

def p_block_content(p):
    '''block_content : declarations statements
                     | declarations
                     | statements
                     | empty'''
    if len(p) == 3:
        p[0] = (p[1], p[2])
    elif len(p) == 2:
        if p[1] and isinstance(p[1], tuple) and p[1][0] == 'declarations':
            p[0] = (p[1], [])
        else:
            p[0] = (('declarations', []), p[1])
    else:
        p[0] = (('declarations', []), [])


# Atribuição
def p_assignment(p):
    '''assignment : ID ASSIGN expression'''
    p[0] = ('assign', p[1], p[3])

# Operações de incremento e decremento
def p_assignment_inc_dec(p):
    '''assignment : ID INCREMENT
                  | ID DECREMENT'''
    op = 'increment' if p[2] == '++' else 'decrement'
    p[0] = (op, p[1])

# Estrutura condicional if-else
def p_if_statement(p):
    '''if_statement : IF LPAREN condition RPAREN block_statement
                    | IF LPAREN condition RPAREN block_statement ELSE block_statement'''
    if len(p) == 6:
        p[0] = ('if', p[3], p[5])
    else:
        p[0] = ('if-else', p[3], p[5], p[7])

# Estrutura de repetição while
def p_while_statement(p):
    '''while_statement : WHILE LPAREN condition RPAREN block_statement'''
    p[0] = ('while', p[3], p[5])

# Estrutura de repetição for
def p_for_statement(p):
    '''for_statement : FOR LPAREN assignment_statement condition SEMICOLON assignment RPAREN block_statement'''
    p[0] = ('for', p[3], p[4], p[6], p[8])

# Condição
def p_condition(p):
    '''condition : expression comparison expression
                 | NOT expression'''
    if len(p) == 4:
        p[0] = ('condition', p[2], p[1], p[3])
    else:
        p[0] = ('not', p[2])

def p_comparison(p):
    '''comparison : EQUALS
                  | NEQUALS
                  | GT
                  | LT'''
    p[0] = p[1]

# Expressão
def p_expression(p):
    '''expression : term
                  | expression PLUS term
                  | expression MINUS term'''
    if len(p) == 2:
        p[0] = p[1]
    else:
        p[0] = ('binop', p[2], p[1], p[3])

# Termo
def p_term(p):
    '''term : factor
            | term TIMES factor
            | term DIVIDE factor'''
    if len(p) == 2:
        p[0] = p[1]
    else:
        p[0] = ('binop', p[2], p[1], p[3])

# Fator
def p_factor(p):
    '''factor : ID
              | NUMBER
              | STRING_LITERAL
              | BOOLEAN_LITERAL
              | LPAREN expression RPAREN
              | function_call'''
    if len(p) == 2:
        p[0] = p[1]
    else:
        p[0] = p[2]

# Menos unário
def p_factor_uminus(p):
    '''factor : MINUS factor %prec UMINUS'''
    p[0] = ('uminus', p[2])

# Chamada de função
def p_function_call(p):
    '''function_call : ID LPAREN expression_list RPAREN'''
    p[0] = ('call', p[1], p[3])

# Tratamento de erros sintáticos
def p_error(p):
    error_msg = ""
    if p:
        error_msg = f"Erro de sintaxe na entrada: '{p.value}' na linha {p.lineno}"
        print(error_msg)
    else:
        error_msg = "Erro de sintaxe na entrada: EOF inesperado"
        print(error_msg)
    
    # Lança uma exceção para interromper o parsing
    raise ParserError(error_msg)

# Definindo precedência de operadores (do menor para o maior)
precedence = (
    ('left', 'PLUS', 'MINUS'),
    ('left', 'TIMES', 'DIVIDE'),
    ('right', 'UMINUS'),
)

# Constrói o parser com debug habilitado para identificar problemas
parser = yacc.yacc(debug=True)

# Função para realizar o parsing
def parse(data):
    try:
        return parser.parse(data)
    except ParserError as e:
        raise e

# Função principal para teste
if __name__ == "__main__":
    test_code = """
    program: TesteSimples;
    decIds:
        x: int;
    main:
        x = 10;
        print(x);
    end
    """
    
    try:
        result = parse(test_code)
        print("\n--- AST GERADA ---")
        import json
        print(json.dumps(result, indent=4))
    except ParserError as e:
        print(f"Erro: {e}")
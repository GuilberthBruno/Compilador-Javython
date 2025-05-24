import ply.yacc as yacc
from lexer import tokens

# Dicionário para armazenar variáveis (tabela de símbolos simples)
symbol_table = {}

# Classe de erro personalizada
class ParserError(Exception):
    pass

# Regras de gramática para o parser

# Programa principal - CORRIGIDO: Adicionada regra para programa sem statements
def p_program(p):
    '''program : PROGRAM COLON ID SEMICOLON declarations statements
               | PROGRAM COLON ID SEMICOLON declarations'''
    if len(p) == 7:
        p[0] = ('program', p[3], p[5], p[6])
    else:
        p[0] = ('program', p[3], p[5], [])

# Declarações de variáveis
def p_declarations(p):
    '''declarations : DECIDS COLON vars_declarations
                    | empty'''
    if len(p) > 2:
        p[0] = ('declarations', p[3])
    else:
        p[0] = ('declarations', [])

def p_vars_declarations(p):
    '''vars_declarations : var_declaration
                         | var_declaration vars_declarations'''
    if len(p) == 2:
        p[0] = [p[1]]
    else:
        p[0] = [p[1]] + p[2]

def p_var_declaration(p):
    '''var_declaration : ID COLON type SEMICOLON'''
    p[0] = ('declare', p[3], p[1])
    # Registra a variável na tabela de símbolos
    symbol_table[p[1]] = {'type': p[3], 'value': None}

def p_type(p):
    '''type : INT
            | FLOAT'''
    p[0] = p[1]

# Bloco de declarações vazias
def p_empty(p):
    'empty :'
    pass

# Bloco de statements
def p_statements(p):
    '''statements : statement_list'''
    p[0] = p[1]

def p_statement_list(p):
    '''statement_list : statement
                      | statement statement_list'''
    if len(p) == 2:
        p[0] = [p[1]]
    else:
        p[0] = [p[1]] + p[2]

# Tipos de statements - CORRIGIDO: Separado em múltiplas regras para maior clareza
def p_statement(p):
    '''statement : assignment_statement
                 | if_statement
                 | while_statement
                 | for_statement
                 | print_statement
                 | input_statement
                 | block_statement'''
    p[0] = p[1]

# Statements que terminam com ponto e vírgula
def p_assignment_statement(p):
    '''assignment_statement : assignment SEMICOLON'''
    p[0] = p[1]

def p_print_statement(p):
    '''print_statement : PRINT LPAREN expression RPAREN SEMICOLON'''
    p[0] = ('print', p[3])

def p_input_statement(p):
    '''input_statement : INPUT LPAREN ID RPAREN SEMICOLON'''
    p[0] = ('input', p[3])

# Bloco de código
def p_block_statement(p):
    '''block_statement : LBRACE statements RBRACE
                       | LBRACE RBRACE'''
    if len(p) == 4:
        p[0] = ('block', p[2])
    else:
        p[0] = ('block', [])

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
    '''if_statement : IF LPAREN condition RPAREN statement
                    | IF LPAREN condition RPAREN statement ELSE statement'''
    if len(p) == 6:
        p[0] = ('if', p[3], p[5])
    else:
        p[0] = ('if-else', p[3], p[5], p[7])

# Estrutura de repetição while
def p_while_statement(p):
    '''while_statement : WHILE LPAREN condition RPAREN statement'''
    p[0] = ('while', p[3], p[5])

# Estrutura de repetição for
def p_for_statement(p):
    '''for_statement : FOR LPAREN assignment COLON condition COLON assignment RPAREN statement'''
    p[0] = ('for', p[3], p[5], p[7], p[9])

# Condição
def p_condition(p):
    '''condition : expression comparison expression
                 | NOT condition'''
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
              | LPAREN expression RPAREN'''
    if len(p) == 2:
        p[0] = p[1]
    else:
        p[0] = p[2]

# Menos unário
def p_factor_uminus(p):
    '''factor : MINUS factor %prec UMINUS'''
    p[0] = ('uminus', p[2])

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
        # Re-levanta a exceção para ser capturada pelo código chamador
        raise e

# Função principal para teste
if __name__ == "__main__":
    while True:
        try:
            s = input('calc > ')
        except EOFError:
            break
        if not s:
            continue
        
        try:
            result = parser.parse(s)
            print(result)
        except ParserError as e:
            print(f"Erro: {e}")
            pass 
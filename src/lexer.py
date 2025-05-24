import ply.lex as lex

# Lista de nomes de tokens
tokens = [
    'ID',          # Identificadores
    'NUMBER',      # Números
    'PLUS',        # + (soma)
    'MINUS',       # - (subtração)
    'UMINUS',      # - (menos unário)
    'TIMES',       # * (multiplicação)
    'DIVIDE',      # / (divisão)
    'NOT',         # ! (negação)
    'EQUALS',      # == (igual)
    'NEQUALS',     # != (diferente)
    'GT',          # > (maior que)
    'LT',          # < (menor que)
    'INCREMENT',   # ++ (incremento)
    'DECREMENT',   # -- (decremento)
    'LPAREN',      # (
    'RPAREN',      # )
    'LBRACE',      # {
    'RBRACE',      # }
    'ASSIGN',      # = (atribuição)
    'COLON',       # : (dois pontos)
    'SEMICOLON',   # ; (ponto e vírgula)
    'COMMA',       # , (vírgula)
]

# Palavras reservadas
reserved = {
    'if': 'IF',
    'else': 'ELSE',
    'while': 'WHILE',
    'int': 'INT',
    'float': 'FLOAT',
    'for': 'FOR',
    'print': 'PRINT',
    'input': 'INPUT',
    'program': 'PROGRAM',
    'decIds': 'DECIDS',
}

# Adiciona palavras reservadas à lista de tokens
tokens = tokens + list(reserved.values())

# Regras para tokens simples
t_PLUS = r'\+'
t_MINUS = r'-'
t_TIMES = r'\*'
t_DIVIDE = r'/'
t_NOT = r'!'
t_EQUALS = r'=='
t_NEQUALS = r'!='
t_GT = r'>'
t_LT = r'<'
t_INCREMENT = r'\+\+'
t_DECREMENT = r'--'
t_LPAREN = r'\('
t_RPAREN = r'\)'
t_LBRACE = r'\{'
t_RBRACE = r'\}'
t_ASSIGN = r'='
t_COLON = r':'
t_SEMICOLON = r';'
t_COMMA = r','

# Regra para identificadores
def t_ID(t):
    r'[a-zA-Z_][a-zA-Z_0-9]*'
    t.type = reserved.get(t.value, 'ID')
    return t

# Regra para números
def t_NUMBER(t):
    r'\d*\.?\d+'
    t.value = float(t.value) if '.' in t.value else int(t.value)
    return t

# Caracteres ignorados (espaços e tabs)
t_ignore = ' \t'

# Regra para ignorar comentários de linha
def t_COMMENT(t):
    r'//.*'
    pass  # Comentários são ignorados

# Regra para nova linha
def t_newline(t):
    r'\n+'
    t.lexer.lineno += len(t.value)

# Regra para erros
def t_error(t):
    print(f"Caractere ilegal '{t.value[0]}' na linha {t.lexer.lineno}")
    t.lexer.skip(1)

# Constrói o lexer
lexer = lex.lex()

# Função para teste do lexer
def tokenize(data):
    lexer.input(data)
    tokens_list = []
    while True:
        tok = lexer.token()
        if not tok:
            break
        tokens_list.append(tok)
    return tokens_list

# Função principal para teste
if __name__ == "__main__":
    data = input("Digite um texto para análise léxica: ")
    lexer.input(data)
    for tok in lexer:
        print(tok)




import ply.lex as lex

# Lista de nomes de tokens - CORRIGIDO: Removidos tokens duplicados
tokens = [
    'ID',          # Identificadores
    'NUMBER',      # Números (inteiros e floats)
    'STRING_LITERAL', # Literais de string
    'BOOLEAN_LITERAL', # Literais booleanos
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

# Palavras reservadas - CORRIGIDO: Adicionadas novas palavras reservadas e tipos
reserved = {
    'if': 'IF',
    'else': 'ELSE',
    'while': 'WHILE',
    'int': 'INT',
    'float': 'FLOAT',
    'bool': 'BOOL',
    'str': 'STR',
    'for': 'FOR',
    'print': 'PRINT',
    'input': 'INPUT',
    'program': 'PROGRAM',
    'decIds': 'DECIDS',
    'void': 'VOID',
    'return': 'RETURN',
    'main': 'MAIN',
    'end': 'END',
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

# Regra para identificadores - CORRIGIDO: Agora os IDs são case-insensitive para as palavras reservadas
def t_ID(t):
    r'[a-zA-Z_][a-zA-Z_0-9]*'
    # Converte para minúsculas para verificação de palavras reservadas, conforme a especificação.
    # [cite_start]A linguagem não é sensível a maiúsculas e minúsculas nos nomes das variáveis, métodos e palavras reservadas[cite: 35].
    t.type = reserved.get(t.value.lower(), 'ID')
    return t

# Regra para números - CORRIGIDO: Aceita inteiros e floats
def t_NUMBER(t):
    r'\d+\.\d+|\d+'
    if '.' in t.value:
        t.value = float(t.value)
    else:
        t.value = int(t.value)
    return t

# Regra para literais de string
def t_STRING_LITERAL(t):
    r'"([^"\\]|\\.)*"'
    # Remove as aspas do valor
    t.value = t.value[1:-1]
    return t

# Regra para literais booleanos
def t_BOOLEAN_LITERAL(t):
    r'true|false'
    t.value = t.value == 'true'
    t.type = 'BOOLEAN_LITERAL'
    return t

# Caracteres ignorados (espaços e tabs)
t_ignore = ' \t'

# Regra para ignorar comentários de linha
def t_COMMENT(t):
    r'//.*'
    [cite_start] 
    pass  # Comentários são ignorados[cite: 23].

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
    test_code = """
    program: Exemplo;
    decIds:
        i: int;
        PI = 3.14; // comentario
        flag : bool;
    
    int fatorial(int n) {
        if (n > 1) {
            return n * fatorial(n - 1);
        } else {
            return 1;
        }
    }

    main:
        decIds:
            x: int;
        print("Digite um numero: ");
        input(x);
        x++;
        print("Fatorial de ", x, " eh ", fatorial(x));
    end
    """
    
    print("Iniciando análise léxica...")
    lexer.input(test_code)
    for tok in lexer:
        print(tok)
grammar javython;

program
    : 'program' ':' ID ';' declarations statements?
    ;

declarations
    : 'decIds' ':' varsDeclarations
    | // vazio
    ;

varsDeclarations
    : varDeclaration+
    ;

varDeclaration
    : ID ':' type ';'
    ;

type
    : 'int'
    | 'float'
    ;

statements
    : statement+
    ;

statement
    : assignmentStatement
    | ifStatement
    | whileStatement
    | forStatement
    | printStatement
    | inputStatement
    | block
    ;

assignmentStatement
    : assignment ';'
    ;

assignment
    : ID '=' expression
    | ID '++'
    | ID '--'
    ;

ifStatement
    : 'if' '(' condition ')' statement ('else' statement)?
    ;

whileStatement
    : 'while' '(' condition ')' statement
    ;

forStatement
    : 'for' '(' assignment ';' condition ';' assignment ')' statement
    ;

printStatement
    : 'print' '(' expression ')' ';'
    ;

inputStatement
    : 'input' '(' ID ')' ';'
    ;

block
    : '{' statements? '}'
    ;

condition
    : expression comparison expression
    | '!' condition
    ;

comparison
    : '==' | '!=' | '>' | '<'
    ;

expression
    : expression '+' term
    | expression '-' term
    | term
    ;

term
    : term '*' factor
    | term '/' factor
    | factor
    ;

factor
    : '-' factor                     
    | '(' expression ')'             
    | NUMBER
    | ID
    ;

// Tokens
ID      : [a-zA-Z_][a-zA-Z_0-9]* ;
NUMBER  : [0-9]+ ('.' [0-9]+)? ;
WS      : [ \t\r\n]+ -> skip ;
COMMENT : '//' ~[\r\n]* -> skip ;
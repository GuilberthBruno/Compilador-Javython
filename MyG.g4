grammar MyG;

prog : stmnt* EOF;

stmnt :
      declar
    | assign
    ;

declar : 'number' ID ';';
assign : ID '=' expr ';';

expr :
      '-' expr                   # unaryMinus
    | '+' expr                   # unaryPlus
    | expr op=('*'|'/') expr     # mulDiv
    | expr op=('+'|'-') expr     # addSub
    | INT                        # intValue
    | ID                         # varRef
    | '(' expr ')'               # parens
    ;

ID : [a-zA-Z][a-zA-Z0-9]*;
INT: [0-9]+;
WS : [ \t\r\n]+ -> skip;
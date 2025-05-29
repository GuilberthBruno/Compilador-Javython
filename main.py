from antlr4 import *
from MyGLexer import MyGLexer
from MyGParser import MyGParser
from codegen import CodeGenerator
import sys

class Parser:
    def __init__(self):
        self.code_generator = CodeGenerator()
    
    def parse_file(self, file_path):
        """Analisa um arquivo de código fonte e retorna o código de três endereços gerado"""
        input_stream = FileStream(file_path)
        return self.parse(input_stream)
    
    def parse_text(self, text):
        """Analisa um texto contendo código fonte e retorna o código de três endereços gerado"""
        input_stream = InputStream(text)
        return self.parse(input_stream)
    
    def parse(self, input_stream):
        """Processa o input stream e retorna o código de três endereços gerado"""
        # Configurar lexer e parser
        lexer = MyGLexer(input_stream)
        token_stream = CommonTokenStream(lexer)
        parser = MyGParser(token_stream)
        
        # Construir a árvore de análise
        parse_tree = parser.prog()
        
        # Gerar código de três endereços
        code = self.code_generator.visit(parse_tree)
        return code

def main():
    if len(sys.argv) < 2:
        print("Uso: python main.py <arquivo_entrada>")
        return
    
    parser = Parser()
    code = parser.parse_file(sys.argv[1])
    
    print("Código de três endereços gerado:")
    for line in code:
        print(line)

if __name__ == "__main__":
    main() 
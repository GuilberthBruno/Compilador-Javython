import sys
from pathlib import Path
from lexer import lexer
from parser import parse
from semantic import SemanticAnalyzer

def main():
    if len(sys.argv) != 2:
        print("Uso: python -m src.main <arquivo.txt>")
        sys.exit(1)
    
    input_file = Path(sys.argv[1])
    if not input_file.exists():
        print(f"Erro: Arquivo '{input_file}' não encontrado")
        sys.exit(1)
    
    # 1. Leitura do código fonte
    with open(input_file, 'r', encoding='utf-8') as file:
        source_code = file.read()
    
    # 2. Análise léxica e sintática
    try:
        ast = parse(source_code)
    except Exception as e:
        print(f"Erro durante análise sintática:\n{e}")
        sys.exit(1)
    
    # 3. Análise semântica
    analyzer = SemanticAnalyzer()
    if analyzer.analyze(ast):
        print("Análise concluída com sucesso!")
    else:
        print("\nErros semânticos encontrados:")
        for error in analyzer.get_errors():
            print(f"- {error}")
        sys.exit(1)

if __name__ == "__main__":
    main()
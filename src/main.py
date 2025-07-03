import sys
from pathlib import Path
from lexer import lexer
from parser import parse, print_arvore  
from semantic import SemanticAnalyzer
import argparse
from LLVMGen import LLVMGenerator

def display_ast(ast):
    """Exibe a AST de forma hierárquica no terminal"""
    print("\n" + "="*50)
    print("ÁRVORE SINTÁTICA ABSTRATA (AST)")
    print("="*50)
    print_arvore(ast)  # Usa a função do parser.py
    print("\n" + "="*50)

def display_three_address_code(code):
    """Exibe o código de três endereços formatado"""
    print("\n" + "="*50)
    print("CÓDIGO DE TRÊS ENDEREÇOS")
    print("="*50)
    for instruction in code:
        print(instruction)
    print("="*50)

def save_to_file(content, output_file):
    """Salva o conteúdo em um arquivo"""
    try:
        with open(output_file, 'w', encoding='utf-8') as file:
            file.write(content)
        print(f"\n✅ Arquivo de saída salvo: {output_file}")
    except Exception as e:
        print(f"\n❌ Erro ao salvar arquivo: {e}")

def generate_jasmin_code(ast):
    """Gera código Jasmin a partir da AST"""
    # TODO: Implementar gerador de código Jasmin
    # Por enquanto, retorna um template básico
    jasmin_code = f"""; Código Jasmin gerado pelo compilador Javython
.class public Main
.super java/lang/Object

.method public <init>()V
    aload_0
    invokespecial java/lang/Object/<init>()V
    return
.end method

.method public static main([Ljava/lang/String;)V
    .limit stack 10
    .limit locals 10
    
    ; TODO: Implementar geração de código a partir da AST
    
    return
.end method
"""
    return jasmin_code

def main():
    parser = argparse.ArgumentParser(description='Compilador Javython')
    parser.add_argument('arquivo', help='Arquivo de entrada (.jy)')
    parser.add_argument('-o', '--output', help='Arquivo de saída')
    parser.add_argument('--jasmin', '-j', action='store_true', help='Gerar código Jasmin')
    parser.add_argument('--llvm', '-l', action='store_true', help='Gerar código LLVM IR')
    parser.add_argument('--no-display', action='store_true', help='Não exibir AST e código no terminal')
    args = parser.parse_args()

    input_file = Path(args.arquivo)
    if not input_file.exists():
        print(f"Erro: Arquivo '{input_file}' não encontrado")
        sys.exit(1)
    
    # Determina o arquivo de saída
    if args.output:
        output_file = Path(args.output)
    else:
        # Gera nome baseado no arquivo de entrada
        base_name = input_file.stem
        if args.jasmin:
            output_file = Path(f"{base_name}.j")
        elif args.llvm:
            output_file = Path(f"{base_name}.ll")
        else:
            output_file = Path(f"{base_name}.ll")  # Padrão LLVM IR
    
    # 1. Leitura do código fonte
    with open(input_file, 'r', encoding='utf-8') as file:
        source_code = file.read()
    
    # 2. Análise léxica e sintática
    try:
        ast = parse(source_code)
    except Exception as e:
        print(f"Erro durante análise sintática:\n{e}")
        sys.exit(1)
    
    # 3. Exibe a AST (se não estiver suprimida)
    if not args.no_display:
        display_ast(ast)
    
    # 4. Análise semântica
    analyzer = SemanticAnalyzer()
    if analyzer.analyze(ast):
        print("\n✅ Análise semântica concluída sem erros!")
        
        # 5. Geração de código
        if args.jasmin:
            # Gera código Jasmin
            jasmin_code = generate_jasmin_code(ast)
            if not args.no_display:
                print("\n" + "="*50)
                print("CÓDIGO JASMIN")
                print("="*50)
                print(jasmin_code)
            save_to_file(jasmin_code, output_file)
            
        else:
            # Gera código LLVM IR (padrão)
            llvm_generator = LLVMGenerator()
            llvm_ir = llvm_generator.generate(ast)
            
            if not args.no_display:
                print("\n" + "="*50)
                print("LLVM IR")
                print("="*50)
                print(llvm_ir)
            save_to_file(llvm_ir, output_file)
            
    else:
        print("\n❌ Erros semânticos encontrados:")
        for error in analyzer.get_errors():
            print(f"- {error}")
        sys.exit(1)
    

if __name__ == "__main__":
    main()
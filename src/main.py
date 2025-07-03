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

def validate_llvm_ir(output_file):
    """Valida o arquivo LLVM IR gerado"""
    import subprocess
    try:
        # Verifica se o arquivo LLVM IR está sintaticamente correto
        result = subprocess.run(['llvm-as', str(output_file), '-o', '/dev/null'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ LLVM IR validado com sucesso!")
            return True
        else:
            print(f"❌ Erro de validação LLVM IR:")
            print(result.stderr)
            return False
    except FileNotFoundError:
        print("⚠️  llvm-as não encontrado. Pulando validação.")
        return True
    except Exception as e:
        print(f"⚠️  Erro durante validação: {e}")
        return True

def compile_llvm_ir(llvm_file):
    """Compila o arquivo LLVM IR para executável"""
    import subprocess
    try:
        base_name = llvm_file.stem
        asm_file = f"{base_name}.s"
        exe_file = base_name
        
        # Gera assembly
        print(f"🔧 Gerando assembly: {asm_file}")
        result = subprocess.run(['llc', str(llvm_file), '-o', asm_file], 
                              capture_output=True, text=True)
        if result.returncode != 0:
            print(f"❌ Erro ao gerar assembly:")
            print(result.stderr)
            return False
        
        # Gera executável
        print(f"🔗 Gerando executável: {exe_file}")
        result = subprocess.run(['gcc', asm_file, '-o', exe_file], 
                              capture_output=True, text=True)
        if result.returncode != 0:
            print(f"❌ Erro ao gerar executável:")
            print(result.stderr)
            return False
        
        print(f"✅ Executável gerado: {exe_file}")
        print(f"🎯 Para executar: ./{exe_file}")
        return True
        
    except FileNotFoundError as e:
        print(f"⚠️  Ferramenta não encontrada: {e}")
        return False
    except Exception as e:
        print(f"⚠️  Erro durante compilação: {e}")
        return False

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
    parser.add_argument('--compile', '-c', action='store_true', help='Compilar LLVM IR para executável')
    parser.add_argument('--no-display', action='store_true', help='Não exibir AST e código no terminal')
    parser.add_argument('--validate', '-v', action='store_true', help='Validar código LLVM IR gerado')
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
            try:
                llvm_generator = LLVMGenerator()
                llvm_ir = llvm_generator.generate(ast)
                
                if not args.no_display:
                    print("\n" + "="*50)
                    print("LLVM IR")
                    print("="*50)
                    print(llvm_ir)
                save_to_file(llvm_ir, output_file)
                
                # Valida o LLVM IR gerado
                validation_success = True
                if args.validate or args.compile:
                    validation_success = validate_llvm_ir(output_file)
                
                if validation_success:
                    print(f"\n✅ Código LLVM IR gerado com sucesso!")
                    print(f"📁 Arquivo: {output_file}")
                    
                    # Compila se solicitado
                    if args.compile:
                        if compile_llvm_ir(output_file):
                            print(f"🎉 Compilação completa!")
                        else:
                            print(f"⚠️  Falha na compilação, mas LLVM IR foi gerado.")
                    else:
                        print(f"🛠️  Para verificar: llvm-as {output_file}")
                        print(f"🚀 Para compilar: llc {output_file} -o {output_file.stem}.s")
                        print(f"🎯 Para executar: gcc {output_file.stem}.s -o {output_file.stem} && ./{output_file.stem}")
                else:
                    print(f"\n⚠️  LLVM IR gerado com possíveis problemas.")
                
            except Exception as e:
                print(f"\n❌ Erro na geração de código LLVM IR:")
                print(f"   {e}")
                import traceback
                traceback.print_exc()
                sys.exit(1)
            
    else:
        print("\n❌ Erros semânticos encontrados:")
        for error in analyzer.get_errors():
            print(f"- {error}")
        sys.exit(1)
    

if __name__ == "__main__":
    main()
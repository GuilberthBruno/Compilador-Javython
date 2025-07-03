#!/usr/bin/env python3
"""
Script para compilar LLVM IR para executável usando llvmlite
"""

import sys
from pathlib import Path
from llvmlite import binding as llvm

def compile_llvm_to_executable(llvm_file):
    """Compila arquivo LLVM IR para executável usando llvmlite"""
    
    # Inicializar LLVM
    llvm.initialize()
    llvm.initialize_native_target()
    llvm.initialize_native_asmprinter()
    
    # Ler o arquivo LLVM IR
    with open(llvm_file, 'r') as f:
        llvm_ir = f.read()
    
    try:
        # Criar módulo LLVM
        module = llvm.parse_assembly(llvm_ir)
        
        # Verificar o módulo
        module.verify()
        
        # Criar target machine
        target = llvm.Target.from_default_triple()
        target_machine = target.create_target_machine()
        
        # Compilar para objeto
        obj_code = target_machine.emit_object(module)
        
        # Salvar arquivo objeto
        base_name = Path(llvm_file).stem
        obj_file = f"{base_name}.o"
        
        with open(obj_file, 'wb') as f:
            f.write(obj_code)
        
        print(f"✅ Arquivo objeto gerado: {obj_file}")
        
        # Tentar linkar com gcc
        import subprocess
        try:
            exe_file = base_name
            result = subprocess.run(['gcc', obj_file, '-o', exe_file], 
                                  capture_output=True, text=True)
            
            if result.returncode == 0:
                print(f"✅ Executável gerado: {exe_file}")
                print(f"🎯 Para executar: ./{exe_file}")
                return True
            else:
                print(f"❌ Erro ao gerar executável:")
                print(result.stderr)
                return False
                
        except FileNotFoundError:
            print("⚠️  gcc não encontrado. Arquivo objeto foi gerado mas não foi possível criar o executável.")
            return False
            
    except Exception as e:
        print(f"❌ Erro ao compilar LLVM IR: {e}")
        return False

def main():
    if len(sys.argv) != 2:
        print("Uso: python compile_llvm.py <arquivo.ll>")
        sys.exit(1)
    
    llvm_file = sys.argv[1]
    
    if not Path(llvm_file).exists():
        print(f"❌ Arquivo não encontrado: {llvm_file}")
        sys.exit(1)
    
    if compile_llvm_to_executable(llvm_file):
        print("🎉 Compilação bem-sucedida!")
    else:
        print("❌ Falha na compilação")
        sys.exit(1)

if __name__ == "__main__":
    main()

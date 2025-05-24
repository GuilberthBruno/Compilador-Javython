from parser import parse

def main():
    # Exemplo de programa válido, sem funções
    programa_exemplo1 = '''
    program: Exemplo1;
    decIds:
        i : int;
        j : int;
        result : float;
    i = 10;
    j = 5;
    result = i + j * 2;
    if (result > 20) {
        print(result);
    } else {
        print(i);
    }
    '''

    print("Testando o analisador sintático:")
    print("\nExemplo 1:")
    try:
        resultado1 = parse(programa_exemplo1)
        print("Análise sintática bem-sucedida!")
        print(resultado1)
    except Exception as e:
        print(f"Erro durante a análise: {e}")
        import traceback
        traceback.print_exc()
        
    

if __name__ == "__main__":
    main() 
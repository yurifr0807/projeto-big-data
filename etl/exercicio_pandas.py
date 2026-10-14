"""
Exercício Prático: Tratamento Básico de Dados com Pandas
Objetivo:
- Criar DataFrame em memória
- Exibir dados originais e tipos de dados
- Converter coluna de texto para numérico (float)
- Calcular a média salarial
- Exibir dados tratados
"""

import pandas as pd


def main():
    # 1. Criação do DataFrame em memória com 5 registros fictícios
    # A coluna 'salario' foi definida propositalmente como texto (string)
    # para simular uma situação real de dado que necessita de tratamento.
    dados = {
        "nome": ["Ana Silva", "Bruno Souza", "Carla Dias", "Diego Lima", "Elena Costa"],
        "idade": [28, 35, 42, 23, 31],
        "sexo": ["F", "M", "F", "M", "F"],
        "salario": ["3500.50", "4200.00", "5800.75", "2900.00", "4600.25"],
    }

    df = pd.DataFrame(dados)

    # 2. Exibição dos dados originais no terminal
    print("=" * 50)
    print("1. DADOS ORIGINAIS:")
    print("=" * 50)
    print(df)

    print("\nTipos de dados iniciais das colunas:")
    print(df.dtypes)

    # 3. Conversão da coluna 'salario' de texto (object) para tipo numérico (float)
    # O método pd.to_numeric converte os valores de string para float
    df["salario"] = pd.to_numeric(df["salario"])

    # 4. Cálculo da média salarial utilizando o método .mean() do Pandas
    media_salarial = df["salario"].mean()

    # 5. Exibição dos tipos de dados após o tratamento
    print("\n" + "=" * 50)
    print("2. TIPOS DE DADOS APÓS TRATAMENTO:")
    print("=" * 50)
    print(df.dtypes)

    # 6. Exibição dos dados tratados e da média calculada
    print("\n" + "=" * 50)
    print("3. DADOS TRATADOS:")
    print("=" * 50)
    print(df)

    print("\n" + "=" * 50)
    print(f"MÉDIA SALARIAL CALCULADA: R$ {media_salarial:.2f}")
    print("=" * 50)


if __name__ == "__main__":
    main()

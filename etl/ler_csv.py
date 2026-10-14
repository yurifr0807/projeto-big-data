"""
Exercício Prático: Leitura e Inspeção de Arquivos CSV com Pandas
Objetivo:
- Ler arquivo CSV do disco com pandas.read_csv()
- Exibir os registros carregados
- Inspecionar nomes das colunas
- Inspecionar tipos de dados inferidos
- Obter a quantidade total de linhas
"""

from pathlib import Path
import pandas as pd


def main():
    # 1. Definição do caminho do arquivo CSV
    # Utilizar Path(__file__).resolve().parent.parent garante que o caminho até a pasta 'dados'
    # seja encontrado corretamente, independentemente de onde o script for executado no terminal.
    caminho_raiz = Path(__file__).resolve().parent.parent
    caminho_csv = caminho_raiz / "dados" / "exemplo.csv"

    print("=" * 60)
    print(f"Lendo arquivo: {caminho_csv.name}")
    print(f"Caminho completo: {caminho_csv}")
    print("=" * 60)

    # 2. Leitura do arquivo CSV usando pandas.read_csv()
    # Por padrão, o read_csv assume a primeira linha como cabeçalho (nomes das colunas)
    # e vírgula (,) como delimitador de campos.
    df = pd.read_csv(caminho_csv)

    # 3. Exibir todos os registros lidos
    print("\n--- 1. REGISTROS CARREGADOS ---")
    print(df)

    # 4. Exibir os nomes das colunas
    # df.columns retorna um índice com os rótulos de todas as colunas
    print("\n--- 2. NOMES DAS COLUNAS ---")
    print(list(df.columns))

    # 5. Exibir os tipos de dados identificados automaticamente
    # O Pandas faz inferência de tipos ao ler o CSV (ex: números viram int64 ou float64)
    print("\n--- 3. TIPOS DE DADOS INFERIDOS ---")
    print(df.dtypes)

    # 6. Exibir a quantidade total de linhas
    # len(df) ou df.shape[0] fornecem o número de registros (linhas) no DataFrame
    total_linhas = len(df)
    total_colunas = df.shape[1]
    print("\n--- 4. DIMENSÕES DO DATAFRAME ---")
    print(f"Total de linhas (registros): {total_linhas}")
    print(f"Total de colunas: {total_colunas}")
    print("=" * 60)


if __name__ == "__main__":
    main()

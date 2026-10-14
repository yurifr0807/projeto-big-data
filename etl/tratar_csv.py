"""
Exercício Prático: Tratamento e Limpeza de Dados com Pandas (ETL)
Objetivo:
- Ler dados brutos de dados/exemplo.csv
- Criar cópia defensiva em memória
- Inspecionar valores nulos e duplicatas
- Padronizar nomes das colunas
- Tratar e converter tipos de dados (idade para Int64, salário para float)
- Justificar a não imputação arbitrária de zeros em dados faltantes
- Remover duplicatas exatas com justificativa
- Salvar dados tratados em dados/tratado/exemplo_tratado.csv
- Comparar volume de registros antes e depois
"""

from pathlib import Path
import pandas as pd


def main():
    # 1. Definição dos caminhos de entrada e saída
    caminho_raiz = Path(__file__).resolve().parent.parent
    caminho_entrada = caminho_raiz / "dados" / "exemplo.csv"
    caminho_saida = caminho_raiz / "dados" / "tratado" / "exemplo_tratado.csv"

    print("=" * 65)
    print("INICIANDO PIPELINE DE TRATAMENTO DE DADOS (ETL)")
    print("=" * 65)

    # Leitura do CSV original
    if not caminho_entrada.exists():
        raise FileNotFoundError(f"Arquivo de entrada não encontrado: {caminho_entrada}")

    df_original = pd.read_csv(caminho_entrada)
    linhas_iniciais = len(df_original)
    print(f"Arquivo lido com sucesso. Total de linhas originais: {linhas_iniciais}")

    # 2. Cópia dos dados em memória para preservar a base original
    # Usar .copy() evita o aviso SettingWithCopyWarning e garante imutabilidade da fonte
    df_tratado = df_original.copy()

    # 3. Diagnóstico de valores nulos e duplicados
    print("\n" + "-" * 50)
    print("DIAGNÓSTICO INICIAL DE QUALIDADE DOS DADOS:")
    print("-" * 50)
    
    # Identifica nulos por coluna
    nulos_por_coluna = df_tratado.isna().sum()
    print("Valores ausentes (nulos) por coluna:")
    print(nulos_por_coluna)

    # Identifica duplicatas exatas
    total_duplicadas = df_tratado.duplicated().sum()
    print(f"\nTotal de linhas duplicadas exatas: {total_duplicadas}")

    # 4. Padronização dos nomes das colunas
    # Converte para minúsculas, remove espaços nas pontas e troca espaços internos por '_'
    df_tratado.columns = (
        df_tratado.columns
        .str.strip()
        .str.lower()
        .str.replace(r"\s+", "_", regex=True)
    )
    print("\nNomes das colunas padronizados:", list(df_tratado.columns))

    # 5. Conversão da coluna 'idade' para tipo inteiro validando dados inválidos
    # errors='coerce' transforma valores corrompidos/inválidos em NaN (em vez de travar o script)
    # astype('Int64') usa o tipo inteiro nativo anulável do Pandas, aceitando valores ausentes
    df_tratado["idade"] = pd.to_numeric(df_tratado["idade"], errors="coerce").astype("Int64")

    # 6. Conversão da coluna 'salario' para tipo numérico (float)
    # errors='coerce' converte qualquer valor não numérico para NaN com segurança
    df_tratado["salario"] = pd.to_numeric(df_tratado["salario"], errors="coerce")

    # 7. Regra sobre valores ausentes:
    # NÃO substituímos valores nulos por 0 automaticamente.
    # Justificativa técnica:
    # Inserir zero em idade ou salário distorce métricas estatísticas essenciais
    # (como média, mediana, desvio padrão) e altera a interpretação do negócio.
    # Manter como NaN/NA preserva a honestidade analítica dos dados.

    # 8. Remoção apenas de duplicatas exatas
    # Justificativa técnica:
    # Apenas linhas 100% idênticas em todas as colunas representam redundâncias claras.
    # Descartar registros com base em duplicatas parciais (ex: mesmo sexo ou mesma idade)
    # poderia eliminar homônimos legítimos ou clientes distintos do mundo real.
    df_tratado = df_tratado.drop_duplicates()

    # 9. Salvar o resultado tratado
    # Garante que o diretório dados/tratado/ existe
    caminho_saida.parent.mkdir(parents=True, exist_ok=True)
    df_tratado.to_csv(caminho_saida, index=False, encoding="utf-8")
    print(f"\nArquivo tratado exportado para: {caminho_saida}")

    # 10. Comparação do volume de registros antes e depois do tratamento
    linhas_finais = len(df_tratado)
    print("\n" + "=" * 65)
    print("COMPARAÇÃO DE VOLUME DE REGISTROS:")
    print("=" * 65)
    print(f"Total de registros ANTES do tratamento : {linhas_iniciais}")
    print(f"Total de registros DEPOIS do tratamento: {linhas_finais}")
    print(f"Linhas descartadas (duplicadas exatas) : {linhas_iniciais - linhas_finais}")
    print("\nPrimeiros registros dos dados tratados:")
    print(df_tratado)
    print("\nTipos finais de dados:")
    print(df_tratado.dtypes)
    print("=" * 65)


if __name__ == "__main__":
    main()

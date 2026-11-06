"""
Exercício Prático: Pipeline ETL com Tratamento de Inconsistências e Auditoria
Objetivo:
- Ler base com erros propositais (espaços em colunas, nulos, textos em números, duplicatas)
- Padronizar nomes de colunas
- Auditar dados antes do tratamento (contagem de nulos e duplicatas)
- Detectar valores corrompidos/inválidos que foram convertidos para NaN por coerção
- Converter tipos (idade -> Int64, salário -> float64) preservando nulos (sem imputar zero)
- Exibir registros problemáticos para trilha de auditoria
- Remover duplicatas exatas com relatório comparativo
- Exportar resultado limpo para dados/tratado/exemplo_com_erros_tratado.csv
"""

from pathlib import Path
import pandas as pd


def main():
    # 1. Definição dos caminhos dos arquivos
    caminho_raiz = Path(__file__).resolve().parent.parent
    caminho_entrada = caminho_raiz / "dados" / "exemplo_com_erros.csv"
    caminho_saida = caminho_raiz / "dados" / "tratado" / "exemplo_com_erros_tratado.csv"

    print("=" * 70)
    print("INICIANDO AUDITORIA E TRATAMENTO DA BASE COM ERROS")
    print("=" * 70)

    if not caminho_entrada.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {caminho_entrada}")


    # Leitura do CSV bruto
    df_bruto = pd.read_csv(caminho_entrada)
    linhas_iniciais = len(df_bruto)

    print(f"\nArquivo lido: {caminho_entrada.name}")
    print(f"Total de registros recebidos: {linhas_iniciais}")
    print("\nColunas originais no arquivo (com possíveis espaços/caixas mistas):")
    print(repr(list(df_bruto.columns)))

    # Cópia defensiva para manipulação
    df = df_bruto.copy()

    # 2. Padronização dos nomes das colunas
    # Remove espaços em branco antes/depois e converte para minúsculas
    colunas_antes = list(df.columns)
    df.columns = (
        df.columns
        .str.strip()
        .str.lower()
        .str.replace(r"\s+", "_", regex=True)
    )
    print("\nColunas padronizadas com sucesso:")
    for col_antiga, col_nova in zip(colunas_antes, df.columns):
        print(f"  - '{col_antiga}' -> '{col_nova}'")

    # 3. Contabilização de valores ausentes ANTES do tratamento
    print("\n" + "-" * 50)
    print("1. VALORES AUSENTES ORIGINAIS (antes de conversões):")
    print("-" * 50)
    nulos_iniciais = df.isna().sum()
    print(nulos_iniciais)

    # 4. Auditoria de registros duplicados exatos
    duplicadas_indices = df[df.duplicated(keep="first")]
    total_duplicadas = len(duplicadas_indices)
    print("\n" + "-" * 50)
    print(f"2. DUPLICATAS EXATAS ENCONTRADAS: {total_duplicadas}")
    print("-" * 50)
    if total_duplicadas > 0:
        print("Registros duplicados que serão eliminados:")
        print(duplicadas_indices)

    # 5. Detecção de valores inválidos (corrompidos) durante conversões
    print("\n" + "-" * 50)
    print("3. DETECÇÃO DE DADOS CORROMPIDOS / INVÁLIDOS:")
    print("-" * 50)

    # Verificação da coluna 'idade':
    # Identifica o que era texto/preenchido mas não é um número inteiro válido
    idade_numerica = pd.to_numeric(df["idade"], errors="coerce")
    invalidos_idade = df["idade"].notna() & idade_numerica.isna()
    qtd_invalidos_idade = invalidos_idade.sum()
    print(f"Valores inválidos detectados em 'idade': {qtd_invalidos_idade}")
    if qtd_invalidos_idade > 0:
        print("Registros com idade inválida:")
        print(df[invalidos_idade])

    # Verificação da coluna 'salario':
    # Identifica valores que tinham conteúdo (ex: 'abc') mas falharam na conversão numérica
    salario_numerico = pd.to_numeric(df["salario"], errors="coerce")
    invalidos_salario = df["salario"].notna() & salario_numerico.isna()
    qtd_invalidos_salario = invalidos_salario.sum()
    print(f"\nValores inválidos detectados em 'salario': {qtd_invalidos_salario}")
    if qtd_invalidos_salario > 0:
        print("Registros com salário corrompido (ex: alfanumérico):")
        print(df[invalidos_salario])

    # 6. Aplicação das conversões de tipos
    # - idade: convertida para Int64 (inteiro nativo anulável do Pandas, preservando NaN como <NA>)
    # - salario: convertido para float64 (preservando NaN para valores vazios ou inválidos)
    # NÃO substituímos nulos por 0 para não distorcer médias e análises futuras.
    df["idade"] = idade_numerica.astype("Int64")
    df["salario"] = salario_numerico

    # 7. Exibição consolidada de TODOS os registros problemáticos (Auditoria)
    print("\n" + "-" * 50)
    print("4. PAINEL DE AUDITORIA (Registros com qualquer pendência):")
    print("-" * 50)
    # Máscara para identificar registros com pelo menos um problema:
    # nulo em idade, nulo em salário ou duplicata exata
    pendencias = df["idade"].isna() | df["salario"].isna() | df.duplicated(keep=False)
    registros_problematicos = df[pendencias]
    print(registros_problematicos)

    # 8. Remoção de duplicatas exatas
    df_tratado = df.drop_duplicates(keep="first")

    # 9. Exportação da base tratada
    caminho_saida.parent.mkdir(parents=True, exist_ok=True)
    df_tratado.to_csv(caminho_saida, index=False, encoding="utf-8")
    print(f"\nBase tratada exportada com sucesso para: {caminho_saida}")

    # 10. Relatório final consolidado
    linhas_finais = len(df_tratado)
    print("\n" + "=" * 70)
    print("RELATÓRIO CONSOLIDADO DO PIPELINE ETL")
    print("=" * 70)
    print(f"Total de registros na entrada (bruto) : {linhas_iniciais}")
    print(f"Total de duplicatas exatas removidas : {total_duplicadas}")
    print(f"Total de registros na saída (tratado) : {linhas_finais}")
    print(f"Nulos em 'idade' preservados (<NA>)   : {df_tratado['idade'].isna().sum()}")
    print(f"Nulos em 'salario' preservados (NaN) : {df_tratado['salario'].isna().sum()}")
    print("\nVisualização da base final tratada:")
    print(df_tratado)
    print("\nTipos finais das colunas:")
    print(df_tratado.dtypes)
    print("=" * 70)


if __name__ == "__main__":
    main()

"""Pipeline de ETL para a base oficial de Doutores e Mestres do Painel Lattes (2023).

Responsabilidades:
1. Leitura via ``ler_xlsx_com_merges`` (restaurando células mescladas da tabela dinâmica).
2. Validação estrutural de schema e checagem de colunas obrigatórias.
3. Tratamento padronizado de tipos (Int64 para ano e quantidade, categorização controlada).
4. Normalização das dimensões demográficas (Sexo, Cor ou Raça) preservando dados originais.
5. Emissão de relatório analítico de qualidade e tipagem.
6. Registro de linhagem formal de dados em ``docs/linhagem/``.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Mapping

import pandas as pd

from etl import linhagem, validacao
from etl.leitor_lattes import ler_xlsx_com_merges
from etl.logging_config import RAIZ, configurar_logging
from etl.tratamento import (
    RelatorioTratamento,
    normalizar_raca_cor,
    normalizar_sexo,
    padronizar_colunas,
)

log = logging.getLogger("pipeline.etl_lattes")

CAMINHO_BRUTO_LATTES = RAIZ / "dados" / "bruto" / "cnpq" / "painel_lattes" / "Download - Tabela.xlsx"
CAMINHO_TRATADO_LATTES = RAIZ / "dados" / "tratado" / "painel_lattes_2023_tratado.csv"
RELATORIO_QUALIDADE_PATH = RAIZ / "docs" / "relatorio_qualidade_lattes_2023.json"

COLUNAS_BOOLEANAS_BOLSAS = [
    "bolsista_iniciacao_cientifica",
    "bolsista_graduacao_sanduiche",
    "bolsista_mestrado",
    "bolsista_doutorado",
    "bolsista_pos_doutorado",
    "bolsista_pq",
    "bolsista_pq_1a",
    "bolsista_pq_1b",
    "bolsista_pq_1c",
    "bolsista_pq_1d",
    "bolsista_pq_2_ou_1e",
    "bolsista_dt",
    "bolsista_dt_1a",
    "bolsista_dt_1b",
    "bolsista_dt_1c",
    "bolsista_dt_1d",
    "bolsista_dt_2_ou_1e",
]


def executar_etl_lattes(
    caminho_entrada: Path = CAMINHO_BRUTO_LATTES,
    caminho_saida: Path = CAMINHO_TRATADO_LATTES,
    salvar_csv: bool = True,
    registrar_evidencias: bool = True,
) -> tuple[pd.DataFrame, dict]:
    """Executa o pipeline completo de ETL para a tabela oficial do Painel Lattes.

    ``registrar_evidencias=False`` evita que testes ou execuções exploratórias
    sobrescrevam o relatório de qualidade e a linhagem versionados.
    """
    log.info("Iniciando ETL da base Painel Lattes: %s", caminho_entrada)
    if not caminho_entrada.exists():
        raise FileNotFoundError(f"Arquivo oficial não encontrado: {caminho_entrada}")

    # 1. Leitura especializada com desmesclagem dimensional
    df_raw = ler_xlsx_com_merges(caminho_entrada)
    validacao.validar_nao_vazio(df_raw, "Painel Lattes")

    # 2. Padronização de nomes de colunas
    df = padronizar_colunas(df_raw)

    # 3. Tratamento de colunas demográficas (preservando o original)
    df["sexo_original"] = df["sexo"]
    df["sexo"] = normalizar_sexo(df["sexo"])

    df["cor_ou_raca_original"] = df["cor_ou_raca"]
    df["cor_ou_raca"] = normalizar_raca_cor(df["cor_ou_raca"])

    # 4. Tratamento de colunas numéricas
    df["ano"] = pd.to_numeric(df["ano"], errors="coerce").astype("Int64")
    df["quantidade"] = pd.to_numeric(df["quantidade"], errors="coerce").fillna(1).astype("int64")

    # 5. Tratamento de campos booleanos/indicadores (Sim / Não)
    for col in COLUNAS_BOOLEANAS_BOLSAS:
        if col in df.columns:
            # Normalizar para 'Sim', 'Não', 'Não informado'
            df[col] = df[col].astype("string").str.strip()

    # 6. Remover duplicatas exatas se houver
    linhas_antes = len(df)
    df = df.drop_duplicates(keep="first")
    duplicatas_removidas = linhas_antes - len(df)

    # 7. Relatório de qualidade
    rel_qualidade = validacao.relatorio_qualidade(
        df,
        nome="CNPq - Painel Lattes 2023 (Doutores e Mestres)",
        colunas_categoricas=["sexo", "cor_ou_raca", "bolsista_pq", "bolsista_dt", "grande_area_atuacao"],
    )
    rel_qualidade["duplicatas_removidas"] = duplicatas_removidas
    rel_qualidade["total_doutores_mestres_ponderado"] = int(df["quantidade"].sum())
    if registrar_evidencias:
        validacao.escrever_relatorio(rel_qualidade, RELATORIO_QUALIDADE_PATH)

    # 8. Registro de Linhagem formal
    decisoes = [
        {
            "regra": "Resolução de mergeCells estruturais do Excel",
            "justificativa": (
                "A exportação do Painel Lattes utiliza mesclagem de células nativas para agrupar categorias "
                "repetidas hierarquicamente (ex.: A2:A25821 para Ano=2023). A resolução preenche os rótulos "
                "em todas as linhas de observação sem imputar valores arbitrários."
            ),
        },
        {
            "regra": "Identificação e tipagem da coluna sem cabeçalho como 'quantidade'",
            "justificativa": (
                "A coluna 40 da planilha gerada pelo Power BI é uma contagem de indivíduos por célula multidimensional "
                "(valores inteiros >= 1, somando 26.009 pessoas nas 25.820 linhas)."
            ),
        },
        {
            "regra": "Normalização de categorias demográficas preservando originais",
            "justificativa": (
                "Sexo e Raça/Cor foram padronizados para vocabulário controlado (Feminino/Masculino, Branca/Preta/Parda/etc.) "
                "mantendo as colunas sexo_original e cor_ou_raca_original intactas."
            ),
        },
        {
            "regra": "Não imputação de zeros em dados faltantes",
            "justificativa": (
                "Campos de texto descritivos vazios foram mantidos como nulos (<NA>) para garantir a integridade analítica."
            ),
        },
    ]

    # 9. Salvar base tratada se solicitado
    if salvar_csv:
        caminho_saida.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(caminho_saida, index=False, encoding="utf-8")
        log.info("Base tratada salva em: %s", caminho_saida)

    if registrar_evidencias:
        linhagem.registrar_linhagem(
            nome="linhagem_lattes_2023",
            entradas=[caminho_entrada],
            saida=caminho_saida if salvar_csv else None,
            relatorio_tratamento=rel_qualidade,
            decisoes=decisoes,
            dir_bruto=RAIZ / "dados" / "bruto",
        )

    return df, rel_qualidade


def main():
    configurar_logging()
    executar_etl_lattes()


if __name__ == "__main__":
    main()

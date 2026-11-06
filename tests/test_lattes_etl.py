"""Testes automatizados do leitor e do pipeline ETL da base oficial do Painel Lattes."""

import pandas as pd
import pytest

from etl import leitor_lattes, tratamento_lattes
from etl.logging_config import RAIZ

CAMINHO_BRUTO_LATTES = RAIZ / "dados" / "bruto" / "cnpq" / "painel_lattes" / "Download - Tabela.xlsx"


@pytest.mark.skipif(not CAMINHO_BRUTO_LATTES.exists(), reason="Arquivo oficial Lattes não disponível")
def test_leitor_lattes_celulas_mescladas_resolvidas():
    df = leitor_lattes.ler_xlsx_com_merges(CAMINHO_BRUTO_LATTES)
    assert len(df) == 25820
    assert len(df.columns) == 40
    assert "quantidade" in df.columns
    # Nenhuma coluna dimensional deve ter valor nulo após a resolução dos merges
    assert df["Ano"].isna().sum() == 0
    assert df["Ano"].iloc[0] == "2023"
    assert df["Ano"].iloc[-1] == "2023"
    assert df["quantidade"].sum() == 26009


@pytest.mark.skipif(not CAMINHO_BRUTO_LATTES.exists(), reason="Arquivo oficial Lattes não disponível")
def test_etl_lattes_pipeline_execucao():
    df_tratado, rel = tratamento_lattes.executar_etl_lattes(
        salvar_csv=False, registrar_evidencias=False
    )
    assert len(df_tratado) == 25820
    assert "sexo_original" in df_tratado.columns
    assert "cor_ou_raca_original" in df_tratado.columns
    assert str(df_tratado["ano"].dtype) == "Int64"
    assert str(df_tratado["quantidade"].dtype) == "int64"

    # Verificar categorias padronizadas
    sexos_validos = {"Feminino", "Masculino", "Não informado"}
    assert set(df_tratado["sexo"].unique()).issubset(sexos_validos)

    racas_validas = {"Branca", "Preta", "Parda", "Amarela", "Indígena", "Não desejo declarar", "Não informado"}
    assert set(df_tratado["cor_ou_raca"].unique()).issubset(racas_validas)

    # Total ponderado de indivíduos
    assert rel["total_doutores_mestres_ponderado"] == 26009
    assert df_tratado["quantidade"].sum() == 26009

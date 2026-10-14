"""
Módulo de Testes Automatizados de Qualidade de Dados (QA / ETL)
Framework: pytest

Verificações implementadas:
1. Contagem de registros do CSV tratado (exatamente 7).
2. Ausência de linhas exatamente duplicadas.
3. Conversão e integridade da coluna 'idade' com tipo Int64 anulável.
4. Presença de valores nulos nos salários de Carla Dias e Elena Costa.
5. Presença de valor nulo na idade de Diego Lima.
6. Padronização adequada dos nomes das colunas (sem espaços, minúsculas).
7. Imutabilidade do CSV original (preservação dos 8 registros e da duplicata).
"""

from pathlib import Path
import pandas as pd
import pytest

# Definição de caminhos relativos robustos
CAMINHO_RAIZ = Path(__file__).resolve().parent.parent
CAMINHO_ORIGINAL = CAMINHO_RAIZ / "dados" / "exemplo_com_erros.csv"
CAMINHO_TRATADO = CAMINHO_RAIZ / "dados" / "tratado" / "exemplo_com_erros_tratado.csv"


@pytest.fixture(scope="module")
def df_tratado():
    """Carrega o DataFrame tratado e valida sua existência."""
    assert CAMINHO_TRATADO.exists(), f"Arquivo tratado não encontrado em: {CAMINHO_TRATADO}"
    df = pd.read_csv(CAMINHO_TRATADO)
    # Garante a tipagem explícita de idade como Int64 anulável
    df["idade"] = pd.to_numeric(df["idade"], errors="coerce").astype("Int64")
    return df


@pytest.fixture(scope="module")
def df_original():
    """Carrega o DataFrame original com erros e valida sua existência."""
    assert CAMINHO_ORIGINAL.exists(), f"Arquivo original não encontrado em: {CAMINHO_ORIGINAL}"
    return pd.read_csv(CAMINHO_ORIGINAL)


def test_1_quantidade_registros_tratados(df_tratado):
    """1. O CSV tratado contém exatamente 7 registros."""
    assert len(df_tratado) == 7, (
        f"Esperado 7 registros no arquivo tratado, mas foram encontrados {len(df_tratado)}."
    )


def test_2_ausencia_de_duplicatas_exatas(df_tratado):
    """2. Não existem linhas exatamente duplicadas na base tratada."""
    duplicadas = df_tratado.duplicated().sum()
    assert duplicadas == 0, f"Foram encontradas {duplicadas} linhas duplicadas no arquivo tratado."


def test_3_coluna_idade_tipo_int64(df_tratado):
    """3. A coluna idade pode ser convertida e mantida como Int64 anulável."""
    assert str(df_tratado["idade"].dtype) == "Int64", (
        f"Tipo esperado para 'idade' é Int64, mas obteve {df_tratado['idade'].dtype}."
    )


def test_4_salarios_nulos_carla_e_elena(df_tratado):
    """4. Carla Dias e Elena Costa possuem salário nulo."""
    # Obter registros de Carla Dias
    registro_carla = df_tratado[df_tratado["nome"] == "Carla Dias"]
    assert not registro_carla.empty, "Registro de 'Carla Dias' não encontrado na base tratada."
    salario_carla = registro_carla["salario"].values[0]
    assert pd.isna(salario_carla), f"Salário de Carla Dias deveria ser NaN/nulo, mas é: {salario_carla}"

    # Obter registros de Elena Costa
    registro_elena = df_tratado[df_tratado["nome"] == "Elena Costa"]
    assert not registro_elena.empty, "Registro de 'Elena Costa' não encontrado na base tratada."
    salario_elena = registro_elena["salario"].values[0]
    assert pd.isna(salario_elena), (
        f"Salário de Elena Costa deveria ser NaN/nulo (valor original 'abc'), mas é: {salario_elena}"
    )


def test_5_idade_nula_diego_lima(df_tratado):
    """5. Diego Lima possui idade nula."""
    registro_diego = df_tratado[df_tratado["nome"] == "Diego Lima"]
    assert not registro_diego.empty, "Registro de 'Diego Lima' não encontrado na base tratada."
    idade_diego = registro_diego["idade"].values[0]
    assert pd.isna(idade_diego), f"Idade de Diego Lima deveria ser nula (<NA>), mas é: {idade_diego}"


def test_6_nomes_das_colunas_padronizados(df_tratado):
    """6. Os nomes das colunas estão padronizados (sem espaços e minúsculas)."""
    colunas_esperadas = ["nome", "idade", "sexo", "salario"]
    assert list(df_tratado.columns) == colunas_esperadas, (
        f"Colunas obtidas {list(df_tratado.columns)} diferem das esperadas {colunas_esperadas}."
    )
    # Garante que nenhuma coluna contém espaços nas pontas ou letras maiúsculas
    for col in df_tratado.columns:
        assert col == col.strip(), f"A coluna '{col}' possui espaços em branco."
        assert col == col.lower(), f"A coluna '{col}' possui letras maiúsculas."


def test_7_imutabilidade_csv_original(df_original):
    """7. O CSV original continua contendo 8 registros, incluindo a duplicata."""
    assert len(df_original) == 8, (
        f"Esperado 8 registros no CSV original, mas foram encontrados {len(df_original)}."
    )
    duplicadas_original = df_original.duplicated().sum()
    assert duplicadas_original == 1, (
        f"Esperado 1 linha duplicada no CSV original, mas foram encontradas {duplicadas_original}."
    )

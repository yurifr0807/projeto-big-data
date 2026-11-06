"""Testes das funções de tratamento (fixtures pequenas, sem serviços externos).

Complementam ``test_tratamento.py`` (exercício original, preservado sem alterações).
"""

import math

import pandas as pd
import pytest

from etl import tratamento as t


def S(*valores):
    return pd.Series(list(valores), dtype="object")


# ---------- colunas ---------- #
def test_padronizar_nome_coluna_acentos_espacos_e_caixa():
    assert t.padronizar_nome_coluna("  Cor ou Raça ") == "cor_ou_raca"
    assert t.padronizar_nome_coluna("Grande Área (CNPq)") == "grande_area_cnpq"
    assert t.padronizar_nome_coluna(" nome ") == "nome"  # mesmo resultado dos scripts originais


def test_padronizar_colunas_nao_altera_original_e_detecta_colisao():
    df = pd.DataFrame({" Idade ": ["1"], "sexo": ["F"]})
    out = t.padronizar_colunas(df)
    assert list(out.columns) == ["idade", "sexo"] and list(df.columns) == [" Idade ", "sexo"]
    with pytest.raises(ValueError, match="duplicados"):
        t.padronizar_colunas(pd.DataFrame({"Área": [1], "area": [2]}))


# ---------- inteiros / anos / datas ---------- #
def test_inteiro_preserva_nulos_e_marca_invalidos():
    v, inval = t.converter_inteiro(S("28", "", None, "abc", "28.5", " 40 ", "31.0"))
    assert str(v.dtype) == "Int64"
    assert v.tolist()[0] == 28 and v.isna().tolist() == [False, True, True, True, True, False, False]
    assert inval.tolist() == [False, False, False, True, True, False, False]
    assert v.iloc[5] == 40 and v.iloc[6] == 31


def test_ano_fora_do_intervalo_vira_nulo_e_invalido():
    v, inval = t.validar_ano(S("2013", "1850", "2999", "x", ""), minimo=2000, maximo=2030)
    assert v.tolist()[0] == 2013
    assert v.isna().tolist() == [False, True, True, True, True]
    assert inval.tolist() == [False, True, True, True, False]


def test_converter_data_formato_brasileiro_e_invalida():
    d, inval = t.converter_data(S("31/12/2020", "2021-01-15", "32/13/2020", ""))
    assert d.iloc[0] == pd.Timestamp(2020, 12, 31) and d.iloc[1] == pd.Timestamp(2021, 1, 15)
    assert inval.tolist() == [False, False, True, False]


# ---------- monetário ---------- #
@pytest.mark.parametrize(
    "texto,esperado",
    [
        ("3500.50", 3500.50), ("3.500,50", 3500.50), ("R$ 1.234,56", 1234.56), ("1,5", 1.5),
        ("1.234", 1234.0), ("1.234.567", 1234567.0), ("1,234.56", 1234.56), ("0", 0.0), ("  42 ", 42.0),
    ],
)
def test_monetario_formatos(texto, esperado):
    v, inval = t.converter_monetario(S(texto))
    assert math.isclose(v.iloc[0], esperado) and not inval.iloc[0]


def test_monetario_invalidos_ausentes_e_negativos():
    v, inval = t.converter_monetario(S("abc", "", None, "-10,00", "(5,00)", "1,2,3", "R$"))
    assert v.isna().all()  # nenhum vira zero
    assert inval.tolist() == [True, False, False, True, True, True, True]


def test_monetario_negativo_permitido():
    v, inval = t.converter_monetario(S("-10,00"), permitir_negativo=True)
    assert v.iloc[0] == -10.0 and not inval.iloc[0]


def test_monetario_arredonda_duas_casas():
    v, _ = t.converter_monetario(S("10,555"))
    assert v.iloc[0] == pytest.approx(10.56, abs=0.011)


# ---------- categorias ---------- #
def test_sexo_normaliza_grafia_sem_inferir():
    out = t.normalizar_sexo(S("Feminino", "FEMININO", " f ", "Masculino", "M", "Não informado", "", None, "outro"))
    assert out.tolist() == [
        "Feminino", "Feminino", "Feminino", "Masculino", "Masculino",
        "Não informado", "Não informado", "Não informado", "Não mapeado",
    ]


def test_raca_normaliza_e_preserva_nao_informado_e_nao_declara():
    out = t.normalizar_raca_cor(S("Branca", "preta", "PARDA", "Amarela", "Indígena", "indigena",
                                  "Não informado", "Não desejo declarar", "", "Alienígena"))
    assert out.tolist() == [
        "Branca", "Preta", "Parda", "Amarela", "Indígena", "Indígena",
        "Não informado", "Não desejo declarar", "Não informado", "Não mapeado",
    ]


def test_raca_nao_informada_nunca_vira_categoria_conhecida():
    out = t.normalizar_raca_cor(S("Não informado", "", None, "Não desejo declarar"))
    assert not set(out) & set(t.CATEGORIAS_RACA_CONHECIDAS)


def test_nao_mapeados_sao_listados_para_revisao():
    orig = S("Branca", "xyz", "xyz", "abc")
    norm = t.normalizar_raca_cor(orig)
    assert t.categorias_nao_mapeadas(orig, norm) == ["abc", "xyz"]


# ---------- duplicatas ---------- #
def test_remove_apenas_duplicatas_exatas():
    df = pd.DataFrame({"a": [1, 1, 1], "b": ["x", "x", "y"]})
    out, n = t.remover_duplicatas_exatas(df)
    assert n == 1 and len(out) == 2 and len(df) == 3


# ---------- orquestração ---------- #
ESQUEMA = {"ano": "ano", "idade": "inteiro", "valor": "monetario", "sexo": "sexo", "cor_ou_raca": "raca_cor", "uf": "texto"}


def _base():
    return pd.DataFrame(
        {
            " Ano ": ["2020", "2020", "1800", "2021"],
            "Idade": ["30", "30", "abc", ""],
            "Valor": ["1.000,00", "1.000,00", "abc", ""],
            "Sexo": ["F", "F", "Masculino", "Não informado"],
            "Cor ou Raça": ["Parda", "Parda", "", "Não desejo declarar"],
            "UF": ["SP ", "SP ", "RJ", ""],
        }
    )


def test_tratar_dataframe_fluxo_completo():
    out, rel = t.tratar_dataframe(_base(), ESQUEMA, ano_minimo=2000, ano_maximo=2030)
    assert rel.linhas_entrada == 4 and rel.linhas_saida == 3 and rel.duplicatas_removidas == 1
    assert rel.invalidos_por_coluna == {"ano": 1, "idade": 1, "valor": 1}
    assert {"sexo_original", "cor_ou_raca_original"} <= set(out.columns)  # originais preservados
    assert str(out["idade"].dtype) == "Int64" and out["valor"].dtype == "float64"
    assert out["valor"].isna().sum() == 2  # 'abc' e vazio permanecem nulos, nunca zero
    assert (out["valor"].dropna() > 0).all()
    assert out.loc[out["sexo_original"] == "Não informado", "sexo"].iloc[0] == "Não informado"
    assert out["uf"].iloc[0] == "SP"  # strip aplicado
    assert pd.isna(out["uf"].iloc[2])  # vazio vira nulo explícito


def test_tratar_dataframe_nao_altera_entrada_e_reporta_colunas_ausentes():
    df = _base()
    copia = df.copy(deep=True)
    out, rel = t.tratar_dataframe(df, {**ESQUEMA, "inexistente": "texto"})
    pd.testing.assert_frame_equal(df, copia)
    assert rel.colunas_ausentes == ["inexistente"] and "inexistente" not in out.columns


def test_tratar_dataframe_tipo_invalido_no_esquema():
    with pytest.raises(ValueError, match="não suportados"):
        t.tratar_dataframe(_base(), {"ano": "numerico_magico"})


def test_tratar_dataframe_base_vazia_nao_quebra():
    vazio = pd.DataFrame({"Ano": [], "Sexo": []}, dtype="object")
    out, rel = t.tratar_dataframe(vazio, {"ano": "ano", "sexo": "sexo"})
    assert out.empty and rel.linhas_entrada == 0 and rel.duplicatas_removidas == 0


def test_tratar_dataframe_reporta_categorias_nao_mapeadas():
    df = pd.DataFrame({"Sexo": ["F", "zzz"], "Cor": ["Branca", "ufo"]})
    _, rel = t.tratar_dataframe(df, {"sexo": "sexo", "cor": "raca_cor"})
    assert rel.nao_mapeados == {"sexo": ["zzz"], "cor": ["ufo"]}


# ---------- LGPD: identificadores ---------- #
def test_colunas_identificadoras_detectadas_sem_falso_positivo():
    cols = ["cpf", "nome", "nome_do_pesquisador", "email", "numero_do_processo", "id_lattes",
            "nome_instituicao", "area", "sexo", "uf", "ano", "valor"]
    assert t.colunas_identificadoras(cols) == ["cpf", "nome", "nome_do_pesquisador", "email", "numero_do_processo", "id_lattes"]


def test_remover_identificadores_nao_altera_entrada():
    df = pd.DataFrame({"cpf": ["1"], "sexo": ["F"]})
    out, removidas = t.remover_identificadores(df)
    assert removidas == ["cpf"] and list(out.columns) == ["sexo"] and "cpf" in df.columns


def test_descarte_de_identificadores_ocorre_apos_deduplicacao():
    # duas propostas distintas (processos diferentes) com atributos idênticos NÃO são duplicatas
    df = pd.DataFrame({"Processo": ["1", "2", "2"], "Ano": ["2020", "2020", "2020"], "Sexo": ["F", "F", "F"]})
    out, rel = t.tratar_dataframe(df, {"ano": "ano", "sexo": "sexo"}, descartar_identificadores=True)
    assert rel.duplicatas_removidas == 1  # só a repetição exata do processo 2
    assert len(out) == 2 and "processo" not in out.columns
    assert rel.identificadores_descartados == ["processo"]


def test_identificadores_mantidos_por_padrao():
    out, rel = t.tratar_dataframe(pd.DataFrame({"CPF": ["1"], "Ano": ["2020"]}), {"ano": "ano"})
    assert "cpf" in out.columns and rel.identificadores_descartados == []

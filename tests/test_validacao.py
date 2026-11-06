"""Testes de validação de schema e relatório de qualidade."""

import json

import pandas as pd
import pytest

from etl import validacao as v


def test_base_vazia_e_rejeitada():
    with pytest.raises(v.ValidacaoErro, match="vazia"):
        v.validar_nao_vazio(pd.DataFrame(), "pq")
    v.validar_nao_vazio(pd.DataFrame({"a": [1]}))


def test_schema_com_colunas_ausentes():
    df = pd.DataFrame({"ano": [2020], "sexo": ["Feminino"]})
    v.validar_schema(df, ["ano", "sexo"])
    with pytest.raises(v.ValidacaoErro, match="cor_ou_raca"):
        v.validar_schema(df, ["ano", "cor_ou_raca"])


def test_dominio_retorna_somente_valores_fora():
    df = pd.DataFrame({"sexo": ["Feminino", "Masculino", "X", None]})
    fora = v.validar_dominio(df, "sexo", ["Feminino", "Masculino"])
    assert fora["sexo"].tolist() == ["X"]


def test_registros_inconsistentes_com_motivos():
    df = pd.DataFrame({"ano": [2020, 1800, 2021], "valor": [10.0, -1.0, 5.0]})
    out = v.registros_inconsistentes(
        df, {"ano fora do intervalo": df["ano"] < 2000, "valor negativo": df["valor"] < 0}
    )
    assert out.index.tolist() == [1]
    assert "ano fora do intervalo" in out["motivos"].iloc[0] and "valor negativo" in out["motivos"].iloc[0]
    assert v.registros_inconsistentes(df, {}).empty


def test_checar_campos_indicador():
    df = pd.DataFrame({"sexo": ["Feminino", None, "Masculino", "Feminino"], "ano": [1, 2, 3, 4]})
    r = v.checar_campos_indicador(df, ["sexo", "ano", "cor"], minimo_preenchimento=0.9)
    assert r["sexo"] == {"presente": True, "preenchimento": 0.75, "ok": False}
    assert r["ano"]["ok"] is True and r["cor"] == {"presente": False, "preenchimento": 0.0, "ok": False}
    assert v.checar_campos_indicador(pd.DataFrame({"a": []}), ["a"])["a"]["preenchimento"] == 0.0


def test_relatorio_qualidade_e_escrita(tmp_path):
    df = pd.DataFrame({"sexo": ["F", "F", None], "ano": [2020, 2020, 2021]})
    rel = v.relatorio_qualidade(df, nome="teste", colunas_categoricas=["sexo", "inexistente"])
    assert rel["linhas"] == 3 and rel["nulos"]["sexo"] == 1 and rel["duplicatas_exatas"] == 1
    assert rel["categorias"]["sexo"]["F"] == 2 and "inexistente" not in rel["categorias"]
    destino = v.escrever_relatorio(rel, tmp_path / "q" / "rel.json")
    assert json.loads(destino.read_text(encoding="utf-8"))["base"] == "teste"


def test_relatorio_qualidade_base_vazia():
    rel = v.relatorio_qualidade(pd.DataFrame({"a": []}))
    assert rel["linhas"] == 0 and rel["duplicatas_exatas"] == 0


def test_grupos_pequenos_para_lgpd():
    df = pd.DataFrame({"uf": ["SP"] * 6 + ["AC"] * 2, "raca": ["Preta"] * 6 + ["Indígena"] * 2})
    risco = v.agrupamentos_com_risco(df, ["uf", "raca"], limite_minimo=5)
    assert risco.to_dict("records") == [{"uf": "AC", "raca": "Indígena", "contagem": 2}]
    assert v.agrupamentos_com_risco(df.iloc[0:0], ["uf"]).empty


def test_grupos_pequenos_somando_coluna_de_contagem():
    df = pd.DataFrame({"uf": ["AC", "AC", "SP"], "n": [2, 2, 10]})
    risco = v.agrupamentos_com_risco(df, ["uf"], limite_minimo=5, coluna_contagem="n")
    assert risco.to_dict("records") == [{"uf": "AC", "contagem": 4}]  # AC soma 4 (< 5); SP soma 10

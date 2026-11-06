"""Testes da linhagem do tratamento (origem, versão original/tratada, decisões)."""

import json

import pytest

from etl import ingestao, linhagem

DECISOES = [{"regra": "remover duplicatas exatas", "justificativa": "só linhas 100% idênticas são redundância certa"}]


def test_linhagem_registra_hashes_origem_e_decisoes(tmp_path):
    bruto = tmp_path / "bruto"
    orig = tmp_path / "dl" / "painel.csv"
    orig.parent.mkdir()
    orig.write_text("a\n1\n", encoding="utf-8")
    res = ingestao.importar_arquivo_manual(orig, subpasta="cnpq", descricao_origem="painel X, 2026-11-05", dir_bruto=bruto)
    tratado = tmp_path / "tratado.csv"
    tratado.write_text("a\n1\n", encoding="utf-8")

    caminho = linhagem.registrar_linhagem(
        nome="teste", entradas=[res.caminho], saida=tratado, relatorio_tratamento={"linhas_entrada": 1},
        decisoes=DECISOES, dir_bruto=bruto, destino_dir=tmp_path / "docs",
    )
    reg = json.loads(caminho.read_text(encoding="utf-8"))
    assert reg["versao_original"][0]["sha256"] == res.sha256
    assert reg["versao_original"][0]["origem_oficial"] == "painel X, 2026-11-05"
    assert reg["versao_tratada"]["arquivo"] == "tratado.csv" and reg["decisoes"] == DECISOES


def test_decisao_sem_justificativa_e_recusada(tmp_path):
    f = tmp_path / "a.csv"
    f.write_text("a", encoding="utf-8")
    with pytest.raises(ValueError, match="justificativa"):
        linhagem.registrar_linhagem(nome="x", entradas=[f], saida=None, relatorio_tratamento={},
                                    decisoes=[{"regra": "r", "justificativa": ""}], destino_dir=tmp_path)


def test_arquivo_inexistente_na_linhagem(tmp_path):
    with pytest.raises(FileNotFoundError):
        linhagem.registrar_linhagem(nome="x", entradas=[tmp_path / "nao.csv"], saida=None,
                                    relatorio_tratamento={}, decisoes=DECISOES, destino_dir=tmp_path)

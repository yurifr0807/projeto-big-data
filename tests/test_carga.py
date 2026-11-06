"""Testes da camada de carga: unitários com SQLite em arquivo temporário; integração com Aiven separada e opcional."""

import os

try:
    import dotenv
    dotenv.load_dotenv()
except ImportError:
    pass

import pandas as pd
import pytest
from sqlalchemy import create_engine, text

from etl import carga_postgresql as c

ENV_OK = {"DB_HOST": "h.aivencloud.com", "DB_PORT": "12345", "DB_NAME": "db", "DB_USER": "u", "DB_PASSWORD": "segredo123"}


@pytest.fixture
def engine(tmp_path):
    return create_engine(f"sqlite:///{tmp_path / 't.db'}")


def test_config_do_ambiente_e_senha_oculta():
    cfg = c.ConfigBanco.do_ambiente(ENV_OK)
    assert cfg.port == 12345 and cfg.sslmode == "require"
    assert "segredo123" not in repr(cfg) and "segredo123" not in str(cfg)
    assert cfg.url().drivername == "postgresql+psycopg"
    assert "segredo123" not in cfg.url().render_as_string(hide_password=True)


def test_config_variaveis_ausentes_e_porta_invalida():
    with pytest.raises(c.CargaErro, match="DB_PASSWORD"):
        c.ConfigBanco.do_ambiente({k: v for k, v in ENV_OK.items() if k != "DB_PASSWORD"})
    with pytest.raises(c.CargaErro, match="DB_PORT"):
        c.ConfigBanco.do_ambiente({**ENV_OK, "DB_PORT": "abc"})


def test_carga_em_lotes_e_contagem(engine):
    lotes = [pd.DataFrame({"a": [1, 2], "b": ["x", "y"]}), pd.DataFrame({"a": [3], "b": ["z"]}), pd.DataFrame({"a": [], "b": []})]
    assert c.carregar_em_lotes(iter(lotes), "fato_teste", engine) == 3
    assert c.contar_linhas(engine, "fato_teste") == 3


def test_carga_dataframe_unico_e_append(engine):
    df = pd.DataFrame({"a": [1]})
    c.carregar_em_lotes(df, "t", engine)
    c.carregar_em_lotes(df, "t", engine)
    assert c.contar_linhas(engine, "t") == 2


def test_if_exists_fail_nao_sobrescreve(engine):
    df = pd.DataFrame({"a": [1]})
    c.carregar_em_lotes(df, "t", engine)
    with pytest.raises(c.CargaErro):
        c.carregar_em_lotes(df, "t", engine, if_exists="fail")
    assert c.contar_linhas(engine, "t") == 1


def test_operacoes_destrutivas_sao_recusadas(engine):
    with pytest.raises(c.CargaErro, match="destrutivas"):
        c.carregar_em_lotes(pd.DataFrame({"a": [1]}), "t", engine, if_exists="replace")


@pytest.mark.parametrize("nome", ["t; DROP TABLE x", "1abc", "a-b", "", "a b"])
def test_identificadores_maliciosos_sao_recusados(engine, nome):
    with pytest.raises(c.CargaErro, match="inválido"):
        c.contar_linhas(engine, nome)
    with pytest.raises(c.CargaErro, match="inválido"):
        c.carregar_em_lotes(pd.DataFrame({"a": [1]}), nome, engine)


def test_falha_em_lote_reverte_transacao(engine):
    c.carregar_em_lotes(pd.DataFrame({"a": [1]}), "t", engine)

    def lotes():
        yield pd.DataFrame({"a": [2]})
        raise RuntimeError("falha simulada no segundo lote")

    with pytest.raises(c.CargaErro, match="revertida"):
        c.carregar_em_lotes(lotes(), "t", engine)
    assert c.contar_linhas(engine, "t") == 1  # o lote 1 da segunda chamada não ficou gravado


def test_tamanho_banco_exige_postgresql(engine):
    with pytest.raises(c.CargaErro, match="PostgreSQL"):
        c.tamanho_banco_bytes(engine)


def test_integridade_referencial_com_fk(engine):
    """Mecanismo de verificação de FK que será usado no modelo estrela (aqui com tabelas de teste)."""
    with engine.begin() as conn:
        conn.execute(text("PRAGMA foreign_keys=ON"))
        conn.execute(text("CREATE TABLE dim (id INTEGER PRIMARY KEY)"))
        conn.execute(text("CREATE TABLE fato (id INTEGER PRIMARY KEY, dim_id INTEGER NOT NULL REFERENCES dim(id))"))
        conn.execute(text("INSERT INTO dim VALUES (1)"))
        conn.execute(text("INSERT INTO fato VALUES (1, 1)"))
    with pytest.raises(Exception):
        with engine.begin() as conn:
            conn.execute(text("PRAGMA foreign_keys=ON"))
            conn.execute(text("INSERT INTO fato VALUES (2, 99)"))


def test_calcular_tamanho_lote_seguro_limites():
    # 40 colunas: 30.000 // 40 = 750 -> limita no tamanho desejado (500)
    assert c.calcular_tamanho_lote_seguro(40, tamanho_desejado=500) == 500
    # 100 colunas: 30.000 // 100 = 300 -> reduz automaticamente para 300
    assert c.calcular_tamanho_lote_seguro(100, tamanho_desejado=500) == 300
    # 500 colunas: 30.000 // 500 = 60 -> reduz automaticamente para 60
    assert c.calcular_tamanho_lote_seguro(500, tamanho_desejado=500) == 60
    # 0 ou colunas negativas retorna o tamanho desejado
    assert c.calcular_tamanho_lote_seguro(0, tamanho_desejado=500) == 500


def test_carga_em_multiplos_lotes_com_ajuste_dinamico(engine):
    # Simula 1.200 registros com 10 colunas, gravados em múltiplos lotes
    df = pd.DataFrame({f"col_{i}": range(1200) for i in range(10)})
    total = c.carregar_em_lotes(df, "t_multilotes", engine, tamanho_lote=250)
    assert total == 1200
    assert c.contar_linhas(engine, "t_multilotes") == 1200


def test_rollback_completo_quando_lote_intermediario_falha(engine):
    # Garante que a transação é atômica: se o 3º lote falhar, os 2 primeiros são revertidos
    with engine.begin() as conn:
        conn.execute(text("CREATE TABLE t_rollback_multi (col_a INTEGER)"))

    def gerador_lotes():
        yield pd.DataFrame({"col_a": range(100)})
        yield pd.DataFrame({"col_a": range(100, 200)})
        raise ValueError("Simulação de falha no terceiro lote")

    with pytest.raises(c.CargaErro) as exc_info:
        c.carregar_em_lotes(gerador_lotes(), "t_rollback_multi", engine)

    # Verifica que o erro raiz foi preservado
    assert exc_info.value.orig_exc is not None
    assert "Simulação de falha" in str(exc_info.value.orig_exc)
    # Prova do rollback atômico: a tabela deve permanecer com 0 registros
    assert c.contar_linhas(engine, "t_rollback_multi") == 0


def test_extrair_erro_raiz_mascara_sql_volumoso():
    # Simula uma exceção do SQLAlchemy com dump volumoso de SQL e parâmetros
    class FakeDBAPIError(Exception):
        pass

    erro_sql = FakeDBAPIError(
        "psycopg.errors.ProgramLimitExceeded: number of parameters must be between 0 and 65535\n"
        "[SQL: INSERT INTO tabela VALUES (?, ?, ... 200.000 placeholders)]\n"
        "[parameters: (1, 2, 3, ...)]"
    )

    tipo, msg, orig = c.extrair_erro_raiz(erro_sql)
    assert tipo == "FakeDBAPIError"
    assert "ProgramLimitExceeded" in msg
    # Confirma que os blocos de SQL e parameters foram expurgados para não poluir logs
    assert "[SQL:" not in msg
    assert "[parameters:" not in msg
    assert orig is erro_sql


# ----------------- integração (Aiven) ----------------- #
pytestmark_integracao = pytest.mark.skipif(
    not all(os.environ.get(v) for v in c.VARIAVEIS_OBRIGATORIAS),
    reason="Integração Aiven ignorada: variáveis DB_HOST/DB_PORT/DB_NAME/DB_USER/DB_PASSWORD não configuradas",
)


@pytest.mark.integracao
@pytestmark_integracao
def test_integracao_conexao_e_tamanho_do_banco():
    eng = c.criar_engine()
    with eng.connect() as conn:
        assert conn.execute(text("SELECT 1")).scalar_one() == 1
    assert c.tamanho_banco_bytes(eng) > 0

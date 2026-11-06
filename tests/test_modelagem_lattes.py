"""Testes automatizados da modelagem, do DDL e das consultas analíticas com banco local (SQLite / Dialeto compatível)."""

from pathlib import Path
import pandas as pd
import pytest
from sqlalchemy import create_engine, text

from etl import carga_postgresql as cp
from etl.logging_config import RAIZ

CAMINHO_TRATADO_LATTES = RAIZ / "dados" / "tratado" / "painel_lattes_2023_tratado.csv"


@pytest.fixture
def db_local(tmp_path):
    """Cria um banco local SQLite para validar o esquema e os indicadores analíticos."""
    engine = create_engine(f"sqlite:///{tmp_path / 'analitico.db'}")
    return engine


def test_esquema_e_carga_local_lattes(db_local):
    """Valida a carga das colunas e tipos usando uma amostra real da base tratada."""
    if not CAMINHO_TRATADO_LATTES.exists():
        pytest.skip("Base tratada Lattes ainda não gerada")

    df = pd.read_csv(CAMINHO_TRATADO_LATTES, nrows=500)
    colunas_remover = [c for c in ["sexo_original", "cor_ou_raca_original"] if c in df.columns]
    df_carga = df.drop(columns=colunas_remover)

    # Inserir no banco local
    total = cp.carregar_em_lotes(df_carga, "perfil_lattes", db_local, if_exists="append")
    assert total == 500

    with db_local.connect() as conn:
        # 1. Total de linhas
        qtd_linhas = conn.execute(text("SELECT COUNT(*) FROM perfil_lattes")).scalar()
        assert qtd_linhas == 500

        # 2. Total ponderado pela coluna quantidade
        qtd_ponderada = conn.execute(text("SELECT SUM(quantidade) FROM perfil_lattes")).scalar()
        assert qtd_ponderada >= 500

        # 3. Análise de gênero
        res_sexo = conn.execute(text("SELECT sexo, SUM(quantidade) FROM perfil_lattes GROUP BY sexo")).fetchall()
        sexos = {r[0]: r[1] for r in res_sexo}
        assert "Feminino" in sexos or "Masculino" in sexos

        # 4. Análise de raça
        res_raca = conn.execute(text("SELECT cor_ou_raca, SUM(quantidade) FROM perfil_lattes GROUP BY cor_ou_raca")).fetchall()
        racas = {r[0]: r[1] for r in res_raca}
        assert any(r in racas for r in ["Branca", "Parda", "Preta"])


def test_consultas_validacao_soma_ponderada(db_local):
    """Garante que consultas que não usam SUM(quantidade) produzem contagens incorretas em dados agregados."""
    # Simular duas linhas agregadas onde quantidade representa pessoas reais
    dados_teste = pd.DataFrame([
        {"ano": 2023, "sexo": "Feminino", "cor_ou_raca": "Preta", "quantidade": 5, "bolsista_pq": "Não"},
        {"ano": 2023, "sexo": "Masculino", "cor_ou_raca": "Branca", "quantidade": 10, "bolsista_pq": "Sim"},
    ])
    dados_teste.to_sql("teste_ponderacao", db_local, index=False)

    with db_local.connect() as conn:
        linhas = conn.execute(text("SELECT COUNT(*) FROM teste_ponderacao")).scalar()
        pessoas = conn.execute(text("SELECT SUM(quantidade) FROM teste_ponderacao")).scalar()
        # Prova técnica de que linhas != pessoas
        assert linhas == 2
        assert pessoas == 15



def test_deteccao_carga_parcial_ou_divergente(tmp_path):
    """Garante que a rotina de carga emite erro se a tabela contiver carga parcial ou divergente."""
    from etl import carga_lattes as cl

    engine = create_engine(f"sqlite:///{tmp_path / 'divergente.db'}")

    # Criar um CSV temporário tratado pequeno com 10 linhas
    csv_temp = tmp_path / "tratado_temp.csv"
    df_temp = pd.DataFrame([
        {"ano": 2023, "sexo": "Feminino", "cor_ou_raca": "Branca", "quantidade": 2} for _ in range(10)
    ])
    df_temp.to_csv(csv_temp, index=False)

    # DDL simplificado para sqlite sem schema
    ddl_temp = tmp_path / "ddl_temp.sql"
    ddl_temp.write_text(
        "CREATE TABLE IF NOT EXISTS perfil_pesquisadores_lattes_2023 ("
        "id_registro INTEGER PRIMARY KEY, ano INTEGER, sexo TEXT, cor_ou_raca TEXT, quantidade INTEGER);"
    )

    # Monkeypatch do schema para sqlite teste
    orig_schema = cl.SCHEMA_LATTES
    cl.SCHEMA_LATTES = ""
    try:
        # Simular uma carga parcial pré-existente (ex.: apenas 5 linhas no banco em vez de 10)
        with engine.begin() as conn:
            conn.execute(text(
                "CREATE TABLE perfil_pesquisadores_lattes_2023 (ano INTEGER, sexo TEXT, cor_ou_raca TEXT, quantidade INTEGER)"
            ))
            for _ in range(5):
                conn.execute(text("INSERT INTO perfil_pesquisadores_lattes_2023 VALUES (2023, 'Feminino', 'Branca', 2)"))

        with pytest.raises(cp.CargaErro, match="DIVERGÊNCIA DETECTADA"):
            cl.carregar_lattes_postgresql(engine, caminho_csv=csv_temp)
    finally:
        cl.SCHEMA_LATTES = orig_schema


def test_verificar_estado_lattes_diagnostico(tmp_path):
    """Valida a inspeção não-destrutiva de estado (vazia vs carregada vs inexistente)."""
    from etl import carga_lattes as cl

    engine = create_engine(f"sqlite:///{tmp_path / 'diagnostico.db'}")
    orig_schema = cl.SCHEMA_LATTES
    cl.SCHEMA_LATTES = ""
    try:
        # 1. Tabela inexistente
        diag_inexistente = cl.verificar_estado_lattes(engine)
        assert diag_inexistente["existe"] is False
        assert diag_inexistente["status"] == "tabela_inexistente"

        # 2. Tabela vazia após DDL (simula estado após rollback atômico)
        with engine.begin() as conn:
            conn.execute(text("CREATE TABLE perfil_pesquisadores_lattes_2023 (quantidade INTEGER)"))
        diag_vazia = cl.verificar_estado_lattes(engine)
        assert diag_vazia["existe"] is True
        assert diag_vazia["linhas"] == 0
        assert diag_vazia["status"] == "pronta_para_carga"

        # 3. Tabela com dados (carga íntegra simulada com valores esperados)
        with engine.begin() as conn:
            conn.execute(text("DELETE FROM perfil_pesquisadores_lattes_2023"))
            # Inserir simulando as 25.820 linhas e soma 26.009
            # Como teste unitário rápido, testamos status de divergência ou correspondência
            conn.execute(text("INSERT INTO perfil_pesquisadores_lattes_2023 VALUES (10)"))
        diag_parcial = cl.verificar_estado_lattes(engine)
        assert diag_parcial["linhas"] == 1
        assert diag_parcial["status"] == "divergente"
    finally:
        cl.SCHEMA_LATTES = orig_schema

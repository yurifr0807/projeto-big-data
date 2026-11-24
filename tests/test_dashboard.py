"""Testes offline de KPIs e queries do dashboard: não conectam à Aiven."""
import pytest
from sqlalchemy import create_engine, text

from dashboard.analytics import (
    known, percentage, number, kpis, safe_distribution, safe_cross, safe_pq_by_sex,
)
from dashboard.db import ConfigError, connection_settings, get_filter_options, query_groups, where_clause


def test_known_categorias_recusadas_e_ausentes():
    for item in [None, "", "Não informado", "Não desejo declarar", "Não mapeado"]:
        assert not known(item)
    assert known("Parda") and known("Feminino")


@pytest.mark.parametrize("num,den,expected", [(10, 20, 50), (0, 20, 0), (20, 20, 100), (2, 20, None), (18, 20, None), (5, 10, 50), (0, 4, None)])
def test_rate_suppresses_small_numerator_or_complement(num, den, expected):
    assert percentage(num, den) == expected


def test_kpis_weighted_denominators_and_coverage():
    sex = [{"sexo": "Feminino", "n": 60}, {"sexo": "Masculino", "n": 35}, {"sexo": "Não informado", "n": 5}]
    race = [{"cor_ou_raca": "Branca", "n": 40}, {"cor_ou_raca": "Preta", "n": 20},
            {"cor_ou_raca": "Parda", "n": 30}, {"cor_ou_raca": "Não desejo declarar", "n": 10}]
    cross = [
        {"sexo":"Feminino", "cor_ou_raca":"Preta", "n": 10, "n_pq": 5},
        {"sexo":"Feminino", "cor_ou_raca":"Parda", "n": 20, "n_pq": 5},
        {"sexo":"Feminino", "cor_ou_raca":"Branca", "n": 25, "n_pq": 10},
        {"sexo":"Feminino", "cor_ou_raca":"Não desejo declarar", "n": 5, "n_pq": 0},
        {"sexo":"Masculino", "cor_ou_raca":"Preta", "n": 10, "n_pq": 0},
        {"sexo":"Masculino", "cor_ou_raca":"Parda", "n": 10, "n_pq": 0},
        {"sexo":"Masculino", "cor_ou_raca":"Branca", "n": 10, "n_pq": 0},
        {"sexo":"Masculino", "cor_ou_raca":"Não desejo declarar", "n": 5, "n_pq": 0},
        {"sexo":"Não informado", "cor_ou_raca":"Branca", "n": 5, "n_pq": 0},
    ]
    result = kpis(sex, race, cross)
    assert result["total"] == 100
    assert result["female_pct"] == 63.2
    assert result["female_coverage"] == 95
    assert result["black_brown_pct"] == 55.6
    assert result["race_coverage"] == 90
    assert result["intersect_pct"] == 35.3 # 30 de 85 com ambos conhecidos
    assert result["pq_pct"] == 20


def test_safe_distribution_suppresses_entire_distribution_when_small_cell():
    data, hidden = safe_distribution([{"sexo": "Feminino", "n": 25}, {"sexo":"Masculino", "n":2}], "sexo")
    assert hidden and data == []


def test_safe_distribution_excludes_missing_and_preserves_weighted_count():
    data, hidden = safe_distribution([{"sexo":"Feminino", "n":7}, {"sexo":"Feminino", "n":5},
                                      {"sexo":"Masculino", "n":10}, {"sexo":"Não informado", "n":2}], "sexo")
    assert not hidden and data[0] == {"categoria":"Feminino", "pessoas":12}


def test_safe_cross_hides_any_positive_cell_below_five():
    data, hidden = safe_cross([{"sexo":"Feminino", "cor_ou_raca":"Preta", "n":3}])
    assert hidden and data == []


def test_safe_cross_excludes_unknown_categories():
    data, hidden = safe_cross([{"sexo":"Feminino", "cor_ou_raca":"Parda", "n":6},
                               {"sexo":"Não informado", "cor_ou_raca":"Parda", "n":1}])
    assert not hidden and data == [{"sexo":"Feminino", "raça/cor":"Parda", "pessoas":6}]


def test_safe_pq_hides_rate_if_small_numerator_or_complement():
    data, hidden = safe_pq_by_sex([{"sexo":"Feminino", "n":100, "n_pq":2}])
    assert hidden and data == []
    data, hidden = safe_pq_by_sex([{"sexo":"Feminino", "n":100, "n_pq":20}])
    assert not hidden and data[0]["presença de PQ (%)"] == 20


def test_where_clause_is_parameterized_and_has_allowlist():
    sql, args = where_clause({"sexo": "Feminino' OR 1=1 --", "uf":"BA"})
    assert "Feminino" not in sql and "sexo = :p_sexo" in sql and "uf_atuacao = :p_uf" in sql
    assert args["p_sexo"] == "Feminino' OR 1=1 --"
    with pytest.raises(ValueError, match="não permitido"):
        where_clause({"qualquer_coluna); DROP TABLE x; --": "teste"})


def test_settings_missing_credentials_and_ssl_validation():
    with pytest.raises(ConfigError, match="Credenciais"):
        connection_settings(env={})
    base={"DB_HOST":"localhost", "DB_PORT":"5432", "DB_NAME":"db", "DB_USER":"ro", "DB_PASSWORD":"fake"}
    assert connection_settings(env=base)["sslmode"] == "require"
    with pytest.raises(ConfigError, match="DB_SSLROOTCERT"):
        connection_settings(env={**base, "DB_SSLMODE":"verify-full"})
    with pytest.raises(ConfigError, match="DB_SSLMODE"):
        connection_settings(env={**base, "DB_SSLMODE":"disable"})
    assert connection_settings(env={**base,"DB_SSLMODE":"verify-full","DB_SSLROOTCERT":"x.pem"})["sslrootcert"] == "x.pem"


@pytest.fixture
def database():
    engine = create_engine("sqlite+pysqlite:///:memory:")
    with engine.connect() as conn:
        conn.execute(text("ATTACH DATABASE ':memory:' AS lattes_analytics"))
        conn.execute(text("""CREATE TABLE lattes_analytics.perfil_pesquisadores_lattes_2023 (
           sexo TEXT, cor_ou_raca TEXT, regiao_atuacao TEXT, uf_atuacao TEXT,
           grande_area_atuacao TEXT, nivel_formacao TEXT, bolsista_pq TEXT, quantidade INTEGER)"""))
        conn.execute(text("""INSERT INTO lattes_analytics.perfil_pesquisadores_lattes_2023
        VALUES ('Feminino','Parda','Nordeste','BA','Ciências Humanas','Mestrado','Sim',3),
               ('Feminino','Parda','Nordeste','BA','Ciências Humanas','Mestrado','Não',4),
               ('Masculino','Branca','Sul','RS','Exatas','Doutorado','Não',10)"""))
        conn.commit()
        yield conn
    engine.dispose()


def test_sql_rollup_weighted_and_filters(database):
    rows = query_groups(database, ("sexo",), {})
    assert number(rows) == 17
    rows = query_groups(database, ("sexo",), {"regiao":"Nordeste"})
    assert rows == [{"sexo":"Feminino", "n":7,"n_pq":3}]
    assert query_groups(database, ("sexo",), {"raca":"Parda' OR 1=1 --"}) == []


def test_sql_rejects_invalid_grouping(database):
    with pytest.raises(ValueError, match="inválidas"):
        query_groups(database, ("sexo; DROP TABLE x",))


def test_options_are_actual_db_values(database):
    options = get_filter_options(database)
    assert options["sexo"] == ["Feminino", "Masculino"]
    assert options["uf"] == ["BA", "RS"]

"""Acesso somente leitura ao PostgreSQL Aiven, usando SQL parametrizado.

O dashboard só consulta AGREGADOS: não expõe as células individuais do Lattes.
As dimensões permitidas são fixas para evitar interpolar SQL não confiável.
"""
from __future__ import annotations

import os
from typing import Mapping

from sqlalchemy import URL, bindparam, create_engine, text
from sqlalchemy.engine import Engine

TABLE = "lattes_analytics.perfil_pesquisadores_lattes_2023"
FILTER_FIELDS = {
    "sexo": "sexo",
    "raca": "cor_ou_raca",
    "regiao": "regiao_atuacao",
    "uf": "uf_atuacao",
    "area": "grande_area_atuacao",
    "formacao": "nivel_formacao",
}
DIMENSION_FIELDS = {"sexo", "cor_ou_raca", "regiao_atuacao", "uf_atuacao", "grande_area_atuacao", "nivel_formacao"}


class ConfigError(ValueError):
    """Configuração insuficiente para conexão com banco."""


def connection_settings(secrets: Mapping | None = None, env: Mapping | None = None) -> dict:
    """Resolve secrets em [connections.postgresql] ou DB_*, sem expor valores."""
    env = os.environ if env is None else env
    secrets = secrets or {}
    nested = secrets.get("connections", {}).get("postgresql", {}) if hasattr(secrets, "get") else {}
    settings = {
        "host": nested.get("host") or secrets.get("DB_HOST") or env.get("DB_HOST"),
        "port": nested.get("port") or secrets.get("DB_PORT") or env.get("DB_PORT") or "5432",
        "database": nested.get("database") or secrets.get("DB_NAME") or env.get("DB_NAME"),
        "username": nested.get("username") or secrets.get("DB_USER") or env.get("DB_USER"),
        "password": nested.get("password") or secrets.get("DB_PASSWORD") or env.get("DB_PASSWORD"),
        "sslmode": nested.get("sslmode") or secrets.get("DB_SSLMODE") or env.get("DB_SSLMODE") or "require",
        "sslrootcert": nested.get("sslrootcert") or secrets.get("DB_SSLROOTCERT") or env.get("DB_SSLROOTCERT"),
    }
    if not all(settings[k] for k in ("host", "database", "username", "password")):
        raise ConfigError("Credenciais PostgreSQL não configuradas. Consulte docs/dashboard_implantacao.md.")
    try:
        settings["port"] = int(settings["port"])
    except (TypeError, ValueError) as exc:
        raise ConfigError("DB_PORT deve ser inteiro.") from exc
    if settings["sslmode"] not in {"verify-full", "verify-ca", "require"}:
        raise ConfigError("DB_SSLMODE deve ser require, verify-ca ou verify-full.")
    if settings["sslmode"] in {"verify-full", "verify-ca"} and not settings["sslrootcert"]:
        raise ConfigError("Informe DB_SSLROOTCERT para validação explícita da CA.")
    return settings


def make_engine(settings: Mapping) -> Engine:
    url = URL.create(
        "postgresql+psycopg",
        username=settings["username"], password=settings["password"],
        host=settings["host"], port=int(settings["port"]), database=settings["database"],
    )
    arguments = {
        "connect_timeout": 8,
        "sslmode": settings["sslmode"],
        "options": "-c default_transaction_read_only=on -c statement_timeout=10000",
    }
    if settings.get("sslrootcert"):
        arguments["sslrootcert"] = settings["sslrootcert"]
    return create_engine(url, connect_args=arguments, pool_pre_ping=True, pool_size=2, max_overflow=0)


def where_clause(filters: Mapping[str, str | None]) -> tuple[str, dict]:
    predicates, parameters = [], {}
    for key, value in filters.items():
        if key not in FILTER_FIELDS:
            raise ValueError(f"Filtro não permitido: {key}")
        if value is not None and str(value) != "":
            name = f"p_{key}"
            predicates.append(f"{FILTER_FIELDS[key]} = :{name}")
            parameters[name] = str(value)
    return (" WHERE " + " AND ".join(predicates)) if predicates else "", parameters


def query_groups(conn, dimensions: tuple[str, ...], filters: Mapping[str, str | None] | None = None) -> list[dict]:
    """Retorna agregados ponderados, nunca linhas da base original."""
    if not dimensions or len(set(dimensions)) != len(dimensions) or not set(dimensions) <= DIMENSION_FIELDS:
        raise ValueError("Dimensões de agrupamento inválidas")
    where, params = where_clause(filters or {})
    select_dims = ", ".join(dimensions)
    statement = text(
        f"SELECT {select_dims}, SUM(quantidade) AS n, "
        f"SUM(CASE WHEN bolsista_pq = 'Sim' THEN quantidade ELSE 0 END) AS n_pq "
        f"FROM {TABLE}{where} GROUP BY {select_dims} ORDER BY {select_dims}"
    )
    return [dict(row) for row in conn.execute(statement, params).mappings()]


def get_filter_options(conn) -> dict[str, list[str]]:
    """Obtém somente valores de categorias, sem revelar contagens pequenas."""
    result = {}
    for key, column in FILTER_FIELDS.items():
        rows = conn.execute(text(f"SELECT DISTINCT {column} FROM {TABLE} WHERE {column} IS NOT NULL ORDER BY {column}"))
        result[key] = [str(row[0]) for row in rows if row[0] is not None and str(row[0]).strip()]
    return result

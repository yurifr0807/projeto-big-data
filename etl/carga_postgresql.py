"""Carga no PostgreSQL (Aiven) — infraestrutura genérica de conexão e carga em lotes.

Este módulo NÃO define tabelas do domínio: o modelo (estrela) só será criado depois de
inspecionar o schema real dos dados oficiais (ver docs/arquitetura.md).

Segurança: credenciais somente via variáveis de ambiente (.env local ou Secrets da
plataforma de deploy). A senha nunca aparece em ``repr``/logs. ``sslmode`` padrão: require.
Não há operações destrutivas: só ``append`` e ``fail`` são aceitos como ``if_exists``.
"""

from __future__ import annotations

import logging
import os
import re
from dataclasses import dataclass, field
from typing import Iterable, Iterator

import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL, Engine

log = logging.getLogger("pipeline.carga")

_IDENT = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
VARIAVEIS_OBRIGATORIAS = ("DB_HOST", "DB_PORT", "DB_NAME", "DB_USER", "DB_PASSWORD")

# Limites do protocolo PostgreSQL (v3.0) para parâmetros em instruções preparadas
LIMITE_MAX_PARAMETROS_POSTGRES = 65_535
LIMITE_SEGURO_PARAMETROS = 30_000
TAMANHO_LOTE_PADRAO = 500


class CargaErro(RuntimeError):
    def __init__(self, message: str, orig_exc: BaseException | None = None):
        super().__init__(message)
        self.orig_exc = orig_exc


def extrair_erro_raiz(exc: BaseException) -> tuple[str, str, BaseException]:
    """Extrai o tipo e a mensagem limpa da exceção raiz (ex.: driver DBAPI), omitindo dumps de SQL e parâmetros."""
    orig = getattr(exc, "orig", None) or getattr(exc, "__cause__", None) or exc
    tipo = type(orig).__name__
    msg_raw = str(orig) if orig is not exc else str(exc)
    # Remove blocos de SQL / parameters gerados pelo SQLAlchemy que possam vazar consultas gigantes ou dados
    msg_limpa = msg_raw.split("\n[SQL:")[0].split("[SQL:")[0].split("\n[parameters:")[0].strip()
    if len(msg_limpa) > 300:
        msg_limpa = msg_limpa[:300] + "... [truncado para segurança/legibilidade]"
    return tipo, msg_limpa, orig


def calcular_tamanho_lote_seguro(
    num_colunas: int,
    tamanho_desejado: int = TAMANHO_LOTE_PADRAO,
    max_parametros: int = LIMITE_SEGURO_PARAMETROS,
) -> int:
    """Calcula tamanho de lote seguro para evitar o limite de 65.535 parâmetros do PostgreSQL.

    O protocolo do PostgreSQL suporta no máximo 65.535 parâmetros por instrução.
    Usamos uma margem de segurança conservadora (padrão 30.000) dividida pela quantidade de colunas.
    """
    if num_colunas <= 0:
        return max(1, tamanho_desejado)
    limite_por_colunas = max_parametros // num_colunas
    return max(1, min(tamanho_desejado, limite_por_colunas))


@dataclass(frozen=True)
class ConfigBanco:
    host: str
    port: int
    dbname: str
    user: str
    password: str = field(repr=False)
    sslmode: str = "require"

    @classmethod
    def do_ambiente(cls, env: dict | None = None) -> "ConfigBanco":
        if env is None:
            try:
                import dotenv
                dotenv.load_dotenv()
            except ImportError:
                pass
            env = os.environ
        faltando = [v for v in VARIAVEIS_OBRIGATORIAS if not env.get(v)]
        if faltando:
            raise CargaErro(f"Variáveis de ambiente ausentes: {faltando}. Veja .env.example.")
        try:
            porta = int(env["DB_PORT"])
        except ValueError as exc:
            raise CargaErro(f"DB_PORT inválida: {env['DB_PORT']!r}") from exc
        return cls(env["DB_HOST"], porta, env["DB_NAME"], env["DB_USER"], env["DB_PASSWORD"],
                   env.get("DB_SSLMODE", "require"))

    def url(self) -> URL:
        return URL.create("postgresql+psycopg", username=self.user, password=self.password,
                          host=self.host, port=self.port, database=self.dbname)


def criar_engine(cfg: ConfigBanco | None = None) -> Engine:
    """Engine PostgreSQL com TLS (``sslmode`` do .env) e ``pool_pre_ping``."""
    cfg = cfg or ConfigBanco.do_ambiente()
    return create_engine(cfg.url(), connect_args={"sslmode": cfg.sslmode}, pool_pre_ping=True)


def _validar_identificador(nome: str) -> str:
    if not _IDENT.match(nome):
        raise CargaErro(f"Identificador SQL inválido: {nome!r}")
    return nome


def carregar_em_lotes(
    dados: pd.DataFrame | Iterable[pd.DataFrame],
    tabela: str,
    engine: Engine,
    *,
    schema: str | None = None,
    if_exists: str = "append",
    tamanho_lote: int = TAMANHO_LOTE_PADRAO,
) -> int:
    """Grava DataFrame (ou iterável de DataFrames, ex.: chunks) na tabela, em transação única.

    Retorna o total de linhas gravadas. Falha (e reverte) se qualquer lote falhar.
    Ajusta dinamicamente o chunksize para garantir que a instrução nunca ultrapasse
    os limites de parâmetros suportados pelo driver PostgreSQL (protocolo v3.0).
    """
    if if_exists not in {"append", "fail"}:
        raise CargaErro("Somente if_exists='append' ou 'fail' são permitidos (sem operações destrutivas).")
    _validar_identificador(tabela)
    if schema:
        _validar_identificador(schema)
    lotes: Iterator[pd.DataFrame] = iter([dados]) if isinstance(dados, pd.DataFrame) else iter(dados)

    total = 0
    try:
        with engine.begin() as conn:
            modo = if_exists
            for lote in lotes:
                if lote.empty:
                    continue
                num_colunas = len(lote.columns)
                chunk_seguro = calcular_tamanho_lote_seguro(num_colunas, tamanho_desejado=tamanho_lote)
                lote.to_sql(
                    tabela,
                    conn,
                    schema=schema,
                    if_exists=modo,
                    index=False,
                    chunksize=chunk_seguro,
                    method="multi",
                )
                modo = "append"  # após o primeiro lote, os demais sempre acrescentam
                total += len(lote)
    except Exception as exc:
        tipo_raiz, msg_raiz, orig = extrair_erro_raiz(exc)
        log.error("Falha na carga de %s [%s]: %s (transação revertida)", tabela, tipo_raiz, msg_raiz)
        raise CargaErro(f"Falha na carga de {tabela}; transação revertida: {tipo_raiz}: {msg_raiz}", orig_exc=orig) from exc
    log.info("Carga concluída em %s: %d linhas", tabela, total)
    return total


def contar_linhas(engine: Engine, tabela: str, schema: str | None = None) -> int:
    """Quantidade de linhas armazenadas (evidência para o entregável 'quantidade de dados armazenados')."""
    nome = _validar_identificador(tabela)
    if schema:
        nome = f"{_validar_identificador(schema)}.{nome}"
    with engine.connect() as conn:
        return int(conn.execute(text(f"SELECT COUNT(*) FROM {nome}")).scalar_one())


def tamanho_banco_bytes(engine: Engine) -> int:
    """Tamanho do banco atual (somente PostgreSQL) para controlar o limite de 1 GB do Free Tier."""
    if engine.dialect.name != "postgresql":
        raise CargaErro("tamanho_banco_bytes só é suportado em PostgreSQL")
    with engine.connect() as conn:
        return int(conn.execute(text("SELECT pg_database_size(current_database())")).scalar_one())

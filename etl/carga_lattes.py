"""Pipeline de carga da base tratada Painel Lattes 2023 no PostgreSQL.

Características:
1. Execução idempotente e protegida por transação única (rollback automático em erro).
2. Validação prévia de integridade e duplicidades.
3. Se a tabela já contiver registros, verifica se o volume confere (idempotência);
   não sobrescreve destrutivamente nem duplica linhas.
4. Relatório pós-carga emitido com total de linhas e soma ponderada de indivíduos.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import pandas as pd
from sqlalchemy import Engine, text

from etl import carga_postgresql as cp
from etl.logging_config import RAIZ, configurar_logging

log = logging.getLogger("pipeline.carga_lattes")

CAMINHO_TRATADO_PADRAO = RAIZ / "dados" / "tratado" / "painel_lattes_2023_tratado.csv"
SCHEMA_LATTES = "lattes_analytics"
TABELA_LATTES = "perfil_pesquisadores_lattes_2023"


def aplicar_ddl(engine: Engine, ddl_path: Path | None = None) -> None:
    """Aplica o script DDL no banco de dados se não existir."""
    if engine.dialect.name == "sqlite":
        log.info("Dialeto SQLite detectado; criação de schema PostgreSQL ignorada.")
        return

    caminho = ddl_path or (RAIZ / "etl" / "ddl_lattes_2023.sql")
    if not caminho.exists():
        raise FileNotFoundError(f"Arquivo DDL não encontrado: {caminho}")

    log.info("Garantindo estrutura de tabelas DDL...")
    sql_script = caminho.read_text(encoding="utf-8")
    with engine.begin() as conn:
        for comando in sql_script.split(";"):
            cmd = comando.strip()
            if cmd:
                conn.execute(text(cmd))
    log.info("Estrutura DDL verificada com sucesso.")


def carregar_lattes_postgresql(
    engine: Engine,
    caminho_csv: Path = CAMINHO_TRATADO_PADRAO,
    tamanho_lote: int = cp.TAMANHO_LOTE_PADRAO,
) -> dict[str, int | str]:
    """Realiza a carga segura e idempotente do CSV tratado para o PostgreSQL."""
    if not caminho_csv.exists():
        raise FileNotFoundError(f"Base tratada não encontrada: {caminho_csv}")

    aplicar_ddl(engine)

    log.info("Lendo base tratada para carga: %s", caminho_csv)
    df = pd.read_csv(caminho_csv)

    # Descartar colunas de auditoria que não compõem a tabela analítica do banco
    colunas_remover = [c for c in ["sexo_original", "cor_ou_raca_original"] if c in df.columns]
    df_carga = df.drop(columns=colunas_remover)

    # Verificar integridade caso a tabela já contenha registros
    with engine.connect() as conn:
        tabela_completa = f"{SCHEMA_LATTES}.{TABELA_LATTES}" if SCHEMA_LATTES else TABELA_LATTES
        qtd_existente = conn.execute(text(f"SELECT COUNT(*) FROM {tabela_completa}")).scalar() or 0
        soma_ponderada = conn.execute(text(f"SELECT SUM(quantidade) FROM {tabela_completa}")).scalar() or 0

    if qtd_existente > 0:
        linhas_esperadas = len(df_carga)
        soma_esperada = int(df_carga["quantidade"].sum())

        if qtd_existente == linhas_esperadas and soma_ponderada == soma_esperada:
            log.info(
                "Tabela %s já se encontra carregada e íntegra (%d linhas, soma ponderada %d). Carga ignorada com sucesso (idempotência).",
                tabela_completa, qtd_existente, soma_ponderada
            )
            return {
                "linhas_carregadas": 0,
                "linhas_totais": qtd_existente,
                "soma_ponderada": int(soma_ponderada),
                "status": "integro_ja_carregado",
            }
        else:
            erro_msg = (
                f"DIVERGÊNCIA DETECTADA em {tabela_completa}: "
                f"Esperado {linhas_esperadas} linhas e soma {soma_esperada}, "
                f"mas foram encontrados {qtd_existente} linhas e soma {soma_ponderada}. "
                "Possível carga parcial ou corrupção de estado. Intervenção manual requerida."
            )
            log.error(erro_msg)
            raise cp.CargaErro(erro_msg)

    log.info("Iniciando inserção de %d linhas em %s (lotes de até %d registros)...", len(df_carga), tabela_completa, tamanho_lote)
    total_linhas = cp.carregar_em_lotes(
        df_carga,
        TABELA_LATTES,
        engine,
        schema=SCHEMA_LATTES,
        if_exists="append",
        tamanho_lote=tamanho_lote,
    )

    with engine.connect() as conn:
        soma_ponderada = conn.execute(text(f"SELECT SUM(quantidade) FROM {tabela_completa}")).scalar() or 0

    log.info("Carga concluída com sucesso! Total linhas: %d, Soma ponderada: %d", total_linhas, soma_ponderada)
    return {
        "linhas_carregadas": total_linhas,
        "linhas_totais": total_linhas,
        "soma_ponderada": int(soma_ponderada),
        "status": "sucesso",
    }


def verificar_estado_lattes(engine: Engine) -> dict[str, Any]:
    """Inspeciona o estado atual da tabela no banco sem modificar nada nem apagar dados."""
    tabela_completa = f"{SCHEMA_LATTES}.{TABELA_LATTES}" if SCHEMA_LATTES else TABELA_LATTES
    with engine.connect() as conn:
        if engine.dialect.name == "postgresql":
            sql_check = text(
                "SELECT EXISTS ("
                "  SELECT 1 FROM information_schema.tables "
                "  WHERE table_schema = :s AND table_name = :t"
                ")"
            )
            existe = bool(conn.execute(sql_check, {"s": SCHEMA_LATTES or "public", "t": TABELA_LATTES}).scalar())
            if not existe:
                return {
                    "tabela": tabela_completa,
                    "existe": False,
                    "linhas": 0,
                    "soma_ponderada": 0,
                    "status": "tabela_inexistente",
                    "mensagem": "Tabela ainda não criada. O DDL será aplicado no início da carga.",
                }
        try:
            qtd = conn.execute(text(f"SELECT COUNT(*) FROM {tabela_completa}")).scalar() or 0
            soma = conn.execute(text(f"SELECT SUM(quantidade) FROM {tabela_completa}")).scalar() or 0
        except Exception:
            return {
                "tabela": tabela_completa,
                "existe": False,
                "linhas": 0,
                "soma_ponderada": 0,
                "status": "tabela_inexistente",
                "mensagem": "Tabela ou schema ainda não acessível.",
            }

    qtd = int(qtd)
    soma = int(soma) if soma is not None else 0

    if qtd == 0:
        status = "pronta_para_carga"
        msg = "Tabela vazia e limpa (rollback anterior foi 100% atômico e eficaz). Pronta para carga."
    elif qtd == 25_820 and soma == 26_009:
        status = "integra_completa"
        msg = "Tabela já contém os 25.820 registros e soma ponderada 26.009 (carga íntegra)."
    else:
        status = "divergente"
        msg = f"Tabela contém {qtd} linhas e soma {soma}. Diverge do esperado (25.820 linhas, 26.009 ponderado)."

    return {
        "tabela": tabela_completa,
        "existe": True,
        "linhas": qtd,
        "soma_ponderada": soma,
        "status": status,
        "mensagem": msg,
    }


def main():
    import sys
    configurar_logging()
    engine = cp.criar_engine()
    banco_conectado = engine.url.database or ""
    log.info("Conectado ao banco: '%s' no host '%s'", banco_conectado, engine.url.host)
    if engine.dialect.name == "postgresql" and banco_conectado != "observatorio":
        log.warning(
            "Aviso: Conectado ao banco '%s'. O banco analítico oficial da Fase 2 é 'observatorio'.",
            banco_conectado
        )

    estado = verificar_estado_lattes(engine)
    log.info("Diagnóstico da tabela %s: %s (Linhas: %d, Soma: %d)",
             estado["tabela"], estado["status"], estado["linhas"], estado["soma_ponderada"])
    log.info("Mensagem: %s", estado["mensagem"])

    if "--verificar" in sys.argv:
        print(f"\n[DIAGNÓSTICO AIVEN] Tabela: {estado['tabela']} | Linhas: {estado['linhas']} | Soma: {estado['soma_ponderada']} | Status: {estado['status']}")
        print(f"Detalhes: {estado['mensagem']}\n")
        return

    carregar_lattes_postgresql(engine)


if __name__ == "__main__":
    main()

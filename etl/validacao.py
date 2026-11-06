"""Validação de schema e relatório de qualidade dos dados.

Funções puras, sem dependência de serviços externos. O esquema real das fontes
só será fixado após o primeiro download oficial; aqui ficam os mecanismos.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Mapping, Sequence

import pandas as pd

log = logging.getLogger("pipeline.validacao")


class ValidacaoErro(ValueError):
    """Dados não atendem ao contrato mínimo para o pipeline/indicadores."""


def validar_nao_vazio(df: pd.DataFrame, nome: str = "base") -> None:
    if df is None or df.empty:
        raise ValidacaoErro(f"{nome}: base vazia (0 linhas); nada a processar.")


def validar_schema(df: pd.DataFrame, obrigatorias: Iterable[str], nome: str = "base") -> None:
    """Exige que todas as colunas obrigatórias existam (após padronização dos nomes)."""
    ausentes = [c for c in obrigatorias if c not in df.columns]
    if ausentes:
        raise ValidacaoErro(f"{nome}: colunas obrigatórias ausentes: {ausentes}. Presentes: {list(df.columns)}")


def validar_dominio(df: pd.DataFrame, coluna: str, permitidos: Iterable[str]) -> pd.DataFrame:
    """Retorna as linhas cujo valor em ``coluna`` não pertence a ``permitidos`` (nulos ignorados)."""
    permitidos = set(permitidos)
    mascara = df[coluna].notna() & ~df[coluna].isin(permitidos)
    return df[mascara]


def registros_inconsistentes(df: pd.DataFrame, regras: Mapping[str, pd.Series]) -> pd.DataFrame:
    """Marca linhas que violam alguma regra. ``regras`` = {descricao: máscara booleana de violação}."""
    if not regras:
        return df.iloc[0:0].assign(motivos=pd.Series(dtype="object"))
    motivos = pd.Series("", index=df.index, dtype="object")
    for descricao, violacao in regras.items():
        violacao = violacao.reindex(df.index).fillna(False).astype(bool)
        motivos = motivos.mask(violacao, motivos + descricao + "; ")
    saida = df[motivos != ""].copy()
    saida["motivos"] = motivos[motivos != ""]
    return saida


def checar_campos_indicador(df: pd.DataFrame, campos: Sequence[str], minimo_preenchimento: float = 0.0) -> dict:
    """Verifica se os campos de um indicador existem e quanto está preenchido (não nulo)."""
    resultado: dict[str, dict] = {}
    for campo in campos:
        if campo not in df.columns:
            resultado[campo] = {"presente": False, "preenchimento": 0.0, "ok": False}
            continue
        p = float(df[campo].notna().mean()) if len(df) else 0.0
        resultado[campo] = {"presente": True, "preenchimento": round(p, 4), "ok": p >= minimo_preenchimento}
    return resultado


def relatorio_qualidade(
    df: pd.DataFrame,
    *,
    nome: str = "base",
    colunas_categoricas: Sequence[str] = (),
    max_categorias: int = 30,
) -> dict:
    """Relatório de qualidade serializável: dimensões, nulos, duplicatas, tipos e distribuição de categorias."""
    rel = {
        "base": nome,
        "gerado_em": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "linhas": int(len(df)),
        "colunas": list(map(str, df.columns)),
        "tipos": {str(c): str(t) for c, t in df.dtypes.items()},
        "nulos": {str(c): int(n) for c, n in df.isna().sum().items()},
        "duplicatas_exatas": int(df.duplicated().sum()) if len(df) else 0,
        "categorias": {},
    }
    for col in colunas_categoricas:
        if col in df.columns:
            contagem = df[col].value_counts(dropna=False).head(max_categorias)
            rel["categorias"][col] = {str(k): int(v) for k, v in contagem.items()}
    return rel


def escrever_relatorio(rel: Mapping, destino: Path) -> Path:
    """Grava o relatório em JSON (UTF-8) e retorna o caminho."""
    destino = Path(destino)
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(json.dumps(rel, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    log.info("Relatório de qualidade gravado em %s", destino)
    return destino


def agrupamentos_com_risco(
    df: pd.DataFrame, grupos: Sequence[str], limite_minimo: int = 5, coluna_contagem: str | None = None
) -> pd.DataFrame:
    """Combinações de ``grupos`` com contagem menor que ``limite_minimo`` (risco de reidentificação, LGPD).

    Se ``coluna_contagem`` for dada, soma essa coluna; senão conta linhas.
    """
    if df.empty:
        return pd.DataFrame(columns=[*grupos, "contagem"])
    agrup = df.groupby(list(grupos), dropna=False, observed=True)
    cont = (agrup[coluna_contagem].sum() if coluna_contagem else agrup.size()).rename("contagem").reset_index()
    return cont[cont["contagem"] < limite_minimo].reset_index(drop=True)

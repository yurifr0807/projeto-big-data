"""Configuração centralizada de logging do pipeline.

Os logs vão para o console e para ``logs/pipeline.log`` (ignorado pelo Git).
"""

from __future__ import annotations

import logging
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
FORMATO = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"


def configurar_logging(nivel: int = logging.INFO, arquivo: Path | None = None) -> logging.Logger:
    """Configura o logger raiz do pipeline (idempotente) e o retorna."""
    logger = logging.getLogger("pipeline")
    logger.setLevel(nivel)
    if logger.handlers:
        return logger

    formatador = logging.Formatter(FORMATO)
    console = logging.StreamHandler()
    console.setFormatter(formatador)
    logger.addHandler(console)

    destino = arquivo or (RAIZ / "logs" / "pipeline.log")
    try:
        destino.parent.mkdir(parents=True, exist_ok=True)
        arq = logging.FileHandler(destino, encoding="utf-8")
        arq.setFormatter(formatador)
        logger.addHandler(arq)
    except OSError as exc:  # pragma: no cover - depende do sistema de arquivos
        logger.warning("Não foi possível gravar log em arquivo (%s): %s", destino, exc)
    return logger

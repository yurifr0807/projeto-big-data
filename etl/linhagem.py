"""Linhagem do tratamento: origem, versão original, versão tratada e decisões justificadas.

Atende à Fase 2 do professor (Entregável 1): permitir verificar a origem dos dados, a versão
original utilizada, a versão resultante e as decisões/justificativas. O registro não contém
dados — apenas metadados e hashes — e por isso pode ser versionado em ``docs/linhagem/``.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Mapping, Sequence

from etl.ingestao import calcular_sha256, carregar_manifesto
from etl.logging_config import RAIZ

log = logging.getLogger("pipeline.linhagem")
DIR_LINHAGEM = RAIZ / "docs" / "linhagem"


def _info_arquivo(caminho: Path, dir_bruto: Path | None) -> dict:
    caminho = Path(caminho)
    if not caminho.is_file():
        raise FileNotFoundError(f"Arquivo da linhagem não encontrado: {caminho}")
    info = {"arquivo": caminho.name, "sha256": calcular_sha256(caminho), "tamanho_bytes": caminho.stat().st_size}
    if dir_bruto is not None:
        try:
            chave = str(caminho.relative_to(dir_bruto)).replace("\\", "/")
        except ValueError:
            chave = None
        entrada = carregar_manifesto(dir_bruto).get(chave) if chave else None
        if entrada:
            info["origem_oficial"] = entrada["origem"]
            info["tipo_origem"] = entrada["tipo_origem"]
            info["ingerido_em"] = entrada["ingerido_em"]
    return info


def registrar_linhagem(
    *,
    nome: str,
    entradas: Sequence[Path],
    saida: Path | None,
    relatorio_tratamento: Mapping,
    decisoes: Sequence[Mapping[str, str]],
    dir_bruto: Path | None = None,
    destino_dir: Path = DIR_LINHAGEM,
) -> Path:
    """Grava ``<destino_dir>/<nome>.json`` e devolve o caminho.

    ``decisoes``: lista de {"regra": ..., "justificativa": ...}; ambos obrigatórios.
    """
    for d in decisoes:
        if not d.get("regra") or not d.get("justificativa"):
            raise ValueError(f"Toda decisão precisa de 'regra' e 'justificativa': {dict(d)}")
    registro = {
        "nome": nome,
        "gerado_em": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "versao_original": [_info_arquivo(p, dir_bruto) for p in entradas],
        "versao_tratada": _info_arquivo(saida, None) if saida else None,
        "relatorio_tratamento": dict(relatorio_tratamento),
        "decisoes": [dict(d) for d in decisoes],
    }
    destino_dir = Path(destino_dir)
    destino_dir.mkdir(parents=True, exist_ok=True)
    caminho = destino_dir / f"{nome}.json"
    caminho.write_text(json.dumps(registro, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    log.info("Linhagem registrada em %s", caminho)
    return caminho

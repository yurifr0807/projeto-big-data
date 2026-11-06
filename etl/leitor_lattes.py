"""Leitura especializada de planilhas exportadas do Power BI / Lattes com células mescladas (mergeCells).

O Painel Lattes exporta tabelas dinâmicas hierárquicas onde as células de grupos repetidos
são mescladas nativamente no XML do Excel (<mergeCell ref="..."/>).
Sem a resolução das mesclagens, apenas a primeira linha de cada bloco carrega o rótulo
(ex.: '2023', país, instituição), deixando as demais como None/vazio.
Este leitor restaura a integridade dimensional de todas as linhas mapeadas.
"""

from __future__ import annotations

import logging
import re
import zipfile
from pathlib import Path
from typing import Sequence

import openpyxl
from openpyxl.utils import range_boundaries
import pandas as pd

from etl.ingestao import IngestaoErro

log = logging.getLogger("pipeline.lattes")


def ler_xlsx_com_merges(
    caminho: Path,
    aba: str = "Sheet 1",
    nome_coluna_contagem: str = "quantidade",
) -> pd.DataFrame:
    """Lê planilha XLSX resolvendo explicitamente os intervalos de células mescladas.

    A última coluna sem cabeçalho (None) é automaticamente identificada e renomeada
    para ``nome_coluna_contagem`` (default: 'quantidade').
    Todos os pontos à esquerda dos nomes originais (ex.: '.Ano' -> 'Ano') são higienizados.
    """
    caminho = Path(caminho)
    if not caminho.is_file():
        raise IngestaoErro(f"Arquivo não encontrado: {caminho}")

    # 1. Extração dos mergeCell diretamente do XML (eficiente e exato)
    try:
        with zipfile.ZipFile(caminho) as z:
            with z.open("xl/worksheets/sheet1.xml") as f:
                content = f.read().decode("utf-8", errors="ignore")
                merges = re.findall(r'<mergeCell ref="([^"]+)"/>', content)
    except Exception as exc:
        raise IngestaoErro(f"Falha ao ler XML de mesclagem em {caminho.name}: {exc}") from exc

    # 2. Leitura dos dados brutos com openpyxl (read_only=True para economia de memória)
    wb = openpyxl.load_workbook(caminho, read_only=True)
    if aba not in wb.sheetnames:
        aba = wb.sheetnames[0]
    ws = wb[aba]

    raw_rows = list(ws.iter_rows(values_only=True))
    wb.close()

    if not raw_rows:
        raise IngestaoErro(f"Planilha vazia: {caminho.name}")

    header = list(raw_rows[0])
    # Se a última coluna não tiver cabeçalho, atribuir nome_coluna_contagem
    if header and header[-1] is None:
        header[-1] = nome_coluna_contagem

    clean_header = [str(c).lstrip(".") if c is not None else nome_coluna_contagem for c in header]
    data = [list(r) for r in raw_rows[1:]]

    # 3. Propagação dos valores das células mescladas (apenas nos intervalos declarados pelo Excel)
    for m in merges:
        min_col, min_row, max_col, max_row = range_boundaries(m)
        c_idx = min_col - 1
        # O cabeçalho é row 1; a primeira linha de dados é row 2 -> data[0]
        top_val = data[min_row - 2][c_idx]
        for r_idx in range(min_row - 2, max_row - 1):
            data[r_idx][c_idx] = top_val

    df = pd.DataFrame(data, columns=clean_header)
    log.info("Lidos %d registros e %d colunas de %s com %d merges resolvidos.", len(df), len(df.columns), caminho.name, len(merges))
    return df

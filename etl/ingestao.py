"""Camada de ingestão: download/importação de arquivos oficiais para ``dados/bruto/``.

Princípios (ver docs/arquitetura.md):

* Os arquivos brutos NUNCA são alterados após gravados; qualquer reprocessamento
  parte deles.
* Toda requisição usa TLS **com verificação de certificado**, timeout e tratamento
  de exceções. Para redes com proxy/CA corporativa, aponte a variável de ambiente
  ``CA_BUNDLE`` (ou ``REQUESTS_CA_BUNDLE``) para o arquivo .pem da CA confiável.
  Este módulo não oferece, de propósito, opção para desligar a verificação TLS.
* Cada arquivo registrado gera uma entrada no manifesto
  (``dados/bruto/manifesto_ingestao.json``) com URL/origem, data, tamanho e SHA-256,
  o que evita downloads redundantes e documenta a procedência.
* Arquivos grandes são lidos em lotes (``ler_csv_em_chunks``).

Nenhuma URL de dados é "inventada": as fontes só entram em ``etl/fontes.py``
depois de verificadas.
"""

from __future__ import annotations

import csv
import hashlib
import json
import logging
import os
import shutil
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator, Sequence

import pandas as pd
import requests

from etl.logging_config import RAIZ, configurar_logging

log = logging.getLogger("pipeline.ingestao")

DIR_BRUTO = RAIZ / "dados" / "bruto"
NOME_MANIFESTO = "manifesto_ingestao.json"
TIMEOUT_PADRAO = (10, 60)  # (conexão, leitura) em segundos
CODIFICACOES_PADRAO = ("utf-8-sig", "utf-8", "cp1252", "latin-1")
USER_AGENT = "projeto-big-data-observatorio-equidade/0.1 (projeto academico; contato: aluno)"


class IngestaoErro(RuntimeError):
    """Falha de ingestão (download, integridade ou leitura)."""


@dataclass(frozen=True)
class ResultadoIngestao:
    caminho: Path
    sha256: str
    tamanho_bytes: int
    baixado: bool  # False quando reaproveitado (sem download redundante)
    origem: str


# --------------------------------------------------------------------------- #
# Utilidades de integridade e manifesto
# --------------------------------------------------------------------------- #
def calcular_sha256(caminho: Path, bloco: int = 1024 * 1024) -> str:
    h = hashlib.sha256()
    with open(caminho, "rb") as f:
        for parte in iter(lambda: f.read(bloco), b""):
            h.update(parte)
    return h.hexdigest()


def _caminho_manifesto(dir_bruto: Path) -> Path:
    return dir_bruto / NOME_MANIFESTO


def carregar_manifesto(dir_bruto: Path = DIR_BRUTO) -> dict:
    caminho = _caminho_manifesto(dir_bruto)
    if not caminho.exists():
        return {}
    try:
        return json.loads(caminho.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise IngestaoErro(f"Manifesto corrompido em {caminho}: {exc}") from exc


def _salvar_manifesto(manifesto: dict, dir_bruto: Path) -> None:
    dir_bruto.mkdir(parents=True, exist_ok=True)
    _caminho_manifesto(dir_bruto).write_text(
        json.dumps(manifesto, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8"
    )


def _registrar(
    manifesto: dict,
    chave: str,
    *,
    origem: str,
    tipo_origem: str,
    caminho: Path,
    sha256: str,
    dir_bruto: Path,
    metadados: dict | None = None,
) -> None:
    manifesto[chave] = {
        "origem": origem,
        "tipo_origem": tipo_origem,  # "download" | "manual"
        "arquivo": str(caminho.relative_to(dir_bruto)).replace("\\", "/"),
        "sha256": sha256,
        "tamanho_bytes": caminho.stat().st_size,
        "ingerido_em": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "metadados": metadados or {},
    }


# --------------------------------------------------------------------------- #
# Download seguro
# --------------------------------------------------------------------------- #
def _verificacao_tls() -> bool | str:
    """Retorna o parâmetro ``verify`` do requests: sempre verificando o certificado."""
    bundle = os.environ.get("CA_BUNDLE") or os.environ.get("REQUESTS_CA_BUNDLE")
    if bundle:
        if not Path(bundle).is_file():
            raise IngestaoErro(f"CA_BUNDLE aponta para arquivo inexistente: {bundle}")
        return bundle
    return True


def baixar_arquivo(
    url: str,
    destino: Path,
    *,
    dir_bruto: Path = DIR_BRUTO,
    chave: str | None = None,
    forcar: bool = False,
    timeout: tuple[int, int] = TIMEOUT_PADRAO,
    sessao: requests.Session | None = None,
    metadados: dict | None = None,
) -> ResultadoIngestao:
    """Baixa ``url`` para ``destino`` (dentro de ``dir_bruto``) em streaming.

    * Reaproveita arquivo existente e registrado no manifesto (sem download redundante),
      a menos que ``forcar=True``.
    * Grava em arquivo temporário e só então move, evitando arquivos parciais.
    * Levanta :class:`IngestaoErro` em falha de rede, TLS, HTTP ou arquivo vazio.
    """
    if not url.lower().startswith("https://") and not url.lower().startswith("http://"):
        raise IngestaoErro(f"URL inválida: {url!r}")
    chave = chave or destino.name
    manifesto = carregar_manifesto(dir_bruto)

    if destino.exists() and not forcar and chave in manifesto:
        sha = calcular_sha256(destino)
        if sha == manifesto[chave]["sha256"]:
            log.info("Reaproveitando %s (já ingerido, SHA-256 confere)", destino.name)
            return ResultadoIngestao(destino, sha, destino.stat().st_size, False, url)
        raise IngestaoErro(
            f"{destino} foi alterado após a ingestão (SHA-256 difere do manifesto). "
            "Arquivos brutos são imutáveis; investigue antes de prosseguir."
        )

    destino.parent.mkdir(parents=True, exist_ok=True)
    temporario = destino.with_suffix(destino.suffix + ".parcial")
    cliente = sessao or requests.Session()
    log.info("Baixando %s", url)
    try:
        with cliente.get(
            url,
            stream=True,
            timeout=timeout,
            verify=_verificacao_tls(),
            headers={"User-Agent": USER_AGENT},
        ) as resposta:
            resposta.raise_for_status()
            with open(temporario, "wb") as f:
                for bloco in resposta.iter_content(chunk_size=1024 * 256):
                    if bloco:
                        f.write(bloco)
    except requests.exceptions.SSLError as exc:
        temporario.unlink(missing_ok=True)
        raise IngestaoErro(
            f"Falha de verificação TLS ao acessar {url}. Informe a CA confiável via "
            f"CA_BUNDLE ou use o download manual (docs/download_manual.md). Detalhe: {exc}"
        ) from exc
    except requests.exceptions.RequestException as exc:
        temporario.unlink(missing_ok=True)
        raise IngestaoErro(f"Falha no download de {url}: {exc}") from exc

    if not temporario.exists() or temporario.stat().st_size == 0:
        temporario.unlink(missing_ok=True)
        raise IngestaoErro(f"Download de {url} retornou arquivo vazio")

    temporario.replace(destino)
    sha = calcular_sha256(destino)
    _registrar(
        manifesto, chave, origem=url, tipo_origem="download", caminho=destino,
        sha256=sha, dir_bruto=dir_bruto, metadados=metadados,
    )
    _salvar_manifesto(manifesto, dir_bruto)
    log.info("Arquivo gravado: %s (%d bytes, sha256=%s…)", destino.name, destino.stat().st_size, sha[:12])
    return ResultadoIngestao(destino, sha, destino.stat().st_size, True, url)


def importar_arquivo_manual(
    origem: Path,
    *,
    subpasta: str,
    descricao_origem: str,
    dir_bruto: Path = DIR_BRUTO,
    forcar: bool = False,
    metadados: dict | None = None,
) -> ResultadoIngestao:
    """Copia um arquivo baixado manualmente (ex.: "Baixar Planilhas" do painel CNPq)
    para ``dados/bruto/<subpasta>/`` e o registra no manifesto.

    ``descricao_origem`` deve conter a URL da página/painel e a data do download.
    O arquivo original NÃO é movido nem alterado.
    """
    origem = Path(origem)
    if not origem.is_file():
        raise IngestaoErro(f"Arquivo de origem não encontrado: {origem}")
    if origem.stat().st_size == 0:
        raise IngestaoErro(f"Arquivo de origem vazio: {origem}")

    destino = dir_bruto / subpasta / origem.name
    chave = f"{subpasta}/{origem.name}"
    manifesto = carregar_manifesto(dir_bruto)
    sha_origem = calcular_sha256(origem)

    if destino.exists() and not forcar:
        if calcular_sha256(destino) == sha_origem:
            log.info("Arquivo %s já importado (mesmo SHA-256); nada a fazer", origem.name)
            return ResultadoIngestao(destino, sha_origem, destino.stat().st_size, False, descricao_origem)
        raise IngestaoErro(
            f"Já existe um arquivo diferente em {destino}. Use forcar=True conscientemente "
            "ou renomeie o novo arquivo (preservando a versão anterior)."
        )

    destino.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(origem, destino)
    _registrar(
        manifesto, chave, origem=descricao_origem, tipo_origem="manual", caminho=destino,
        sha256=sha_origem, dir_bruto=dir_bruto, metadados=metadados,
    )
    _salvar_manifesto(manifesto, dir_bruto)
    log.info("Arquivo importado manualmente: %s", chave)
    return ResultadoIngestao(destino, sha_origem, destino.stat().st_size, True, descricao_origem)


# --------------------------------------------------------------------------- #
# Leitura (CSV / JSON / XLSX) com detecção de codificação e delimitador
# --------------------------------------------------------------------------- #
def detectar_codificacao(
    caminho: Path, candidatas: Sequence[str] = CODIFICACOES_PADRAO, amostra_bytes: int = 1 << 20
) -> str:
    """Primeira codificação candidata que decodifica a amostra sem erro."""
    with open(caminho, "rb") as f:
        amostra = f.read(amostra_bytes)
    for cod in candidatas:
        try:
            amostra.decode(cod)
            return cod
        except UnicodeDecodeError:
            continue
    raise IngestaoErro(f"Não foi possível decodificar {caminho} com {list(candidatas)}")


def detectar_delimitador(caminho: Path, codificacao: str, candidatos: str = ",;\t|") -> str:
    """Detecta o delimitador pela amostra do início do arquivo."""
    with open(caminho, "r", encoding=codificacao, newline="") as f:
        amostra = f.read(64 * 1024)
    if not amostra.strip():
        raise IngestaoErro(f"Arquivo sem conteúdo: {caminho}")
    try:
        return csv.Sniffer().sniff(amostra, delimiters=candidatos).delimiter
    except csv.Error:
        primeira = amostra.splitlines()[0]
        return max(candidatos, key=primeira.count)


def ler_csv(caminho: Path, **kwargs) -> pd.DataFrame:
    """Lê CSV inteiro como texto (``dtype=str``): a tipagem é feita no ETL, de forma explícita."""
    cod = kwargs.pop("encoding", None) or detectar_codificacao(caminho)
    sep = kwargs.pop("sep", None) or detectar_delimitador(caminho, cod)
    try:
        return pd.read_csv(caminho, encoding=cod, sep=sep, dtype=str, keep_default_na=False, **kwargs)
    except (pd.errors.ParserError, pd.errors.EmptyDataError) as exc:
        raise IngestaoErro(f"CSV inválido {caminho}: {exc}") from exc


def ler_csv_em_chunks(
    caminho: Path,
    *,
    colunas: Sequence[str] | None = None,
    tamanho_chunk: int = 100_000,
    **kwargs,
) -> Iterator[pd.DataFrame]:
    """Itera sobre o CSV em lotes, lendo só as colunas pedidas (poupa memória).

    ``colunas`` é comparado após ``strip`` do cabeçalho; colunas ausentes geram erro explícito.
    """
    cod = kwargs.pop("encoding", None) or detectar_codificacao(caminho)
    sep = kwargs.pop("sep", None) or detectar_delimitador(caminho, cod)
    usecols = None
    if colunas is not None:
        cabecalho = pd.read_csv(caminho, encoding=cod, sep=sep, nrows=0).columns
        mapa = {c.strip(): c for c in cabecalho}
        ausentes = [c for c in colunas if c not in mapa]
        if ausentes:
            raise IngestaoErro(f"Colunas ausentes em {caminho.name}: {ausentes}")
        usecols = [mapa[c] for c in colunas]
    leitor = pd.read_csv(
        caminho, encoding=cod, sep=sep, dtype=str, keep_default_na=False,
        usecols=usecols, chunksize=tamanho_chunk, **kwargs,
    )
    for numero, lote in enumerate(leitor, start=1):
        log.debug("Lote %d com %d linhas", numero, len(lote))
        yield lote


def ler_json(caminho: Path) -> pd.DataFrame:
    """Lê JSON (lista de registros ou objeto com chave de registros) como DataFrame de texto."""
    try:
        return pd.read_json(caminho, dtype=False, encoding=detectar_codificacao(caminho))
    except ValueError as exc:
        raise IngestaoErro(f"JSON inválido {caminho}: {exc}") from exc


def ler_xlsx(caminho: Path, aba: str | int = 0) -> pd.DataFrame:
    """Lê uma aba de XLSX como texto. Requer ``openpyxl``."""
    try:
        return pd.read_excel(caminho, sheet_name=aba, dtype=str, keep_default_na=False)
    except ImportError as exc:
        raise IngestaoErro("Leitura de XLSX requer 'openpyxl' (pip install openpyxl)") from exc
    except (ValueError, OSError) as exc:
        raise IngestaoErro(f"XLSX inválido {caminho}: {exc}") from exc


def ler_arquivo(caminho: Path, **kwargs) -> pd.DataFrame:
    """Despacha pela extensão (.csv/.txt, .json, .xlsx/.xls)."""
    ext = Path(caminho).suffix.lower()
    if ext in {".csv", ".txt"}:
        return ler_csv(caminho, **kwargs)
    if ext == ".json":
        return ler_json(caminho)
    if ext in {".xlsx", ".xls"}:
        return ler_xlsx(caminho, **kwargs)
    raise IngestaoErro(f"Formato não suportado: {ext}")


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #
def _main(argv: Sequence[str] | None = None) -> int:
    import argparse

    from etl import fontes

    p = argparse.ArgumentParser(description="Ingestão de fontes oficiais para dados/bruto/")
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("listar", help="Lista as fontes verificadas e como obtê-las")
    sub.add_parser("baixar-documentacao", help="Baixa a documentação oficial do CNPq (PDFs)")
    m = sub.add_parser("importar", help="Registra um arquivo baixado manualmente em dados/bruto/")
    m.add_argument("arquivo", type=Path)
    m.add_argument("--subpasta", required=True, help="ex.: cnpq/painel_pq")
    m.add_argument("--origem", required=True, help="URL do painel/página e data do download")
    args = p.parse_args(argv)

    configurar_logging()
    try:
        if args.cmd == "listar":
            for f in fontes.FONTES:
                print(f"[{f.status}] {f.id} — {f.nome}\n    {f.como_obter}")
        elif args.cmd == "baixar-documentacao":
            for doc in fontes.DOCUMENTACAO_CNPQ:
                baixar_arquivo(doc.url, DIR_BRUTO / "cnpq" / "documentacao" / doc.arquivo,
                               chave=f"cnpq/documentacao/{doc.arquivo}", metadados={"descricao": doc.descricao})
        else:
            importar_arquivo_manual(args.arquivo, subpasta=args.subpasta, descricao_origem=args.origem)
    except IngestaoErro as exc:
        log.error("%s", exc)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())

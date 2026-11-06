"""Tratamento (T do ETL): padronização, tipagem e normalização de categorias.

Regras gerais (ver docs/regras_negocio.md):

* Valores originais são preservados em colunas ``<coluna>_original``; a recodificação
  só ocorre por tabelas explícitas de equivalência (acentos/caixa/grafia), nunca por
  inferência a partir de nome, localização ou outro atributo.
* Valores ausentes ou "Não informado" NUNCA são convertidos em categoria conhecida e
  NUNCA viram zero. Valores não reconhecidos viram "Não mapeado" e são reportados.
* Conversões inválidas viram nulo (``NA``) e são contabilizadas, nunca descartadas
  silenciosamente.

As regras de padronização de colunas e tipagem reaproveitam a lógica validada em
``tratar_csv.py`` / ``tratar_csv_com_erros.py`` (strip/lower/underscore; Int64 anulável;
numérico com coerção), generalizada em funções testáveis.
"""

from __future__ import annotations

import logging
import re
import unicodedata
from dataclasses import dataclass, field
from typing import Mapping

import pandas as pd

log = logging.getLogger("pipeline.tratamento")

# Categorias padronizadas
SEXO_FEMININO = "Feminino"
SEXO_MASCULINO = "Masculino"
NAO_INFORMADO = "Não informado"
NAO_DECLARA = "Não desejo declarar"
NAO_MAPEADO = "Não mapeado"

RACA_BRANCA = "Branca"
RACA_PRETA = "Preta"
RACA_PARDA = "Parda"
RACA_AMARELA = "Amarela"
RACA_INDIGENA = "Indígena"

CATEGORIAS_SEXO_CONHECIDAS = (SEXO_FEMININO, SEXO_MASCULINO)
CATEGORIAS_RACA_CONHECIDAS = (RACA_BRANCA, RACA_PRETA, RACA_PARDA, RACA_AMARELA, RACA_INDIGENA)


def _sem_acentos(texto: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFKD", texto) if not unicodedata.combining(c))


def _chave(valor: object) -> str:
    """Chave de comparação: sem acentos, minúscula, espaços colapsados."""
    if valor is None or (not isinstance(valor, str) and pd.isna(valor)):
        return ""
    return re.sub(r"\s+", " ", _sem_acentos(str(valor)).strip().lower())


# Equivalências de GRAFIA (não inferência). Chaves já normalizadas por ``_chave``.
_MAPA_SEXO: dict[str, str] = {
    "feminino": SEXO_FEMININO, "f": SEXO_FEMININO, "fem": SEXO_FEMININO, "mulher": SEXO_FEMININO,
    "masculino": SEXO_MASCULINO, "m": SEXO_MASCULINO, "masc": SEXO_MASCULINO, "homem": SEXO_MASCULINO,
    "": NAO_INFORMADO, "nao informado": NAO_INFORMADO, "ni": NAO_INFORMADO,
    "nao informada": NAO_INFORMADO, "nao declarado": NAO_INFORMADO, "nao declarada": NAO_INFORMADO,
    "nan": NAO_INFORMADO, "null": NAO_INFORMADO,
}
_MAPA_RACA: dict[str, str] = {
    "branca": RACA_BRANCA, "branco": RACA_BRANCA,
    "preta": RACA_PRETA, "preto": RACA_PRETA,
    "parda": RACA_PARDA, "pardo": RACA_PARDA,
    "amarela": RACA_AMARELA, "amarelo": RACA_AMARELA,
    "indigena": RACA_INDIGENA,
    "": NAO_INFORMADO, "nao informado": NAO_INFORMADO, "nao informada": NAO_INFORMADO,
    "ni": NAO_INFORMADO, "nan": NAO_INFORMADO, "null": NAO_INFORMADO,
    "nao desejo declarar": NAO_DECLARA, "prefiro nao declarar": NAO_DECLARA,
    "nao declarado": NAO_DECLARA, "nao declarada": NAO_DECLARA,
}


# --------------------------------------------------------------------------- #
# Nomes de colunas
# --------------------------------------------------------------------------- #
def padronizar_nome_coluna(nome: str) -> str:
    """strip → minúsculas → sem acentos → não alfanumérico vira ``_`` (superconjunto da regra dos scripts originais)."""
    n = _sem_acentos(str(nome)).strip().lower()
    n = re.sub(r"[^a-z0-9]+", "_", n)
    return n.strip("_")


def padronizar_colunas(df: pd.DataFrame) -> pd.DataFrame:
    """Retorna cópia com nomes padronizados; falha se a padronização gerar nomes duplicados."""
    novos = [padronizar_nome_coluna(c) for c in df.columns]
    repetidos = sorted({c for c in novos if novos.count(c) > 1})
    if repetidos:
        raise ValueError(f"Padronização geraria nomes de coluna duplicados: {repetidos}")
    saida = df.copy()
    saida.columns = novos
    return saida


# --------------------------------------------------------------------------- #
# Conversões de tipo (retornam valores + máscara de inválidos)
# --------------------------------------------------------------------------- #
def _texto_preenchido(serie: pd.Series) -> pd.Series:
    s = serie.astype("string").str.strip()
    return s.mask(s == "", pd.NA)


def converter_inteiro(serie: pd.Series) -> tuple[pd.Series, pd.Series]:
    """Converte para ``Int64`` anulável. Inválidos: texto não numérico ou número não inteiro."""
    s = _texto_preenchido(serie)
    num = pd.to_numeric(s, errors="coerce")
    nao_inteiro = num.notna() & (num != num.round())
    invalidos = (s.notna() & num.isna()) | nao_inteiro
    num = num.mask(nao_inteiro)
    return num.astype("Int64"), invalidos.fillna(False).astype(bool)


def validar_ano(serie: pd.Series, minimo: int = 1900, maximo: int | None = None) -> tuple[pd.Series, pd.Series]:
    """Converte para ``Int64`` e invalida anos fora de [minimo, maximo] (padrão: ano corrente + 1)."""
    if maximo is None:
        maximo = pd.Timestamp.today().year + 1
    anos, invalidos = converter_inteiro(serie)
    fora = anos.notna() & ((anos < minimo) | (anos > maximo))
    fora = fora.fillna(False).astype(bool)
    return anos.mask(fora), (invalidos | fora)


def converter_data(serie: pd.Series, dayfirst: bool = True) -> tuple[pd.Series, pd.Series]:
    s = _texto_preenchido(serie)
    datas = pd.to_datetime(s, errors="coerce", dayfirst=dayfirst, format="mixed")
    invalidos = s.notna() & datas.isna()
    return datas, invalidos.fillna(False).astype(bool)


_RE_MILHAR_PONTO = re.compile(r"^\d{1,3}(\.\d{3})+$")


def _monetario_para_float(valor: object) -> float | None:
    """Converte string monetária brasileira/internacional para float; None se inválida.

    Regras: remove ``R$`` e espaços; parênteses ou ``-`` indicam negativo; se houver
    ``.`` e ``,`` o ÚLTIMO é o separador decimal; só ``,`` → decimal; só ``.`` →
    milhar quando segue o padrão ``1.234`` / ``1.234.567`` (convenção brasileira),
    senão decimal (``3500.50``).
    """
    if valor is None or (not isinstance(valor, str) and pd.isna(valor)):
        return None
    t = str(valor).strip()
    if not t:
        return None
    negativo = t.startswith("(") and t.endswith(")")
    t = re.sub(r"(?i)r\$|\s", "", t.strip("()"))
    if t.startswith("-"):
        negativo, t = True, t[1:]
    if not re.fullmatch(r"[\d.,]+", t) or not re.search(r"\d", t):
        return None
    if "," in t and "." in t:
        dec = "," if t.rfind(",") > t.rfind(".") else "."
        mil = "." if dec == "," else ","
        t = t.replace(mil, "").replace(dec, ".")
    elif "," in t:
        if t.count(",") > 1:
            return None
        t = t.replace(",", ".")
    elif "." in t:
        if _RE_MILHAR_PONTO.match(t):
            t = t.replace(".", "")
        elif t.count(".") > 1:
            return None
    try:
        v = float(t)
    except ValueError:
        return None
    return -v if negativo else v


def converter_monetario(serie: pd.Series, permitir_negativo: bool = False) -> tuple[pd.Series, pd.Series]:
    """Converte valores monetários em ``float64`` (2 casas). Inválidos/negativos (se não permitidos) → NaN.

    Ausentes permanecem NaN: **não** são imputados com zero.
    """
    s = _texto_preenchido(serie)
    valores = s.map(_monetario_para_float).astype("float64")
    invalidos = s.notna() & valores.isna()
    if not permitir_negativo:
        negativos = valores < 0
        invalidos = invalidos | negativos.fillna(False)
        valores = valores.mask(negativos)
    return valores.round(2), invalidos.fillna(False).astype(bool)


# --------------------------------------------------------------------------- #
# Normalização de categorias
# --------------------------------------------------------------------------- #
def _normalizar_categoria(serie: pd.Series, mapa: Mapping[str, str]) -> pd.Series:
    chaves = serie.map(_chave)
    return chaves.map(lambda k: mapa.get(k, NAO_MAPEADO)).astype("string")


def normalizar_sexo(serie: pd.Series) -> pd.Series:
    """Feminino/Masculino/Não informado/Não mapeado (valor desconhecido; nunca presumido)."""
    return _normalizar_categoria(serie, _MAPA_SEXO)


def normalizar_raca_cor(serie: pd.Series) -> pd.Series:
    """Categorias IBGE + 'Não informado' + 'Não desejo declarar'; desconhecidas → 'Não mapeado'."""
    return _normalizar_categoria(serie, _MAPA_RACA)


def categorias_nao_mapeadas(original: pd.Series, normalizada: pd.Series) -> list[str]:
    """Valores originais distintos que caíram em 'Não mapeado' (para revisão humana)."""
    return sorted(original[normalizada == NAO_MAPEADO].dropna().astype(str).unique().tolist())


# --------------------------------------------------------------------------- #
# Duplicatas
# --------------------------------------------------------------------------- #
def remover_duplicatas_exatas(df: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    """Remove apenas linhas 100% idênticas (mantém a primeira). Retorna (df, removidas)."""
    saida = df.drop_duplicates(keep="first")
    return saida, len(df) - len(saida)


# --------------------------------------------------------------------------- #
# LGPD: descarte de identificadores diretos
# --------------------------------------------------------------------------- #
_PADROES_IDENTIFICADOR = re.compile(
    r"^(cpf|nome|nome_(do_|da_)?(pesquisador|pesquisadora|proponente|bolsista|beneficiario|beneficiaria|candidato|candidata)"
    r"|e?_?mail|email|telefone|celular|(numero|num|n)_?(do_)?processo|processo|id_?lattes|lattes_?id|numero_?lattes)$"
)


def colunas_identificadoras(colunas) -> list[str]:
    """Colunas (já padronizadas) que parecem identificadores diretos de pessoa/processo."""
    return [c for c in colunas if _PADROES_IDENTIFICADOR.match(c)]


def remover_identificadores(df: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    """Descarta identificadores diretos (CPF, nome, e-mail, telefone, nº do processo, id Lattes)."""
    ids = colunas_identificadoras(df.columns)
    return df.drop(columns=ids), ids


# --------------------------------------------------------------------------- #
# Orquestração por esquema declarativo
# --------------------------------------------------------------------------- #
TIPOS_SUPORTADOS = {"texto", "inteiro", "ano", "data", "monetario", "sexo", "raca_cor"}


@dataclass
class RelatorioTratamento:
    linhas_entrada: int = 0
    linhas_saida: int = 0
    duplicatas_removidas: int = 0
    invalidos_por_coluna: dict[str, int] = field(default_factory=dict)
    nulos_por_coluna: dict[str, int] = field(default_factory=dict)
    nao_mapeados: dict[str, list[str]] = field(default_factory=dict)
    colunas_ausentes: list[str] = field(default_factory=list)
    identificadores_descartados: list[str] = field(default_factory=list)

    def como_dict(self) -> dict:
        return {
            "linhas_entrada": self.linhas_entrada,
            "linhas_saida": self.linhas_saida,
            "duplicatas_removidas": self.duplicatas_removidas,
            "invalidos_por_coluna": self.invalidos_por_coluna,
            "nulos_por_coluna": self.nulos_por_coluna,
            "nao_mapeados": self.nao_mapeados,
            "colunas_ausentes": self.colunas_ausentes,
            "identificadores_descartados": self.identificadores_descartados,
        }


def tratar_dataframe(
    df: pd.DataFrame,
    esquema: Mapping[str, str],
    *,
    ano_minimo: int = 1900,
    ano_maximo: int | None = None,
    remover_duplicatas: bool = True,
    descartar_identificadores: bool = False,
) -> tuple[pd.DataFrame, RelatorioTratamento]:
    """Aplica padronização de colunas, tipagem por ``esquema`` ({coluna_padronizada: tipo}) e deduplicação.

    Colunas do esquema ausentes no DataFrame são reportadas em ``colunas_ausentes`` (nunca criadas).
    Colunas de sexo/raça geram ``<col>_original`` com o valor de origem.

    ``descartar_identificadores=True`` remove identificadores diretos (LGPD) **depois** da
    deduplicação: se fossem removidos antes, propostas distintas com os mesmos atributos
    seriam tomadas por duplicatas e perdidas. O padrão é False até o schema real ser conhecido.
    """
    desconhecidos = {t for t in esquema.values() if t not in TIPOS_SUPORTADOS}
    if desconhecidos:
        raise ValueError(f"Tipos não suportados no esquema: {sorted(desconhecidos)}")

    rel = RelatorioTratamento(linhas_entrada=len(df))
    saida = padronizar_colunas(df)

    for coluna, tipo in esquema.items():
        if coluna not in saida.columns:
            rel.colunas_ausentes.append(coluna)
            continue
        bruto = saida[coluna]
        if tipo == "texto":
            saida[coluna] = _texto_preenchido(bruto)
            continue
        if tipo in {"sexo", "raca_cor"}:
            saida[f"{coluna}_original"] = bruto
            norm = normalizar_sexo(bruto) if tipo == "sexo" else normalizar_raca_cor(bruto)
            saida[coluna] = norm
            nm = categorias_nao_mapeadas(bruto, norm)
            if nm:
                rel.nao_mapeados[coluna] = nm
            continue
        if tipo == "inteiro":
            valores, inval = converter_inteiro(bruto)
        elif tipo == "ano":
            valores, inval = validar_ano(bruto, ano_minimo, ano_maximo)
        elif tipo == "data":
            valores, inval = converter_data(bruto)
        else:  # monetario
            valores, inval = converter_monetario(bruto)
        saida[coluna] = valores
        rel.invalidos_por_coluna[coluna] = int(inval.sum())

    if remover_duplicatas:
        saida, rel.duplicatas_removidas = remover_duplicatas_exatas(saida)

    if descartar_identificadores:
        saida, rel.identificadores_descartados = remover_identificadores(saida)

    rel.linhas_saida = len(saida)
    rel.nulos_por_coluna = {c: int(n) for c, n in saida.isna().sum().items() if n}
    log.info(
        "Tratamento: %d → %d linhas; duplicatas removidas=%d; inválidos=%s",
        rel.linhas_entrada, rel.linhas_saida, rel.duplicatas_removidas, rel.invalidos_por_coluna,
    )
    return saida, rel

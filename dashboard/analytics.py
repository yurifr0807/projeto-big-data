"""Indicadores descritivos ponderados e regras mínimas de divulgação.

As verificações de k=5 reduzem exposição em uma exibição isolada, mas NÃO
eliminam ataques por diferenças entre consultas e filtros dinâmicos. Uma
publicação irrestrita exige revisão adicional de privacidade (ver documentação).
"""
from __future__ import annotations

from collections import defaultdict
from typing import Iterable, Mapping

MIN_GROUP = 5
MISSING = {"", "não informado", "não desejo declarar", "não mapeado", "ignorado", "não se aplica"}


def known(value: object) -> bool:
    return value is not None and str(value).strip().casefold() not in MISSING


def number(rows: Iterable[Mapping], key: str = "n") -> int:
    return sum(int(row.get(key) or 0) for row in rows)


def percentage(num: int, den: int, minimum: int = MIN_GROUP) -> float | None:
    """Suprime taxa se numerador ou complemento positivo ficar abaixo de k."""
    if den < minimum or num < 0 or num > den:
        return None
    if 0 < num < minimum or 0 < den - num < minimum:
        return None
    return round(100 * num / den, 1)


def kpis(sex_rows: list[Mapping], race_rows: list[Mapping], cross_rows: list[Mapping]) -> dict:
    total = number(sex_rows)
    known_sex = number(r for r in sex_rows if known(r.get("sexo")))
    women = number(r for r in sex_rows if str(r.get("sexo")) == "Feminino")
    known_race = number(r for r in race_rows if known(r.get("cor_ou_raca")))
    black_brown = number(r for r in race_rows if r.get("cor_ou_raca") in {"Preta", "Parda"})
    known_both = number(r for r in cross_rows if known(r.get("sexo")) and known(r.get("cor_ou_raca")))
    women_black_brown = number(
        r for r in cross_rows
        if r.get("sexo") == "Feminino" and r.get("cor_ou_raca") in {"Preta", "Parda"}
    )
    pq_total = number(cross_rows, "n_pq")
    return {
        "total": total if total >= MIN_GROUP else None,
        "female_pct": percentage(women, known_sex),
        "female_known": known_sex if known_sex >= MIN_GROUP else None,
        "female_coverage": percentage(known_sex, total),
        "black_brown_pct": percentage(black_brown, known_race),
        "race_known": known_race if known_race >= MIN_GROUP else None,
        "race_coverage": percentage(known_race, total),
        "intersect_pct": percentage(women_black_brown, known_both),
        "both_known": known_both if known_both >= MIN_GROUP else None,
        "pq_pct": percentage(pq_total, total),
        "pq_count": pq_total if pq_total >= MIN_GROUP and (total - pq_total >= MIN_GROUP or total == pq_total) else None,
    }


def safe_distribution(rows: Iterable[Mapping], label: str, *, skip_missing: bool = True) -> tuple[list[dict], bool]:
    """Não mostra distribuição se uma célula positiva ficar abaixo de k.

    O gráfico inteiro é retido, não apenas a célula, evitando recuperação
    imediata por subtração do total do gráfico.
    """
    counts: dict[str, int] = defaultdict(int)
    for row in rows:
        value = row.get(label)
        if skip_missing and not known(value):
            continue
        counts[str(value)] += int(row.get("n") or 0)
    if any(0 < n < MIN_GROUP for n in counts.values()) or sum(counts.values()) < MIN_GROUP:
        return [], True
    return ([{"categoria": k, "pessoas": v} for k, v in sorted(counts.items(), key=lambda pair: -pair[1])], False)


def safe_cross(rows: Iterable[Mapping]) -> tuple[list[dict], bool]:
    counts = defaultdict(int)
    for row in rows:
        sex, race = row.get("sexo"), row.get("cor_ou_raca")
        if known(sex) and known(race):
            counts[(str(sex), str(race))] += int(row.get("n") or 0)
    if not counts or any(0 < n < MIN_GROUP for n in counts.values()):
        return [], True
    return ([{"sexo": s, "raça/cor": r, "pessoas": n} for (s, r), n in sorted(counts.items())], False)


def safe_pq_by_sex(rows: Iterable[Mapping]) -> tuple[list[dict], bool]:
    output = []
    for row in rows:
        sex = row.get("sexo")
        if not known(sex):
            continue
        n, n_pq = int(row.get("n") or 0), int(row.get("n_pq") or 0)
        rate = percentage(n_pq, n)
        if rate is None:
            return [], True  # Não publica o complemento por diferença.
        output.append({"sexo": str(sex), "presença de PQ (%)": rate})
    return (output, not bool(output))

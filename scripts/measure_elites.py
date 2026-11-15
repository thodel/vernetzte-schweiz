"""Messung der Kandidaten Elites suisses ↔ Einheit über Name und Lebensjahre (scripts/elites_match.py).

    python scripts/measure_elites.py draw    # → data/review/elites_kandidaten.csv (Seed 30, je Stufe 20)
    python scripts/measure_elites.py draw 2  # → elites_kandidaten_2.csv (Seed 31, ohne Paare aus Messung 1)
    python scripts/measure_elites.py         # → data/norm/elites_quality.json

Messung 2 (Seed 31) wurde gezogen, nachdem drei Fehlerarten aus Messung 1 ausgeschlossen waren
(zweiter Vorname anders, Witwe unter Männername, erst mit über 75 im Buch).

Zu jedem Paar: Name, Lebensjahre und Gremien (mit Rolle und Jahren) aus den Elites suisses,
dazu Gemeinde, Jahre und Berufsfeld der Einheit. Urteil: `richtig` (dieselbe Person),
`falsch` (eine andere Person), `unklar`. Die Spanne zählt «unklar» einmal als falsch und
einmal als richtig.
"""

from __future__ import annotations

import csv
import json
import random
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import NORM, ROOT, open_csv, write_csv  # noqa: E402

REVIEWS = {1: ROOT / "data" / "review" / "elites_kandidaten.csv", 2: ROOT / "data" / "review" / "elites_kandidaten_2.csv"}
SEEDS = {1: 30, 2: 31}
TIERS = ("wahrscheinlich", "möglich", "schwach")
FIELDS = ["nr", "stufe", "entity_id", "es_id", "es_qid", "es", "gremien", "einheit", "berufsfeld", "why", "urteil", "begruendung"]
N = 20


def draw(nr: int = 1) -> None:
    seen = {(r["entity_id"], r["es_id"]) for k, p in REVIEWS.items() if k < nr and p.exists() for r in open_csv(p)}
    cands = [c for c in open_csv(NORM / "elites_candidates.csv.gz") if (c["entity_id"], c["es_id"]) not in seen]
    groups: dict[str, list] = defaultdict(list)
    for m in open_csv(NORM / "elites_suisses_mitglied.csv.gz"):
        groups[m["es_id"]].append(f"{m['role'] + ' ' if m['role'] else ''}{m['group']} {m['start']}–{m['end']}".strip())
    ents = {e["entity_id"]: e for e in open_csv(NORM / "entities.csv.gz") if e["entity_id"] in {c["entity_id"] for c in cands}}
    rnd = random.Random(SEEDS[nr])
    out = []
    for tier in TIERS:
        pool = [c for c in cands if c["tier"] == tier]
        for c in rnd.sample(pool, min(N, len(pool))):
            e = ents[c["entity_id"]]
            out.append({"nr": f"{len(out) + 1:03d}", "stufe": tier, "entity_id": c["entity_id"], "es_id": c["es_id"],
                        "es_qid": c["es_qid"], "es": f"{c['es_name']} ({c['birth']}–{c['death']})",
                        "gremien": " | ".join(groups.get(c["es_id"], []))[:400],
                        "einheit": f"{e['surname']}, {e['forename']} · {e['municipality']} {e['first_year']}–{e['last_year']}",
                        "berufsfeld": e["occupations"][:200], "why": c["why"], "urteil": "", "begruendung": ""})
    write_csv(REVIEWS[nr], FIELDS, out)
    print(f"{REVIEWS[nr].relative_to(ROOT)}: {len(out)} Paare")


def report() -> None:
    out = {}
    for nr, path in REVIEWS.items():
        if path.exists():
            print(f"Messung {nr}")
            out[f"messung_{nr}"] = report_one(list(csv.DictReader(open(path, encoding="utf-8"))))
    (NORM / "elites_quality.json").write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n")


def report_one(rows: list[dict]) -> dict:
    res = {}
    for tier in TIERS:
        c = Counter(r["urteil"] for r in rows if r["stufe"] == tier)
        n = sum(c.values())
        if not n:
            continue
        res[tier] = {"n": n, **c, "precision_low": round(c["richtig"] / n, 3), "precision_high": round((c["richtig"] + c["unklar"]) / n, 3)}
        print(f"{tier:15} n={n:3} richtig {c['richtig']:3} falsch {c['falsch']:3} unklar {c['unklar']:3} → "
              f"{c['richtig'] / n:.0%}–{(c['richtig'] + c['unklar']) / n:.0%}")
    return res


if __name__ == "__main__":
    draw(int(sys.argv[2]) if len(sys.argv) > 2 else 1) if sys.argv[1:2] == ["draw"] else report()

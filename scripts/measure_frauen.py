"""Messung des Experiments «Wege von Frauen» (scripts/frauen_wege.py, docs/frauen_wege.md).

    python scripts/measure_frauen.py draw   # → data/review/frauen_wege.csv (Seed 40)
    python scripts/measure_frauen.py        # → data/norm/frauen_wege_quality.json

Gruppen: Ehemann → Witwe 15, Ehefrau → Witwe 15, ledig → verheiratet in derselben Gemeinde 15 und
in einer anderen 10, ledig → Witwe 10. Zu jedem Paar die gedruckten Einträge beider Spuren.
Urteil: `richtig` (dieselbe Frau bzw. ihr Mann), `falsch`, `unklar`.
"""
from __future__ import annotations

import csv
import json
import random
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import NORM, ROOT, open_csv, write_csv  # noqa: E402

REVIEW = ROOT / "data" / "review" / "frauen_wege.csv"
GROUPS = [("mann→witwe", None, 15), ("verheiratet→witwe", None, 15), ("ledig→verheiratet", True, 15),
          ("ledig→verheiratet", False, 10), ("ledig→witwe", None, 10)]


def group(r: dict) -> str:
    same = r["von_gemeinde"] == r["nach_gemeinde"]
    return r["typ"] + ("" if r["typ"] != "ledig→verheiratet" else (" (gleiche Gemeinde)" if same else " (andere Gemeinde)"))


def draw() -> None:
    rows = open_csv(ROOT / "links" / "frauen_wege.csv")
    rnd = random.Random(40)
    out = []
    for typ, same, n in GROUPS:
        pool = [r for r in rows if r["typ"] == typ and (same is None or (r["von_gemeinde"] == r["nach_gemeinde"]) == same)]
        for r in rnd.sample(pool, min(n, len(pool))):
            out.append({"nr": f"{len(out) + 1:03d}", "gruppe": group(r), **r, "urteil": "", "begruendung": ""})
    write_csv(REVIEW, ["nr", "gruppe", *open_csv(ROOT / "links" / "frauen_wege.csv")[0].keys(), "urteil", "begruendung"], out)
    print(f"{REVIEW.relative_to(ROOT)}: {len(out)} Paare")


def report() -> None:
    rows = list(csv.DictReader(open(REVIEW, encoding="utf-8")))
    res = {}
    for g in dict.fromkeys(r["gruppe"] for r in rows):
        c = Counter(r["urteil"] for r in rows if r["gruppe"] == g)
        n = sum(c.values())
        res[g] = {"n": n, **c, "precision_low": round(c["richtig"] / n, 3), "precision_high": round((c["richtig"] + c["unklar"]) / n, 3)}
        print(f"{g:40} n={n:3} richtig {c['richtig']:3} falsch {c['falsch']:3} unklar {c['unklar']:3} → "
              f"{c['richtig'] / n:.0%}–{(c['richtig'] + c['unklar']) / n:.0%}")
    (NORM / "frauen_wege_quality.json").write_text(json.dumps(res, ensure_ascii=False, indent=1) + "\n")


if __name__ == "__main__":
    draw() if sys.argv[1:2] == ["draw"] else report()

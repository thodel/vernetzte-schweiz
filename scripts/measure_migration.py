"""M10: Messung der Wanderungs-Kandidaten (scripts/migration.py).

    python scripts/measure_migration.py draw 2   # Stichprobe 2 ziehen → data/review/m10_wanderungen_2.csv
    python scripts/measure_migration.py          # auswerten → data/norm/migration_quality.json

Stichprobe 1 (Seed 10): je Stufe 40 zufällige Paare, gezogen nach den ersten Regeln; danach
wurden die Regeln angepasst. Stichprobe 2 (Seed 11): je Stufe bis zu 40 Paare, die nicht in
Stichprobe 1 standen, gezogen nach dem letzten Regelwechsel: die Messung. Zu jedem Paar
stehen die letzten zwei Einträge am alten und die ersten zwei am neuen Ort, wie gedruckt
(Telefonbuch: Name, Zusatz, Strasse, Nummer, Ortsüberschrift; Adressbuch: die Zeile).
Urteil: `richtig` (dieselbe Person, anderer Wohn- oder Geschäftsort), `falsch` (andere
Person, oder dieselbe Zeile unter falschem Ort), `unklar`. Die Spanne zählt «unklar» einmal
als falsch und einmal als richtig.
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

REVIEW = {1: ROOT / "data" / "review" / "m10_wanderungen.csv", 2: ROOT / "data" / "review" / "m10_wanderungen_2.csv"}
SEEDS = {1: 10, 2: 11}
FIELDS = ["nr", "stufe", "from_entity", "to_entity", "von", "nach", "km", "evidence", "a_text", "b_text", "urteil", "begruendung"]
N = 40


def texts(ids: set[str]) -> dict[str, list[tuple[int, str]]]:
    """Je Einheit ihre Einträge als (Jahr, gedruckter Text)."""
    rec_ent = {r["record_id"]: r["entity_id"] for r in open_csv(ROOT / "links" / "entities.csv.gz") if r["entity_id"] in ids}
    out: dict[str, list] = defaultdict(list)
    for r in open_csv(NORM / "ptt_entries.csv.gz"):
        e = rec_ent.get(r["id"])
        if e:
            parts = [f"{r['name1']}, {r['name2']}".strip(", "), r["supplement"], r["street"], f"Nr {r['phone']}" if r["phone"] else "",
                     f"[{r['place_name']}]"]
            out[e].append((int(r["year"]), f"{r['year']} TB " + " | ".join(p for p in parts if p)))
    for r in open_csv(NORM / "ab_entries.csv"):
        e = rec_ent.get(r["id"])
        if e:
            out[e].append((int(r["volume"][:4]), f"{r['volume'][:4]} AB {r['city']}: {r['text']}"))
    return out


def draw(nr: int) -> None:
    rows = open_csv(ROOT / "links" / "migration.csv")
    seen = {(r["from_entity"], r["to_entity"]) for k, p in REVIEW.items() if k < nr and p.exists() for r in open_csv(p)}
    rnd = random.Random(SEEDS[nr])
    pick = []
    for tier in ("stark", "mittel", "schwach"):
        pool = [r for r in rows if r["tier"] == tier and (r["from_entity"], r["to_entity"]) not in seen]
        pick += rnd.sample(pool, min(N, len(pool)))
    t = texts({r["from_entity"] for r in pick} | {r["to_entity"] for r in pick})
    out = []
    for i, r in enumerate(pick, 1):
        a = sorted(t[r["from_entity"]])[-2:]
        b = sorted(t[r["to_entity"]])[:2]
        out.append({"nr": f"{i:03d}", "stufe": r["tier"], "from_entity": r["from_entity"], "to_entity": r["to_entity"],
                    "von": f"{r['from_muni']} {r['from_last']}", "nach": f"{r['to_muni']} {r['to_first']}", "km": r["km"],
                    "evidence": r["evidence"], "a_text": " ‖ ".join(x for _, x in a), "b_text": " ‖ ".join(x for _, x in b),
                    "urteil": "", "begruendung": ""})
    write_csv(REVIEW[nr], FIELDS, out)
    print(f"{REVIEW[nr].relative_to(ROOT)}: {len(out)} Paare")


def report() -> None:
    out = {}
    for nr, path in REVIEW.items():
        if path.exists():
            print(f"Stichprobe {nr}" + (" (Regeln danach angepasst)" if nr == 1 else ""))
            out[f"stichprobe_{nr}"] = report_one(list(csv.DictReader(open(path, encoding="utf-8"))))
    (NORM / "migration_quality.json").write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n")


def report_one(rows: list[dict]) -> dict:
    res = {}
    for tier in ("stark", "mittel", "schwach"):
        c = Counter(r["urteil"] for r in rows if r["stufe"] == tier)
        n = sum(c.values())
        res[tier] = {"n": n, **c, "precision_low": round(c["richtig"] / n, 3) if n else None,
                     "precision_high": round((c["richtig"] + c["unklar"]) / n, 3) if n else None}
        if not n:
            continue
        print(f"  {tier:8} n={n:3} richtig {c['richtig']:3} falsch {c['falsch']:3} unklar {c['unklar']:3} → "
              f"{res[tier]['precision_low']:.0%}–{res[tier]['precision_high']:.0%}")
    return res


if __name__ == "__main__":
    draw(int(sys.argv[2])) if sys.argv[1:2] == ["draw"] else report()

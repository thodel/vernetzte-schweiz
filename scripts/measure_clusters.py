"""Güte der Bündelung (M3) → data/norm/cluster_quality.json.

    python scripts/measure_clusters.py

Grundlage sind die von Hand beurteilten Stichproben in data/review/m3_stichprobe.csv.
Stichproben 1–4 dienten zum Einstellen der Regeln; Stichprobe 5 wurde nach dem letzten
Regelwechsel gezogen und ist die Messung.

Schichten:
- `person_tb`, `person_ab`, `firma`: zwei zufällige Einträge einer zufälligen Einheit mit
  mindestens zwei Einträgen. Urteil richtig / falsch / unklar → **Präzision**.
- `lang`: erster und letzter Eintrag einer Einheit über mindestens 10 Jahre → Präzision
  dort, wo Vater und Sohn am ehesten verwechselt werden.
- `nur_nummer`: Kanten, die allein auf gleicher Nummer beruhen.
- `naechste_ausgabe`: ein zufälliger Telefonbuch-Eintrag gegen die nächste Ausgabe derselben
  Gemeinde (höchstens 3 Jahre später). verknüpft / verpasst / unklar / fehlt →
  **Vollständigkeit** = verknüpft unter denen, die wieder vorkommen.
- `getrennt`: Paare, die getrennt blieben, obwohl Name, Nummer oder Strasse passen; zeigt,
  welche Fälle die Regeln verfehlen (kein Anteil an allen Einheiten).
«unklar» wird als Spanne berichtet.
"""

from __future__ import annotations

import csv
import json
from collections import Counter

from common import NORM, ROOT

REVIEW = ROOT / "data" / "review" / "m3_stichprobe.csv"
MEASURED = "5"


def summarise(rows: list[dict]) -> list[dict]:
    out = []
    for sample in sorted({r["stichprobe"] for r in rows}):
        for layer in dict.fromkeys(r["schicht"] for r in rows if r["stichprobe"] == sample):
            c = Counter(r["urteil"] for r in rows if r["stichprobe"] == sample and r["schicht"] == layer)
            n = sum(c.values())
            row = {"sample": sample, "layer": layer, "n": n, "counts": dict(c), "measured": sample == MEASURED}
            if layer == "naechste_ausgabe":
                base = c["verknüpft"] + c["verpasst"] + c["unklar"]
                row["recall_low"] = round(c["verknüpft"] / base, 3) if base else None
                row["recall_high"] = round((c["verknüpft"] + c["unklar"]) / base, 3) if base else None
            elif layer == "getrennt":
                row["should_merge"] = round(c["gleich"] / n, 3)
            else:
                row["precision_low"] = round(c["richtig"] / n, 3)
                row["precision_high"] = round((c["richtig"] + c["unklar"]) / n, 3)
            out.append(row)
    return out


def main() -> None:
    rows = list(csv.DictReader(open(REVIEW, encoding="utf-8")))
    q = summarise(rows)
    (NORM / "cluster_quality.json").write_text(json.dumps(q, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    for r in q:
        extra = {k: v for k, v in r.items() if k.startswith(("precision", "recall", "should"))}
        print(f"Stichprobe {r['sample']}{'*' if r['measured'] else ' '} {r['layer']:17} n={r['n']:3} {r['counts']} {extra}")


if __name__ == "__main__":
    main()

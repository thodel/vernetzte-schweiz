"""Messung der Berufsübersetzung in der Suche (docs/berufssuche.md).

    python scripts/measure_berufe.py draw    # Stichproben ziehen → data/review/berufe_*.csv
    python scripts/measure_berufe.py         # auswerten → data/norm/berufe_quality.json

Zwei Stichproben, gezogen aus den Daten der Seite (site/data, nach build_pages.py und
build_maps.py):

1. **Zuordnung** (`berufe_zuordnung.csv`, Seed 20): 80 zufällige Paare (Einheit, Beruf) aus
   allen Zuordnungen der feinen Liste (`fk/`). Frage: Nennt das Berufsfeld diesen Beruf?
2. **Gewinn** (`berufe_gewinn.csv`, Seed 21): für fünf Suchwörter je 12 Treffer, die nur
   die Übersetzung findet, nicht der Wortlaut. Frage: Hat der Treffer den gesuchten Beruf?
   Das ist, was jemand sieht, der «Übersetzungen mitsuchen» einschaltet.

Urteil: `richtig`, `falsch`, `unklar`. Die Spanne zählt «unklar» einmal als falsch und
einmal als richtig.
"""

from __future__ import annotations

import csv
import gzip
import json
import random
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_pages import fold  # noqa: E402
from common import NORM, ROOT, write_csv  # noqa: E402

DATA = ROOT / "site" / "data"
REVIEW = ROOT / "data" / "review"
FILES = {"zuordnung": REVIEW / "berufe_zuordnung.csv", "gewinn": REVIEW / "berufe_gewinn.csv"}
QUERIES = ["Metzger", "Uhrmacher", "boulanger", "instituteur", "Schreiner"]
FIELDS = ["nr", "frage", "suchwort", "beruf", "entity_id", "name", "gemeinde", "berufsfeld", "urteil", "begruendung"]


def load(path: Path):
    return json.loads(gzip.open(path, "rt", encoding="utf-8").read()) if path.suffix == ".gz" else json.loads(path.read_text())


def keys_of(word: str, vocab: dict) -> list[int]:
    """Wie occKeysOf() in site/assets/pages.js."""
    w = fold(word)
    if w in vocab:
        return vocab[w]
    c: Counter = Counter()
    for x, ks in vocab.items():
        if x.startswith(w):
            c.update(ks)
    top = max(c.values(), default=0)
    return [k for k, v in c.items() if v >= top / 4]


def wording_ids(word: str) -> set[str]:
    """Treffer nach Wortlaut, wie die Berufssuche (ow/: Wörter, die so beginnen)."""
    w = fold(word)
    shard = load(DATA / "ow" / f"{w[:1]}.json.gz")
    return {i for x, ids in shard["w"].items() if x.startswith(w) for i in ids}


def draw() -> None:
    B = load(DATA / "berufe.json")
    label = lambda i: B["k"][i][2]  # noqa: E731
    fk = {int(p.name.split(".")[0]): load(p) for p in (DATA / "fk").glob("*.json.gz")}
    places = [p[0] for p in load(DATA / "maps.json.gz")["places"]]
    full = {}  # ganzes Berufsfeld, nicht die gekürzte Zeile der Seite
    for r in csv.DictReader(gzip.open(NORM / "entities.csv.gz", "rt", encoding="utf-8")):
        full[r["entity_id"]] = r["occupations"]

    def row(nr, frage, q, k, eid):
        name, p = fk[k][eid][0], fk[k][eid][1]
        return {"nr": nr, "frage": frage, "suchwort": q, "beruf": label(k), "entity_id": eid, "name": name,
                "gemeinde": places[p], "berufsfeld": full.get(eid, fk[k][eid][4])[:300], "urteil": "", "begruendung": ""}

    rnd = random.Random(20)
    pairs = sorted((k, eid) for k, rows in fk.items() for eid in rows)
    out = [row(f"{i:03d}", "zuordnung", "", k, eid) for i, (k, eid) in enumerate(rnd.sample(pairs, 80), 1)]
    write_csv(FILES["zuordnung"], FIELDS, out)
    print(f"{FILES['zuordnung'].relative_to(ROOT)}: {len(out)} Paare aus {len(pairs)} Zuordnungen")

    rnd = random.Random(21)
    out, stats = [], {}
    for q in QUERIES:
        ks = keys_of(q, B["v"])
        found = wording_ids(q)
        added = sorted({(k, e) for k in ks for e in fk.get(k, {}) if e not in found}, key=lambda x: x[1])
        uniq = {}
        for k, e in added:
            uniq.setdefault(e, k)
        stats[q] = {"beruf": [label(k) for k in ks], "wortlaut": len(found), "nur_uebersetzung": len(uniq)}
        for e in rnd.sample(sorted(uniq), min(12, len(uniq))):
            out.append(row(f"{len(out) + 1:03d}", "gewinn", q, uniq[e], e))
    write_csv(FILES["gewinn"], FIELDS, out)
    print(f"{FILES['gewinn'].relative_to(ROOT)}: {len(out)} Treffer; {json.dumps(stats, ensure_ascii=False)}")
    (NORM / "berufe_gewinn_umfang.json").write_text(json.dumps(stats, ensure_ascii=False, indent=1) + "\n")


def report() -> None:
    res = {}
    for name, path in FILES.items():
        rows = list(csv.DictReader(open(path, encoding="utf-8")))
        groups = {"alle": rows}
        if name == "gewinn":
            groups.update({q: [r for r in rows if r["suchwort"] == q] for q in QUERIES})
        res[name] = {}
        for g, rs in groups.items():
            c = Counter(r["urteil"] for r in rs)
            n = sum(c.values())
            res[name][g] = {"n": n, **c, "precision_low": round(c["richtig"] / n, 3), "precision_high": round((c["richtig"] + c["unklar"]) / n, 3)}
            print(f"{name:10} {g:12} n={n:3} richtig {c['richtig']:3} falsch {c['falsch']:3} unklar {c['unklar']:3} → "
                  f"{c['richtig'] / n:.0%}–{(c['richtig'] + c['unklar']) / n:.0%}")
    (NORM / "berufe_quality.json").write_text(json.dumps(res, ensure_ascii=False, indent=1) + "\n")


if __name__ == "__main__":
    draw() if sys.argv[1:2] == ["draw"] else report()

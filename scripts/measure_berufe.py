"""Messung der Berufsübersetzung in der Suche (docs/berufssuche.md).

    python scripts/measure_berufe.py draw    # Stichproben ziehen → data/review/berufe_*.csv
    python scripts/measure_berufe.py draw2   # Runde 2 (nach Glaser, Viehhändler) → berufe_gewinn_2.csv
    python scripts/measure_berufe.py         # auswerten → data/norm/berufe_quality.json

Zwei Stichproben, gezogen aus den Daten der Seite (site/data, nach build_pages.py und
build_maps.py):

1. **Zuordnung** (`berufe_zuordnung.csv`, Seed 20): 80 zufällige Paare (Einheit, Beruf) aus
   allen Zuordnungen der feinen Liste (`fk/`). Frage: Nennt das Berufsfeld diesen Beruf?
2. **Gewinn** (`berufe_gewinn.csv`, Seed 21): für fünf Suchwörter je 12 Treffer, die nur
   die Übersetzung findet, nicht der Wortlaut. Frage: Hat der Treffer den gesuchten Beruf?
   Das ist, was jemand sieht, der «Übersetzungen mitsuchen» einschaltet.

**Runde 2** (`berufe_gewinn_2.csv`, Seed 22), nachdem Glaser, Vieh- und Pferdehändler und
Viehinspektor eigene Berufe wurden: je 12 neue Treffer, die nur die Übersetzung findet, für
«Metzger» und «Schreiner» (ohne die in Runde 1 beurteilten Einheiten) und für die neuen Berufe
«Glaser» und «Viehhändler». Die Auswertung rechnet Runde 1 zudem nach den neuen Regeln nach
(nur als Prüfung): Welche beurteilten Treffer fände die Suche noch?

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
FILES = {"zuordnung": REVIEW / "berufe_zuordnung.csv", "gewinn": REVIEW / "berufe_gewinn.csv",
         "gewinn_2": REVIEW / "berufe_gewinn_2.csv"}
QUERIES = ["Metzger", "Uhrmacher", "boulanger", "instituteur", "Schreiner"]
QUERIES_2 = ["Metzger", "Schreiner", "Glaser", "Viehhändler"]
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

    draw_gain(B, fk, row, QUERIES, 21, "gewinn", set(), "berufe_gewinn_umfang.json")


def draw_gain(B, fk, row, queries, seed, name, skip, stats_file) -> None:
    label = lambda i: B["k"][i][2]  # noqa: E731
    rnd = random.Random(seed)
    out, stats = [], {}
    for q in queries:
        ks = keys_of(q, B["v"])
        found = wording_ids(q)
        added = sorted({(k, e) for k in ks for e in fk.get(k, {}) if e not in found}, key=lambda x: x[1])
        uniq = {}
        for k, e in added:
            uniq.setdefault(e, k)
        stats[q] = {"beruf": [label(k) for k in ks], "wortlaut": len(found), "nur_uebersetzung": len(uniq)}
        pool = sorted(e for e in uniq if (q, e) not in skip)
        for e in rnd.sample(pool, min(12, len(pool))):
            out.append(row(f"{len(out) + 1:03d}", "gewinn", q, uniq[e], e))
    write_csv(FILES[name], FIELDS, out)
    print(f"{FILES[name].relative_to(ROOT)}: {len(out)} Treffer; {json.dumps(stats, ensure_ascii=False)}")
    (NORM / stats_file).write_text(json.dumps(stats, ensure_ascii=False, indent=1) + "\n")


def draw2() -> None:
    B = load(DATA / "berufe.json")
    fk = {int(p.name.split(".")[0]): load(p) for p in (DATA / "fk").glob("*.json.gz")}
    places = [p[0] for p in load(DATA / "maps.json.gz")["places"]]
    full = {r["entity_id"]: r["occupations"] for r in csv.DictReader(gzip.open(NORM / "entities.csv.gz", "rt", encoding="utf-8"))}

    def row(nr, frage, q, k, eid):
        return {"nr": nr, "frage": frage, "suchwort": q, "beruf": B["k"][k][2], "entity_id": eid, "name": fk[k][eid][0],
                "gemeinde": places[fk[k][eid][1]], "berufsfeld": full.get(eid, fk[k][eid][4])[:300], "urteil": "", "begruendung": ""}
    skip = {(r["suchwort"], r["entity_id"]) for r in csv.DictReader(open(FILES["gewinn"], encoding="utf-8"))}
    draw_gain(B, fk, row, QUERIES_2, 22, "gewinn_2", skip, "berufe_gewinn_umfang_2.json")


def recheck() -> dict:
    """Runde 1 nach den heutigen Regeln: welche beurteilten Zuordnungen und Treffer bleiben?"""
    B = load(DATA / "berufe.json")
    key = {k[0]: i for i, k in enumerate(B["k"])}
    lab = {k[2]: k[0] for k in B["k"]}
    fk = {int(p.name.split(".")[0]): set(load(p)) for p in (DATA / "fk").glob("*.json.gz")}
    res = {}
    rows = list(csv.DictReader(open(FILES["zuordnung"], encoding="utf-8")))
    keep = [r for r in rows if r["beruf"] in lab and r["entity_id"] in fk.get(key[lab[r["beruf"]]], set())]
    res["zuordnung"] = Counter(r["urteil"] for r in keep)
    rows = list(csv.DictReader(open(FILES["gewinn"], encoding="utf-8")))
    res["gewinn"] = {}
    for q in QUERIES:
        ks = keys_of(q, B["v"])
        found = wording_ids(q)
        keep = [r for r in rows if r["suchwort"] == q and r["entity_id"] not in found and any(r["entity_id"] in fk.get(k, set()) for k in ks)]
        res["gewinn"][q] = Counter(r["urteil"] for r in keep)
    return res


def report() -> None:
    res = {}
    for name, path in FILES.items():
        if not path.exists():
            continue
        rows = list(csv.DictReader(open(path, encoding="utf-8")))
        groups = {"alle": rows}
        if name.startswith("gewinn"):
            groups.update({q: [r for r in rows if r["suchwort"] == q] for q in (QUERIES if name == "gewinn" else QUERIES_2)})
        res[name] = {}
        for g, rs in groups.items():
            c = Counter(r["urteil"] for r in rs)
            n = sum(c.values())
            res[name][g] = {"n": n, **c, "precision_low": round(c["richtig"] / n, 3), "precision_high": round((c["richtig"] + c["unklar"]) / n, 3)}
            print(f"{name:10} {g:12} n={n:3} richtig {c['richtig']:3} falsch {c['falsch']:3} unklar {c['unklar']:3} → "
                  f"{c['richtig'] / n:.0%}–{(c['richtig'] + c['unklar']) / n:.0%}")
    chk = recheck()
    res["runde_1_nachgerechnet"] = {"zuordnung": dict(chk["zuordnung"]), "gewinn": {q: dict(c) for q, c in chk["gewinn"].items()}}
    for g, c in [("zuordnung", chk["zuordnung"]), *chk["gewinn"].items()]:
        n = sum(c.values())
        print(f"Runde 1 neu {g:12} n={n:3} richtig {c['richtig']:3} falsch {c['falsch']:3} unklar {c['unklar']:3}"
              + (f" → {c['richtig'] / n:.0%}–{(c['richtig'] + c['unklar']) / n:.0%}" if n else ""))
    (NORM / "berufe_quality.json").write_text(json.dumps(res, ensure_ascii=False, indent=1) + "\n")


if __name__ == "__main__":
    {"draw": draw, "draw2": draw2}.get(sys.argv[1] if sys.argv[1:] else "", report)()

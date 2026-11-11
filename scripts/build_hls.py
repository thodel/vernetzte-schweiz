"""M9: Vom HLS zum Eintrag → site/data/hls.json.gz und site/data/hls/<xx>.json.gz.

    python scripts/build_hls.py

Grundlage ist die umgekehrte Prüfung (`scripts/hls_coverage.py`, docs/hls_abdeckung.md):
`data/norm/hls_coverage.csv.gz` je HLS-Person und `data/norm/hls_candidates.csv.gz` je
Person und Einheit. Aus dem HLS kommen nur Name, Lebensdaten, Fachgebiet und die Nummer
für den Link, kein Artikeltext.

hls.json.gz (Liste, Suche, Übersicht):
- `fields`: Fachgebiete; `rows`: [HLS-Nummer, Name, Geburt, Tod, Geschlecht (m/f), Stufe,
  Grundlage, Kanton des ersten Ortes, erster Ort, Zahl der Kandidaten, Fachgebiete (Indizes)]

hls/<xx>.json.gz (64 Teile nach FNV der HLS-Nummer) je Person:
{n, b, d, g, f (Stufe), r (Grund bei «nicht gefunden»), s (Grundlage), a [erwachsen von, bis],
 p [[Gemeinde, von, bis, Quellen, [Jahre mit Buch]]],
 c [[Einheit, Name, Gemeinde, [Jahre], Stufe, Begründung, Beruf, ort/anderswo]]}
"""

from __future__ import annotations

import shutil
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from build_pages import OUT, dump, fnv  # noqa: E402
from common import NORM, open_csv  # noqa: E402

TIER_ORDER = {"normdaten": 0, "wahrscheinlich": 1, "möglich": 2, "schwach": 3, "anderswo": 4}


def main() -> None:
    cov = open_csv(NORM / "hls_coverage.csv.gz")
    cands: dict[str, list] = defaultdict(list)
    for c in open_csv(NORM / "hls_candidates.csv.gz"):
        cands[c["hls_id"]].append(c)
    ents = {s["entity_id"]: s for s in open_csv(NORM / "entities.csv.gz")}
    canton: dict[str, str] = {}
    for r in open_csv(NORM / "ptt_entries.csv.gz"):
        if r["municipality_1914"] and r["canton"]:
            canton.setdefault(r["municipality_1914"], r["canton"])
    for s in ents.values():
        if s["municipality"] and s["canton"]:
            canton.setdefault(s["municipality"], s["canton"])

    fields = sorted({f for r in cov for f in r["fields"].split("|") if f})
    fidx = {f: i for i, f in enumerate(fields)}
    rows, shards = [], defaultdict(dict)
    for r in cov:
        places = []
        for cell in r["places"].split(";"):
            muni, y0, y1, srcs, yrs = cell.split("|")
            places.append([muni, int(y0), int(y1), srcs, [int(y) for y in yrs.split(",") if y]])
        # Orte mit Ort und Jahr aus dem Text zuerst, dann nach Jahr
        places.sort(key=lambda p: ("text" not in p[3], p[1], p[0]))
        cs = []
        for c in sorted(cands.get(r["hls_id"], ()), key=lambda c: (TIER_ORDER.get(c["tier"], 9), c["entity_id"])):
            s = ents.get(c["entity_id"])
            if not s:
                continue
            label = s["name"] if s["kind"] == "firma" and s["name"] else \
                ", ".join(x for x in (s["surname"], s["forename"]) if x)
            yrs = sorted({int(y) for y in s["years"].split() if y.isdigit()})
            cs.append([c["entity_id"], label, s["municipality"], yrs, c["tier"], c["why"], s["occupations"][:90],
                       c["where"]])
        first = places[0][0] if places else ""
        b, d = int(r["birth"]), int(r["death"]) if r["death"] else 0
        g = "f" if r["gender"] == "f" else "m"
        n_here = sum(1 for c in cs if c[7] == "ort")
        rows.append([r["hls_id"], r["name"], b, d, g, r["found"], r["basis"], canton.get(first, ""), first, n_here,
                     [fidx[f] for f in r["fields"].split("|") if f in fidx]])
        shards[fnv(r["hls_id"], 0x3F)][r["hls_id"]] = {
            "n": r["name"], "b": b, "d": d, "g": g, "f": r["found"], "r": r["reason"], "s": r["basis"],
            "a": [int(r["adult_from"]), int(r["adult_to"])], "p": places, "c": cs[:40]}
    rows.sort(key=lambda x: x[1].split()[-1:] + [x[1]])
    shutil.rmtree(OUT / "hls", ignore_errors=True)
    for k, v in shards.items():
        dump(OUT / "hls" / f"{k}.json.gz", v)
    dump(OUT / "hls.json.gz", {"fields": fields, "rows": rows})
    print(f"site/data/hls.json.gz: {len(rows)} HLS-Personen; hls/: {len(shards)} Teile")


if __name__ == "__main__":
    main()

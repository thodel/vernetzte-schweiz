"""M8: Telefonbuch-Einträge zum Blättern und für die Volltextsuche → site/data/r/, ft/.

    python scripts/build_entries.py

Grundlage sind die Einträge (nicht die Einheiten), alle 638 701 Telefonbuch-Einträge bis
1914, auch die ohne sicheren Ort.

- `books.json` — je Kanton (bzw. «–» für Einträge ohne aufgelösten Ort, wie in der Übersicht
  Kanton × Jahr) und Jahr: Zahl der
  Einträge, Telefonbücher (Signaturen), Gemeinden. Die Zellen der Übersicht verweisen
  darauf.
- `r/<Kanton>-<Jahr>.json.gz` — die Einträge dieser Zelle in Lesereihenfolge:
  [Signatur (Index in `books`), Seite, Bild-Nr. (0 = unbekannt), Name, Namenzusatz,
  Zusatz, Strasse, Telefonnummer, Gemeinde 1914, Einheit].
- `ft/<xx>.json.gz` — Volltext: je Feld und Wort die Fundstellen. Schlüssel «Feld:Wort» mit Feld n (Name), v (Vorname/Namenzusatz),
  b (Beruf/Zusatz), s (Strasse), o (Ort), t (Telefonnummer); Fundstelle = Zelle × 100 000 +
  Zeile. Wörter ohne Akzente, klein, ab 2 Zeichen. Teil = FNV des Wortes, 64 Teile.
- `vocab.json.gz` — alle Wörter mit ihren Feldern, für die ungefähre Suche.

Seitenbilder: Für Charge A (bis 1910) ist die Bild-Nummer bekannt (`image` =
«telefonbuch_136» → IIIF «<Signatur>_0136»). Für Charge B (1911–1914) stimmt die Seite nicht
mit der Bild-Nummer überein (Versatz je Band unbekannt); dort bleibt sie 0.
"""

from __future__ import annotations

import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from build_pages import OUT, dump, fnv, fold  # noqa: E402
from common import NORM, ROOT, open_csv  # noqa: E402

FIELDS = {"n": ("name1",), "v": ("name2",), "b": ("supplement",), "s": ("street",), "o": ("municipality_1914", "locality"),
          "t": ("phone",)}
CELL = 100_000


def words(text: str, field: str) -> set[str]:
    if field == "t":
        d = re.sub(r"\D", "", text or "")
        return {d} if d else set()
    return {w for w in (fold(x) for x in re.findall(r"[A-Za-zÀ-ÿ]+", text or "")) if len(w) >= 2}


def main() -> None:
    member = {m["record_id"]: m["entity_id"] for m in open_csv(ROOT / "links" / "entities.csv.gz")}
    rows = open_csv(NORM / "ptt_entries.csv.gz")
    rows.sort(key=lambda r: (int(r["year"]), r["refcode"], int(r["seq"] or 0)))
    cells: dict[tuple[str, int], list] = defaultdict(list)
    for r in rows:
        kt = r["canton"] or "–"  # wie die Übersicht Kanton × Jahr (build_site.py)
        cells[(kt, int(r["year"]))].append(r)
    refs: list[str] = sorted({r["refcode"] for r in rows})
    ref_idx = {x: i for i, x in enumerate(refs)}
    books, post = [], defaultdict(list)
    vocab: dict[str, set] = defaultdict(set)
    for ci, ((kt, year), rs) in enumerate(sorted(cells.items(), key=lambda x: (x[0][0] == "–", x[0][0], x[0][1]))):
        out = []
        for n, r in enumerate(rs):
            m = re.search(r"(\d+)$", r["image"] or "")
            img = int(m.group(1)) if (r["batch"] == "A" and m) else 0
            out.append([ref_idx[r["refcode"]], r["page"], img, r["name1"], r["name2"], r["supplement"], r["street"],
                        r["phone"], r["municipality_1914"] or r["locality"], member.get(r["id"], "")])
            for f, cols in FIELDS.items():
                for w in set().union(*(words(r[c], f) for c in cols)):
                    post[f"{f}:{w}"].append(ci * CELL + n)
                    vocab[w].add(f)
        dump(OUT / "r" / f"{kt}-{year}.json.gz", out)
        books.append({"kt": kt, "y": year, "n": len(rs), "refs": sorted({ref_idx[r["refcode"]] for r in rs}),
                      "munis": [m for m, _ in Counter(r["municipality_1914"] for r in rs if r["municipality_1914"]).most_common()]})
    shards: dict[str, dict] = defaultdict(dict)
    for key, ids in post.items():
        w = key.split(":", 1)[1]
        shards[fnv(w, 0x3F)][key] = ids
    for k, v in shards.items():
        dump(OUT / "ft" / f"{k}.json.gz", v)
    dump(OUT / "books.json", {"refs": refs, "cells": books})
    dump(OUT / "vocab.json.gz", sorted([w, "".join(sorted(f))] for w, f in vocab.items()))
    print(f"site/data: {len(rows)} Einträge in {len(cells)} Zellen (r/), {len(post)} Wörter je Feld in {len(shards)} "
          f"Teilen (ft/), Wortschatz {len(vocab)}")


if __name__ == "__main__":
    main()

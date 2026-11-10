"""Rohstufe der Telefonbücher anreichern → data/norm/ptt_entries.csv.gz.

.cache/ptt_raw.csv.gz (aus ingest_ptt.py) + Ortsauflösung (places.py) + Zerlegung der
Einträge (parse_ptt.py) → eine Tabelle, ein Eintrag je Zeile (Datenvertrag).
"""

from __future__ import annotations

import time

from common import NORM, ROOT, open_csv, write_csv
from places import PLACE_FIELDS, resolve_all

RAW = ROOT / ".cache" / "ptt_raw.csv.gz"
BASE = ["id", "batch", "seq", "year", "network", "refcode", "page", "image",
        "name1", "name2", "supplement", "street", "locality", "phone"]


def main() -> None:
    t = time.time()
    rows = open_csv(RAW)
    stats = resolve_all(rows)
    fields = BASE + [f for f in PLACE_FIELDS if f != "place_raw"]
    try:
        from parse_ptt import PARSE_FIELDS, parse_all
        stats.update(parse_all(rows))
        fields += PARSE_FIELDS
    except ImportError:
        pass
    write_csv(NORM / "ptt_entries.csv.gz", fields, rows)
    for k, v in sorted(stats.items()):
        print(f"{k:40} {v:>8}")
    print(f"{len(rows)} Zeilen in {time.time() - t:.0f} s")


if __name__ == "__main__":
    main()

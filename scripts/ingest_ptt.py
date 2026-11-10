"""Telefonbuch-Einträge der PTT (Charge A) → data/norm/ptt_entries.csv.

Liest den lokalen Checkout von DHBern/PTT_phonebook_data_tsv und bricht ab, wenn er nicht
auf dem Commit aus `config/sources.toml` steht. Übernommen werden die eintragsweise
aufbereiteten Dateien tsv/a/<RefCode>.tsv, Jahre im Zeitfenster; die alte seitenweise
Sammeldatei (a1*.tsv) nicht.
"""

from __future__ import annotations

import csv
import subprocess
import sys
from collections import Counter
from pathlib import Path

from common import NORM, config, in_window, write_csv

FIELDS = ["id", "year", "network", "refcode", "page", "image",
          "name1", "name2", "supplement", "street", "locality", "phone"]


def clean(v: str | None) -> str:
    return " ".join((v or "").split())


def main() -> None:
    cfg = config()
    ptt = cfg["ptt"]
    repo = Path(ptt["local"]).expanduser()
    head = subprocess.run(["git", "-C", str(repo), "rev-parse", "HEAD"],
                          capture_output=True, text=True, check=True).stdout.strip()
    if head != ptt["commit"]:
        sys.exit(f"PTT-Checkout steht auf {head[:12]}, gepinnt ist {ptt['commit'][:12]}. "
                 f"git -C {repo} checkout {ptt['commit'][:12]} oder sources.toml nachführen.")
    rows, stats = [], Counter()
    for path in sorted((repo / ptt["batch_a"]).glob("*.tsv")):
        stem = path.stem.strip()
        if not stem.startswith("P-260"):
            continue
        with open(path, newline="", encoding="utf-8-sig", errors="replace") as f:
            for n, r in enumerate(csv.DictReader(f, delimiter="\t", quoting=csv.QUOTE_NONE), start=1):
                year = clean(r.get("Year"))
                if not in_window(year, cfg):
                    stats["ausserhalb Zeitfenster"] += 1
                    continue
                if not (clean(r.get("EntityName1")) or clean(r.get("EntityName2"))):
                    stats["ohne Namen"] += 1
                    continue
                refcode = clean(r.get("RefCode")).removeprefix("PTT-Archiv,").strip() or stem
                rows.append({
                    "id": f"ptt:{stem}:{n}", "year": year, "network": clean(r.get("Network")),
                    "refcode": refcode, "page": clean(r.get("Page")), "image": clean(r.get("File")),
                    "name1": clean(r.get("EntityName1")), "name2": clean(r.get("EntityName2")),
                    "supplement": clean(r.get("Supplement")), "street": clean(r.get("Street")),
                    "locality": clean(r.get("Locality")), "phone": clean(r.get("PhoneNumber")),
                })
                stats["übernommen"] += 1
    write_csv(NORM / "ptt_entries.csv.gz", FIELDS, rows)
    for k, v in stats.most_common():
        print(f"{k:26} {v:>8}")
    print(f"Dateien: {len({r['refcode'] for r in rows})}, Netze: {len({r['network'] for r in rows})}")


if __name__ == "__main__":
    main()

"""Telefonbuch-Einträge der PTT → .cache/ptt_raw.csv.gz (Rohstufe für places.py, parse_ptt.py).

Liest den lokalen Checkout von DHBern/PTT_phonebook_data_tsv und bricht ab, wenn er nicht
auf dem Commit aus `config/sources.toml` steht. Übernommen werden
- Charge A: die eintragsweise aufbereiteten Dateien tsv/a/<RefCode>.tsv (nicht die alte
  seitenweise Sammeldatei a1*.tsv),
- Charge B: die Zeilen aus tsv/b*.tsv,
- Neulesungen: data/override/ptt/<Band>.tsv ersetzt alle Zeilen dieses Bandes aus Charge B (Spalten wie
  dort, dazu `Image` = Nummer des Seitenbilds); so gelesen ist Band 2c (Tessin) 1911 und 1912.
  Liegt daneben <Band>.ersetzt.txt (Zeilennummern der Quelle, einzeln oder als Spanne «5867-16604»), ersetzt
  die Neulesung nur diese Zeilen; die übrigen behalten ihre Id, die neu gelesenen zählen ab 100 001 (Band 2b
  1913 und 1914: alles nach dem Block Basel, docs/neulesung_2b.md),
jeweils Jahre im Zeitfenster. Die Zeilennummer `seq` zählt je Quelldatei (A) bzw. je
Band (`File`, B) in Lesereihenfolge, auch über Zeilen ohne Namen hinweg; sie ist Teil der Id.
"""

from __future__ import annotations

import csv
import os
import subprocess
import sys
from collections import Counter
from pathlib import Path

from common import config, in_window, write_csv

FIELDS = ["id", "batch", "seq", "year", "network", "refcode", "page", "image",
          "name1", "name2", "supplement", "street", "locality", "phone"]
ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / ".cache" / "ptt_raw.csv.gz"
PARTIAL_START = 100_001      # erste Zeilennummer neu gelesener Zeilen bei Teil-Ersatz


def clean(v: str | None) -> str:
    return " ".join((v or "").split())


def main() -> None:
    cfg = config()
    ptt = cfg["ptt"]
    repo = Path(os.environ.get("PTT_LOCAL") or ptt["local"]).expanduser()   # PTT_LOCAL: anderer Checkout am gepinnten Commit
    overrides = {p.stem: p for p in sorted((ROOT / ptt["overrides"]).glob("*.tsv"))} if ptt.get("overrides") else {}
    partial = {stem: replaced_rows(p.with_suffix(".ersetzt.txt")) for stem, p in overrides.items()
               if p.with_suffix(".ersetzt.txt").exists()}
    head = subprocess.run(["git", "-C", str(repo), "rev-parse", "HEAD"],
                          capture_output=True, text=True, check=True).stdout.strip()
    if head != ptt["commit"]:
        sys.exit(f"PTT-Checkout steht auf {head[:12]}, gepinnt ist {ptt['commit'][:12]}. "
                 f"git -C {repo} checkout {ptt['commit'][:12]} oder sources.toml nachführen.")
    rows, stats = [], Counter()

    def take(r: dict, batch: str, stem: str, n: int, refcode: str) -> None:
        year = clean(r.get("Year"))
        if not in_window(year, cfg):
            stats[f"{batch}: ausserhalb Zeitfenster"] += 1
            return
        if not (clean(r.get("EntityName1")) or clean(r.get("EntityName2"))):
            stats[f"{batch}: ohne Namen"] += 1
            return
        rows.append({
            "id": f"ptt:{stem}:{n}", "batch": batch, "seq": n, "year": year,
            "network": clean(r.get("Network")), "refcode": refcode, "page": clean(r.get("Page")),
            "image": clean(r.get("File")) if batch == "A" else clean(r.get("Image")),
            "name1": clean(r.get("EntityName1")), "name2": clean(r.get("EntityName2")),
            "supplement": clean(r.get("Supplement")), "street": clean(r.get("Street")),
            "locality": clean(r.get("Locality")), "phone": clean(r.get("PhoneNumber")),
        })
        stats[f"{batch}: übernommen"] += 1

    for path in sorted((repo / ptt["batch_a"]).glob("*.tsv")):
        stem = path.stem.strip()
        if not stem.startswith("P-260"):
            continue
        for n, r in enumerate(read_tsv(path), start=1):
            refcode = clean(r.get("RefCode")).removeprefix("PTT-Archiv,").strip() or stem
            take(r, "A", stem, n, refcode)

    for path in sorted(repo.glob(ptt["batch_b"])):
        counter: Counter = Counter()
        for r in read_tsv(path):
            stem = clean(r.get("File"))
            if stem in partial:
                counter[stem] += 1                      # Teil-Ersatz: Zählung der Quelle bleibt stehen
                if counter[stem] in partial[stem]:
                    stats["B: durch Neulesung ersetzt"] += 1
                    continue
            elif stem in overrides:
                stats["B: durch Neulesung ersetzt"] += 1
                continue
            else:
                counter[stem] += 1
            take(r, "B", stem, counter[stem], stem)
    for stem, path in overrides.items():
        for n, r in enumerate(read_tsv(path), start=PARTIAL_START if stem in partial else 1):
            take(r, "B", stem, n, stem)
            stats["B: aus Neulesung"] += 1

    write_csv(RAW, FIELDS, rows)
    for k, v in sorted(stats.items()):
        print(f"{k:30} {v:>8}")
    print(f"Bände/Dateien: {len({r['refcode'] for r in rows})} → {RAW.relative_to(RAW.parent.parent)}")


def replaced_rows(path: Path) -> set[int]:
    """Zeilennummern der Quelle, die eine Neulesung ersetzt: je Zeile eine Nummer oder eine Spanne «5867-16604»."""
    out: set[int] = set()
    for item in path.read_text(encoding="utf-8").split():
        a, _, b = item.partition("-")
        out.update(range(int(a), int(b or a) + 1))
    return out


def read_tsv(path: Path):
    with open(path, newline="", encoding="utf-8-sig", errors="replace") as f:
        yield from csv.DictReader(f, delimiter="\t", quoting=csv.QUOTE_NONE)


if __name__ == "__main__":
    main()

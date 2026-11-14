"""Prüft, ob die Wanderungen (M10, links/migration.csv) alle Daten enthalten, und rechnet sie sonst neu.

    python scripts/check_migration.py            # Bericht; Exit 1, wenn veraltet
    python scripts/check_migration.py --update   # veraltet → scripts/migration.py neu, danach Stempel
    python scripts/check_migration.py --ci       # wie --update, aber ohne Exit 1 (Pages-Workflow)
    python scripts/check_migration.py --upstream # dazu: neue Daten in den Quell-Repos (gh, Netz)?

`migration.py` liest Einheiten, Einträge, Normdaten und HLS-Kandidaten und die Berufs- und
Vornamenregeln aus anderen Skripten. Kommt eine Gemeinde, ein Jahrgang oder eine neue Fassung
einer dieser Dateien dazu, ist links/migration.csv veraltet, ohne dass es jemand merkt. Darum
schreibt jeder Lauf von `migration.py` einen Stempel (data/norm/migration_inputs.json): je
Eingabe eine Prüfsumme über den Inhalt (bei .gz entpackt, damit der Zeitstempel im gzip-Kopf
nicht zählt) und je Gemeinde die Jahrgänge mit der Zahl der Einträge. Dieses Skript vergleicht
den Stand mit dem Stempel und nennt, was neu ist: Gemeinden, Jahrgänge, geänderte Dateien.
Dazu prüft es, ob jede Einheit in links/migration.csv noch existiert.

Mit `--upstream` schaut es eine Stufe weiter vorn: Haben die Repos in config/sources.toml (Städte,
Telefonbücher) seit dem gepinnten Commit eine der übernommenen Dateien geändert? Dann gibt es neue
Daten, die noch nicht eingelesen sind; sie kommen über `commit` neu setzen und `make ingest link
entities` in die Einheiten und von dort mit diesem Skript in die Wanderungen.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import fnmatch
import json
import os
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import NORM, ROOT, config, open_csv  # noqa: E402

LINKS = ROOT / "links"
STAMP = NORM / "migration_inputs.json"
SCRIPTS = ROOT / "scripts"
# alles, was migration.py find() liest: Daten und die Regeln aus den importierten Skripten
INPUTS = [
    NORM / "entities.csv.gz", NORM / "ptt_entries.csv.gz", NORM / "ab_entries.csv", NORM / "hls_candidates.csv.gz",
    LINKS / "entities.csv.gz", LINKS / "authority.csv",
    SCRIPTS / "migration.py", SCRIPTS / "link_ptt_ab.py", SCRIPTS / "parse_ptt.py",
    SCRIPTS / "occupations.py", SCRIPTS / "occupations_fine.py", SCRIPTS / "common.py",
]


def digest(path: Path) -> str:
    if not path.exists():
        return ""
    h = hashlib.sha256()
    with (gzip.open if path.suffix == ".gz" else open)(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()[:16]


def volumes() -> dict[str, dict[str, int]]:
    """Einträge je Gemeinde und Jahr, wie migration.py coverage() sie zählt."""
    c: dict[str, Counter] = defaultdict(Counter)
    for r in open_csv(LINKS / "entities.csv.gz"):
        c[r["municipality"]][r["year"]] += 1
    return {m: dict(sorted(v.items())) for m, v in sorted(c.items())}


def current() -> dict:
    return {"inputs": {str(p.relative_to(ROOT)): digest(p) for p in INPUTS}, "volumes": volumes()}


def write_stamp(state: dict | None = None) -> None:
    """Aufgerufen am Ende von migration.py find()."""
    st = state or current()
    j = lambda x: json.dumps(x, ensure_ascii=False, sort_keys=True, separators=(",", ":"))  # noqa: E731
    lines = ['{"inputs": ' + json.dumps(st["inputs"], ensure_ascii=False, sort_keys=True, indent=1) + ",", '"volumes": {']
    vol = sorted(st["volumes"].items())
    lines += [f"{j(m)}: {j(v)}" + ("," if i < len(vol) - 1 else "") for i, (m, v) in enumerate(vol)]
    STAMP.write_text("\n".join(lines) + "\n}}\n")  # eine Zeile je Gemeinde: der Diff zeigt neue Jahrgänge


def compare(old: dict, new: dict) -> list[str]:
    out = []
    for p, h in new["inputs"].items():
        if old.get("inputs", {}).get(p) != h:
            out.append(f"geändert: {p}" if h else f"fehlt: {p}")
    ov, nv = old.get("volumes", {}), new["volumes"]
    added = sorted(m for m in nv if m not in ov)
    if added:
        out.append(f"neue Gemeinden ({len(added)}): " + ", ".join(added[:20]) + (" …" if len(added) > 20 else ""))
    gone = sorted(m for m in ov if m not in nv)
    if gone:
        out.append(f"weggefallene Gemeinden ({len(gone)}): " + ", ".join(gone[:20]) + (" …" if len(gone) > 20 else ""))
    years, changed = [], []
    for m in sorted(set(nv) & set(ov)):
        for y, n in nv[m].items():
            if y not in ov[m]:
                years.append(f"{m} {y}")
            elif abs(n - ov[m][y]) > max(5, 0.05 * ov[m][y]):
                changed.append(f"{m} {y} ({ov[m][y]} → {n})")
    if years:
        out.append(f"neue Jahrgänge ({len(years)}): " + ", ".join(years[:20]) + (" …" if len(years) > 20 else ""))
    if changed:
        out.append(f"Jahrgänge mit anderer Zahl der Einträge ({len(changed)}): " + ", ".join(changed[:20])
                   + (" …" if len(changed) > 20 else ""))
    return out


def dangling() -> list[str]:
    """Einheiten in links/migration.csv, die es in den Einheiten nicht mehr gibt."""
    ids = {r["entity_id"] for r in open_csv(NORM / "entities.csv.gz")}
    return sorted({e for r in open_csv(LINKS / "migration.csv") for e in (r["from_entity"], r["to_entity"])} - ids)


def upstream() -> list[str]:
    """Quell-Repos: geänderte übernommene Dateien zwischen gepinntem Commit und main (GitHub compare)."""
    cfg = config()
    srcs = [(c["label"], c["repo"], c["commit"],
             [f["path"] for f in c["files"]] + [c[k] for k in ("authority", "officeholders") if c.get(k)])
            for c in cfg["city"]]
    p = cfg["ptt"]
    srcs.append(("Telefonbücher", p["repo"], p["commit"], [p["batch_a"] + "/*", p["batch_b"]]))
    out = []
    for label, repo, pin, pats in srcs:
        try:
            r = subprocess.run(["gh", "api", f"repos/{repo}/compare/{pin}...HEAD", "--jq",
                                "[.ahead_by, ([.files[]?.filename] | join(\"\\n\"))] | @tsv"],
                               capture_output=True, text=True, timeout=60, check=True)
        except (OSError, subprocess.SubprocessError) as e:
            out.append(f"{label}: nicht prüfbar ({getattr(e, 'stderr', '') or e})".strip())
            continue
        ahead, _, files = r.stdout.rstrip("\n").partition("\t")
        hit = sorted({f for f in files.replace("\\n", "\n").split("\n") if f and any(fnmatch.fnmatch(f, x) for x in pats)})
        if hit:
            out.append(f"{label} ({repo}): {len(hit)} übernommene Dateien seit {pin[:7]} geändert, "
                       f"{ahead} Commits: " + ", ".join(hit[:6]) + (" …" if len(hit) > 6 else ""))
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--update", action="store_true", help="veraltet → migration.py neu rechnen")
    ap.add_argument("--ci", action="store_true", help="wie --update, Exit 0 (Pages-Workflow)")
    ap.add_argument("--upstream", action="store_true", help="auch neue Daten in den Quell-Repos melden")
    a = ap.parse_args()
    if a.upstream:
        up = upstream()
        print("Quell-Repos: " + ("\n  " + "\n  ".join(up) if up else "nichts Neues seit den gepinnten Commits."))
        if up:
            print("  → commit in config/sources.toml neu setzen, make ingest link entities, dann dieses Skript.")
    new = current()
    old = json.loads(STAMP.read_text()) if STAMP.exists() else {}
    why = compare(old, new) if old else ["kein Stempel (data/norm/migration_inputs.json)"]
    lost = dangling() if (LINKS / "migration.csv").exists() else ["links/migration.csv fehlt"]
    if lost:
        why.append(f"Einheiten in links/migration.csv, die es nicht mehr gibt ({len(lost)}): " + ", ".join(lost[:10]))
    if not why:
        print("Wanderungen aktuell: alle Gemeinden, Jahrgänge und Eingaben wie beim letzten Lauf.")
        return 0
    print("Wanderungen veraltet:\n  " + "\n  ".join(why))
    if a.ci and os.environ.get("GITHUB_ACTIONS"):
        print("::warning title=Wanderungen veraltet::" + "; ".join(why)[:900]
              + " – lokal python scripts/check_migration.py --update und links/migration.csv committen.")
    if not (a.update or a.ci):
        print("Neu rechnen: python scripts/check_migration.py --update")
        return 1
    import migration  # noqa: PLC0415 – erst hier, der Lauf dauert
    migration.find()  # schreibt am Ende den Stempel
    rest = dangling()
    if rest:
        print(f"nach dem Lauf noch {len(rest)} fehlende Einheiten: {rest[:10]}")
        return 0 if a.ci else 1
    print("Wanderungen neu gerechnet, Stempel geschrieben.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

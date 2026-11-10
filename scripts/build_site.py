"""Kennzahlen für die Startseite → site/data/stats.json.

Liest nur data/norm/ (im Repo), braucht also keine Quell-Checkouts; GitHub Pages ruft es
bei jedem Push auf.
"""

from __future__ import annotations

import json
import tomllib
from collections import Counter, defaultdict

from common import NORM, ROOT, open_csv


def main() -> None:
    with open(ROOT / "config" / "sources.toml", "rb") as f:
        cfg = tomllib.load(f)
    ab = open_csv(NORM / "ab_entries.csv")
    auth = open_csv(NORM / "ab_authority.csv")
    ptt = open_csv(NORM / "ptt_entries.csv.gz")

    cities = []
    for c in cfg["city"]:
        rows = [r for r in ab if r["city"] == c["id"]]
        a = [r for r in auth if r["city"] == c["id"]]
        per_volume = Counter(r["volume"] for r in rows)
        cities.append({
            "id": c["id"], "label": c["label"], "repo": c["repo"], "commit": c["commit"][:7],
            "site": c.get("site", ""),
            "entries": len(rows),
            "volumes": [{"year": int(v), "entries": n} for v, n in sorted(per_volume.items())],
            "kinds": dict(Counter(r["kind"] for r in rows).most_common()),
            "authority": {
                "links": len(a),
                "entries": len({r["id"] for r in a}),
                "persons_qid": len({r["qid"] for r in a if r["qid"]}),
                "hls": len({r["hls_id"] for r in a if r["hls_id"]}),
                "gnd": len({r["gnd"] for r in a if r["gnd"]}),
                "tiers": dict(Counter(r["tier"] for r in a).most_common()),
                "hls_confirmed": sum(1 for r in a if r["hls_check"].startswith("bestätigt")),
            },
        })

    grid: dict[str, Counter] = defaultdict(Counter)
    for r in ptt:
        grid[r["network"]][r["year"]] += 1
    years = sorted({y for g in grid.values() for y in g})
    networks = sorted(grid, key=lambda n: -sum(grid[n].values()))

    stats = {
        "window": cfg["window"],
        "ptt": {
            "commit": cfg["ptt"]["commit"][:7], "repo": cfg["ptt"]["repo"],
            "entries": len(ptt), "networks": len(grid), "years": years,
            "grid": [{"network": n, "total": sum(grid[n].values()),
                      "counts": [grid[n].get(y, 0) for y in years]} for n in networks],
        },
        "cities": cities,
        "totals": {
            "ab_entries": len(ab), "ptt_entries": len(ptt),
            "authority_entries": len({r["id"] for r in auth}),
            "qids": len({r["qid"] for r in auth if r["qid"]}),
        },
    }
    out = ROOT / "site" / "data" / "stats.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(stats, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{out.relative_to(ROOT)}: {len(ab)} Adressbuch-Einträge, {len(ptt)} Telefonbuch-Einträge, "
          f"{len(networks)} Netze, {stats['totals']['qids']} Wikidata-Personen")


if __name__ == "__main__":
    main()

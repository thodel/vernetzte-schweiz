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

    # Telefonbücher: Kanton (aufgelöster Ort) × Jahrgang
    grid: dict[str, Counter] = defaultdict(Counter)
    for r in ptt:
        grid[r["canton"] or "–"][r["year"]] += 1
    years = sorted({y for g in grid.values() for y in g})
    cantons = sorted(grid, key=lambda n: (n == "–", -sum(grid[n].values())))
    conf_order = ["hoch", "mittel", "unsicher", "keine"]
    conf = {b: Counter(r["place_confidence"] for r in ptt if r["batch"] == b) for b in ("A", "B")}
    batch_years = {b: [min(r["year"] for r in ptt if r["batch"] == b), max(r["year"] for r in ptt if r["batch"] == b)]
                   for b in ("A", "B")}
    recovered = sum(1 for r in ptt if r["place_method"].startswith("jahresabgleich"))

    # Verknüpfung Telefonbuch ↔ Adressbuch (M2)
    link_stats = json.loads((NORM / "link_stats.json").read_text(encoding="utf-8"))
    quality = json.loads((NORM / "link_quality.json").read_text(encoding="utf-8"))
    held_out = next(v for k, v in quality["precision"].items() if k.startswith("2"))
    links = []
    for c in cfg["city"]:
        ls = link_stats.get(c["id"], {})
        ab_years = sorted({int(r["volume"]) for r in ab if r["city"] == c["id"]})
        links.append({
            "id": c["id"], "label": c["label"], "volumes": ab_years,
            "ptt_entries": ls.get("ptt_entries", 0), "ptt_linked": ls.get("ptt_linked", 0),
            "pairs": ls.get("pairs", 0),
            "tiers": [{"tier": t, "decisions": ls.get("decisions", {}).get(t, 0),
                       "precision": next(({"low": q["low"], "high": q["high"], "n": q["n"]}
                                          for q in held_out if q["city"] == c["id"] and q["tier"] == t), None)}
                      for t in ("sicher", "wahrscheinlich", "möglich")],
        })

    # Einheiten über die Jahre und Normdaten (M3)
    ent = json.loads((NORM / "cluster_stats.json").read_text(encoding="utf-8"))
    cq = json.loads((NORM / "cluster_quality.json").read_text(encoding="utf-8"))
    ent["quality"] = [q for q in cq if q["measured"] and q["layer"] != "getrennt"]
    auth_rows = open_csv(ROOT / "links" / "authority.csv")
    review = ROOT / "data" / "review" / "m3_normdaten.csv"
    reviewed = open_csv(review) if review.exists() else []

    def judged_share(tier: str) -> dict | None:
        rows = [r for r in reviewed if r["tier"] == tier]
        c = Counter(r["urteil"] for r in rows)
        return {"n": len(rows), "low": c["richtig"] / len(rows), "high": (c["richtig"] + c["unklar"]) / len(rows)} \
            if rows else None
    authority = {
        "stadt": sum(1 for r in auth_rows if r["source"] == "stadt"),
        "ptt": dict(Counter(r["tier"] for r in auth_rows if r["source"] == "telefonbuch")),
        "hls": sum(1 for r in auth_rows if r["hls_id"]),
        "gnd": sum(1 for r in auth_rows if r["gnd"]),
        "precision": judged_share("wahrscheinlich"),
        "precision2": judged_share("möglich"),
    }

    stats = {
        "window": cfg["window"],
        "entities": ent,
        "authority": authority,
        "links": links,
        "recall": quality["recall_aarau_phone_sign"],
        "ptt": {
            "commit": cfg["ptt"]["commit"][:7], "repo": cfg["ptt"]["repo"],
            "entries": len(ptt), "years": years,
            "municipalities": len({r["hist_code_1914"] for r in ptt if r["hist_code_1914"]}),
            "grid": [{"canton": n, "total": sum(grid[n].values()),
                      "counts": [grid[n].get(y, 0) for y in years]} for n in cantons],
            "confidence": [{"batch": b, "years": batch_years[b], "total": sum(conf[b].values()),
                            "counts": {k: conf[b].get(k, 0) for k in conf_order}} for b in ("A", "B")],
            "recovered": recovered,
            "types": dict(Counter(r["entity_type"] for r in ptt).most_common()),
            "with_street": sum(1 for r in ptt if r["street_name"]),
            "with_initials": sum(1 for r in ptt if r["initials"]),
        },
        "cities": cities,
        "totals": {
            "ab_entries": len(ab), "ptt_entries": len(ptt),
            "authority_entries": len({r["id"] for r in auth}),
            "qids": len({r["qid"] for r in auth_rows}),
            "ptt_linked": sum(c["ptt_linked"] for c in links),
        },
    }
    out = ROOT / "site" / "data" / "stats.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(stats, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{out.relative_to(ROOT)}: {len(ab)} Adressbuch-Einträge, {len(ptt)} Telefonbuch-Einträge, "
          f"{stats['ptt']['municipalities']} Gemeinden 1914, {stats['totals']['qids']} Wikidata-Personen")


if __name__ == "__main__":
    main()

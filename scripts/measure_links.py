"""Güte der Verknüpfung Telefonbuch ↔ Adressbuch → data/norm/link_quality.json.

    python scripts/measure_links.py

Präzision: aus den von Hand beurteilten Paaren in data/review/m2_stichprobe.csv. Gezählt
wird Stichprobe 2, gezogen nach dem Festlegen der Regeln (Stufe zum Zeitpunkt der Ziehung);
Stichprobe 1 diente zum Einstellen und wird nur als solche ausgewiesen. «unklar» wird als
Spanne berichtet: untere Grenze = unklar falsch, obere = unklar richtig.

Vollständigkeit (Aarau): Einträge mit Telefonzeichen in den Bänden 1896 und 1899 sollten
im Telefonbuch eines nahen Jahrgangs (± 2 Jahre) stehen. Gezählt wird, wie viele davon
verknüpft sind — insgesamt und unter denen, deren Familienname im Telefonbuch dieser
Jahre überhaupt vorkommt (erreichbar).
"""

from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict

from common import NORM, ROOT, open_csv
from link_ptt_ab import LINKS, TIERS, firm_key, nkey

REVIEW = ROOT / "data" / "review" / "m2_stichprobe.csv"


def precision() -> dict:
    out: dict = {}
    rows = list(csv.DictReader(open(REVIEW, encoding="utf-8")))
    for sample in sorted({r["stichprobe"] for r in rows}):
        c = Counter((r["city"], r["tier_bei_ziehung"], r["urteil"]) for r in rows if r["stichprobe"] == sample)
        strata = []
        for city in sorted({k[0] for k in c}):
            for tier in TIERS:
                ok, bad, unk = (c[(city, tier, u)] for u in ("richtig", "falsch", "unklar"))
                n = ok + bad + unk
                if n:
                    strata.append({"city": city, "tier": tier, "n": n, "richtig": ok, "falsch": bad,
                                   "unklar": unk, "low": round(ok / n, 3), "high": round((ok + unk) / n, 3)})
        out[sample] = strata
    return out


def recall(links: list[dict]) -> list[dict]:
    ab = [r for r in open_csv(NORM / "ab_entries.csv") if r["city"] == "aarau"]
    ptt_years: dict[str, set[int]] = defaultdict(set)
    for r in open_csv(NORM / "ptt_entries.csv.gz"):
        if r["municipality_1914"] == "Aarau":
            for k in {nkey(r["surname"]), firm_key(r["name1"])} - {""}:
                ptt_years[k].add(int(r["year"]))
    linked: dict[str, set[int]] = defaultdict(set)
    for l in links:
        linked[l["ab_id"]].add(int(l["ptt_year"]))
    out = []
    for vol in sorted({r["volume"] for r in ab if r["phone_flag"] == "1"}):
        v = int(vol)
        flagged = [r for r in ab if r["volume"] == vol and r["phone_flag"] == "1"]
        reach = [r for r in flagged
                 if any(abs(y - v) <= 2 for k in {nkey(r["surname"]), firm_key(r["surname"])} for y in ptt_years.get(k, ()))]
        hit = [r for r in flagged if any(abs(y - v) <= 2 for y in linked[r["id"]])]
        out.append({"volume": v, "flagged": len(flagged), "reachable": len(reach), "linked": len(hit)})
    return out


def main() -> None:
    links = list(csv.DictReader(open(LINKS / "ptt_ab.csv", encoding="utf-8")))
    q = {"precision": precision(), "recall_aarau_phone_sign": recall(links)}
    (NORM / "link_quality.json").write_text(json.dumps(q, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    for sample, strata in q["precision"].items():
        print(f"Stichprobe {sample}")
        for s in strata:
            print(f"  {s['city']:6} {s['tier']:15} n={s['n']:3}  richtig {s['richtig']:3}  falsch {s['falsch']:2}  "
                  f"unklar {s['unklar']:2}  → {s['low']:.0%}–{s['high']:.0%}")
    for r in q["recall_aarau_phone_sign"]:
        print(f"Aarau {r['volume']}: {r['flagged']} mit Telefonzeichen, {r['reachable']} erreichbar, {r['linked']} verknüpft")


if __name__ == "__main__":
    main()

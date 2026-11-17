"""Zuzüge: wer steht in einem Adressbuchband einer Stadt zum ersten Mal, und woher stammt er?

Teil der Wanderungen (docs/wanderungen.md, Abschnitt «Zuzüge mit Heimatort»). Bisher nur Aarau
1867–1899: die einzige Stadt, deren Bände über viele Jahrgänge den Heimatort nennen.

- Je Band eine Liste: Einwohnerliste, sonst Gebäudeliste. Fehlt der Einwohnerliste der Heimatort,
  kommt er aus der Gebäudeliste desselben Bandes.
- Personen werden von Band zu Band verknüpft (gleicher oder ähnlicher Familienname, Vorname und
  Heimatort ohne Widerspruch, Punkte für Beruf, Strasse, Haus), 1:1 nach Punkten; ein Band darf fehlen.
- Status im späteren Band: bleibt, haushalt (gleicher Name im selben Haus), witwe, neu_familie
  (Name schon in der Stadt), neu. Zuzüge = neu + neu_familie.

    python scripts/zuzuege.py        # links/zuzuege.csv, data/norm/zuzuege_stats.json
    python scripts/zuzuege.py site   # site/data/zuzuege.json.gz
"""

from __future__ import annotations

import difflib
import gzip
import json
import re
import sys
from collections import Counter, defaultdict

from common import NORM, ROOT, open_csv, write_csv
from link_ptt_ab import WIDOW, compare_forenames, forename_tokens, nkey, skey, stems
from occupations import CLASSES, LABELS
from occupations import classify as occ_class
from origins import classify as origin

LINKS = ROOT / "links"
OUT = LINKS / "zuzuege.csv"
STATS = NORM / "zuzuege_stats.json"
# Städte mit Heimatort über mehrere Bände; Jahr der Umnummerierung der Gebäude (gemessen an verknüpften
# Paaren: 1869 → 1877 gleiche Nummer in 29 von 565 Fällen, sonst ~75 %)
CITIES = {"Aarau": 1877}
LOOKBACK = 2  # eine Person darf in einem Band fehlen (Lesefehler, Lücke)
FIELDS = ["record_id", "entity_id", "city", "volume", "prev_volume", "status", "linked_from", "points", "evidence",
          "surname", "forename", "occupation", "occ_class", "origin", "origin_name", "origin_class", "origin_region",
          "origin_lat", "origin_lon"]

NOT_PERSON = re.compile(r"\b(Scheune|Stallung|Holzschopf|Schopf|Remise|Magazin|Werkstätte|Waschhaus|Schöpfe?)\b"
                        r"|handlung\b|^\W*\d+ u\. \d+")
PERSONISH = re.compile(r"\b(Wittwe|Wwe|Witwe|geb\.|Frau|Jungfer|Jgfr|Frl|Töchter|Geschwister|Schwestern|Professor"
                       r"|Dr\.|Pfarrer)", re.I)


def is_person(x: dict) -> bool:
    """Firmen («&», Cie) und Gebäude («Scheune», «Holzschopf») der Gebäudelisten sind keine Personen."""
    t = x["text"][:90]
    if "&" in t or re.search(r"\b(Cie|Comp)\b", t):
        return False
    if forename_tokens(x["forename"]):
        return not NOT_PERSON.search(t) or bool(x["occupation"])
    return bool(PERSONISH.search(t)) or bool(x["occupation"] and not NOT_PERSON.search(t))


def prepare(x: dict, renumbered: int) -> dict:
    o = origin(x["origin"]) if x["origin"] else None
    ok = nkey(o.name) if o and o.cls != "leer" else ""
    return {"id": x["id"], "vol": int(x["volume"]), "sk": nkey(x["surname"]), "surname": x["surname"],
            "forename": x["forename"], "fn": forename_tokens(x["forename"]), "origin": x["origin"], "ok": ok,
            "o": o if ok else None, "stems": stems(x["occupation"] or ""), "occ": x["occupation"] or "",
            "street": skey(x["street"]), "house": re.sub(r"\D", "", x["building_no"] or ""),
            "sys": int(x["volume"]) < renumbered,
            "widow": bool(WIDOW.search(" ".join([x["forename"], x["civil_status"], x["text"]]))),
            "maiden": nkey(x["maiden_name"]), "alliance": nkey(x["alliance_name"])}


def ratio(a: str, b: str) -> float:
    return difflib.SequenceMatcher(None, a, b).ratio()


def score(a: dict, b: dict) -> tuple[int, list[str]] | None:
    """Punkte für «a (früher) = b (später)»; None bei Widerspruch in Vorname oder Heimatort."""
    f = compare_forenames(a["fn"], b["fn"])
    if f == "widerspruch":
        return None
    pts = {"gleich": 3, "abkürzung": 2, "initiale": 1, "": 0}[f]
    ev = [f"vorname:{f}" if f else "vorname:fehlt"]
    if a["ok"] and b["ok"]:
        if a["ok"] != b["ok"] and ratio(a["ok"], b["ok"]) < 0.8:
            return None
        pts += 3
        ev.append("herkunft")
    if a["stems"] & b["stems"]:
        pts += 2
        ev.append("beruf")
    if a["street"] and a["street"] == b["street"]:
        pts += 1
        ev.append("strasse")
        if a["house"] and a["house"] == b["house"] and a["sys"] == b["sys"]:
            pts += 1
            ev.append("haus")
    return pts, ev


def link(earlier: list[dict], later: list[dict]) -> dict[str, tuple[str, int, list[str]]]:
    """Verknüpft Einträge eines Bandes mit den vorangehenden; 1:1, beste Punkte zuerst, bei Gleichstand
    der jüngere Band."""
    by_name, by_house = defaultdict(list), defaultdict(list)
    for a in earlier:
        by_name[a["sk"][:2]].append(a)
        if a["house"]:
            by_house[(a["house"], a["sys"])].append(a)
    cands = []
    for b in later:
        pool = {a["id"]: a for a in by_name[b["sk"][:2]]}
        if b["house"]:
            pool.update({a["id"]: a for a in by_house[(b["house"], b["sys"])]})
        for a in pool.values():
            same = a["sk"] == b["sk"]
            if not same:
                r = ratio(a["sk"], b["sk"])
                same_house = a["house"] and a["house"] == b["house"] and a["sys"] == b["sys"]
                # Lesefehler im Namen: ähnlich und lang genug, oder im selben Haus (Udel/Adel)
                if not ((min(len(a["sk"]), len(b["sk"])) >= 5 and r >= 0.85) or (same_house and r >= 0.6)):
                    continue
            s = score(a, b)
            if s and s[0] >= (3 if same else 5):
                cands.append((s[0] - (0 if same else 1), a["vol"], a["id"], b["id"], s[1] + ([] if same else ["name:ähnlich"])))
    cands.sort(key=lambda c: (-c[0], -c[1]))
    links, used_a = {}, set()
    for pts, _, aid, bid, ev in cands:
        if aid in used_a or bid in links:
            continue
        used_a.add(aid)
        links[bid] = (aid, pts, ev)
    return links


def status(b: dict, prev: list[dict], linked: bool) -> str:
    if linked:
        return "bleibt"
    same = [a for a in prev if a["sk"] == b["sk"]]
    # gleicher Name im selben Haus (über die Umnummerierung: in derselben Strasse): Sohn, Witwe, Angehörige
    if any((a["house"] and a["house"] == b["house"]) if a["sys"] == b["sys"] else (a["street"] and a["street"] == b["street"])
           for a in same):
        return "haushalt"
    if b["widow"] and same:
        return "witwe"
    names = {a["sk"] for a in prev}
    if same or (b["maiden"] and b["maiden"] in names) or (b["alliance"] and b["alliance"] in names):
        return "neu_familie"
    return "neu"


def rosters(rows: list[dict], renumbered: int) -> dict[int, list[dict]]:
    kinds = defaultdict(set)
    for x in rows:
        kinds[x["volume"]].add(x["kind"])
    out = {}
    for v in sorted(kinds):
        main = "einwohner" if "einwohner" in kinds[v] else "bewohner"
        R = [prepare(x, renumbered) for x in rows if x["volume"] == v and x["kind"] == main and is_person(x)]
        if main == "einwohner" and "bewohner" in kinds[v]:
            B = defaultdict(list)
            for x in rows:
                if x["volume"] == v and x["kind"] == "bewohner" and x["origin"]:
                    B[nkey(x["surname"])].append(prepare(x, renumbered))
            for r in R:
                if r["ok"]:
                    continue
                c = [b for b in B[r["sk"]] if b["ok"] and compare_forenames(r["fn"], b["fn"]) in ("gleich", "abkürzung")
                     and (not r["house"] or not b["house"] or r["house"] == b["house"])]
                if len({b["ok"] for b in c}) == 1:
                    r.update(ok=c[0]["ok"], o=c[0]["o"], origin=c[0]["origin"] + " [Gebäudeliste]")
        out[int(v)] = R
    return out


def find() -> None:
    entries = [x for x in open_csv(NORM / "ab_entries.csv") if x["municipality"] in CITIES and x["entry_type"] == "person"]
    entity = {}
    with gzip.open(LINKS / "entities.csv.gz", "rt", encoding="utf-8") as f:
        import csv  # noqa: PLC0415
        for r in csv.DictReader(f):
            if r["source"] == "ab" and r["municipality"] in CITIES:
                entity[r["record_id"]] = r["entity_id"]
    out, stats = [], {}
    for city, renumbered in CITIES.items():
        R = rosters([x for x in entries if x["municipality"] == city], renumbered)
        vols = sorted(R)
        st = {}
        for i, v in enumerate(vols):
            links = link([r for w in vols[max(0, i - LOOKBACK):i] for r in R[w]], R[v]) if i else {}
            prev = R[vols[i - 1]] if i else []
            c, fo = Counter(), Counter()
            for b in R[v]:
                s = status(b, prev, b["id"] in links) if i else "erster_band"
                c[s] += 1
                o = b["o"]
                if o and o.cls in ("CH", "CH?", "Ausland"):
                    grp = "zuzug" if s in ("neu", "neu_familie") else "bleibt" if s == "bleibt" else "andere"
                    fo[(grp, "Ausland" if o.cls == "Ausland" else "CH")] += 1
                lk = links.get(b["id"])
                out.append({"record_id": b["id"], "entity_id": entity.get(b["id"], ""), "city": city, "volume": v,
                            "prev_volume": vols[i - 1] if i else "", "status": s, "linked_from": lk[0] if lk else "",
                            "points": lk[1] if lk else "", "evidence": " ".join(lk[2]) if lk else "",
                            "surname": b["surname"], "forename": b["forename"], "occupation": b["occ"],
                            "occ_class": occ_class(b["occ"]) if b["occ"] else "", "origin": b["origin"],
                            "origin_name": o.name if o else "", "origin_class": o.cls if o else "",
                            "origin_region": o.region if o else "", "origin_lat": o.lat if o and o.lat else "",
                            "origin_lon": o.lon if o and o.lon else ""})
            st[v] = {"personen": len(R[v]), **dict(c),
                     "zuzug_mit_heimatort": fo[("zuzug", "CH")] + fo[("zuzug", "Ausland")], "zuzug_ausland": fo[("zuzug", "Ausland")],
                     "bleibt_mit_heimatort": fo[("bleibt", "CH")] + fo[("bleibt", "Ausland")], "bleibt_ausland": fo[("bleibt", "Ausland")]}
        stats[city] = st
    write_csv(OUT, FIELDS, out)
    STATS.write_text(json.dumps(stats, ensure_ascii=False, indent=1) + "\n")
    for city, st in stats.items():
        for v, s in st.items():
            z = s.get("neu", 0) + s.get("neu_familie", 0)
            share = f"{s['zuzug_ausland'] / s['zuzug_mit_heimatort']:.0%}" if s["zuzug_mit_heimatort"] else "–"
            print(f"{city} {v}: {s['personen']} Personen, {z} Zuzüge, Ausland unter Zuzügen mit Heimatort {share}")


def site() -> None:
    """site/data/zuzuege.json.gz für #/wanderungen?v=zuzug.

    - `stats`: wie data/norm/zuzuege_stats.json
    - `classes`: [Schlüssel, Bezeichnung] der Berufsklassen
    - `rows`: nur Zuzüge: [Stadt, Band, Status (0 neu, 1 neu_familie), Name, Beruf, Berufsklasse (-1 keine),
      Heimatort wie gelesen, Ort, Klasse (0 CH, 1 CH?, 2 Ausland, 3 offen, 4 leer/keiner), Kanton oder Land,
      Breite, Länge, entity]
    """
    ck = {k: i for i, (k, _, _) in enumerate(CLASSES)}
    oc = {"CH": 0, "CH?": 1, "Ausland": 2, "offen": 3}
    rows = []
    for r in open_csv(OUT):
        if r["status"] not in ("neu", "neu_familie"):
            continue
        rows.append([r["city"], int(r["volume"]), 0 if r["status"] == "neu" else 1,
                     f"{r['surname']}, {r['forename']}".strip(", "), r["occupation"][:60], ck.get(r["occ_class"], -1),
                     r["origin"], r["origin_name"], oc.get(r["origin_class"], 4), r["origin_region"],
                     float(r["origin_lat"]) if r["origin_lat"] else None, float(r["origin_lon"]) if r["origin_lon"] else None,
                     r["entity_id"]])
    out = {"stats": json.loads(STATS.read_text()), "classes": [[k, LABELS[k]] for k, _, _ in CLASSES], "rows": rows}
    path = ROOT / "site" / "data" / "zuzuege.json.gz"
    path.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(path, "wt", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, separators=(",", ":"))
    print(f"{path.relative_to(ROOT)}: {len(rows)} Zuzüge")


if __name__ == "__main__":
    site() if sys.argv[1:] == ["site"] else find()

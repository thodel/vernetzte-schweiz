"""Zuzüge: wer steht in einem Adressbuchband einer Stadt zum ersten Mal, und woher stammt er?

Teil der Wanderungen (docs/wanderungen.md, Abschnitt «Zuzüge mit Heimatort»). Aarau 1867–1899 nennt
den Heimatort über viele Bände; Zürich 1867–1914 und Bern 1861–1900 haben mehrere Bände, aber keinen Heimatort;
Baden und Lausanne haben je zwei Bände ohne Heimatort. Basel 1862 rechnet das Basler Repo selbst; hier wird es nur
übernommen (`imported`).

- Je Band eine Liste: Einwohnerliste, sonst Gebäudeliste. Fehlt der Einwohnerliste der Heimatort,
  kommt er aus der Gebäudeliste desselben Bandes.
- Personen werden von Band zu Band verknüpft (gleicher oder ähnlicher Familienname, Vorname und
  Heimatort ohne Widerspruch, Punkte für Beruf, Strasse, Haus), 1:1 nach Punkten; ein Band darf fehlen.
- Status im späteren Band: bleibt, haushalt (gleicher Name im selben Haus), witwe, neu_familie
  (Name schon in der Stadt), neu. Zuzüge = neu + neu_familie.

    python scripts/zuzuege.py        # links/zuzuege.csv.gz, data/norm/zuzuege_stats.json
    python scripts/zuzuege.py site   # site/data/zuzuege.json.gz
"""

from __future__ import annotations

import difflib
import gzip
import json
import re
import sys
from collections import Counter, defaultdict

from common import NORM, ROOT, config, fetch, in_window, open_csv, read_csv, write_csv
from link_ptt_ab import WIDOW, compare_forenames, forename_tokens, nkey, skey, stems, token_match
from occupations import CLASSES, LABELS
from occupations import classify as occ_class
from origins import classify as origin

LINKS = ROOT / "links"
OUT = LINKS / "zuzuege.csv.gz"
STATS = NORM / "zuzuege_stats.json"
# Städte mit mehreren Bänden: (Jahr der Umnummerierung der Gebäude oder 0, Nummern über die ganze Stadt).
# Aarau nummeriert die Gebäude durch und hat zwischen 1869 und 1877 umnummeriert (gleiche Nummer bei
# verknüpften Paaren 29 von 565, sonst ~75 %); Zürich, Bern, Baden und Lausanne nummerieren je Strasse (Baden 1910:
# 66 von 98 Hausnummern an mehreren Strassen; 1900 hat nur 4 % der Einträge eine Nummer). Bern hat 1882 umnummeriert
# («Die Häuser-Nummerirung in Bern»): gleiche Hausnummer bei verknüpften Paaren 1879→1883 9 von 2 640, zwischen den
# Bänden 1861–1879 59–80 %. Baden (1900, 1910) und Lausanne (1896, 1907) haben je zwei Bände, ohne Heimatort.
CITIES = {"Aarau": (1877, True), "Zürich": (0, False), "Bern": (1882, False), "Baden": (0, False), "Lausanne": (0, False)}
# Städte, deren Bände die Strassen verschieden abkürzen: die Abkürzung wird vor dem Vergleich auf die ausgeschriebene
# Form gebracht (`street_canon`). {Stadt: (nur Bände vor diesem Jahr oder 0, nur abgeschnittene Namen)}.
# Bern kürzt bis 1883 auch im Wortinnern ab («Krmg.», «Mezg.»). Zürich vor 1893 nur durch Abschneiden
# («Hirschengr.», «Stüssihofst.», «Rinderm.»); der freie Vergleich machte dort aus Strassen eigenen Namens andere
# («Seestr.» → «Seefeldstr.», «Baurstr.» → «Braurstr.», «Schlossg.» → «Schlosserg.»).
ABBR_STREETS = {"Bern": (0, False), "Zürich": (1893, True)}
# Zweite Umnummerierung über die Konkordanz der Stadt (sources.toml `renumbering`): Aarau 1900. Eine neue Nummer
# steht für eine oder mehrere alte («96/1256»); jede Gruppe alter Nummern wird auf die erste zurückgeführt, die neue
# Nummer auf dieselbe. Neue Nummern ohne alte (Neubauten) bilden ein eigenes System. {Stadt: (Jahr, Nummer → Haus)}
HOUSES: dict[str, tuple[int, dict[str, str], dict[str, str]]] = {}
STREET_SUFFIX = re.compile(r"(gase|strase|str|weg|plaz|platz)$")
# Ein Quartier gilt im Vorband als nicht erfasst, wenn es dort weniger als ein Viertel der Einträge hat
# (Zürich 1867: Riesbach 111, 1875: 1 571). Neue dort sind kein Zuzug, sondern Status «gebiet».
COVERAGE = 0.25
LOOKBACK = 2  # eine Person darf in einem Band fehlen (Lesefehler, Lücke)
FIELDS = ["record_id", "entity_id", "city", "volume", "district", "prev_volume", "status", "linked_from", "points", "evidence",
          "surname", "forename", "occupation", "occ_class", "origin", "origin_name", "origin_class", "origin_region",
          "origin_lat", "origin_lon"]

NOT_PERSON = re.compile(r"\b(Scheune|Stallung|Holzschopf|Schopf|Remise|Magazin|Werkstätte|Waschhaus|Schöpfe?)\b"
                        r"|handlung\b|^\W*\d+ u\. \d+")
PERSONISH = re.compile(r"\b(Wittwe|Wwe|Witwe|geb\.|Frau|Jungfer|Jgfr|Frl|Töchter|Geschwister|Schwestern|Professor"
                       r"|Dr\.|Pfarrer)", re.I)


# Firma, Anstalt oder Verein im Namen selbst («Petranit A. G.», «Hämig, Söhne», «Eilboten-Institut»);
# auch im geerbten Familiennamen einer «—»-Zeile («Erne & Cie.», dann «— Eduard»)
FIRM_NAME = re.compile(r"&|\b(Cie|Comp|Co)\b|\bA\.?\s?-?G\.?$|\bAG\b|A\.E\.G|Aktien|G\.\s?m\.\s?b\.\s?H|GmbH|gesellschaft"
                       r"|enossenschaft|\bVerein|\bSöhne\b|\bGebr\b|\bGebrüder\b|[Ff]abrik\b|[Ii]nstitut\b|[Aa]nstalt\b")


def is_person(x: dict) -> bool:
    """Firmen («&», Cie, A.-G.), Anstalten und Gebäude («Scheune», «Holzschopf») sind keine Personen."""
    t = x["text"][:90]
    if "&" in t or re.search(r"\b(Cie|Comp)\b", t):
        return False
    if any(FIRM_NAME.search(x.get(f) or "") for f in ("surname", "forename")):
        return False
    if forename_tokens(x["forename"]):
        return not NOT_PERSON.search(t) or bool(x["occupation"])
    return bool(PERSONISH.search(t)) or bool(x["occupation"] and not NOT_PERSON.search(t))


def street_canon(streets: list[str], min_n: int = 30, cut_only: bool = False) -> dict[str, str]:
    """Abgekürzter Strassenschlüssel → ausgeschriebener, aus den Schlüsseln einer Stadt selbst. Ziel ist eine Form mit
    gleicher Endung (-gasse, -strasse …), gleichem Anfangsbuchstaben, mindestens so häufig und mindestens `min_n`
    Mal, in der die Abkürzung als Buchstabenfolge steckt («krm» in «kram», «grcht» in «gerechtigkeits»); nur wenn
    genau eine Form passt. Eine reine Verlängerung um mehr als vier Buchstaben gilt nicht («Lorraine» ist nicht
    «Lorraine, Quartierhof»). `cut_only`: nur abgeschnittene Namen ohne Endung, mindestens fünf Buchstaben, auf
    einen Mitlaut endend («hirschengr» → «hirschengraben»; nicht «muhle» → «muhlebach»)."""
    n = Counter(k for k in map(skey, streets) if k)

    def split(k: str) -> tuple[str, str]:
        m = STREET_SUFFIX.search(k)
        return (k[:m.start()], m.group()) if m else (k, "")

    def inside(a: str, b: str) -> bool:
        it = iter(b)
        return all(ch in it for ch in a)

    cores = Counter()
    for k, c in n.items():
        cores[split(k)] += c
    targets = [t for t, c in cores.items() if c >= min_n and len(t[0]) >= 3]
    out = {}
    for k in n:
        core, suf = split(k)
        if len(core) < 3 or cut_only and (suf or len(core) < 5 or core[-1] in "aeiouy"):
            continue
        cand = {t for t in targets if t != (core, suf) and t[1] == suf and len(t[0]) > len(core) and t[0][0] == core[0]
                and inside(core, t[0]) and cores[t] >= cores[(core, suf)]
                and not (t[0].startswith(core) and len(t[0]) - len(core) > 4)
                and (not cut_only or t[0].startswith(core))}
        if len(cand) == 1:
            t = cand.pop()
            out[k] = t[0] + t[1]
    for k in out:  # Ketten auflösen («altbg.» → «altenbg.» → …)
        seen = {k}
        while out[k] in out and out[out[k]] not in seen:
            seen.add(out[k])
            out[k] = out[out[k]]
    return out


def load_houses(cfg: dict) -> None:
    for c in cfg["city"]:
        rn = c.get("renumbering")
        if not rn:
            continue
        new, old = {}, {}
        for r in read_csv(fetch(c["repo"], c["commit"], rn["path"])):
            n, olds = re.sub(r"\D", "", r["new_no"] or ""), re.findall(r"\d+", r["old_no"] or "")
            if not n or not olds:
                continue
            rep = old.get(olds[0], olds[0])
            new.setdefault(n, rep)
            for o in olds:
                old.setdefault(o, rep)
        HOUSES[c["label"]] = (int(rn["year"]), new, old)


def system(x: dict, house: str, renumbered: int):
    """Nummernsystem und Haus: True vor `renumbered`, sonst False; nach der zweiten Umnummerierung über die
    Konkordanz zurück ins System davor, «neu», wo sie die Nummer nicht kennt."""
    vol, rn = int(x["volume"]), HOUSES.get(x.get("municipality", ""))
    if not rn or vol < renumbered or not house:
        return vol < renumbered, house
    if vol < rn[0]:
        return False, rn[2].get(house, house)
    old = rn[1].get(house)
    return (False, old) if old else ("neu", house)


def prepare(x: dict, renumbered: int, global_no: bool = True, canon: dict[str, str] | None = None) -> dict:
    o = origin(x["origin"]) if x["origin"] else None
    ok = nkey(o.name) if o and o.cls != "leer" else ""
    street = skey(x["street"])
    street = (canon or {}).get(street, street)
    sys_, house = system(x, house_key(x, global_no, street), renumbered)
    return {"id": x["id"], "vol": int(x["volume"]), "sk": nkey(x["surname"]), "surname": x["surname"],
            "forename": x["forename"], "fn": forename_tokens(x["forename"]), "origin": x["origin"], "ok": ok,
            "o": o if ok else None, "stems": stems(x["occupation"] or ""), "occ": x["occupation"] or "",
            "street": street, "house": house,
            "sys": sys_,
            "district": x["district"],
            "widow": bool(WIDOW.search(" ".join([x["forename"], x["civil_status"], x["text"]]))),
            "maiden": nkey(x["maiden_name"]), "alliance": nkey(x["alliance_name"])}


def house_key(x: dict, global_no: bool, street: str | None = None) -> str:
    """Hausnummer; wo je Strasse nummeriert wird, mit der Strasse (Schlüssel, gegebenenfalls ausgeschrieben)."""
    no = re.sub(r"\D", "", x["building_no"] or "")
    return no if global_no or not no else f"{skey(x['street']) if street is None else street}|{no}"


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


def similar_names(earlier: set[str], later: set[str]) -> dict[str, list[str]]:
    """Ähnliche Familiennamen (Lesefehler: Rauchenstein/Rauschenstein): gleiche zwei Anfangsbuchstaben,
    beide mindestens 5 Buchstaben, Ähnlichkeit ≥ 0,85. Je Name im späteren Band die früheren Namen."""
    by2 = defaultdict(list)
    for k in earlier:
        if len(k) >= 5:
            by2[k[:2]].append(k)
    out = {}
    for k in later:
        if len(k) < 5:
            continue
        hits = []
        for e in by2[k[:2]]:
            if e == k or abs(len(e) - len(k)) > 3:
                continue
            m = difflib.SequenceMatcher(None, e, k)
            if m.quick_ratio() >= 0.85 and m.ratio() >= 0.85:
                hits.append(e)
        if hits:
            out[k] = hits
    return out


def in_order(a: list, b: list) -> bool:
    """Passen die Vornamen Stelle für Stelle? «Joh. Heinr.» und «Joh. Bapt.» nicht (Vater und Sohn in derselben
    Strasse), «R.» und «Rud.» schon, «Jos.» und «Jos. Saul» auch (der zweite fehlt auf einer Seite)."""
    return bool(a and b) and all(token_match(x, y) for x, y in zip(a, b))


def enough(pts: int, ev: list[str], same: bool, a: dict | None = None, b: dict | None = None) -> bool:
    """Reicht es für eine Verknüpfung? Gleicher Familienname ab 3 Punkten, ähnlicher ab 5. Ein nur schwach
    passender Vorname (Initiale, Abkürzung: 1 Punkt) reicht mit gleichem Beruf (3 Punkte) und, seit 24.11.2026,
    auch mit derselben Strasse (2 Punkte), dann aber nur, wenn die Vornamen Stelle für Stelle passen
    (`in_order`): «Hügi, R.» an der Könizstrasse 1883 und 1900. Ohne Vornamen reicht die Strasse nicht."""
    if pts >= (3 if same else 5):
        return True
    return (same and "vorname:initiale" in ev and "strasse" in ev and a is not None and b is not None
            and in_order(a["fn"], b["fn"]))


def link(earlier: list[dict], later: list[dict]) -> dict[str, tuple[str, int, list[str]]]:
    """Verknüpft Einträge eines Bandes mit den vorangehenden; 1:1, beste Punkte zuerst, bei Gleichstand
    der jüngere Band. Kandidaten: gleicher Familienname, ähnlicher Familienname, oder im selben Haus
    ein Name mit Ähnlichkeit ≥ 0,6 (Udel/Adel)."""
    by_name, by_house = defaultdict(list), defaultdict(list)
    for a in earlier:
        by_name[a["sk"]].append(a)
        if a["house"]:
            by_house[(a["house"], a["sys"])].append(a)
    sim = similar_names(set(by_name), {b["sk"] for b in later})
    cands = []
    for b in later:
        pool = {a["id"]: a for a in by_name[b["sk"]]}
        for k in sim.get(b["sk"], ()):
            pool.update({a["id"]: a for a in by_name[k]})
        if b["house"]:
            pool.update({a["id"]: a for a in by_house[(b["house"], b["sys"])]})
        for a in pool.values():
            same = a["sk"] == b["sk"]
            if not same and not (a["sk"] in sim.get(b["sk"], ()) or ratio(a["sk"], b["sk"]) >= 0.6):
                continue
            s = score(a, b)
            if s and enough(s[0], s[1], same, a, b):
                cands.append((s[0] - (0 if same else 1), a["vol"], a["id"], b["id"], s[1] + ([] if same else ["name:ähnlich"])))
    cands.sort(key=lambda c: (-c[0], -c[1], c[2], c[3]))
    links, used_a = {}, set()
    for pts, _, aid, bid, ev in cands:
        if aid in used_a or bid in links:
            continue
        used_a.add(aid)
        links[bid] = (aid, pts, ev)
    return links


def status(b: dict, prev_by_name: dict[str, list[dict]], linked: bool) -> str:
    if linked:
        return "bleibt"
    same = prev_by_name.get(b["sk"], [])
    # gleicher Name im selben Haus (über die Umnummerierung: in derselben Strasse): Sohn, Witwe, Angehörige
    if any((a["house"] and a["house"] == b["house"]) if a["sys"] == b["sys"]
           else (a["street"] and a["street"] == b["street"]) for a in same):
        return "haushalt"
    if b["widow"] and same:
        return "witwe"
    if same or (b["maiden"] and b["maiden"] in prev_by_name) or (b["alliance"] and b["alliance"] in prev_by_name):
        return "neu_familie"
    return "neu"


def rosters(rows: list[dict], renumbered: int, global_no: bool = True, canon: dict[str, str] | None = None,
            canon_until: int = 0) -> dict[int, list[dict]]:
    kinds = defaultdict(set)
    for x in rows:
        kinds[x["volume"]].add(x["kind"])
    out = {}
    for v in sorted(kinds):
        cv = canon if not canon_until or int(v) < canon_until else None
        main = "einwohner" if "einwohner" in kinds[v] else "bewohner"
        R = [prepare(x, renumbered, global_no, cv) for x in rows if x["volume"] == v and x["kind"] == main and is_person(x)]
        if main == "einwohner" and "bewohner" in kinds[v]:
            B = defaultdict(list)
            for x in rows:
                if x["volume"] == v and x["kind"] == "bewohner" and x["origin"]:
                    B[nkey(x["surname"])].append(prepare(x, renumbered, global_no, cv))
            for r in R:
                if r["ok"]:
                    continue
                c = [b for b in B[r["sk"]] if b["ok"] and compare_forenames(r["fn"], b["fn"]) in ("gleich", "abkürzung")
                     and (not r["house"] or not b["house"] or r["house"] == b["house"])]
                if len({b["ok"] for b in c}) == 1:
                    r.update(ok=c[0]["ok"], o=c[0]["o"], origin=c[0]["origin"] + " [Gebäudeliste]")
        out[int(v)] = R
    return out


ORIGIN_ZERO = {"zuzug_mit_heimatort": 0, "zuzug_ausland": 0, "bleibt_mit_heimatort": 0, "bleibt_ausland": 0}


def imported(entity: dict[str, str], known: set[str]) -> tuple[list[dict], dict[str, dict]]:
    """Zuzüge, die ein Quell-Repo selbst rechnet (`zuzuege`, `zuzuege_stats` in config/sources.toml; Basel: über die
    alte Hausnummer und die Bände 1841/1850 vor dem Zeitfenster). Übernommen werden die Bände im Zeitfenster; ihr
    Vorband nur mit der Personenzahl, als erste Spalte der Tabelle auf der Seite. `known`: ids der Adressbuch-Einträge."""
    cfg = config()
    out, stats = [], {}
    for c in cfg["city"]:
        if not c.get("zuzuege"):
            continue
        city, pre = c["label"], c["id"]
        st = {r["volume"]: r for r in read_csv(fetch(c["repo"], c["commit"], c["zuzuege_stats"]))}
        vols = [v for v in st if in_window(v, cfg) and st[v]["prev_volume"]]
        S = {}
        for v in vols:
            p = st[v]["prev_volume"]
            if not in_window(p, cfg):
                S[p] = {"personen": int(st[p]["personen"]), "erster_band": int(st[p]["personen"]), "nicht_erfasst": [],
                        "ausserhalb": True, **ORIGIN_ZERO}
            S[v] = {"personen": int(st[v]["personen"]), **{k: int(st[v][k]) for k in ("neu", "neu_familie", "bleibt", "witwe", "haushalt")},
                    "nicht_erfasst": [], **ORIGIN_ZERO}
        missing = 0
        for r in read_csv(fetch(c["repo"], c["commit"], c["zuzuege"])):
            if r["volume"] not in vols:
                continue
            rid = f"{pre}:{r['entry_id']}"
            missing += rid not in known
            out.append({"record_id": rid, "entity_id": entity.get(rid, ""), "city": city, "volume": r["volume"],
                        "district": "", "prev_volume": r["prev_volume"], "status": r["status"],
                        "linked_from": f"{pre}:{r['linked_from']}" if r["linked_from"] else "", "points": r["points"],
                        "evidence": r["evidence"], "surname": r["surname"], "forename": r["forename"],
                        "occupation": r["occupation_raw"], "occ_class": occ_class(r["occupation_raw"]) if r["occupation_raw"] else "",
                        "origin": "", "origin_name": "", "origin_class": "", "origin_region": "", "origin_lat": "", "origin_lon": ""})
        stats[city] = S
        print(f"{city}: übernommen aus {c['repo']}@{c['commit'][:7]}, Bände {', '.join(vols)}; "
              f"{missing} Einträge ohne Gegenstück in ab_entries")
    return out, stats


def find() -> None:
    load_houses(config())
    ab = open_csv(NORM / "ab_entries.csv.gz")
    entries = [x for x in ab if x["municipality"] in CITIES and x["entry_type"] == "person"]
    known = {x["id"] for x in ab if x["municipality"] not in CITIES}  # für die übernommenen Städte
    del ab
    entity = {}
    with gzip.open(LINKS / "entities.csv.gz", "rt", encoding="utf-8") as f:
        import csv  # noqa: PLC0415
        for r in csv.DictReader(f):
            if r["source"] == "ab":
                entity[r["record_id"]] = r["entity_id"]
    out, stats = [], {}
    for city, (renumbered, global_no) in CITIES.items():
        rows = [x for x in entries if x["municipality"] == city]
        until, cut_only = ABBR_STREETS.get(city, (0, False))
        canon = (street_canon([x["street"] for x in rows if not until or int(x["volume"]) < until], cut_only=cut_only)
                 if city in ABBR_STREETS else None)
        if canon:
            print(f"{city}: {len(canon)} abgekürzte Strassenschlüssel ausgeschrieben")
        R = rosters(rows, renumbered, global_no, canon, until)
        vols = sorted(R)
        st = {}
        for i, v in enumerate(vols):
            links = link([r for w in vols[max(0, i - LOOKBACK):i] for r in R[w]], R[v]) if i else {}
            prev = defaultdict(list)
            for a in R[vols[i - 1]] if i else []:
                prev[a["sk"]].append(a)
            uncovered = set()
            if i:
                now = Counter(b["district"] for b in R[v])
                before = Counter(a["district"] for a in R[vols[i - 1]])
                if before[""] and city in now:  # Zürich 1867: die Stadt selbst ohne Quartiernamen
                    before[city] += before.pop("")
                if set(now) & set(before) - {""}:  # gleiche Quartiernamen in beiden Bänden
                    uncovered = {d for d, k in now.items() if d and k >= 200 and before[d] < COVERAGE * k}
            c, fo = Counter(), Counter()
            for b in R[v]:
                s = status(b, prev, b["id"] in links) if i else "erster_band"
                if s in ("neu", "neu_familie") and b["district"] in uncovered:
                    s = "gebiet"
                c[s] += 1
                o = b["o"]
                if o and o.cls in ("CH", "CH?", "Ausland"):
                    grp = "zuzug" if s in ("neu", "neu_familie") else "bleibt" if s == "bleibt" else "andere"
                    fo[(grp, "Ausland" if o.cls == "Ausland" else "CH")] += 1
                lk = links.get(b["id"])
                out.append({"record_id": b["id"], "entity_id": entity.get(b["id"], ""), "city": city, "volume": v, "district": b["district"],
                            "prev_volume": vols[i - 1] if i else "", "status": s, "linked_from": lk[0] if lk else "",
                            "points": lk[1] if lk else "", "evidence": " ".join(lk[2]) if lk else "",
                            "surname": b["surname"], "forename": b["forename"], "occupation": b["occ"],
                            "occ_class": occ_class(b["occ"]) if b["occ"] else "", "origin": b["origin"],
                            "origin_name": o.name if o else "", "origin_class": o.cls if o else "",
                            "origin_region": o.region if o else "", "origin_lat": o.lat if o and o.lat else "",
                            "origin_lon": o.lon if o and o.lon else ""})
            st[v] = {"personen": len(R[v]), **dict(c), "nicht_erfasst": sorted(uncovered),
                     "zuzug_mit_heimatort": fo[("zuzug", "CH")] + fo[("zuzug", "Ausland")], "zuzug_ausland": fo[("zuzug", "Ausland")],
                     "bleibt_mit_heimatort": fo[("bleibt", "CH")] + fo[("bleibt", "Ausland")], "bleibt_ausland": fo[("bleibt", "Ausland")]}
        stats[city] = st
    rows, more = imported(entity, known)
    out += rows
    stats.update(more)
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

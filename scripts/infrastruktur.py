"""Infrastruktur: Ausbau von Telefonnetz, Bahn, Post, Strom, Gas und Wasser im Spiegel der Telefon- und Adressbücher.

Drei Teile (docs/infrastruktur.md, Seite #/infrastruktur):

1. Telefonnetz
   - Reihen je Stadt: Einträge im Telefonbuch je Jahr. Je Stadt und Jahr zählt nur der Band mit den
     meisten Einträgen (Basel 1899 liegt doppelt vor); ein Jahr mit weniger als 60 % des vorigen gilt
     als unvollständig gelesen und fällt weg.
   - Gemeinden: erstes Jahr mit einem Eintrag (vor 1911 nur, wo ein Regionalbuch vorliegt; ab 1911
     ganze Schweiz), Einträge 1914, öffentliche Sprechstellen.
   - Telefon in der Wohnung: Anteil der Einträge mit einem Wohnungsanschluss («Wohnung», «Privat», «domicile»,
     «appartement») je Jahr in den langen Stadtreihen.
2. Berufe der Infrastruktur (GROUPS): je 1000 Einträge in den Adressbuchreihen (Zürich 1867–1914,
   Aarau 1867–1899 …) und in den Telefonbüchern; Gemeinden mit mindestens einem solchen Eintrag 1911–1914.
3. Bahnhofstrasse: Gemeinden mit einer Bahnhofstrasse / Rue de la Gare in den Adressen 1911–1914.

    python scripts/infrastruktur.py        # data/norm/infrastruktur.json
    python scripts/infrastruktur.py site   # site/data/infrastruktur.json.gz
"""

from __future__ import annotations

import gzip
import json
import re
import sys
from collections import Counter, defaultdict
from datetime import date

from common import NORM, ROOT, open_csv

OUT = NORM / "infrastruktur.json"
NATIONAL_FROM = 1911  # ab hier ganze Schweiz in den Telefonbüchern (Bände 1, 2a–2c, 3)
DROP = 0.6            # Jahr mit < 60 % der Einträge des vorigen behaltenen Jahrs: unvollständig gelesen
MIN_POINTS = 8        # Stadtreihe: so viele Jahre vor 1911 …
MIN_LAST = 150        # … und so viele Einträge im letzten Jahr

# Berufe und Betriebe der Infrastruktur. Muster über Beruf, Zusatz und (bei Firmen und Ämtern) Namen.
GROUPS: list[tuple[str, str]] = [
    # Bahnen vor der Verstaatlichung 1902 meist abgekürzt: N.O.B. (Nordostbahn), J.-S. (Jura-Simplon), S.C.B. (Centralbahn),
    # V.S.B. (Vereinigte Schweizerbahnen), J.-B.-L. (Jura-Bern-Luzern); danach S.B.B. / C.F.F.
    ("bahn", r"eisenbahn|bundesbahn|\bs\.? ?b\.? ?b\b|\bc\.? ?f\.? ?f\b|\bn\.\s?-?\s?o\.\s?-?\s?b\b|\bj\.\s?-?\s?s\.?(?![a-zäöü])"
             r"|\bs\.\s?c\.\s?-?\s?b\b|\bv\.\s?s\.\s?b\b|\bj\.\s?-?\s?b\.\s?-?\s?l\b|chemin de fer|bahnarb|bahnnarb|bahnhofarb"
             r"|bahnhofangest|bahngest|bahnan ?gest|bahnaufseh|bahnhüter|bahnhofportier|(im|am|auf d\.?) (güter)?bahnhof"
             r"|stationsgehilf|lampist|bremser|lokomotiv|locomotiv|(?<!tram)(?<!omnibus)(?<!post)kondukt"
             r"|zugführer|weichenw|rangier|stationsvorst|stationsbeamt|stationsvorstand|chef de gare|chef de train|bahnmeister"
             r"|bahnarbeit|bahnangest|bahnbeamt|bahnwärter|bahningenieur|aiguilleur|cheminot|ferroviai|güterexpedition"
             r"|zahnradbahn|drahtseilbahn|bergbahn|funiculaire|gotthardbahn|rhätische bahn|nordostbahn|centralbahn|jura-simplon"),
    ("post_tel", r"\bpost\b|postkondukt|postbureau|postbeamt|postangest|posthalter|postcommis|postkommis|postverwalt|briefträger|facteur"
                 r"|buraliste|postillon|telegraph|télégraph|telegraf|telephon|téléphon|telefon"),
    ("strom", r"elektri|électri|elettric|elektrotech|électrotech|kraftwerk|elektrizitätswerk|usine électrique|lichtwerk"
              r"|installateur|dynamo|akkumul|accumul|starkstrom|schwachstrom"),
    ("gas_wasser", r"gaswerk|gasanstalt|gasfabrik|usine à gaz|wasserversorg|wasserwerk|service des eaux|pumpwerk"
                   r"|gas-,? (und |u\. ?)?wasser|appareilleur|sanitär|sanitaire|wasserleitung"),
    ("auto_velo", r"automobil|\bauto\b|autogarage|\bgarage|chauffeur|taxameter|\btaxi|motorwag|motorrad|motocycl|\bvelo"
                  r"|fahrrad|bicycl|\bcycles\b|pneu"),
    ("tram_schiff", r"\btram|strassenbahn|dampfschiff|schiffahrt|navigation|\bbateaux?\b|dampfboot|omnibus"),
    ("bau", r"ingenieur|ingénieur|ingegnere|geometer|géomètre|bauunternehm|entrepreneur|tiefbau|strassenbau|brückenbau"
            r"|beton|zement|ciment|kanalis|baumeister"),
]
COMPILED = [(k, re.compile(p, re.I)) for k, p in GROUPS]
# Gaststätten und Hotels heissen oft nach Bahnhof oder Post («Hôtel de la Gare», «Wirtschaft z. Post»): kein Bahn- oder Postberuf
INN = re.compile(r"hotel|hôtel|wirtschaft|restaur|café|cafe\b|buffet|gasthof|gasthaus|pension|brasserie|auberge|albergo"
                 r"|\bz(um|ur)?\.? ?(post|bahnhof)|de la (gare|poste)|alla (stazione|posta)", re.I)
# Öffentliche Sprechstellen des Telefonnetzes
CALL_OFFICE = re.compile(r"sprechstation|sprechstelle|station téléphonique|cabine téléphonique|telefono pubblico"
                         r"|posto telefonico|stazione telefonica", re.I)
# Anschluss in der Wohnung (meist zweite Linie neben dem Geschäft)
HOME = re.compile(r"\bwohnung\b|\bwhg\b|\bprivat\b|domicile|appartement|\bappart\b|abitazione|\bpriv\.", re.I)
STATION_STREET = re.compile(r"bahnhof(str|platz|weg|quai)|rue de la gare|avenue de la gare|place de la gare|via (della )?stazione"
                            r"|viale stazione|piazza (della )?stazione", re.I)


def groups(*texts: str) -> list[str]:
    t = " ".join(x for x in texts if x)
    inn = bool(INN.search(t))
    return [k for k, rx in COMPILED if rx.search(t) and not (inn and k in ("bahn", "post_tel"))]


def municipalities_1914() -> dict[str, int]:
    """Gemeinden je Kanton am 1.1.1914."""
    day = date(1914, 1, 1)
    out: Counter = Counter()
    for r in open_csv(ROOT / "data" / "ref" / "municipalities_1914.csv"):
        d, m, y = (int(p) for p in r["valid_from"].split("."))
        if date(y, m, d) > day:
            continue
        if r["valid_to"]:
            d, m, y = (int(p) for p in r["valid_to"].split("."))
            if date(y, m, d) < day:
                continue
        out[r["canton"]] += 1
    return dict(out)


def ptt_text(x: dict) -> tuple[str, ...]:
    """Beruf und Zusatz; bei Firmen und Ämtern auch der Name («Elektrizitätswerk Wangen»)."""
    return (x["occupation"], x["supplement"]) + ((x["name1"], x["name2"]) if x["entity_type"] != "person" else ())


def telephone(P: list[dict]) -> dict:
    per_book: Counter = Counter()
    kinds: dict = defaultdict(Counter)
    for x in P:
        per_book[(x["municipality_1914"], int(x["year"]), x["refcode"])] += 1
        if HOME.search(" ".join((x["occupation"], x["supplement"], x["name1"], x["name2"]))):
            kinds[(x["municipality_1914"], int(x["year"]), x["refcode"])]["home"] += 1
    best: dict = {}
    for (m, y, ref), n in per_book.items():
        if n > best.get((m, y), (0, ""))[0]:
            best[(m, y)] = (n, ref)
    series, home = {}, {}
    for m in sorted({m for m, _ in best}):
        kept, last = [], 0
        for y in sorted(y for mm, y in best if mm == m):
            n = best[(m, y)][0]
            if n >= 20 and n >= DROP * last:
                kept.append([y, n])
                last = n
        if m and sum(1 for y, _ in kept if y < NATIONAL_FROM) >= MIN_POINTS and kept[-1][1] >= MIN_LAST:
            series[m] = kept
            home[m] = [[y, round(kinds[(m, y, best[(m, y)][1])]["home"] / n, 4)] for y, n in kept]
    # Gemeinden: erstes Jahr, Einträge im letzten Jahr, Sprechstellen
    first: dict = {}
    n1914: Counter = Counter()
    geo: dict = {}
    call: dict = defaultdict(set)
    for x in P:
        m, y = x["municipality_1914"], int(x["year"])
        if not m:
            continue
        first[m] = min(first.get(m, 9999), y)
        if y == 1914:
            n1914[m] += 1
        if x["lat"] and m not in geo:
            geo[m] = (x["canton"], round(float(x["lat"]), 4), round(float(x["lon"]), 4))
        if y >= NATIONAL_FROM and CALL_OFFICE.search(" ".join(ptt_text(x))):
            call[y].add(m)
    call_first = {}
    for y in sorted(call):
        for m in call[y]:
            call_first.setdefault(m, y)
    places = [[m, *geo[m], first[m], n1914[m], call_first.get(m, 0)] for m in sorted(first) if m in geo]
    total = municipalities_1914()
    cantons = {}
    for c in sorted(total):
        ms = [p for p in places if p[1] == c]
        cantons[c] = {"gemeinden": total[c],
                      **{f"bis_{y}": sum(1 for p in ms if p[4] <= y) for y in (1910, 1911, 1912, 1913, 1914)},
                      "sprechstellen_1914": sum(1 for p in ms if p[6] and p[6] <= 1914)}
    return {"series": series, "home": home, "places": places, "cantons": cantons,
            "call_offices": {y: len(v) for y, v in sorted(call.items())}}


def occupations(P: list[dict], A: list[dict]) -> dict:
    # Adressbuchreihen: Städte mit mindestens zwei Bänden, je 1000 Einträge
    ab: dict = defaultdict(Counter)
    ab_n: Counter = Counter()
    for x in A:
        if x["entry_type"] not in ("person", "firma") or x["kind"] == "berufe":
            continue
        key = (x["municipality"], int(x["volume"]))
        ab_n[key] += 1
        for g in groups(x["occupation"]):
            ab[key][g] += 1
    vols = defaultdict(list)
    for m, v in ab_n:
        if ab_n[(m, v)] >= 500:
            vols[m].append(v)
    ab_series = {m: [[v, ab_n[(m, v)], {g: ab[(m, v)][g] for g, _ in GROUPS}] for v in sorted(vs)]
                 for m, vs in sorted(vols.items()) if len(vs) >= 2}
    # Telefonbücher: ganze Schweiz 1911–1914 (Einträge und Gemeinden je Gruppe), Stadtreihen je 1000 Einträge
    nat: dict = defaultdict(Counter)
    nat_m: dict = defaultdict(lambda: defaultdict(set))
    nat_n: Counter = Counter()
    first: dict = defaultdict(dict)
    examples: dict = defaultdict(list)
    for x in P:
        y = int(x["year"])
        gs = groups(*ptt_text(x))
        if y >= NATIONAL_FROM:
            nat_n[y] += 1
        for g in gs:
            m = x["municipality_1914"]
            if y >= NATIONAL_FROM:
                nat[y][g] += 1
                if m:
                    nat_m[y][g].add(m)
            if m:
                first[g][m] = min(first[g].get(m, 9999), y)
            if y == 1914 and len(examples[g]) < 400:
                examples[g].append([x["municipality_1914"], (x["name1"] + (" " + x["forename"] if x["forename"] else "")).strip()[:60],
                                    (x["occupation"] or x["supplement"])[:70]])
    national = {y: {"eintraege": nat_n[y], **{g: [nat[y][g], len(nat_m[y][g])] for g, _ in GROUPS}} for y in sorted(nat_n)}
    return {"ab": ab_series, "national": national, "first": {g: first[g] for g, _ in GROUPS},
            "examples": {g: examples[g] for g, _ in GROUPS}}


def station_streets(P: list[dict]) -> dict:
    by_year: dict = defaultdict(set)
    first: dict = {}
    for x in P:
        y = int(x["year"])
        if STATION_STREET.search(" ".join((x["street"], x["street_name"]))):
            m = x["municipality_1914"]
            if m:
                first[m] = min(first.get(m, 9999), y)
                if y >= NATIONAL_FROM:
                    by_year[y].add(m)
    return {"per_year": {y: len(v) for y, v in sorted(by_year.items())}, "first": first}


def find() -> None:
    P = open_csv(NORM / "ptt_entries.csv.gz")
    A = open_csv(NORM / "ab_entries.csv")
    out = {"telefon": telephone(P), "berufe": occupations(P, A), "bahnhofstrasse": station_streets(P),
           "groups": [k for k, _ in GROUPS]}
    OUT.write_text(json.dumps(out, ensure_ascii=False, separators=(",", ":")) + "\n")
    t = out["telefon"]
    print(f"Stadtreihen: {', '.join(t['series'])}")
    for c, v in t["cantons"].items():
        print(c, v)
    print("Sprechstellen", t["call_offices"])
    for y, v in out["berufe"]["national"].items():
        print(y, v)
    print("Bahnhofstrasse", out["bahnhofstrasse"]["per_year"])


def site() -> None:
    path = ROOT / "site" / "data" / "infrastruktur.json.gz"
    path.parent.mkdir(parents=True, exist_ok=True)
    data = json.loads(OUT.read_text())
    with gzip.open(path, "wt", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, separators=(",", ":"))
    print(f"{path.relative_to(ROOT)}")


if __name__ == "__main__":
    site() if sys.argv[1:] == ["site"] else find()

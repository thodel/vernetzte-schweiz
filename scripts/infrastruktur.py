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
4. Weitere Spuren (spuren()):
   - Rufnummern: verschiedene Nummern (≈ Anschlüsse) und höchste Nummer des geschlossenen Bereichs je Stadt und Jahr.
   - Gemeindewerke: Elektrizitäts-, Gas- und Wasserwerke als Abonnenten, erstes Jahr je Gemeinde (mit Suchwort).
   - Ämter am Netz: Gemeindekanzlei, Bahnhof, Post mit eigenem Eintrag.
   - Fremdenverkehr: Anteil der Hotels und Kurhäuser im ersten Jahrgang einer Gemeinde.
   - Einwohner: Einträge je 1000 Einwohner (Volkszählungen 1888, 1900, 1910; BFS, Gemeindestand 2000).
   - Bahn: Bahnhöfe mit Eröffnungsjahr (Wikidata, P1619) und Telefon 1911 in Gemeinden mit und ohne Bahnhof.

    python scripts/infrastruktur.py        # data/norm/infrastruktur.json
    python scripts/infrastruktur.py site   # site/data/infrastruktur.json.gz
    python scripts/infrastruktur.py ref PX STATIONS   # data/ref/population_1850_2000.csv, data/ref/stations_wikidata.csv

PX: BFS px-x-4004000000_101 (Bevölkerungsentwicklung nach institutionellen Gliederungen 1850–2000,
https://www.bfs.admin.ch/bfsstatic/dam/assets/241082/master, Latin-1). STATIONS: CSV der Wikidata-Abfrage
in docs/infrastruktur.md (Spalten s, sLabel, d, c).
"""

from __future__ import annotations

import gzip
import json
import math
import re
import sys
from collections import Counter, defaultdict
from datetime import date

from common import NORM, ROOT, open_csv, write_csv

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
CALL_OFFICE = re.compile(r"sprechstation|sprechstelle|gemeinde-?station|station (téléphonique|publique|communale)"
                         r"|cabine (téléphonique|publique)|telefono pubblico|posto telefonico"
                         r"|stazione (telefonica|pubblica|comunale|consortile)", re.I)
# Anschluss in der Wohnung (meist zweite Linie neben dem Geschäft)
HOME = re.compile(r"\bwohnung\b|\bwhg\b|\bprivat\b|domicile|appartement|\bappart\b|abitazione|\bpriv\.", re.I)
STATION_STREET = re.compile(r"bahnhof(str|platz|weg|quai)|rue de la gare|avenue de la gare|place de la gare|via (della )?stazione"
                            r"|viale stazione|piazza (della )?stazione", re.I)


# Gemeindewerke als Abonnenten (Name eines Betriebs oder Amts, nicht Beruf einer Person)
WORKS = [
    ("strom", re.compile(r"elektri[cz]itätswerk|electricitätswerk|kraftwerk|lichtwerk|usine électrique|service (de l'|de l’|des? )?électricité"
                         r"|azienda elettrica|officina elettrica|société (d'|d’)électricité|elektrizitätsgenossenschaft", re.I)),
    ("gas", re.compile(r"gaswerk|gasanstalt|usine à gaz|service du gaz|officina del gas"
                       r"|(?<![a-zäöü])gas-,? ?(wasser|(und|u\.|&) ?(wasser|elektri))", re.I)),
    # «Wasser- und Elektrizitätswerk», nicht «Mineralwasser- und Colonialwarenhandlung»
    ("wasser", re.compile(r"wasserwerk|wasserversorg|service des eaux|(?<![a-zäöü])wasser- ?(und|u\.|&) ?(elektri|licht|gas)|acquedotto", re.I)),
]
# Ämter mit eigenem Eintrag
OFFICES = [
    ("gemeinde", re.compile(r"gemeinde(rats)?kanzl|gemeindeschreiberei|gemeindehaus|gemeindeverwalt|stadtkanzlei|stadthaus"
                            r"|greffe (municipal|communal)|secrétariat (communal|municipal)|bureau communal|^municipalité|^commune\b"
                            r"|cancelleria comunale|^municipio|ufficio comunale", re.I)),
    ("bahnhof", re.compile(r"^(bahnhof|station|gare|stazione|güterexpedition|güterbahnhof)\b|^stationsbureau|^bureau de la gare", re.I)),
    ("post", re.compile(r"^(post|postbureau|postablage|postbüro|bureau (de|des) postes?|poste|ufficio postale|posta|telegraph"
                        r"|telegraphenbureau|bureau télégraphique|télégraphe)\b", re.I)),
]
# kein Amt: «Station communale» ist die Gemeindesprechstelle, «Poste de gendarmerie» ein Polizeiposten
NOT_OFFICE = re.compile(r"gendarm|police|polizei|douane|pompier|secours|d['’]appel|\bgarde\b", re.I)
HOTEL = re.compile(r"hotel|hôtel|kurhaus|kuranstalt|grand-hôtel|pension\b|albergo|sanatori|kurort|fremdenpension", re.I)
POP_YEARS = (1880, 1888, 1900, 1910)
YEARS = list(range(1880, 1915))
HOME_MIN = 100       # Wohnungsanteil erst ab so vielen Einträgen: darunter entscheiden einzelne Fälle
GAP = 300  # Lücke, die einen eigenen Nummernblock (Nachbarzentrale, Lesefehler) vom Hauptbereich trennt
MAX_DENSITY = 250    # Einträge je 1000 Einwohner darüber: Ortszuordnung falsch (La Chaux-de-Fonds unter La Chaux VD)
STATION_RADIUS = 3.0  # km: Bahnhof gehört zur nächsten Gemeinde in diesem Umkreis


def groups(*texts: str) -> list[str]:
    t = " ".join(x for x in texts if x)
    inn = bool(INN.search(t))
    return [k for k, rx in COMPILED if rx.search(t) and not (inn and k in ("bahn", "post_tel"))]


def municipalities_alive() -> set[str]:
    """Namen der Gemeinden am 1.1.1914."""
    day = date(1914, 1, 1)
    out = set()
    for r in open_csv(ROOT / "data" / "ref" / "municipalities_1914.csv"):
        d, m, y = (int(p) for p in r["valid_from"].split("."))
        if date(y, m, d) > day:
            continue
        if r["valid_to"]:
            d, m, y = (int(p) for p in r["valid_to"].split("."))
            if date(y, m, d) < day:
                continue
        out.add(r["name"])
    return out


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
            home[m] = [[y, round(kinds[(m, y, best[(m, y)][1])]["home"] / n, 4)] for y, n in kept if n >= HOME_MIN]
    # Gemeinden: erstes Jahr, Einträge im letzten Jahr, Sprechstellen
    first: dict = {}
    n1914: Counter = Counter()
    geo: dict = {}
    call: dict = defaultdict(set)
    per_year: Counter = Counter()
    seen: dict = defaultdict(set)
    books: dict = defaultdict(set)
    for x in P:
        m, y = x["municipality_1914"], int(x["year"])
        per_year[y] += 1
        books[y].add(x["refcode"])
        if not m:
            continue
        seen[y].add(m)
        first[m] = min(first.get(m, 9999), y)
        if y == 1914:
            n1914[m] += 1
        if x["lat"] and m not in geo:
            geo[m] = (x["canton"], round(float(x["lat"]), 4), round(float(x["lon"]), 4))
        if CALL_OFFICE.search(" ".join((x["name1"], x["name2"], x["occupation"], x["supplement"]))):
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
                      **{f"bis_{y}": sum(1 for p in ms if p[4] <= y) for y in (1890, 1900, 1910, 1914)},
                      "sprechstellen_1914": sum(1 for p in ms if p[6] and p[6] <= 1914)}
    # Bestand der Quelle je Jahr: Bücher, Einträge, Gemeinden mit Eintrag
    coverage = [[y, len(books[y]), per_year[y], len(seen[y])] for y in YEARS]
    return {"series": series, "home": home, "places": places, "cantons": cantons, "coverage": coverage,
            "call_offices": {y: len(v) for y, v in sorted(call.items())}}


def occupations(P: list[dict], A: list[dict], tel: dict) -> dict:
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
    # Band 2c (Tessin) ist nur 1911 und 1912 gelesen: für den Vergleich der Jahre zählen nur Bände, die jedes Jahr vorliegen
    vols: dict = defaultdict(set)
    for x in P:
        if int(x["year"]) >= NATIONAL_FROM:
            vols[int(x["year"])].add(x["refcode"].split("_")[1])
    every = set.intersection(*vols.values()) if vols else set()
    city: dict = defaultdict(Counter)
    city_n: Counter = Counter()
    for x in P:
        y = int(x["year"])
        gs = groups(*ptt_text(x))
        national = y >= NATIONAL_FROM and x["refcode"].split("_")[1] in every
        if national:
            nat_n[y] += 1
        if x["municipality_1914"] in tel["series"]:
            ck = (x["municipality_1914"], y, x["refcode"])
            city_n[ck] += 1
            for g in gs:
                city[ck][g] += 1
        for g in gs:
            m = x["municipality_1914"]
            if national:
                nat[y][g] += 1
                if m:
                    nat_m[y][g].add(m)
            if m:
                first[g][m] = min(first[g].get(m, 9999), y)
            if y == 1914 and len(examples[g]) < 400:
                examples[g].append([x["municipality_1914"], (x["name1"] + (" " + x["forename"] if x["forename"] else "")).strip()[:60],
                                    (x["occupation"] or x["supplement"])[:70]])
    national = {y: {"eintraege": nat_n[y], **{g: [nat[y][g], len(nat_m[y][g])] for g, _ in GROUPS}} for y in sorted(nat_n)}
    # je Stadt und Jahr der Band mit den meisten Einträgen, wie in den Stadtreihen
    best: dict = {}
    for (m, y, ref), n in city_n.items():
        if n > best.get((m, y), (0, ""))[0]:
            best[(m, y)] = (n, ref)
    cities = {m: [[y, n, {g: city[(m, y, best[(m, y)][1])][g] for g, _ in GROUPS}] for y, n in rows if n >= HOME_MIN]
              for m, rows in tel["series"].items()}
    return {"ab": ab_series, "national": national, "first": {g: first[g] for g, _ in GROUPS}, "cities": cities,
            "volumes": sorted(every),
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


def office(x: dict) -> str | None:
    """Art des Amts bei einem Eintrag eines Amts oder einer Firma, sonst None."""
    if x["entity_type"] == "person":
        return None
    name = " ".join(p for p in (x["name1"], x["name2"]) if p).strip()
    if INN.search(name) or CALL_OFFICE.search(name) or NOT_OFFICE.search(name):
        return None
    for k, rx in OFFICES:
        if rx.search(name):
            return k
    return None


def works(x: dict) -> list[str]:
    """Arten der Werke im Namen eines Betriebs oder Amts («Gas-, Wasser- u. Elektrizitätswerk» ist dreierlei)."""
    if x["entity_type"] == "person":
        return []
    name = " ".join((x["name1"], x["name2"]))
    return [k for k, rx in WORKS if rx.search(name)]


def term(x: dict) -> str:
    """Suchwort, mit dem der Eintrag im Buch seiner Gemeinde zu finden ist."""
    return re.sub(r"[^\w .&'’-]+.*$", "", x["name1"]).strip()[:40]


def cumulative(first: dict) -> list[int]:
    """Gemeinden, die bis zum Jahr mindestens einmal vorkommen, für jedes Jahr in YEARS."""
    ys = Counter(v[0] if isinstance(v, list) else v for v in first.values())
    out, n = [], 0
    for y in YEARS:
        n += ys.get(y, 0)
        out.append(n)
    return out


def top_of_range(numbers: list[int]) -> int:
    """Höchste Nummer des zusammenhängenden Bereichs um die mittlere Nummer; ein Block nach einer Lücke > GAP zählt nicht."""
    v = sorted(set(numbers))
    i = len(v) // 2
    top = v[i]
    for n in v[i + 1:]:
        if n - top > GAP:
            break
        top = n
    return top


def km(a: tuple, b: tuple) -> float:
    dx = (a[1] - b[1]) * 111.32 * math.cos(math.radians((a[0] + b[0]) / 2))
    return math.hypot((a[0] - b[0]) * 110.57, dx)


def ref_municipalities() -> dict[str, dict]:
    return {r["name"]: r for r in open_csv(ROOT / "data" / "ref" / "municipalities_1914.csv")}


def unit_2000(r: dict, units: set[str]) -> str:
    """Gemeinde von 2000, zu der eine Gemeinde von 1914 gehört: die eigene Nummer, wenn es sie 2000 noch gab, sonst die heutige."""
    if r["bfs"] in units and not (r["valid_to"] and int(r["valid_to"][-4:]) < 2000):
        return r["bfs"]
    return r["bfs_today"] if r["bfs_today"] in units else ""


def spuren(P: list[dict], tel: dict) -> dict:
    series = tel["series"]
    places = {p[0]: p for p in tel["places"]}
    # Rufnummern je Stadt und Jahr (nur Jahre, in denen ≥ 80 % der Einträge eine Nummer haben)
    nums: dict = defaultdict(list)
    tot: Counter = Counter()
    best_ref = {}
    for x in P:
        m, y = x["municipality_1914"], int(x["year"])
        if m in series:
            tot[(m, y, x["refcode"])] += 1
            if x["phone_norm"].isdigit():
                nums[(m, y, x["refcode"])].append(int(x["phone_norm"]))
    for (m, y, ref), n in tot.items():
        if n > tot.get((m, y, best_ref.get((m, y), "")), 0):
            best_ref[(m, y)] = ref
    numbers = {}
    for m, rows in series.items():
        out = []
        for y, n in rows:
            v = sorted(nums[(m, y, best_ref[(m, y)])])
            if len(v) >= 0.8 * n:
                out.append([y, n, len(set(v)), top_of_range(v)])
        if len(out) >= 3:
            numbers[m] = out
    # Gemeindewerke, Ämter, Fremdenverkehr
    werk_first: dict = defaultdict(dict)
    office_first: dict = defaultdict(dict)
    first_year: dict = {}
    for x in P:
        m, y = x["municipality_1914"], int(x["year"])
        if not m:
            continue
        first_year[m] = min(first_year.get(m, 9999), y)
        for w in works(x):
            if y < werk_first[w].get(m, [9999])[0]:
                werk_first[w][m] = [y, term(x)]
        o = office(x)
        if o and y < office_first[o].get(m, [9999])[0]:
            office_first[o][m] = [y, term(x)]
    first_n: Counter = Counter()
    first_hotel: Counter = Counter()
    for x in P:
        m, y = x["municipality_1914"], int(x["year"])
        if m and y == first_year[m]:
            first_n[m] += 1
            if HOTEL.search(" ".join((x["name1"], x["name2"], x["occupation"], x["supplement"]))):
                first_hotel[m] += 1
    tourism = sorted(([m, first_year[m], first_n[m], first_hotel[m]] for m in first_n
                      if first_n[m] >= 5 and first_hotel[m] >= 0.5 * first_n[m] and m in places),
                     key=lambda r: (r[1], -r[3]))
    hotel_share = {}
    for lo, hi in ((1880, 1899), (1900, 1910), (1911, 1911), (1912, 1914)):
        ms = [m for m in first_n if lo <= first_year[m] <= hi]
        hotel_share[f"{lo}-{hi}"] = [len(ms), sum(first_hotel[m] for m in ms), sum(first_n[m] for m in ms),
                                     sum(1 for m in ms if first_hotel[m])]
    # Einwohner (Gemeindestand 2000)
    pop = {r["bfs"]: r for r in open_csv(ROOT / "data" / "ref" / "population_1850_2000.csv")}
    ref = ref_municipalities()
    unit = {m: unit_2000(r, set(pop)) for m, r in ref.items()}
    per_unit: dict = defaultdict(Counter)
    for x in P:
        u = unit.get(x["municipality_1914"], "")
        # nur sicher verortete Einträge: ein unplausibler Lauf (places.py) landet sonst ganz in einem Dorf
        if u and x["place_confidence"] != "unsicher":
            per_unit[u][int(x["year"])] += 1
    density = []
    for u, c in per_unit.items():
        p = int(pop[u]["1910"] or 0)
        if p:
            ms = [m for m in unit if unit[m] == u and m in places]
            lat = sum(places[m][2] for m in ms) / len(ms) if ms else 0
            lon = sum(places[m][3] for m in ms) / len(ms) if ms else 0
            if ms and c.get(1911):
                density.append([pop[u]["name"], round(lat, 4), round(lon, 4), p, c[1911], c[1914],
                                round(1000 * c[1911] / p, 1)])
    implausible = sorted((r for r in density if r[6] > MAX_DENSITY), key=lambda r: -r[6])
    density = sorted((r for r in density if r[6] <= MAX_DENSITY), key=lambda r: -r[3])
    city_density = {}
    for m, rows in series.items():
        u = unit.get(m, "")
        if not u:
            continue
        out = []
        for py in POP_YEARS:
            near = [(abs(y - py), y, n) for y, n in rows if abs(y - py) <= 2]
            # Gebiet: nur Städte, deren Gebiet sich bis 2000 nicht durch Eingemeindungen änderte, sonst wäre der Nenner zu gross
            if near and int(pop[u][str(py)] or 0):
                _, y, n = min(near)
                out.append([py, y, n, int(pop[u][str(py)]), round(1000 * n / int(pop[u][str(py)]), 1)])
        merged = [k for k, v in unit.items() if v == u and k != m]
        if out and not merged:  # mit späteren Eingemeindungen wäre die Einwohnerzahl von 2000 zu gross
            city_density[m] = out
    # Bahnhöfe (Wikidata) zur nächsten Gemeinde
    stations = []
    for r in open_csv(ROOT / "data" / "ref" / "stations_wikidata.csv"):
        pt = (float(r["lat"]), float(r["lon"]))
        best = min(((km(pt, (p[2], p[3])), p[0]) for p in places.values()), default=(99, ""))
        if best[0] <= STATION_RADIUS and r["year"]:
            stations.append([r["label"], int(r["year"]), best[1], round(pt[0], 4), round(pt[1], 4)])
    station_first: dict = {}
    for _, y, m, *_ in stations:
        station_first[m] = min(station_first.get(m, 9999), y)
    total = sum(municipalities_1914().values())
    phone_1911 = {m for m, p in places.items() if p[4] <= 1911}
    call_1914 = {m for m, p in places.items() if p[6]}
    with_st = {m for m, y in station_first.items() if y <= 1910}
    # Gleich grosse Gemeinden mit und ohne Bahnhof (Einwohner 1910; nur Gemeinden, deren Gebiet bis 2000 gleich blieb)
    members = Counter(u for u in unit.values() if u)
    pop1910 = {m: int(pop[u]["1910"]) for m, u in unit.items() if u and members[u] == 1 and pop[u]["1910"]}
    alive = municipalities_alive()
    classes = []
    for lo, hi in ((0, 499), (500, 999), (1000, 1999), (2000, 4999), (5000, 10**7)):
        row = [lo, hi]
        for st in (True, False):
            ms = [m for m, p in pop1910.items() if lo <= p <= hi and m in alive and (m in with_st) == st]
            row += [len(ms), sum(1 for m in ms if m in phone_1911), sum(1 for m in ms if m in call_1914)]
        classes.append(row)
    rail = {"classes": classes, "stations": len(stations), "dated_municipalities": len(station_first),
            "with_station": [len(with_st), len(with_st & phone_1911), len(with_st & call_1914)],
            "phone_1911": len(phone_1911), "call_1914": len(call_1914), "gemeinden": total, "places": stations}
    return {
        "numbers": numbers,
        "werke": {"first": {k: werk_first[k] for k, _ in WORKS}},
        "aemter": {"first": {k: office_first[k] for k, _ in OFFICES}},
        "tourismus": {"places": tourism, "share": hotel_share},
        "einwohner": {"places": density, "cities": city_density, "implausible": [[r[0], r[3], r[4]] for r in implausible]},
        "bahn": rail,
    }


def build_ref(px: str, stations: str) -> None:
    """Referenzdateien aus der BFS-Tabelle (PX) und der Wikidata-Abfrage der Bahnhöfe."""
    s = open(px, encoding="latin-1").read()
    names = re.findall(r'"([^"]*)"', re.search(r'VALUES\("Kanton[^"]*"\)=(.*?);', s, re.S).group(1))
    years = re.findall(r'"(\d{4})"', re.search(r'VALUES\("Jahr"\)=(.*?);', s, re.S).group(1))
    data = re.search(r"\nDATA=(.*?);", s, re.S).group(1).split()
    rows = []
    for i, n in enumerate(names):
        mm = re.match(r"\.{6}(\d{4}) (.+)", n)
        if mm:
            v = dict(zip(years, data[i * len(years):(i + 1) * len(years)]))
            rows.append({"bfs": str(int(mm.group(1))), "name": mm.group(2),
                         **{y: "" if v[y] in ('"..."', '"-"', "...") else v[y] for y in ("1880", "1888", "1900", "1910", "1920")}})
    write_csv(ROOT / "data" / "ref" / "population_1850_2000.csv", ["bfs", "name", "1880", "1888", "1900", "1910", "1920"], rows)
    out = []
    import csv as _csv
    for r in _csv.DictReader(open(stations, encoding="utf-8")):
        c = re.match(r"Point\(([-\d.]+) ([-\d.]+)\)", r["c"])
        if c:
            out.append({"qid": r["s"].rsplit("/", 1)[-1], "label": r["sLabel"], "year": r["d"][:4] if r["d"] else "",
                        "lat": c.group(2), "lon": c.group(1)})
    out.sort(key=lambda r: int(r["qid"][1:]))
    write_csv(ROOT / "data" / "ref" / "stations_wikidata.csv", ["qid", "label", "year", "lat", "lon"], out)
    print(f"{len(rows)} Gemeinden, {len(out)} Bahnhöfe ({sum(1 for r in out if r['year'])} mit Eröffnungsjahr)")


def find() -> None:
    P = open_csv(NORM / "ptt_entries.csv.gz")
    A = open_csv(NORM / "ab_entries.csv")
    tel = telephone(P)
    out = {"telefon": tel, "berufe": occupations(P, A, tel), "bahnhofstrasse": station_streets(P),
           "spuren": spuren(P, tel), "groups": [k for k, _ in GROUPS]}
    # Verlauf 1880–1914: Gemeinden, die bis zum Jahr mindestens einmal vorkommen. Ein Jahr ohne Buch oder ein
    # schlecht gelesener Band senkt die Zahl nicht; vor 1911 wächst sie auch, weil Bücher dazukommen.
    sp = out["spuren"]
    out["verlauf"] = {
        "years": YEARS,
        "telefon": cumulative({p[0]: p[4] for p in tel["places"]}),
        "sprech": cumulative({p[0]: p[6] for p in tel["places"] if p[6]}),
        "bahnhofstrasse": cumulative(out["bahnhofstrasse"]["first"]),
        **{f"werk_{k}": cumulative(v) for k, v in sp["werke"]["first"].items()},
        **{f"amt_{k}": cumulative(v) for k, v in sp["aemter"]["first"].items()},
        **{k: cumulative(v) for k, v in out["berufe"]["first"].items()},
    }
    OUT.write_text(json.dumps(out, ensure_ascii=False, separators=(",", ":")) + "\n")
    t = out["telefon"]
    print(f"Stadtreihen: {', '.join(t['series'])}")
    for c, v in t["cantons"].items():
        print(c, v)
    print("Sprechstellen", t["call_offices"])
    for y, v in out["berufe"]["national"].items():
        print(y, v)
    print("Bahnhofstrasse", out["bahnhofstrasse"]["per_year"])
    for m, rows in sp["numbers"].items():
        print("Nummern", m, rows)
    V = out["verlauf"]
    for k, v in V.items():
        if k != "years":
            print("Verlauf", k, {y: v[y - 1880] for y in (1885, 1890, 1900, 1910, 1914)})
    print("Tourismus", len(sp["tourismus"]["places"]), sp["tourismus"]["share"], sp["tourismus"]["places"][:15])
    print("Einwohner", sp["einwohner"]["places"][:8])
    for m, v in sp["einwohner"]["cities"].items():
        print("  ", m, v)
    b = sp["bahn"]
    print("Bahn", {k: v for k, v in b.items() if k != "places"})


def site() -> None:
    path = ROOT / "site" / "data" / "infrastruktur.json.gz"
    path.parent.mkdir(parents=True, exist_ok=True)
    data = json.loads(OUT.read_text())
    with gzip.open(path, "wt", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, separators=(",", ":"))
    print(f"{path.relative_to(ROOT)}")


if __name__ == "__main__":
    if sys.argv[1:2] == ["ref"]:
        build_ref(sys.argv[2], sys.argv[3])
    elif sys.argv[1:] == ["site"]:
        site()
    else:
        find()

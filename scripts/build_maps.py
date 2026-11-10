"""M6: Daten für die Karten → site/data/maps.json.gz und site/data/nm/<xx>.json.gz.

    python scripts/build_maps.py

Grundlage sind die Einheiten aus M3, nicht die Einträge: Eine Person oder Firma zählt
einmal, auch wenn sie 20 Jahre im Telefonbuch steht. Gezählt werden nur Einheiten mit
mindestens einem Telefonbuch-Eintrag; «erstes Jahr» ist der erste Telefonbuch-Jahrgang,
in dem sie steht, also der erste *vorliegende* Jahrgang, nicht zwingend das Jahr des
Anschlusses.

maps.json.gz:
- `places`: [Name, Kanton, Breite, Länge] je Gemeinde mit Koordinaten (Index = Stelle)
- `editions`: je Gemeinde die Jahre mit Telefonbuch-Einträgen (vorliegende Ausgaben)
- `classes`: [Schlüssel, Bezeichnung] der Berufsklassen (scripts/occupations.py)
- `ent`: [Gemeinde, erstes Jahr, letztes Jahr, Art (0 Person, 1 Firma), Klasse (-1 = keine)]
- `top`: je Gemeinde und Zeitraum die fünf häufigsten Familiennamen (Personen)

ow/<xx>.json.gz: Berufswörter für die Suche nach Berufen, nach den ersten zwei Buchstaben des
Wortes: {"w": {Wort: [entity_id, …]}, "e": {entity_id: [Name, Gemeinde, erstes Jahr,
letztes Jahr, Berufe, Quelle t/a/b]}}. Wörter ab 4 Buchstaben aus dem Berufsfeld, ohne Akzente; alle
Einheiten, auch die nur im Adressbuch stehen (Jahre dann aus beiden Quellen).

nm/<xx>.json.gz: je Familienname (Teil nach den ersten zwei Buchstaben wie die Suche)
[[Gemeinde, Jahr, Personen], …] — wie viele Personen dieses Namens in welchem Jahr wo im
Telefonbuch stehen.
"""

from __future__ import annotations

import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from build_pages import OUT, dump, fold, name_shard, src_flag  # noqa: E402
from common import NORM, ROOT, open_csv  # noqa: E402
from occupations import CLASSES, classify  # noqa: E402

import re  # noqa: E402

# Wörter im Berufsfeld, die keinen Beruf nennen
OCC_STOP = {"wohnung", "wohng", "bureau", "buero", "burean", "und", "appartement", "appart", "filiale", "magazin",
            "lager", "privat", "derselbe", "dieselbe", "dasselbe", "siehe", "voir", "aussi", "auch", "unter", "sous",
            "frau", "herrn", "fils", "sohn", "sohne", "freres", "nachf", "succ", "cie", "comp", "rue", "strasse",
            "gasse", "platz", "route", "chemin", "avenue", "villa", "maison"}

PERIODS = {"alle": (1880, 1914), "1880–1899": (1880, 1899), "1900–1910": (1900, 1910), "1911–1914": (1911, 1914)}


def main() -> None:
    geo: dict[str, list] = defaultdict(lambda: [0.0, 0.0, 0])
    canton: dict[str, str] = {}
    editions: dict[str, set] = defaultdict(set)
    ptt_years: dict[str, set] = {}
    for r in open_csv(NORM / "ptt_entries.csv.gz"):
        muni = r["municipality_1914"]
        if not muni or r["place_confidence"] not in ("hoch", "mittel"):
            continue
        editions[muni].add(int(r["year"]))
        canton.setdefault(muni, r["canton"])
        if r["lat"]:
            g = geo[muni]
            g[0] += float(r["lat"])
            g[1] += float(r["lon"])
            g[2] += 1
    member, all_years = defaultdict(set), defaultdict(set)
    for m in open_csv(ROOT / "links" / "entities.csv.gz"):
        all_years[m["entity_id"]].add(int(m["year"]))
        if m["source"] == "ptt":
            member[m["entity_id"]].add(int(m["year"]))
    ptt_years = member

    names = sorted((m for m in geo if geo[m][2]), key=fold)
    idx = {m: i for i, m in enumerate(names)}
    places = [[m, canton.get(m, ""), round(geo[m][0] / geo[m][2], 4), round(geo[m][1] / geo[m][2], 4)] for m in names]
    ckey = {k: i for i, (k, _, _) in enumerate(CLASSES)}

    ent, by_name = [], defaultdict(lambda: defaultdict(Counter))
    ow_words: dict[str, dict[str, list]] = defaultdict(lambda: defaultdict(list))
    ow_ent: dict[str, dict[str, list]] = defaultdict(dict)
    display: dict[str, Counter] = defaultdict(Counter)
    top: dict[str, dict[str, Counter]] = defaultdict(lambda: defaultdict(Counter))
    for s in open_csv(NORM / "entities.csv.gz"):
        if s["municipality"] not in idx:
            continue
        p = idx[s["municipality"]]
        firm = s["kind"] == "firma"
        # Berufssuche: alle Einheiten, auch die nur im Adressbuch stehen
        ya = all_years[s["entity_id"]]
        words = {fold(w) for w in re.findall(r"[A-Za-zÀ-ÿ]{4,}", s["occupations"])} - OCC_STOP
        label = s["name"] if firm and s["name"] else ", ".join(x for x in (s["surname"], s["forename"]) if x)
        for w in words:
            if len(w) < 4:
                continue
            ow_words[w[:2]][w].append(s["entity_id"])
            ow_ent[w[:2]][s["entity_id"]] = [label, p, min(ya), max(ya), s["occupations"][:80], src_flag(s)]
        ys = ptt_years.get(s["entity_id"])
        if not ys:
            continue
        c = classify(s["occupations"], s["name"] if firm else "")
        ent.append([p, min(ys), max(ys), int(firm), ckey.get(c, -1)])
        if firm or not s["surname"].strip():
            continue
        sur = s["surname"].strip()
        key = fold(sur)
        if len(key) < 2:
            continue
        display[key][sur] += 1
        for y in ys:
            by_name[key][(p, y)][0] += 1
        for period, (a, b) in PERIODS.items():
            if min(ys) <= b and max(ys) >= a:
                top[s["municipality"]][period][sur] += 1

    dump(OUT / "maps.json.gz", {
        "places": places,
        "editions": [sorted(editions[m]) for m in names],
        "classes": [[k, label] for k, label, _ in CLASSES],
        "periods": list(PERIODS),
        "ent": ent,
        "top": {str(idx[m]): {per: c.most_common(5) for per, c in v.items()} for m, v in top.items() if m in idx},
    })
    shards: dict[str, dict] = defaultdict(dict)
    for key, cells in by_name.items():
        label = display[key].most_common(1)[0][0]
        shards[name_shard(label)][label] = sorted([p, y, n[0]] for (p, y), n in cells.items())
    for k, v in shards.items():
        dump(OUT / "nm" / f"{k}.json.gz", v)
    for k, words in ow_words.items():
        dump(OUT / "ow" / f"{k}.json.gz", {"w": dict(words), "e": ow_ent[k]})
    print(f"site/data/maps.json.gz: {len(places)} Gemeinden, {len(ent)} Einheiten mit Telefonbuch-Eintrag; "
          f"nm/: {len(by_name)} Familiennamen in {len(shards)} Teilen; ow/: {sum(len(w) for w in ow_words.values())} "
          f"Berufswörter in {len(ow_words)} Teilen")


if __name__ == "__main__":
    main()

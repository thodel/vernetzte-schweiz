"""M6: Daten für die Karten → site/data/maps.json.gz und site/data/nm/<xx>.json.gz.

    python scripts/build_maps.py

Grundlage sind die Einheiten aus M3, nicht die Einträge: Eine Person oder Firma zählt
einmal, auch wenn sie 20 Jahre im Telefonbuch steht. «Erstes Jahr im Telefonbuch» ist der
erste *vorliegende* Jahrgang, nicht zwingend das Jahr des Anschlusses. Die Adressbücher
(Aarau 1884–1899, Basel 1862) zählen nur, wo die Seite es wählen lässt.

maps.json.gz:
- `places`: [Name, Kanton, Breite, Länge] je Gemeinde mit Koordinaten (Index = Stelle)
- `editions`: je Gemeinde die Jahre mit Telefonbuch-Einträgen (vorliegende Ausgaben)
- `classes`: [Schlüssel, Bezeichnung] der Berufsklassen (scripts/occupations.py)
- `ent`: [Gemeinde, erstes und letztes Jahr im Telefonbuch, erstes und letztes Jahr im
  Adressbuch (0 = nicht darin), Art (0 Person, 1 Firma), Klasse (-1 = keine)] für alle
  Einheiten mit Gemeinde-Koordinaten

pl/<xx>.json.gz (FNV des Gemeindenamens): je Gemeinde die Personen als
[Familienname, erstes Jahr, letztes Jahr, Quelle 0 = Telefonbuch / 1 = Adressbuch]; daraus
rechnet die Seite die häufigsten Namen für einen beliebigen Jahresbereich.

ow/<xx>.json.gz: Berufswörter für die Suche nach Berufen, nach den ersten zwei Buchstaben des
Wortes: {"w": {Wort: [entity_id, …]}, "e": {entity_id: [Name, Gemeinde, erstes Jahr,
letztes Jahr, Berufe, Quelle t/a/b]}}. Wörter ab 4 Buchstaben aus dem Berufsfeld, ohne Akzente; alle
Einheiten, auch die nur im Adressbuch stehen (Jahre dann aus beiden Quellen).

nm/<xx>.json.gz: je Familienname (Teil nach den ersten zwei Buchstaben wie die Suche)
[[Gemeinde, erstes Jahr, letztes Jahr, Quelle], …] je Person — wo Personen dieses Namens in
welchen Jahren im Telefon- bzw. Adressbuch stehen.
"""

from __future__ import annotations

import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from build_pages import OUT, dump, fnv, fold, name_shard, src_flag  # noqa: E402
from common import NORM, ROOT, open_csv  # noqa: E402
from occupations import CLASSES, classify  # noqa: E402

import re  # noqa: E402

# Wörter im Berufsfeld, die keinen Beruf nennen
OCC_STOP = {"wohnung", "wohng", "bureau", "buero", "burean", "und", "appartement", "appart", "filiale", "magazin",
            "lager", "privat", "derselbe", "dieselbe", "dasselbe", "siehe", "voir", "aussi", "auch", "unter", "sous",
            "frau", "herrn", "fils", "sohn", "sohne", "freres", "nachf", "succ", "cie", "comp", "rue", "strasse",
            "gasse", "platz", "route", "chemin", "avenue", "villa", "maison"}



def main() -> None:
    geo: dict[str, list] = defaultdict(lambda: [0.0, 0.0, 0])
    canton: dict[str, str] = {}
    editions: dict[str, set] = defaultdict(set)
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
    years: dict[str, dict[str, set]] = defaultdict(lambda: {"ptt": set(), "ab": set()})
    for m in open_csv(ROOT / "links" / "entities.csv.gz"):
        years[m["entity_id"]][m["source"]].add(int(m["year"]))

    names = sorted((m for m in geo if geo[m][2]), key=fold)
    idx = {m: i for i, m in enumerate(names)}
    places = [[m, canton.get(m, ""), round(geo[m][0] / geo[m][2], 4), round(geo[m][1] / geo[m][2], 4)] for m in names]
    ckey = {k: i for i, (k, _, _) in enumerate(CLASSES)}

    ent = []
    by_name: dict[str, list] = defaultdict(list)
    by_place: dict[str, list] = defaultdict(list)
    ow_words: dict[str, dict[str, list]] = defaultdict(lambda: defaultdict(list))
    ow_ent: dict[str, dict[str, list]] = defaultdict(dict)
    display: dict[str, Counter] = defaultdict(Counter)
    for s in open_csv(NORM / "entities.csv.gz"):
        if s["municipality"] not in idx:
            continue
        p = idx[s["municipality"]]
        firm = s["kind"] == "firma"
        y = years[s["entity_id"]]
        ya = y["ptt"] | y["ab"]
        # Berufssuche: alle Einheiten, auch die nur im Adressbuch stehen
        words = {fold(w) for w in re.findall(r"[A-Za-zÀ-ÿ]{4,}", s["occupations"])} - OCC_STOP
        label = s["name"] if firm and s["name"] else ", ".join(x for x in (s["surname"], s["forename"]) if x)
        for w in words:
            if len(w) < 4:
                continue
            ow_words[w[:2]][w].append(s["entity_id"])
            ow_ent[w[:2]][s["entity_id"]] = [label, p, min(ya), max(ya), s["occupations"][:80], src_flag(s)]
        c = classify(s["occupations"], s["name"] if firm else "")
        span = lambda ys: [min(ys), max(ys)] if ys else [0, 0]  # noqa: E731
        ent.append([p, *span(y["ptt"]), *span(y["ab"]), int(firm), ckey.get(c, -1)])
        sur = s["surname"].strip()
        if firm or len(fold(sur)) < 2:
            continue
        key = fold(sur)
        display[key][sur] += 1
        for src, ys in (("ptt", y["ptt"]), ("ab", y["ab"])):
            if ys:
                row = [min(ys), max(ys), 0 if src == "ptt" else 1]
                by_name[key].append([p, *row])
                by_place[s["municipality"]].append([sur, *row])

    dump(OUT / "maps.json.gz", {
        "places": places,
        "editions": [sorted(editions[m]) for m in names],
        "classes": [[k, label] for k, label, _ in CLASSES],
        "ent": ent,
    })
    shards: dict[str, dict] = defaultdict(dict)
    for key, rows in by_name.items():
        shards[name_shard(display[key].most_common(1)[0][0])][display[key].most_common(1)[0][0]] = sorted(rows)
    for k, v in shards.items():
        dump(OUT / "nm" / f"{k}.json.gz", v)
    pshards: dict[str, dict] = defaultdict(dict)
    for muni, rows in by_place.items():
        pshards[fnv(muni)][muni] = sorted(rows)
    for k, v in pshards.items():
        dump(OUT / "pl" / f"{k}.json.gz", v)
    for k, words in ow_words.items():
        dump(OUT / "ow" / f"{k}.json.gz", {"w": dict(words), "e": ow_ent[k]})
    print(f"site/data/maps.json.gz: {len(places)} Gemeinden, {len(ent)} Einheiten; nm/: {len(by_name)} Familiennamen "
          f"in {len(shards)} Teilen; pl/: {len(by_place)} Gemeinden; ow/: "
          f"{sum(len(w) for w in ow_words.values())} Berufswörter in {len(ow_words)} Teilen")


if __name__ == "__main__":
    main()

"""Einwohnerzahlen aus den Gemeindeartikeln des HLS → data/ref/hls_population.csv.

Das HLS nennt die Einwohner einer Gemeinde im Kopf des Artikels («1764 1411 Einwohner; 1850 2253;
1900 2390; 1950 2831; 2000 2948») oder, bei Städten, in einer Tabelle «Bevölkerungsstruktur» mit der
Zeile «Einwohner». Gelesen werden nur die Jahre 1850–1950 und nur Zahlen ohne «ca.».

Der Artikel wird über Namen und Kanton einer Gemeinde vom 1.1.1914 zugeordnet (auch «Ehemalige
Gemeinde»). Grundlage ist der HLS-Export, aus dem auch hls_mcp gebaut ist (`hls_articles.csv`, nicht im
Repo); das Skript läuft darum lokal, sein Ergebnis wird eingecheckt.

    python scripts/hls_population.py [hls_articles.csv]

Quelle: Historisches Lexikon der Schweiz (HLS), hls-dhs-dss.ch, CC BY-SA 4.0.
"""

from __future__ import annotations

import csv
import html
import re
import sys
from collections import Counter
from pathlib import Path

from common import ROOT, open_csv, write_csv
from hls_coverage import EXONYMS, HLS_CSV
from infrastruktur import municipalities_alive
from places import key

OUT = ROOT / "data" / "ref" / "hls_population.csv"
YEARS = (1850, 1950)
SP = "\u00a0\u202f\u2009"                        # geschützte und schmale Leerzeichen im Tausender
NUM = rf"\d[\d {SP}’']*"
PAREN = r"(?: \([^)]*\))?"                         # «251 Einw. (62 Feuerstätten)»
# «1850 2253 Einwohner; 1900 2390; 1950 2831»: das erste Glied nennt die Einheit, die folgenden nicht
PROSE = re.compile(rf"(?:(\d{{4}}) (?:ca\. )?)?({NUM}) (?:Einwohner|Einw\.){PAREN}((?:[;,] (?:um )?\d{{4}} (?:ca\. )?{NUM}{PAREN})*)")
NEXT = re.compile(rf"[;,] (um )?(\d{{4}}) (ca\. )?({NUM})")
SUFFIX = re.compile(r"[, ]+\(?(Gemeinde|Stadt|Stadtgemeinde|Politische Gemeinde)\)?$")
CANTON = re.compile(rf"[, {SP}]+\(?([A-Z]{{2}})\)?$")


def number(s: str) -> int | None:
    d = re.sub(rf"[ {SP}’']", "", s)
    return int(d) if d.isdigit() else None


def prose(text: str) -> dict[int, int]:
    """Jahr → Einwohner aus den Reihen im Fliesstext; genaue Zahlen, kein «um» und kein «ca.».

    Nennt der Artikel mehrere Reihen («Polit. Gem.: 2000 3'422 Einw. Ehem. Munizipalgem.: 1850 1'185 Einw.;
    1870 1'155 …»), zählt je Jahr die erste.
    """
    out: dict[int, int] = {}
    for m in PROSE.finditer(text):
        pairs = ([(m.group(1), m.group(2))] if m.group(1) and "ca. " not in m.group(0)[:12] else [])
        pairs += [(y, v) for um, y, ca, v in NEXT.findall(m.group(3)) if not um and not ca]
        for y, v in pairs:
            if number(v) and int(y) not in out:
                out[int(y)] = number(v)
    return out


def table(page: str) -> dict[int, int]:
    """Jahr → Einwohner aus der Zeile «Einwohner» einer Tabelle; die Kopfzeile davor nennt die Jahre."""
    out: dict[int, int] = {}
    head: list[str] = []
    for tr in re.findall(r"<tr.*?</tr>", page, re.S):
        cells = [html.unescape(re.sub(r"<[^>]+>", "", c)).strip() for c in re.findall(r"<t[hd][^>]*>(.*?)</t[hd]>", tr, re.S)]
        if cells and cells[0] == "Jahr":
            head = cells
        elif cells and cells[0].startswith("Einwohner") and head:
            for y, v in zip(head[1:], cells[1:]):
                ym = re.match(r"(\d{4})[a-z]?$", y)          # «1870b» trägt eine Fussnote
                if ym and number(v):
                    out[int(ym.group(1))] = number(v)
    return out


def name_and_canton(title: str, place_class: str) -> tuple[str, str]:
    """«Biel BE, Gemeinde» → ("Biel", "BE"); der Kanton sonst aus der Ortsklasse («Schweiz -> BE»)."""
    t = SUFFIX.sub("", re.sub(rf"[{SP}]", " ", title).strip())
    canton = ""
    m = CANTON.search(t)
    if m:
        t, canton = t[: m.start()], m.group(1)
    t = SUFFIX.sub("", t).strip()
    if not canton:
        cs = re.findall(r"Schweiz -> ([A-Z]{2})", place_class)
        canton = cs[0] if len(cs) == 1 else ""
    return t, canton


def gazetteer() -> dict[tuple[str, str], str]:
    """(Namensschlüssel, Kanton) → Gemeinde 1914; der Kanton Jura gehörte 1914 zu Bern."""
    alive = municipalities_alive()
    out = {}
    for r in open_csv(ROOT / "data" / "ref" / "municipalities_1914.csv"):
        if r["name"] in alive:
            out[(key(re.sub(r"\s*\([A-Z]{2}\)$", "", r["name"])), r["canton"])] = r["name"]
    return out


def main(path: Path = HLS_CSV) -> None:
    csv.field_size_limit(10**9)
    gaz = gazetteer()
    by_name = Counter(k for k, _ in gaz)
    rows, stats = [], Counter()
    seen: dict[str, str] = {}
    with open(path, encoding="utf-8") as f:
        for a in csv.DictReader(f):
            if a["category"] != "geo" or "Gemeinde" not in a["lexical_class"]:
                continue
            stats["artikel"] += 1
            pop = {**prose(a["content_text"]), **table(a["content_html"])}
            pop = {y: v for y, v in pop.items() if YEARS[0] <= y <= YEARS[1]}
            if not pop:
                stats["ohne_zahlen"] += 1
                continue
            name, canton = name_and_canton(a["title"], a["place_class"])
            k = key(EXONYMS.get(key(name), name))
            cands = [canton, "BE"] if canton == "JU" else [canton]
            muni = next((gaz[(k, c)] for c in cands if (k, c) in gaz), "")
            if not muni and not canton and by_name[k] == 1:
                muni = next(v for (kk, _), v in gaz.items() if kk == k)
            if not muni:
                stats["keine_gemeinde_1914"] += 1
                continue
            if muni in seen:                       # zwei Artikel für eine Gemeinde: der erste zählt
                stats["doppelt"] += 1
                continue
            seen[muni] = a["id"]
            stats["zugeordnet"] += 1
            rows += [{"hls_id": a["id"], "title": re.sub(rf"[{SP}]", " ", a["title"]), "municipality_1914": muni,
                      "year": y, "population": v} for y, v in sorted(pop.items())]
    rows.sort(key=lambda r: (r["municipality_1914"], r["year"]))
    write_csv(OUT, ["hls_id", "title", "municipality_1914", "year", "population"], rows)
    print(dict(stats), f"{len(rows)} Zeilen → {OUT.relative_to(ROOT)}")
    print("Jahre:", sorted(Counter(r["year"] for r in rows).items(), key=lambda x: -x[1])[:12])


if __name__ == "__main__":
    main(Path(sys.argv[1]) if len(sys.argv) > 1 else HLS_CSV)

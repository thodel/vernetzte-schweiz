"""Heimatort eines Adressbucheintrags → Schweiz (Kanton), Ausland (Land) oder offen.

Die Aarauer Gebäude- und Einwohnerlisten 1867–1899 nennen bei rund 60 % der Personen den
Heimatort («von Erfurt», «Küttigen (Bern)»). `classify()` löst ihn auf, in dieser Reihenfolge:

1. Klammerzusatz: Kanton → CH; «Großh. Baden», «Württ.», «Preussen», «Tirol» … → Ausland.
2. Gemeinden 1914 und Ortschaften (`data/ref`), dann alte Schreibungen (-wyl, ß, y),
   dann Orte vor Fusionen (EXTRA), dann der erste Teil eines Doppelnamens («Langnau» →
   Langnau im Emmental).
3. Ausländische Orte aus `data/ref/places_foreign.csv` (GeoNames DE/AT/FR/IT/LI, nur die Namen,
   die in den Adressbüchern vorkommen; neu bauen mit `python scripts/origins.py ref <geonames-dir>`).
4. Unscharf gegen die Schweizer Liste (difflib ≥ 0,86) → `CH?`.
5. Sonst `offen`.

    python scripts/origins.py            # Auszählung über alle Einträge mit Heimatort
    python scripts/origins.py ref DIR    # data/ref/places_foreign.csv aus GeoNames-Dumps in DIR
"""

from __future__ import annotations

import csv
import difflib
import re
import sys
import unicodedata
from collections import Counter, defaultdict
from functools import cache
from typing import NamedTuple

from common import NORM, ROOT, open_csv, write_csv

REF = ROOT / "data" / "ref"
FOREIGN_REF = REF / "places_foreign.csv"
GEONAMES_COUNTRIES = ("DE", "AT", "FR", "IT", "LI")


class Origin(NamedTuple):
    name: str     # bereinigter Ortsname
    cls: str      # CH, CH?, Ausland, offen, leer
    region: str   # Kanton (CH) oder Land (Ausland, «AT/DE» wenn mehrdeutig)
    lat: float | None = None
    lon: float | None = None


def key(s: str) -> str:
    s = unicodedata.normalize("NFC", s).lower().replace("ß", "ss")
    return re.sub(r"[-\s.]", "", s)


def variants(k: str) -> set[str]:
    """Alte Schreibungen eines Schlüssels (Zezwyl → zezwil, Ryken → riken, Oberentfelden → entfelden)."""
    out = {k}
    for a, b in (("wyl", "wil"), ("weil", "wil"), ("y", "i"), ("th", "t"), ("kon", "ken"), ("ken", "kon")):
        out |= {v.replace(a, b) for v in list(out)}
    for p in ("unter", "ober", "nieder", "alt", "neu"):
        out |= {v[len(p):] for v in list(out) if v.startswith(p) and len(v) > len(p) + 3}
    return out


def clean(o: str) -> str:
    s = unicodedata.normalize("NFC", o).strip()
    s = re.sub(r"\s*\[Gebäudeliste\]$", "", s)
    s = re.sub(r"^(von|v\.|aus)\s+", "", s)
    if not s.startswith("St."):
        s = s.split(".")[0]
    return re.split(r"[,;(]", s)[0].strip(" .")


REGIONS = {"sachsen": "DE", "württemberg": "DE", "wurttemberg": "DE", "bayern": "DE", "preussen": "DE",
           "tyrol": "AT", "tirol": "AT", "vorarlberg": "AT", "elsass": "FR", "italien": "IT", "frankreich": "FR",
           "deutschland": "DE", "würtemberg": "DE", "oesterreich": "AT", "österreich": "AT", "hessen": "DE", "schlesien": "DE", "pfalz": "DE"}
# Schweizer Orte vor Fusionen oder in alter Schreibung, die in den Referenzlisten fehlen
EXTRA = {key(n): c for n, c in [
    ("Fluntern", "ZH"), ("Unterstrass", "ZH"), ("Oberstrass", "ZH"), ("Aussersihl", "ZH"), ("Hirslanden", "ZH"),
    ("Wollishofen", "ZH"), ("Hottingen", "ZH"), ("Riesbach", "ZH"), ("Wipkingen", "ZH"), ("Enge", "ZH"),
    ("Wiedikon", "ZH"), ("Leimbach", "ZH"), ("Rued", "AG"), ("Kirchrued", "AG"), ("Baselaugst", "BL"),
    ("Basellaugst", "BL"), ("Ryken", "AG"), ("Gipf", "AG"), ("Kerenzen", "GL"), ("Starrkirch", "SO"),
    ("Genf", "GE"), ("Büblikon", "AG"), ("Dätwyl", "AG"), ("Billigen", "AG"),
    ("Länggasse", "BE"), ("Mattenhof", "BE"), ("Holligen", "BE")]}
SKIP = {"daselbst", "das", "dto", "ob", "dort", "hier"}
CANTONS = {"bern": "BE", "zürich": "ZH", "zurich": "ZH", "zch": "ZH", "zür": "ZH", "solothurn": "SO", "soloth": "SO",
           "sol": "SO", "thurgau": "TG", "thurg": "TG", "luzern": "LU", "baselland": "BL", "basell": "BL",
           "baselld": "BL", "stgallen": "SG", "stgall": "SG", "stg": "SG", "glarus": "GL", "graubünden": "GR",
           "schaffhausen": "SH", "schaffh": "SH", "waadt": "VD", "aargau": "AG", "aarg": "AG", "appenzell": "AR",
           "tessin": "TI", "schwyz": "SZ", "freiburg": "FR", "zug": "ZG", "uri": "UR", "wallis": "VS",
           "neuenburg": "NE", "genf": "GE", "unterwalden": "NW", "baselstadt": "BS"}
FOREIGN = [(r"w[uü]rt|wtbg", "DE"), (r"baden|grh|großh|grossh", "DE"), (r"bayern|baiern", "DE"), (r"preu", "DE"),
           (r"sachsen", "DE"), (r"hessen|hannover|schlesien|pfalz|nassau|westfal|mecklenb|thüring|deutschl", "DE"),
           (r"tirol|tyrol|vorarlb|österr|oesterr|böhmen|mähren|ungarn", "AT"), (r"elsa|lothr|frankr", "FR"),
           (r"ital", "IT"), (r"polen|russ", "RU"), (r"spanien", "ES"), (r"engl", "GB")]


def hint(o: str) -> tuple[str, str] | None:
    """Klammerzusatz: («Bern») → CH/BE, («Großh. Baden») → Ausland/DE; auch ohne Klammer «Grh. Baden»."""
    if re.match(r"(von\s+|v\.\s*)?(gr(o(ss|ß))?h(erzogt(h)?um)?)\.?\s+baden\b", o.strip(), re.I):
        return "Ausland", "DE"
    for m in re.findall(r"\(([^)]{2,25})\)", o):
        k = key(m)
        if k in CANTONS:
            return "CH", CANTONS[k]
        for pat, c in FOREIGN:
            if re.search(pat, m.lower()):
                return "Ausland", c
    return None


@cache
def swiss() -> tuple[dict, dict, dict, list, dict]:
    """(exakt, Varianten, Präfix, sortierte Varianten, Koordinaten) aus data/ref."""
    exact: dict[str, str] = {}
    geo: dict[str, tuple[float, float]] = {}
    by_bfs: dict[str, tuple[float, float]] = {}
    locs = open_csv(REF / "localities.csv")
    for r in locs:
        try:
            ll = (float(r["lat"]), float(r["lon"]))
        except ValueError:
            continue
        geo.setdefault(key(r["name"]), ll)
        by_bfs.setdefault(r["bfs_today"], ll)
    munis = open_csv(REF / "municipalities_1914.csv")
    for r in munis:
        for n in (r["name"], r["name"].split(" (")[0], r["name_today"]):
            exact.setdefault(key(n), r["canton"])
            if r["bfs_today"] in by_bfs:
                geo.setdefault(key(n), by_bfs[r["bfs_today"]])
    for r in locs:
        exact.setdefault(key(r["name"]), r["canton"])
    var: dict[str, str] = {}
    for k, c in exact.items():
        for v in sorted(variants(k)):
            var.setdefault(v, c)
            if k in geo:
                geo.setdefault(v, geo[k])
    prefix: dict[str, str] = {}
    for r in munis + locs:
        nm = r["name"]
        first = re.split(r"[ (/]", nm)[0]
        if first != nm:
            for v in variants(key(first)):
                prefix.setdefault(v, r["canton"])
                if key(nm) in geo:
                    geo.setdefault(v, geo[key(nm)])
    return exact, var, prefix, sorted(var), geo


@cache
def foreign() -> dict[str, tuple[str, float | None, float | None]]:
    if not FOREIGN_REF.exists():
        return {}
    return {r["key"]: (r["countries"], float(r["lat"]) if r["lat"] else None, float(r["lon"]) if r["lon"] else None)
            for r in open_csv(FOREIGN_REF)}


def swiss_only(o: str) -> Origin:
    """Alle Schritte ausser dem ausländischen Nachschlagen und der unscharfen Suche."""
    exact, var, prefix, _, geo = swiss()
    s = clean(o)
    k = key(s)
    h = hint(o)
    if h and k and k not in SKIP:
        if "(" not in o:  # «Grh. Baden»: nur das Land, kein Ort
            return Origin(re.sub(r"^(von|v\.)\s*", "", o.strip()), h[0], h[1])
        fo = foreign().get(k)
        ll = geo.get(k) if h[0] == "CH" else fo[1:] if fo and h[1] in fo[0].split("/") else None
        return Origin(s, h[0], h[1], *(ll or (None, None)))
    if not k or k in SKIP or len(k) < 3:
        return Origin(s, "leer", "")
    if k == "aarau" or k in exact:
        return Origin(s, "CH", exact.get(k, "AG"), *geo.get(k, (None, None)))
    if k in REGIONS:
        return Origin(s, "Ausland", REGIONS[k])
    if k in CANTONS:  # nur der Kanton («soloth», «aarg»)
        return Origin(s, "CH", CANTONS[k])
    for v in sorted(variants(k)):
        if v in var:
            return Origin(s, "CH", var[v], *geo.get(v, (None, None)))
    if k in EXTRA:
        return Origin(s, "CH", EXTRA[k], *geo.get(k, (None, None)))
    for v in sorted(variants(k)):
        if v in prefix:
            return Origin(s, "CH", prefix[v], *geo.get(v, (None, None)))
    return Origin(s, "offen", "")


@cache
def classify(o: str) -> Origin:
    r = swiss_only(o)
    if r.cls != "offen":
        return r
    k = key(r.name)
    if k in foreign():
        c, lat, lon = foreign()[k]
        return Origin(r.name, "Ausland", c, lat, lon)
    _, var, _, keys, geo = swiss()
    for v in sorted(variants(k)):
        m = difflib.get_close_matches(v, keys, n=1, cutoff=0.86)
        if m:
            return Origin(r.name, "CH?", var[m[0]], *geo.get(m[0], (None, None)))
    return r


def build_ref(gn_dir: str) -> None:
    """data/ref/places_foreign.csv: GeoNames-Orte (P, A) mit einem Namen, der als Heimatort vorkommt
    und nicht schon als Schweizer Ort aufgeht. Koordinaten vom grössten Ort dieses Namens."""
    wanted = {key(swiss_only(x["origin"]).name) for x in open_csv(NORM / "ab_entries.csv")
              if x["origin"] and swiss_only(x["origin"]).cls in ("offen", "Ausland")}
    wanted.discard("")
    hits: dict[str, dict] = defaultdict(lambda: {"countries": set(), "pop": -1, "lat": "", "lon": "", "name": ""})
    for c in GEONAMES_COUNTRIES:
        with open(f"{gn_dir}/{c}.txt", encoding="utf-8") as f:
            for line in f:
                g = line.rstrip("\n").split("\t")
                if g[6] not in ("P", "A"):
                    continue
                for n in {g[1], g[2], *(g[3].split(",") if g[3] else [])}:
                    k = key(n)
                    if k in wanted:
                        h = hits[k]
                        h["countries"].add(c)
                        pop = int(g[14] or 0) if g[6] == "P" else -1
                        if pop > h["pop"]:
                            h.update(pop=pop, lat=round(float(g[4]), 4), lon=round(float(g[5]), 4), name=g[1])
    rows = [{"key": k, "name": h["name"], "countries": "/".join(sorted(h["countries"])), "lat": h["lat"], "lon": h["lon"]}
            for k, h in sorted(hits.items())]
    write_csv(FOREIGN_REF, ["key", "name", "countries", "lat", "lon"], rows)
    print(f"{FOREIGN_REF.relative_to(ROOT)}: {len(rows)} von {len(wanted)} gesuchten Namen in GeoNames")


def report() -> None:
    res: Counter = Counter()
    by: dict[str, Counter] = defaultdict(Counter)
    for x in open_csv(NORM / "ab_entries.csv"):
        if x["origin"] and x["entry_type"] == "person":
            o = classify(x["origin"])
            res[o.cls] += 1
            by[o.cls][(o.name, o.region)] += 1
    print(dict(res))
    for cls in ("Ausland", "CH?", "offen"):
        print(cls, by[cls].most_common(40))


if __name__ == "__main__":
    csv.field_size_limit(1 << 30)
    build_ref(sys.argv[2]) if sys.argv[1:2] == ["ref"] else report()

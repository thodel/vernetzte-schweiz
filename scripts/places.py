"""Orte der Telefonbuch-Einträge auflösen → Spalten place_* in der Telefonbuch-Tabelle.

Ein Eintrag trägt seinen Ort in `locality`, in Charge B als «Ortschaft (Zentrale[, …])»,
und zwar als Überschrift, die beim Lesen auf alle folgenden Zeilen übertragen wurde. Fällt
eine Überschrift aus, erben ganze Seiten den falschen Ort: Zürich 1912 steht als
«Zwillikon (Affoltern a. A.)», 14 074 Zeilen lang. Darum zwei Schritte:

1. **Name → Ort.** Ortsteil, Zentrale und Kantonszusatz trennen, bekannte Lesefehler
   (Ea→La, 8t.→St.) beheben, im Gemeindeverzeichnis 1914 und im Ortschaftenverzeichnis
   suchen (genau, als Abkürzung, unscharf). Gleichnamige Orte trennt der Kantonszusatz, die
   Nähe zur Zentrale und die Kantone, die ein Band sonst abdeckt.
2. **Lauf prüfen.** Eine Folge gleicher Überschriften ist plausibel, wenn sie nicht mehr
   als `CAP` Zeilen hat oder der Ort eine Stadt ist (mindestens drei Postleitzahlen). Ein
   unplausibler Lauf wird über die anderen Jahrgänge geprüft: dieselben Abonnenten (Name
   und Rufnummer, oder Name und Strasse) stehen meist mehrere Jahre im Buch; was die
   plausiblen Läufe der anderen Jahre für sie sagen, entscheidet je Zeile (eindeutige
   Stimmen) oder je Seite (nur wenn die Mehrheit eine Stadt ist: Stadtblöcke sind
   seitenweise einheitlich, Seiten zusammengelegter Dörfer nicht). Was so nicht zu klären
   ist, behält die Überschrift mit `place_confidence = unsicher`.

Handkorrekturen: data/review/places_manual.csv (place_raw → hist_code oder Ortschaft).
"""

from __future__ import annotations

import csv
import difflib
import math
import re
import unicodedata
from collections import Counter, defaultdict
from functools import lru_cache

from common import ROOT, open_csv

REF = ROOT / "data" / "ref"
CAP = 150            # Zeilen, die eine Dorf-Überschrift höchstens trägt
CITY_PLZ = 3         # ab so vielen Postleitzahlen gilt ein Ort als Stadt
NEAR_KM = 40

CANTON_HINTS = {
    "b": "BE", "be": "BE", "bern": "BE", "sol": "SO", "so": "SO", "vd": "VD", "vaud": "VD",
    "st g": "SG", "sg": "SG", "st gall": "SG", "z": "ZH", "zh": "ZH", "zch": "ZH", "zur": "ZH",
    "lu": "LU", "luz": "LU", "ag": "AG", "aarg": "AG", "tg": "TG", "thurg": "TG", "thg": "TG",
    "gr": "GR", "graub": "GR", "fr": "FR", "frib": "FR", "ne": "NE", "neuch": "NE", "vs": "VS",
    "val": "VS", "valais": "VS", "ti": "TI", "tess": "TI", "bl": "BL", "baselland": "BL",
    "zeh": "ZH", "zurich": "ZH", "luzern": "LU", "st gallen": "SG", "aargau": "AG",
    "solothurn": "SO", "freiburg": "FR", "thurgau": "TG", "wallis": "VS", "gl": "GL", "glarus": "GL", "sh": "SH", "schaffh": "SH", "zg": "ZG", "zug": "ZG",
    "sz": "SZ", "schwyz": "SZ", "ow": "OW", "nw": "NW", "ur": "UR", "app": "AR", "ap": "AR",
    "ar": "AR", "ai": "AI", "ge": "GE", "geneve": "GE",
}
OCR_FIXES = [
    (re.compile(r"^Ea\b"), "La"), (re.compile(r"^JX"), "N"), (re.compile(r"\b8t\."), "St."),
    (re.compile(r"\b8t\b"), "St"), (re.compile(r"\bSt-"), "St-"),
]
CONNECTORS = {"im", "am", "an", "bei", "b", "ob", "sur", "sous", "pres", "près", "i", "a", "in", "auf", "near",
              "dorf", "platz", "bad"}
PLACE_FIELDS = [
    "place_raw", "place_name", "place_kind", "hist_code_1914", "municipality_1914",
    "bfs_today", "canton", "lat", "lon", "exchange_raw", "place_method", "place_confidence",
]


def key(s: str) -> str:
    s = s.lower().replace("ß", "ss")
    s = "".join(c for c in unicodedata.normalize("NFKD", s) if not unicodedata.combining(c))
    s = re.sub(r"\bsaint\b|\bsankt\b", "st", s)
    s = re.sub(r"\bsainte\b", "ste", s)
    return " ".join(re.sub(r"[^a-z0-9]+", " ", s).split())


def split_locality(raw: str) -> tuple[str, str, str]:
    """«Bibern, Sol. (Hessigkofen)» → ("Bibern", "SO", "Hessigkofen")."""
    s = raw.strip()
    for rx, rep in OCR_FIXES:
        s = rx.sub(rep, s)
    paren = ""
    m = re.search(r"\((.*)\)?\s*$", s)
    if m:
        paren = m.group(1).rstrip(")").strip()
        s = s[: m.start()].strip()
    name, hint = s, ""
    if "," in s:
        name, rest = s.split(",", 1)
        hint = CANTON_HINTS.get(key(rest), "")
    else:
        # «Winterberg ZH», «Biel B.», «Gossau St. Gallen»
        toks = name.split()
        for n in (2, 1):
            if len(toks) > n and key(" ".join(toks[-n:])) in CANTON_HINTS and len(" ".join(toks[-n:])) <= 10:
                name, hint = " ".join(toks[:-n]), CANTON_HINTS[key(" ".join(toks[-n:]))]
                break
    return name.strip(" .,;:"), hint, paren


class Gazetteer:
    def __init__(self) -> None:
        self.cands: dict[str, list[dict]] = defaultdict(list)
        self.alias: dict[str, str] = {}
        locs = open_csv(REF / "localities.csv")
        plz_count: Counter = Counter()      # Postleitzahlen je Ortsname: Grössenmass

        coords: dict[str, tuple[float, float, float]] = {}
        for r in locs:
            base = re.sub(r"\s+\d+$", "", r["name"])            # «Lausanne 25» → Lausanne
            base = re.sub(r"\s+[A-Z]{2}$", "", base)            # «Winterberg ZH» → Winterberg
            plz_count[(key(base), r["bfs_today"])] += 1
            share = float(r["share"] or 0)
            if r["bfs_today"] not in coords or share > coords[r["bfs_today"]][2]:
                if key(base) == key(r["municipality_today"]) or r["bfs_today"] not in coords:
                    coords[r["bfs_today"]] = (float(r["lat"]), float(r["lon"]), share)
            self.cands[key(base)].append({
                "kind": "ortschaft", "name": base, "canton": r["canton"], "bfs_today": r["bfs_today"],
                "hist_code": "", "municipality_1914": "", "lat": float(r["lat"]), "lon": float(r["lon"]),
                "plz": 1,
            })
        for m in open_csv(REF / "municipalities_1914.csv"):
            name = re.sub(r"\s*\([A-Z]{2}\)$", "", m["name"])     # «Biel (BE)» → Biel
            first = m["bfs_today"].split(";")[0]
            lat, lon, _ = coords.get(first, (math.nan, math.nan, 0))
            self.cands[key(name)].append({
                "kind": "gemeinde_1914", "name": m["name"], "canton": m["canton"], "bfs_today": m["bfs_today"],
                "hist_code": m["hist_code"], "municipality_1914": m["name"], "lat": lat, "lon": lon,
                "plz": 1,
            })
        # Ortschaften gleichen Namens im selben Kanton wie eine Gemeinde 1914 gehen in dieser
        # auf (die Postleitzahl «Zürich 8041» liegt heute in Adliswil, gemeint ist Zürich);
        # die Gemeinde übernimmt die Koordinaten der Ortschaft in ihrer heutigen Gemeinde.
        for k, cs in self.cands.items():
            gem = [c for c in cs if c["kind"] == "gemeinde_1914"]
            for c in cs:
                c["plz"] = max(plz_count.get((k, b), 1) for b in c["bfs_today"].split(";"))
                if c["kind"] != "ortschaft":
                    continue
                for g in gem:
                    if g["canton"] == c["canton"]:
                        if c["bfs_today"] in g["bfs_today"].split(";") or math.isnan(g["lat"]):
                            g["lat"], g["lon"] = c["lat"], c["lon"]
                        c["merged"] = True
            self.cands[k] = [c for c in cs if not c.get("merged")]
        # «La Chaux-de-Fonds» auch ohne Artikel auffindbar
        for k in list(self.cands):
            m = re.match(r"^(la|le|les|l) (.+)$", k)
            if m and m.group(2) not in self.cands:
                self.alias[m.group(2)] = k
        self.by_first: dict[str, list[str]] = defaultdict(list)
        for k in self.cands:
            self.by_first[k[:1]].append(k)
        self._cc: dict[str, tuple[list[dict], str]] = {}
        self.manual = {}
        mp = ROOT / "data" / "review" / "places_manual.csv"
        if mp.exists():
            for r in csv.DictReader(open(mp, encoding="utf-8")):
                self.manual[r["place_raw"]] = r

    @lru_cache(maxsize=None)
    def lookup(self, name: str) -> tuple[tuple, str]:
        k = key(name)
        if not k:
            return (), ""
        if k in self.cands:
            return tuple(map(id, self.cands[k])), "name"
        if k in self.alias:
            return tuple(map(id, self.cands[self.alias[k]])), "name"
        # «Langnau» → «Langnau im Emmental», «Matten» → «Matten bei Interlaken»
        longer = [ck for ck in self.by_first.get(k[:1], ())
                  if ck.startswith(k + " ") and ck[len(k) + 1:].split()[0] in CONNECTORS]
        if longer:
            return tuple(id(c) for h in longer for c in self.cands[h]), "namensanfang"
        toks = k.split()
        raw_toks = key(name.replace(".", ". ")).split()
        hits = []
        if len(toks) > 1 or "." in name:
            for ck in self.by_first.get(k[:1], ()):
                ct = ck.split()
                if len(ct) == len(raw_toks) and all(c == t or c.startswith(t) for c, t in zip(ct, raw_toks)):
                    hits.append(ck)
        if not hits:
            close = difflib.get_close_matches(k, self.by_first.get(k[:1], ()), n=3, cutoff=0.86)
            if close:
                hits = close[:1]
                return tuple(id(c) for h in hits for c in self.cands[h]), "unscharf"
            return (), ""
        return tuple(id(c) for h in hits for c in self.cands[h]), "abkürzung"

    def candidates(self, name: str) -> tuple[list[dict], str]:
        if name not in self._cc:
            self._cc[name] = self._candidates(name)
        return self._cc[name]

    def _candidates(self, name: str) -> tuple[list[dict], str]:
        ids, how = self.lookup(name)
        if not ids:
            return [], ""
        idset = set(ids)
        k = key(name)
        pool = self.cands.get(k) or [c for cs in self.cands.values() for c in cs if id(c) in idset]
        return [c for c in pool if id(c) in idset], how


def dist_km(a: dict, b: tuple[float, float]) -> float:
    if math.isnan(a["lat"]) or math.isnan(b[0]):
        return math.inf
    dy = (a["lat"] - b[0]) * 111.2
    dx = (a["lon"] - b[1]) * 111.2 * math.cos(math.radians(b[0]))
    return math.hypot(dx, dy)


def series(row: dict) -> str:
    """Band-Reihe für die Kantons-Vorlieben: B «1», «2a», …; A das Netz."""
    if row["batch"] == "B":
        parts = row["refcode"].split("_")
        return f"B{parts[2]}" if len(parts) > 2 else "B"
    return f"A{row['network']}"


class Resolver:
    def __init__(self, gaz: Gazetteer) -> None:
        self.gaz = gaz
        self.prior: dict[str, Counter] = defaultdict(Counter)
        self.cache: dict[tuple, dict] = {}

    def pick(self, cands: list[dict], hint: str, paren: str, ser: str) -> tuple[dict | None, str]:
        if len(cands) == 1:
            return cands[0], "eindeutig"
        pool = [c for c in cands if c["canton"] == hint] if hint else cands
        if hint and pool:
            if len(pool) == 1:
                return pool[0], "kanton"
        pool = pool or cands
        refs = [p.strip() for p in re.split(r"[,;]", paren) if p.strip()]
        if ser.startswith("A") and len(ser) > 1:
            refs.append(ser[1:].split("/")[0].strip())       # Netz der Charge A, z. B. «St. Gallen»
        for part in refs:
            ex, _ = self.gaz.candidates(split_locality(part)[0])
            ex = [e for e in ex if not math.isnan(e["lat"])]
            if ex:
                # die Zentrale selbst kann mehrdeutig sein: nächstes Paar nehmen
                near = [(dist_km(c, (e["lat"], e["lon"])), c) for c in pool for e in ex]
                near = [t for t in near if t[0] <= NEAR_KM]
                if near:
                    # in der Nähe der Zentrale geht eine Gemeinde 1914 einer gleichnamigen
                    # Postleitzahl-Ortschaft vor («Basel» im Netz Basel ist Basel BS)
                    gem_near = [t for t in near if t[1]["kind"] == "gemeinde_1914"]
                    return min(gem_near or near, key=lambda t: t[0])[1], "zentrale"
        # Eine Gemeinde 1914 dieses Namens schlägt gleichnamige Ortschaften anderswo (oft nur
        # Postleitzahl-Reste wie «Basel» in Basel-Land); die Kantons-Vorliebe des Bandes
        # entscheidet nur zwischen mehreren Gemeinden oder zwischen Ortschaften.
        gem = [c for c in pool if c["kind"] == "gemeinde_1914"]
        if len(gem) == 1:
            return gem[0], "gemeinde"
        pr = self.prior.get(ser)
        if pr and len({c["canton"] for c in pool}) > 1:
            ranked = sorted({c["canton"] for c in pool}, key=lambda k: -pr[k])
            if pr[ranked[0]] > 0 and pr[ranked[0]] > 2 * pr[ranked[1]]:
                pool = [c for c in pool if c["canton"] == ranked[0]]
                if len(pool) == 1:
                    return pool[0], "band"
        gem = [c for c in pool if c["kind"] == "gemeinde_1914"]
        if len(gem) == 1:
            return gem[0], "gemeinde"
        if len(pool) > 1 and all(dist_km(a, (b["lat"], b["lon"])) <= 10 for a in pool for b in pool):
            return (gem or pool)[0], "nah"
        return None, "mehrdeutig"

    def resolve(self, raw: str, ser: str, network: str) -> dict:
        ck = (raw, ser)
        if ck in self.cache:
            return self.cache[ck]
        out = {f: "" for f in PLACE_FIELDS}
        out["place_raw"] = raw
        source = raw or network
        method_base = "überschrift" if raw else "netz"
        man = self.gaz.manual.get(source)
        name, hint, paren = split_locality(source)
        out["exchange_raw"] = paren
        cands, how = self.gaz.candidates(name)
        if man:
            cands = [c for cs in self.gaz.cands.values() for c in cs
                     if (man.get("hist_code") and c["hist_code"] == man["hist_code"])
                     or (man.get("name") and c["name"] == man["name"] and c["canton"] == man.get("canton", c["canton"]))]
            how = "hand"
        c, why = self.pick(cands, hint, paren, ser) if cands else (None, "")
        if c is None and paren and not man:
            # Ortsteil unbekannt: auf die Zentrale zurückfallen
            first = re.split(r"[,;]", paren)[0]
            ecands, _ = self.gaz.candidates(split_locality(first)[0])
            c, why = self.pick(ecands, hint, "", ser) if ecands else (None, "")
            if c is not None:
                how, why = "zentrale", why
        if c is not None:
            out.update({
                "place_name": c["name"], "place_kind": c["kind"], "hist_code_1914": c["hist_code"],
                "municipality_1914": c["municipality_1914"], "bfs_today": c["bfs_today"], "canton": c["canton"],
                "lat": "" if math.isnan(c["lat"]) else round(c["lat"], 5),
                "lon": "" if math.isnan(c["lon"]) else round(c["lon"], 5),
                "place_method": f"{method_base}:{how}:{why}",
                "place_confidence": "hoch" if how in ("name", "hand") and why in ("eindeutig", "kanton", "zentrale")
                else "mittel",
                "_plz": c["plz"],
            })
        else:
            out.update({"place_method": f"{method_base}:{how or 'unbekannt'}:{why}", "place_confidence": "keine", "_plz": 0})
        self.cache[ck] = out
        return out


def phone_key(p: str) -> str:
    return re.sub(r"\D", "", p)


def resolve_all(rows: list[dict]) -> Counter:
    """Fügt jeder Zeile die Spalten PLACE_FIELDS hinzu; gibt Zähler zurück."""
    gaz = Gazetteer()
    res = Resolver(gaz)
    stats: Counter = Counter()

    # Pass 1: eindeutige Auflösungen → Kantons-Vorlieben je Band-Reihe
    for r in rows:
        name, hint, paren = split_locality(r["locality"] or r["network"])
        cands, _ = gaz.candidates(name)
        if len(cands) == 1:
            res.prior[series(r)][cands[0]["canton"]] += 1
    # Pass 2: auflösen
    for r in rows:
        r.update(res.resolve(r["locality"], series(r), r["network"]))

    # Läufe gleicher Überschrift je Band
    runs: list[list[dict]] = []
    prev = None
    for r in rows:
        k = (r["refcode"], r["locality"])
        if prev == k and runs:
            runs[-1].append(r)
        else:
            runs.append([r])
            prev = k
    plausible = set()
    for i, run in enumerate(runs):
        head = run[0]
        city = head["_plz"] >= CITY_PLZ
        # Charge A nennt den Ort je Eintrag, nicht als übertragene Überschrift
        if head["batch"] == "A" or len(run) <= CAP or city:
            plausible.add(i)
        for r in run:
            r["_run"] = i
    # Stimmen aus plausiblen Läufen: Abonnent → Ort
    votes: dict[tuple, Counter] = defaultdict(Counter)
    place_of: dict[str, dict] = {}
    cities: set[str] = set()

    def keys(r: dict) -> list[tuple]:
        n1 = key(r["name1"])
        out = []
        if n1 and phone_key(r["phone"]):
            out.append(("t", n1, phone_key(r["phone"])))
        if n1 and key(r["street"]):
            out.append(("s", n1, key(r["name2"]), key(r["street"])))
        return out

    for i in plausible:
        for r in runs[i]:
            if r["place_confidence"] in ("hoch", "mittel") and r["batch"] == "B":
                pk = r["hist_code_1914"] or f"{r['place_name']}|{r['canton']}"
                place_of[pk] = {f: r[f] for f in PLACE_FIELDS if f not in ("place_raw", "exchange_raw", "place_method", "place_confidence")}
                if r["_plz"] >= CITY_PLZ:
                    cities.add(pk)
                for k in keys(r):
                    votes[k][(pk, r["year"])] += 1

    def row_vote(r: dict) -> Counter:
        c: Counter = Counter()
        for k in keys(r):
            for (pk, y), n in votes.get(k, {}).items():
                if y != r["year"]:
                    c[pk] += 1
        return c

    def apply(r: dict, pk: str, method: str, conf: str) -> None:
        r.update(place_of[pk])
        r["place_method"] = method
        r["place_confidence"] = conf

    for i, run in enumerate(runs):
        if i in plausible:
            stats["zeilen in plausiblen läufen"] += len(run)
            continue
        stats["zeilen in unplausiblen läufen"] += len(run)
        rv = {id(r): row_vote(r) for r in run}
        total: Counter = Counter()
        by_page: dict[str, Counter] = defaultdict(Counter)
        for r in run:
            v = rv[id(r)]
            if v:
                top = v.most_common(1)[0][0]
                total[top] += 1
                by_page[r["page"]][top] += 1
        for r in run:
            v = rv[id(r)]
            pv = by_page.get(r["page"])
            page_pk = None
            if pv and sum(pv.values()) >= 5:
                pk, n = pv.most_common(1)[0]
                # nur Stadtblöcke seitenweise: eine Seite zusammengelegter Dörfer gehört
                # nicht einem Ort
                if pk in cities and n / sum(pv.values()) >= 0.6:
                    page_pk = pk
            if v and len(v) == 1:
                apply(r, next(iter(v)), "jahresabgleich:zeile", "hoch" if sum(v.values()) >= 2 else "mittel")
                stats["jahresabgleich:zeile"] += 1
            elif page_pk:
                apply(r, page_pk, "jahresabgleich:seite", "mittel")
                stats["jahresabgleich:seite"] += 1
            else:
                r["place_method"] += ":lauf-unplausibel"
                r["place_confidence"] = "unsicher"
                stats["unsicher"] += 1
    for r in rows:
        r.pop("_plz", None)
        r.pop("_run", None)
        stats[f"konfidenz {r['place_confidence']}"] += 1
    return stats

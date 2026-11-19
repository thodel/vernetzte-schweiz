"""Einträge in Basel ↔ Häuser des Historischen Grundbuchs Basel (EOS, ca. 1400–1700).

    python scripts/eos_link.py fetch   # Dossiers von thodel/eos_persons (gepinnter Commit) → data/ref/eos/
    python scripts/eos_link.py         # → links/eos_haeuser.csv, data/norm/eos_stats.json

Die Personen im Grundbuch lebten 150 bis 450 Jahre vor den Adress- und Telefonbüchern; verbunden
wird darum der **Wohnort**, das Haus (docs/eos.md):
- **Adresse:** Strasse und Hausnummer eines Eintrags = Adresse eines Dossiers. Das Grundbuch führt
  die Häuser unter der heutigen Adresse («Aeschenvorstadt 3»), mit Nummernbereichen («4-16») und
  Listen («20, 24»). Strassennamen werden angeglichen (Varianten «A / B», ohne «St.», ß, th,
  Umlaute; «Johanns-» = «Johann-»).
- **Hausname:** Nennt der Eintrag einen Hausnamen («zum Arm», «zur Mägd») und kennt das Grundbuch
  ihn an derselben Strasse, ist das Haus gefunden, auch wenn die Nummer abweicht. Stimmen Nummer und
  Hausname überein, prüft das die Nummer.
- **Familie:** Kommt der Familienname der Einheit unter den Personen des Hauses im Grundbuch vor,
  steht das dabei (gleicher Name im selben Haus, nicht notwendig dieselbe Familie).
"""

from __future__ import annotations

import csv
import gzip
import json
import re
import sys
import unicodedata
import urllib.request
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import NORM, ROOT, open_csv, write_csv  # noqa: E402
from link_ptt_ab import nkey  # noqa: E402

EOS_REPO = "thodel/eos_persons"
EOS_COMMIT = "e57f771f3dab2cfb473b427726680b0062b7555a"
REF = ROOT / "data" / "ref" / "eos"
OUT = ROOT / "links" / "eos_haeuser.csv"
FIELDS = ["entity_id", "dossier", "stufe", "hgb_adresse", "hgb_jahre", "hgb_personen", "beleg", "hausname", "familie",
          "quelle", "jahre", "adresse"]
HOUSE = re.compile(r"\b(?:zum|zur|zem|zun|im|zu der|zu dem)\s+([A-ZÄÖÜa-zäöü][\wäöüéè\-]+(?:\s+[A-ZÄÖÜ][\wäöü]+)?)")


def fetch() -> None:
    REF.mkdir(parents=True, exist_ok=True)
    for name in ("dossiers_geo.json", "dossiers.csv"):
        url = f"https://raw.githubusercontent.com/{EOS_REPO}/{EOS_COMMIT}/{name}"
        data = urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "vernetzte-schweiz"}), timeout=300).read()
        (REF / f"{name}.gz").write_bytes(gzip.compress(data, mtime=0))
        print(f"data/ref/eos/{name}.gz: {len(data):,} Bytes")


def fold(s: str) -> str:
    s = (s or "").lower().replace("ß", "ss")
    s = unicodedata.normalize("NFD", s)
    return "".join(c for c in s if not unicodedata.combining(c))


def street_keys(name: str) -> set[str]:
    """Schlüssel eines Strassennamens; mehrere bei «A / B» und Klammern."""
    name = re.sub(r"\(.*?\)", " ", name or "")
    keys = set()
    for part in name.split("/"):
        s = fold(part)
        s = re.sub(r"\b(st\.?|sankt|saint)\s+", "", s)
        s = s.replace("th", "t").replace("strasse", "str").replace("str.", "str").replace("gaesslein", "gasslein")
        s = re.sub(r"[^a-z]", "", s)
        s = re.sub(r"(johann|peter|leonhard|alban|martin|clara|elisabet)s", r"\1", s)
        if len(s) >= 4:
            keys.add(s)
    return keys


def numbers(addr: str) -> list[tuple[str, int]]:
    """Strasse und Nummern einer Grundbuch-Adresse: «Aeschengraben 4-16», «… 20, 24», «A 1 und B 2»."""
    out = []
    # «Freie Strasse Theil von 35 neben 33», «Utengasse Th. v. 3 neben 5»: das Haus ist ein Teil von 35
    addr = re.sub(r"\bTh(?:ei)?l?\.?\s*v(?:on)?\.?\s*(\d+[a-z]?)(?:\s+(?:neben|u\.|und)\s+\d+[a-z]?)?", r"\1", addr or "")
    for part in re.split(r"\s+und\s+", addr):
        m = re.match(r"(.+?)\s+(\d[\d\s,\-a-z]*)$", part.strip())
        if not m:
            continue
        street, nums = m.groups()
        for chunk in re.split(r"\s*,\s*", nums):
            r = re.match(r"(\d+)[a-z]?\s*-\s*(\d+)", chunk)
            if r:
                lo, hi = int(r.group(1)), int(r.group(2))
                if hi - lo <= 20:
                    out += [(street, n) for n in range(lo, hi + 1)]
            elif re.match(r"\d+", chunk):
                out.append((street, int(re.match(r"\d+", chunk).group())))
    return out


GENERIC_HOUSE = {"hus", "huse", "huses", "huss", "haus", "hauss", "behausung", "gesess", "herberg", "herberig", "gesellschaft",
                 "gesellschaftshaus", "zunfthaus", "zunft", "badstube", "badstuben", "garten", "hof", "keller", "laden",
                 "magazine", "hotel", "restaurant", "wirtschaft", "zum", "zur", "zem", "zer", "ze", "zu", "der", "dem", "den",
                 "roten", "rote", "rot", "schwarzen", "schwarz", "wilden", "wild", "alten", "alt", "neuen", "neu", "grossen",
                 "gross", "kleinen", "klein", "cleinen", "weissen", "weiss", "hohen", "hoch", "schonen", "schon", "guldin",
                 "goldenen", "golden", "obern", "obere", "untern", "vordern", "hintern", "und", "von", "vom", "sie", "im"}


def stem(w: str) -> str:
    """Hauptwort eines Hausnamens, alte Schreibung angeglichen («Megt» = «Mägd», «Wolff» = «Wolf»)."""
    w = fold(w)
    w = w.replace("ae", "e").replace("y", "i").replace("ck", "k").replace("th", "t").replace("dt", "t").replace("ph", "f")
    w = re.sub(r"(.)\1", r"\1", w)
    w = re.sub(r"d$", "t", w)
    w = w.replace("a", "e") if w.startswith("ma") else w   # Magd/Megt
    return w[:5]


def house_names(text: str) -> set[str]:
    """Hauptwörter der Hausnamen in einem Text («zum wilden Mann» → «man»; «Hus zer Megt» → «megt»)."""
    out = set()
    for m in re.finditer(r"\b(?:zum|zur|zem|zer|ze|zun|im|zu der|zu dem)\s+((?:[\wäöüÄÖÜéè]+\s+){0,2}[\wäöüÄÖÜéè]+)", text or "", re.I):
        words = [w for w in re.findall(r"[a-zäöüéè]+", fold(m.group(1))) if w not in GENERIC_HOUSE and len(w) >= 3]
        if words:
            out.add(stem(words[0]))
    return out


def variant_names(v: str) -> set[str]:
    """Hausnamen aus den Varianten des Grundbuchs («Hus zem Wolff | Wolff | Olsperg»)."""
    out = set()
    for part in (v or "").split("|"):
        part = part.strip()
        hn = house_names(part)
        if not hn:  # nackter Name: «Olsperg», «Löwenfelss»
            words = [w for w in re.findall(r"[a-zäöüéè]+", fold(part)) if w not in GENERIC_HOUSE and len(w) >= 3]
            hn = {stem(words[0])} if words else set()
        out |= hn
    return out


def main() -> None:
    feats = json.loads(gzip.open(REF / "dossiers_geo.json.gz").read())["features"]
    variants = {r["dossierid"]: r["variant_names"] for r in csv.DictReader(gzip.open(REF / "dossiers.csv.gz", "rt", encoding="utf-8"))}
    dos = {f["id"]: f for f in feats if f.get("type") in ("Liegenschaft", "Laden", "Keller")}
    by_addr: dict[tuple[str, int], set] = defaultdict(set)
    by_name: dict[tuple[str, str], set] = defaultdict(set)
    street_of: dict[str, set] = {}
    for d in dos.values():
        street_of[d["id"]] = street_keys(d["street"])
        for street, n in numbers(d["address"]):
            for k in street_keys(street) | street_of[d["id"]]:
                by_addr[(k, n)].add(d["id"])
        for hn in variant_names(variants.get(d["id"], "")):
            for k in street_of[d["id"]]:
                by_name[(k, hn)].add(d["id"])
        d["surnames"] = {nkey(p["n"].split()[-1]) for p in d.get("persons", []) if p.get("n")}

    # Einträge in Basel mit Strasse
    recs = []
    for r in open_csv(NORM / "ab_entries.csv"):
        if r["city"] == "basel" and r["street"]:
            recs.append(("ab", r["id"], int(r["volume"][:4]), r["street"], r["building_no"], r["text"]))
    for r in open_csv(NORM / "ptt_entries.csv.gz"):
        if r["municipality_1914"] == "Basel" and r["street_name"]:
            recs.append(("ptt", r["id"], int(r["year"]), r["street_name"], r["house_no"],
                         f"{r['name1']} {r['name2']} {r['supplement']}"))
    rec_ent = {m["record_id"]: m["entity_id"] for m in open_csv(ROOT / "links" / "entities.csv.gz")}
    ent_sk = {e["entity_id"]: nkey(e["surname"]) for e in open_csv(NORM / "entities.csv.gz") if e["municipality"] == "Basel"}

    stats, check = Counter(), Counter()
    hits: dict[tuple[str, str], dict] = {}
    for src, rid, year, street, no, text in recs:
        eid = rec_ent.get(rid)
        if not eid:
            continue
        keys = street_keys(street)
        stats[f"{src}:einträge"] += 1
        m = re.match(r"\d+", no or "")
        n = int(m.group()) if m else None
        by_a = set().union(*(by_addr.get((k, n), set()) for k in keys)) if n is not None else set()
        hn = house_names(text)
        by_h = set().union(*(by_name.get((k, h), set()) for k in keys for h in hn)) if hn else set()
        if any(k in {kk for s in street_of.values() for kk in s} for k in keys):
            stats[f"{src}:strasse_im_grundbuch"] += 1
        if by_h and n is not None:
            # Prüfung der Nummer: Kennt das Grundbuch den Hausnamen an dieser Strasse, steht er unter
            # derselben Nummer (gleich), höchstens zwei daneben (nachbar) oder anderswo (anders)?
            near = any(by_addr.get((k, n + dd), set()) & by_h for k in keys for dd in (-2, -1, 1, 2))
            check[f"{src}:{year // 10 * 10}:{'gleich' if by_a & by_h else 'nachbar' if near else 'anders'}"] += 1
        found = [(d, "adresse+hausname") for d in by_a & by_h] or \
                [(d, "hausname") for d in by_h] or [(d, "adresse") for d in by_a]
        if len({d for d, _ in found}) > 3:
            continue  # zu unbestimmt
        for d, how in found:
            h = hits.setdefault((eid, d), {"src": set(), "years": set(), "how": set(), "hn": set(), "addr": set()})
            h["src"].add(src); h["years"].add(year); h["how"].add(how); h["hn"] |= hn
            h["addr"].add(f"{street} {no}".strip())
            stats[f"{src}:{how}"] += 1
    rows = []
    for (eid, d), h in hits.items():
        f = dos[d]
        how = "adresse+hausname" if "adresse+hausname" in h["how"] else ("hausname" if "hausname" in h["how"] else "adresse")
        fam = ent_sk.get(eid, "") in f["surnames"]
        # Stufe: Hausname bestätigt die Nummer (sicher); Hausname an derselben Strasse oder Adresse im
        # Telefonbuch (Nummern wie heute: 77 % gleich, 91 % ±2, Prüfung über Hausnamen) wahrscheinlich;
        # nur Adresse im Adressbuch 1862 (Nummerierung nicht geprüft) möglich
        tier = ("sicher" if how == "adresse+hausname" else
                "wahrscheinlich" if how == "hausname" or "ptt" in h["src"] else "möglich")
        rows.append({"entity_id": eid, "dossier": d, "stufe": tier, "hgb_adresse": f["address"],
                     "hgb_jahre": f"{f.get('year_min', '')}–{f.get('year_max', '')}", "hgb_personen": f.get("n_persons", 0),
                     "beleg": how, "hausname": " ".join(sorted(h["hn"])), "familie": "ja" if fam else "",
                     "quelle": "+".join(sorted(h["src"])), "jahre": f"{min(h['years'])}–{max(h['years'])}",
                     "adresse": " | ".join(sorted(h["addr"]))[:120]})
        stats[f"einheiten:{how}"] += 1
        stats[f"stufe:{tier}"] += 1
        stats["einheiten:familie"] += fam
    rows.sort(key=lambda r: (r["dossier"], r["entity_id"]))
    write_csv(OUT, FIELDS, rows)
    out = {"paare": len(rows), "einheiten": len({r["entity_id"] for r in rows}), "häuser": len({r["dossier"] for r in rows}),
           **dict(sorted(stats.items())), "nummernprüfung": dict(sorted(check.items())), "eos_commit": EOS_COMMIT}
    (NORM / "eos_stats.json").write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n")
    print(json.dumps(out, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    fetch() if sys.argv[1:2] == ["fetch"] else main()

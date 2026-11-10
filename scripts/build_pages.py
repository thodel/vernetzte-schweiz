"""M4: Daten für Suche, Einheiten-, Adress- und Ortsseiten → site/data/.

    python scripts/build_pages.py

Liest nur Dateien im Repo (data/norm/, links/). Alles wird in Teile zerlegt, damit der
Browser nur lädt, was eine Seite braucht:

Die Teile sind gzip-gepackt (`.json.gz`); der Browser entpackt sie.

- `names/<xx>.json.gz` — Suchindex, nach den ersten zwei Buchstaben des Familien- bzw.
  Firmennamens (ohne Akzente, klein); je Einheit eine kurze Zeile.
- `e/<xx>.json.gz` — Einheiten mit allen Einträgen, Normdaten und möglichen weiteren
  Adressbuch-Einträgen; `xx` = Zeichen 2–3 der `entity_id`.
- `a/<xx>.json.gz` — Adressen (Gemeinde, Strasse, Hausnummer) mit den Einträgen aller Jahre;
  `xx` = FNV-1a des Adressschlüssels, letztes Byte hex (gleich gerechnet in app.js).
- `g/<xx>.json.gz` (FNV des Gemeindenamens) und `places.json` — Gemeinden 1914:
  Einträge je Jahr, häufigste Namen.
"""

from __future__ import annotations

import gzip
import json
import re
import shutil
import sys
import tomllib
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from cluster import street  # noqa: E402
from common import NORM, ROOT, open_csv  # noqa: E402
from link_ptt_ab import house, num  # noqa: E402

OUT = ROOT / "site" / "data"
CITY_LABEL = {"aarau": "Aarau", "basel": "Basel"}
KIND_LABEL = {"einwohner": "Einwohner", "berufe": "Berufe", "bewohner": "Gebäude", "behoerden": "Behörden"}


def fold(s: str) -> str:
    """Klein, ohne Akzente, nur Buchstaben a–z (wie fold() in app.js)."""
    s = (s or "").replace("ß", "ss").replace("æ", "ae").replace("œ", "oe").replace("Æ", "ae").replace("Œ", "oe")
    s = unicodedata.normalize("NFD", s.lower())
    return re.sub(r"[^a-z]", "", "".join(c for c in s if not unicodedata.combining(c)))


def fnv(s: str) -> str:
    """FNV-1a 32 über UTF-8, letztes Byte als zwei Hex-Zeichen (wie fnv() in app.js)."""
    h = 0x811C9DC5
    for b in s.encode("utf-8"):
        h ^= b
        h = (h * 0x01000193) & 0xFFFFFFFF
    return f"{h & 0xFF:02x}"


def name_shard(label: str) -> str:
    k = fold(re.sub(r"^(von|v\.|de|du|la|le|van|zum|zur)\s+", "", label.strip(), flags=re.I))
    return (k + "__")[:2] if k else "__"


def addr_key(muni: str, st: str, no: str) -> str:
    return f"{muni}|{st}|{no}"


def dump(path: Path, obj) -> None:
    """JSON; endet der Name auf .gz, gepackt und ohne Zeitstempel (der Browser entpackt mit
    DecompressionStream). GitHub Pages liefert .gz-Dateien unverändert aus."""
    path.parent.mkdir(parents=True, exist_ok=True)
    data = json.dumps(obj, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    if path.suffix == ".gz":
        data = gzip.compress(data, mtime=0)
    path.write_bytes(data)


def main() -> None:
    with open(ROOT / "config" / "sources.toml", "rb") as f:
        cfg = tomllib.load(f)
    vol_urls = {c["id"]: c.get("volume_urls", {}) for c in cfg["city"]}
    summ = {s["entity_id"]: s for s in open_csv(NORM / "entities.csv.gz")}
    member = {m["record_id"]: m["entity_id"] for m in open_csv(ROOT / "links" / "entities.csv.gz")}
    auth = {a["entity_id"]: a for a in open_csv(ROOT / "links" / "authority.csv")}

    records: dict[str, list] = defaultdict(list)
    addresses: dict[str, dict] = {}
    place_years: dict[str, Counter] = defaultdict(Counter)
    place_geo: dict[str, list] = defaultdict(lambda: [0.0, 0.0, 0])
    place_meta: dict[str, dict] = {}

    def add_address(muni: str, raw_street: str, st: str, no: str, eid: str, rec: dict) -> str:
        if not (st and no):
            return ""
        k = addr_key(muni, st, no)
        a = addresses.setdefault(k, {"k": k, "m": muni, "names": Counter(), "r": []})
        a["names"][f"{raw_street.strip()} {no}"] += 1
        a["r"].append({"y": rec["y"], "s": rec["s"], "e": eid, "t": rec["t"]})
        return k

    # Telefonbücher
    ptt_by_id = {}
    for r in open_csv(NORM / "ptt_entries.csv.gz"):
        muni = r["municipality_1914"]
        if muni and r["place_confidence"] in ("hoch", "mittel"):
            place_years[muni][int(r["year"])] += 1
            if r["lat"]:
                g = place_geo[muni]
                g[0] += float(r["lat"])
                g[1] += float(r["lon"])
                g[2] += 1
            place_meta.setdefault(muni, {"canton": r["canton"], "bfs": r["bfs_today"]})
        eid = member.get(r["id"])
        if not eid:
            continue
        ptt_by_id[r["id"]] = r
        text = " | ".join(x for x in (", ".join(y for y in (r["name1"], r["name2"]) if y), r["supplement"]) if x)
        rec = {"id": r["id"], "y": int(r["year"]), "s": "ptt", "t": text, "a": r["street"], "ph": r["phone"],
               "c": f"PTT-Archiv P-260, {r['refcode']}, S. {r['page']}"}
        no = num(house(r["house_no"]))
        rec["ak"] = add_address(muni, r["street_name"] or r["street"], street(r["street_name"]), no, eid, rec)
        records[eid].append(rec)

    # Adressbücher
    ab_text = {}
    for r in open_csv(NORM / "ab_entries.csv"):
        ab_text[r["id"]] = r
        eid = member.get(r["id"])
        if not eid:
            continue
        city = r["city"]
        rec = {"id": r["id"], "y": int(r["volume"]), "s": "ab", "t": r["text"],
               "a": " ".join(x for x in (r["street"], r["building_no"]) if x), "ph": "",
               "c": f"Adressbuch {CITY_LABEL[city]} {r['volume']}" + (f", S. {r['page']}" if r["page"] else "")
                    + f" ({KIND_LABEL.get(r['kind'], r['kind'])})"}
        if vol_urls[city].get(r["volume"]):
            rec["u"] = vol_urls[city][r["volume"]]
        no = num(house(r["building_no"]))
        rec["ak"] = add_address(CITY_LABEL[city], r["street"], street(r["street"]), no, eid, rec)
        records[eid].append(rec)

    # mögliche weitere Adressbuch-Einträge (M2-Paare ausserhalb der Einheit)
    maybe: dict[str, list] = defaultdict(list)
    for l in open_csv(ROOT / "links" / "ptt_ab.csv"):
        eid = member.get(l["ptt_id"])
        if eid and member.get(l["ab_id"]) != eid and l["ab_id"] in ab_text:
            maybe[eid].append({"id": l["ab_id"], "y": int(l["ab_volume"]), "tier": l["tier"], "t": ab_text[l["ab_id"]]["text"]})

    # Einheiten und Suchindex
    shards: dict[str, dict] = defaultdict(dict)
    names: dict[str, list] = defaultdict(list)
    for eid, s in summ.items():
        rs = sorted(records.get(eid, []), key=lambda r: (r["y"], r["s"], r["id"]))
        if not rs:
            continue
        label = s["name"] if s["kind"] == "firma" and s["name"] else ", ".join(x for x in (s["surname"], s["forename"]) if x)
        a = auth.get(eid)
        ent = {"id": eid, "k": s["kind"], "n": label, "m": s["municipality"], "c": s["canton"],
               "y": [int(s["first_year"]), int(s["last_year"])], "ph": s["phones"], "o": s["occupations"], "r": rs}
        if a:
            ent["au"] = {k: a[k] for k in ("qid", "label", "birth", "death", "hls_id", "gnd", "tier", "source",
                                           "evidence", "hls_check")}
        seen = {r["id"] for r in rs}
        mb = sorted({m["id"]: m for m in maybe.get(eid, []) if m["id"] not in seen}.values(), key=lambda m: (m["y"], m["id"]))
        if mb:
            ent["mb"] = mb[:20]
        shards[eid[1:3]][eid] = ent
        names[name_shard(s["surname"] or label)].append(
            [eid, label, s["municipality"], int(s["first_year"]), int(s["last_year"]), "f" if s["kind"] == "firma" else "p",
             len(rs), (a["tier"][0] if a else ""), s["occupations"][:60]])

    if OUT.exists():
        for sub in ("e", "a", "g", "names"):
            shutil.rmtree(OUT / sub, ignore_errors=True)
    for k, v in shards.items():
        dump(OUT / "e" / f"{k}.json.gz", v)
    for k, v in names.items():
        v.sort(key=lambda x: (fold(x[1]), x[2], x[3]))
        dump(OUT / "names" / f"{k}.json.gz", v)

    # Adressen
    ashards: dict[str, dict] = defaultdict(dict)
    for k, a in addresses.items():
        a["r"].sort(key=lambda r: (r["y"], r["s"]))
        ashards[fnv(k)][k] = {"m": a["m"], "n": a["names"].most_common(1)[0][0], "r": a["r"]}
    for k, v in ashards.items():
        dump(OUT / "a" / f"{k}.json.gz", v)

    # Gemeinden
    ents_by_place: dict[str, Counter] = defaultdict(Counter)
    surnames: dict[str, Counter] = defaultdict(Counter)
    for s in summ.values():
        ents_by_place[s["municipality"]][s["kind"]] += 1
        if s["kind"] == "person" and s["surname"]:
            surnames[s["municipality"]][s["surname"].strip()] += 1
    places, gshards = [], defaultdict(dict)
    for muni in sorted(set(place_years) | set(ents_by_place), key=fold):
        g = place_geo.get(muni)
        meta = place_meta.get(muni, {})
        geo = [round(g[0] / g[2], 5), round(g[1] / g[2], 5)] if g and g[2] else None
        years = dict(sorted(place_years.get(muni, {}).items()))
        gshards[fnv(muni)][muni] = {
            "n": muni, "c": meta.get("canton", ""), "bfs": meta.get("bfs", ""), "geo": geo, "years": years,
            "ent": dict(ents_by_place.get(muni, {})), "top": surnames[muni].most_common(10),
        }
        places.append([muni, meta.get("canton", ""), sum(years.values())])
    for k, v in gshards.items():
        dump(OUT / "g" / f"{k}.json.gz", v)
    dump(OUT / "places.json", places)
    print(f"site/data: {sum(len(v) for v in shards.values())} Einheiten in {len(shards)} Teilen, "
          f"{len(addresses)} Adressen, {len(places)} Gemeinden, Suchindex {len(names)} Teile")


if __name__ == "__main__":
    main()

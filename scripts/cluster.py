"""M3, Teil 1: Einträge derselben Person oder Firma über die Jahre bündeln.

    python scripts/cluster.py

Ein **Eintrag** ist eine Zeile eines Telefonbuch-Jahrgangs oder eines Adressbuch-Bandes.
Eine **Einheit** (Person oder Firma) ist die Menge der Einträge, die sie meinen. Gebündelt
wird je Gemeinde 1914 und Namensschlüssel (Personen: Familienname, Firmen: Leitname);
Personen und Firmen bleiben getrennt.

Kanten (Belege, dass zwei Einträge dieselbe Einheit meinen):
- **Telefonbuch ↔ Telefonbuch**, höchstens 5 Jahre Abstand: gleiche Telefonnummer, Vorname,
  Adresse, Beruf (Regeln in `edge`).
- **Adressbuch ↔ Adressbuch** desselben Bandes (Einwohner-, Berufs-, Gebäudeverzeichnis)
  und benachbarter Bände: dieselben Regeln ohne Telefonnummer.
- **Telefonbuch ↔ Adressbuch**: die Paare aus M2 (`links/ptt_ab.csv`) der Stufen `sicher`
  und `wahrscheinlich`. `möglich` bleibt ein Paar und bündelt nicht.

Die Kanten werden nach Stärke verarbeitet. Zwei Bündel werden nur vereinigt, wenn nichts
widerspricht (`conflict`): zwei unvereinbare Vornamen, verschiedene Allianznamen, Witwe und
Nicht-Witwe, oder zwei gleichzeitige Einträge, die nicht dieselbe Einheit sein können
(Vater und Sohn im selben Jahrgang). So verkettet «J.» nicht Johann und Jakob.

Ausgabe:
- links/entities.csv.gz — je Eintrag die Einheit (record_id → entity_id)
- links/entity_edges.csv.gz — die Kanten, die zur Bündelung führten, mit Belegen
- data/norm/entities.csv.gz — je Einheit Name, Ort, Jahre, Nummern, Adressen
- data/norm/cluster_stats.json
"""

from __future__ import annotations

import csv
import hashlib
import json
import re
import sys
from collections import Counter, defaultdict
from functools import lru_cache
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from common import NORM, config, open_csv, write_csv  # noqa: E402
from link_ptt_ab import (  # noqa: E402
    LINKS, NAME_PARTICLES, WIDOW, compare_forenames, firm_key, forename_tokens, house, initial, nkey,
    num, prepare_ptt, skey, stems,
)
from parse_ptt import FIRM  # noqa: E402

PHONE_GAP = 3        # gleiche Nummer allein verbindet nur über so viele Jahre
MAX_GAP = 5          # Jahre zwischen zwei direkt verbundenen Einträgen
# Bindewörter fallen weg; Rechtsformen bleiben, vereinheitlicht: «Preiswerk Söhne» und
# «Preiswerk & Co.» sind zwei Firmen
FIRM_FILLER = {"und", "u", "et", "e", "firma", "vorm", "vormals"}
FIRM_FORM = {
    "co": "&co", "cie": "&co", "comp": "&co", "ci": "&co", "cia": "&co", "compagnie": "&co",
    "ag": "ag", "sa": "ag", "aktiengesellschaft": "ag", "sohne": "sohne", "soehne": "sohne", "fils": "sohne",
    "gebr": "gebr", "gebrueder": "gebr", "gebruder": "gebr", "freres": "gebr", "frere": "gebr",
    "nachf": "nachf", "nachfolger": "nachf", "succ": "nachf", "successeur": "nachf", "successeurs": "nachf",
    "erben": "erben", "geschw": "geschw",
}
# Nachfolger und Söhne sind eine andere Einheit als der Namensgeber («Winter, G.'s Söhne»)
SUCCESSOR = re.compile(r"\b(Söhne|Sohn|Soehne|Erben|Nachf|Nachfolger|Fils|Successeurs?|Succ)\b", re.I)
# Witwe, auch angehängt («MmeVve»)
WIDOW_ANY = re.compile(r"(Wwe|Witwe|Wittwe|Vve|Veuve)\b|\b(Wb|Ved)\b")
# «Derselbe (Wohnung)»: zweite Nummer des vorangehenden Eintrags
DERSELBE = re.compile(r"^(Derselbe|Dieselbe|Dasselbe|Le même|La même|Idem)\b", re.I)
ENTITY_FIELDS = ["record_id", "entity_id", "source", "year", "municipality"]
EDGE_FIELDS = ["a", "b", "kind", "strength", "evidence"]
SUMMARY_FIELDS = [
    "entity_id", "kind", "municipality", "bfs_today", "canton", "name", "surname", "forename",
    "first_year", "last_year", "years", "n_ptt", "n_ab", "phones", "addresses", "occupations",
]


def firm_name_key(name: str) -> str:
    """Firmenname ohne Rechtsform und Bindewörter, Wörter sortiert («Gebr. Sulzer» = «Sulzer Gebr.»)."""
    words = [nkey(w) for w in re.findall(r"[A-Za-zÀ-ÿ]+", name or "")]
    return " ".join(sorted({FIRM_FORM.get(w, w) for w in words
                            if w and w not in FIRM_FILLER and w not in NAME_PARTICLES}))


def street(raw: str) -> str:
    """Strassenschlüssel wie in M2, dazu abgekürzte Grundwörter ausgeschrieben
    («Schanzeng.» = «Schanzengasse», «Münsterpl.» = «Münsterplatz»)."""
    k = skey(raw)
    if re.search(r"(str|stras)$", k):
        return re.sub(r"(str|stras)$", "strase", k)
    if (raw or "").rstrip().endswith(".") and len(k) > 4:
        for pat, rep in ((r"vorst$", "vorstat"), (r"pl$", "plaz"), (r"w$", "weg"), (r"g$", "gase")):
            if re.search(pat, k):
                return re.sub(pat, rep, k)
    return k


def line_key(*parts: str) -> str:
    """Name und Namenzusatz der Zeile, ohne Satzzeichen («Orelli, Frau Prof.»)."""
    return " ".join(nkey(w) for p in parts for w in re.findall(r"[A-Za-zÀ-ÿ]+", p or "") if nkey(w))


# ── Einträge vorbereiten ─────────────────────────────────────────────────

NAME_COLUMNS = ("name1", "name2", "surname", "alliance_name", "forename", "initials", "title", "entity_type")


def resolve_derselbe(rows: list[dict]) -> None:
    """«Derselbe»-Zeilen übernehmen Namen und Art des Eintrags, auf den sie verweisen
    (parent_id, sonst der vorangehende Eintrag derselben Ausgabe); Nummer und Adresse bleiben."""
    by_id = {r["id"]: r for r in rows}
    prev: dict = {}
    for r in sorted(rows, key=lambda r: (r["refcode"], int(r["seq"] or 0))):
        if DERSELBE.match(r["name1"]):
            p = by_id.get(r["parent_id"]) or prev.get(r["refcode"])
            if p is not None:
                for c in NAME_COLUMNS:
                    r[c] = p[c]
                r["_same_as"] = p["id"]
        else:
            prev[r["refcode"]] = r


def ptt_records(cfg: dict) -> list[dict]:
    out = []
    rows = open_csv(NORM / "ptt_entries.csv.gz")
    resolve_derselbe(rows)
    for r in rows:
        if r["place_confidence"] not in ("hoch", "mittel") or not r["municipality_1914"]:
            continue
        if not prepare_ptt(r):
            continue
        out.append({
            "id": r["id"], "source": "ptt", "year": int(r["year"]), "muni": r["municipality_1914"],
            "bfs": r["bfs_today"], "canton": r["canton"], "sk": r["_sk"], "firm": r["_firm"],
            "fn": tuple(r["_fn"]), "ak": r["_ak"],
            "widow": r["_widow"] or bool(WIDOW_ANY.search(" ".join((r["name1"], r["name2"], r["supplement"])))), "st": street(r["street_name"]), "no": num(r["_no"]),
            "line": line_key(r["name1"], r["name2"]),
            "full": line_key(r["name1"], r["name2"], r["supplement"], r["street"]),
            "succ": bool(SUCCESSOR.search(" ".join((r["name1"], r["name2"], r["supplement"])))),
            "occ": frozenset(r["_occ"]), "phone": r["phone_norm"], "fnk": firm_name_key(r["name1"]) if r["_firm"] else "",
            "slot": ("ptt", r["refcode"]),
            "name": (r["name1"] + (", " + r["name2"] if r["name2"] else "")).strip(),
            "surname": r["surname"] or r["name1"], "forename": r["forename"] or r["name2"],
            "occupation": r["occupation"] or r["supplement"],
            "address": r["street"], "same_as": r.get("_same_as", ""),
        })
    return out


def ab_records(cfg: dict) -> list[dict]:
    labels = {c["id"]: c["label"] for c in cfg["city"]}
    out = []
    for r in open_csv(NORM / "ab_entries.csv"):
        firm = r["entry_type"] == "firma" or bool(FIRM.search(f"{r['surname']} {r['forename']}"))
        sk = firm_key(r["surname"]) if firm else nkey(r["surname"])
        if not sk or len(sk) < 2:
            continue
        out.append({
            "id": r["id"], "source": "ab", "year": int(r["volume"]), "muni": labels[r["city"]],
            "bfs": "", "canton": "", "sk": sk, "firm": firm,
            "fn": tuple(forename_tokens(r["forename"])) if not firm else (), "ak": nkey(r["alliance_name"]),
            "widow": bool(WIDOW.search(r["text"])), "st": street(r["street"]), "line": "", "full": "", "succ": bool(SUCCESSOR.search(r["text"])), "no": num(house(r["building_no"])),
            "occ": frozenset(stems(r["occupation"])), "phone": "", "fnk": firm_name_key(r["surname"]) if firm else "",
            "slot": ("ab", r["volume"]), "kind": r["kind"],
            "name": r["text"][:120], "surname": r["surname"], "forename": r["forename"],
            "occupation": r["occupation"], "address": " ".join(x for x in (r["street"], r["building_no"]) if x),
            "same_as": "",
        })
    return out


# ── Kanten ────────────────────────────────────────────────────────────────

def edge(a: dict, b: dict) -> tuple[int, list[str]] | None:
    """Stärke (höher = früher verarbeitet) und Belege, oder None. Gleiche Gemeinde, gleicher
    Namensschlüssel und gleiche Art (Person/Firma) sind vorausgesetzt."""
    if a["ak"] and b["ak"] and a["ak"] != b["ak"]:
        return None
    if a["widow"] != b["widow"] or a["succ"] != b["succ"]:
        return None
    phone = bool(a["phone"] and a["phone"] == b["phone"])
    street = bool(a["st"] and a["st"] == b["st"])
    number = street and bool(a["no"] and a["no"] == b["no"])
    occ = bool(a["occ"] & b["occ"])
    ev = [e for e, ok in (("telefon", phone), ("strasse", street), ("hausnummer", number), ("beruf", occ)) if ok]
    same_slot = a["slot"] == b["slot"]
    if a["firm"]:
        if not same_slot and abs(a["year"] - b["year"]) <= PHONE_GAP and a["full"] and a["full"] == b["full"]:
            return (5, ["ganze-zeile"] + ev)
        named = bool(a["fnk"] and a["fnk"] == b["fnk"])
        if named:
            ev.insert(0, "firmenname")
        if same_slot:
            ok = named and (phone or number)
        else:
            ta, tb = set(a["fnk"].split()), set(b["fnk"].split())
            ok = (named and (phone or street or occ)) or (phone and street and (ta <= tb or tb <= ta)) or \
                 (phone and abs(a["year"] - b["year"]) <= PHONE_GAP)
        return (6 if phone and named else 4 if named else 3, ev) if ok else None
    fn = compare_forenames(list(a["fn"]), list(b["fn"]))
    if fn == "widerspruch":
        return None
    if fn:
        ev.insert(0, f"vorname:{fn}")
    if a["ak"] and a["ak"] == b["ak"]:
        ev.append("allianzname")
    alliance = "allianzname" in ev
    # gleiche Zeile: Name und Namenzusatz (Ämter, «Frau Prof.», nicht erkannte Vornamen),
    # oder die ganze Zeile mit Zusatz und Adresse
    near = abs(a["year"] - b["year"]) <= PHONE_GAP
    full = near and bool(a["full"] and a["full"] == b["full"])
    line = bool(a["line"] and a["line"] == b["line"])
    if full:
        ev.insert(0, "ganze-zeile")
    elif line:
        ev.insert(0, "zeile")
    if same_slot:
        # derselbe Jahrgang/Band: zweite Nummer derselben Person, oder dieselbe Person in
        # Einwohner-, Berufs- und Gebäudeverzeichnis
        if a["source"] == "ab":
            ok = (fn and (number or (fn != "initiale" and (street or occ or alliance)))) or \
                 (fn in ("gleich", "abkürzung") and not a["no"] and not b["no"])
        else:
            ok = (phone and (fn or alliance or number or not (a["fn"] and b["fn"]))) or \
                 (fn in ("gleich", "abkürzung") and number)
        return (5, ev) if ok else None
    if phone and (fn or alliance or street or line):
        return (7 if fn and fn != "initiale" else 6, ev)
    if full:
        return (5, ev)
    if line and near and (street or not (a["st"] or b["st"])):
        return (4, ev)
    if line and (street or occ):
        return (4, ev)
    if phone and abs(a["year"] - b["year"]) <= PHONE_GAP:
        # gleiche Nummer, gleicher Familienname, kein Widerspruch: die Zeile ist oft verlesen
        return (4, ev)
    if fn in ("gleich", "abkürzung") and (street or occ or alliance):
        return (5 if street else 4, ev)
    if fn == "initiale" and number:
        return (4, ev)
    if fn == "initiale" and street and (occ or alliance):
        return (3, ev)
    if not fn and number and (occ or alliance):
        return (3, ev)
    return None


def distinct(a: dict, b: dict) -> bool:
    """Zwei Einträge desselben Bandes (Telefonbuch: derselben Ausgabe) sind sicher zwei
    Einheiten: Eine Einheit darf mehrfach stehen (zweite Nummer, Geschäft und Wohnung,
    Einwohner- und Berufsverzeichnis), aber nicht als Vater und Sohn mit eigener Nummer.
    Getrennt sind sie, wenn weder Nummer noch Adresse noch ein ausgeschriebener Vorname sie
    verbindet."""
    if a["same_as"] == b["id"] or b["same_as"] == a["id"]:
        return False
    if a["firm"]:
        return bool(a["fnk"] and b["fnk"] and a["fnk"] != b["fnk"])
    if (a["ak"] and b["ak"] and a["ak"] != b["ak"]) or a["widow"] != b["widow"] or a["succ"] != b["succ"]:
        return True
    fn = compare_forenames(list(a["fn"]), list(b["fn"]))
    if fn == "widerspruch":
        return True
    if fn in ("gleich", "abkürzung") or (a["phone"] and a["phone"] == b["phone"]):
        return False
    same_house = a["st"] and a["st"] == b["st"] and (a["no"] == b["no"] or not (a["no"] and b["no"]))
    return not same_house


# ── Bündeln mit Widerspruchsprüfung ────────────────────────────────────────

class Clusters:
    """Union-Find; je Bündel ein Steckbrief (Witwe, Nachfolger, Allianznamen, Vornamen,
    Einträge je Band), damit die Widerspruchsprüfung nicht alle Einträge neu liest."""

    def __init__(self, recs: list[dict]):
        self.recs = recs
        self.parent = list(range(len(recs)))
        self.members = {i: [i] for i in range(len(recs))}
        self.info = {}
        for i, r in enumerate(recs):
            self.info[i] = {"widow": r["widow"], "succ": r["succ"], "aks": {r["ak"]} - {""},
                            "fns": {r["fn"]} - {()}, "slots": {r["slot"]: [r]}}

    def find(self, i: int) -> int:
        while self.parent[i] != i:
            self.parent[i] = self.parent[self.parent[i]]
            i = self.parent[i]
        return i

    def conflict(self, ra: int, rb: int) -> str:
        A, B = self.info[ra], self.info[rb]
        if A["widow"] != B["widow"]:
            return "witwe"
        if A["succ"] != B["succ"]:
            return "nachfolger"
        if A["aks"] and B["aks"] and not A["aks"] & B["aks"]:
            return "allianzname"
        for x in A["fns"]:
            for y in B["fns"]:
                if _contradicts(x, y):
                    return "vorname"
        small, big = (A, B) if len(A["slots"]) <= len(B["slots"]) else (B, A)
        for slot, ys in small["slots"].items():
            for x in big["slots"].get(slot, ()):
                for y in ys:
                    if distinct(x, y):
                        return "gleichzeitig"
        return ""

    def union(self, i: int, j: int) -> str:
        ri, rj = self.find(i), self.find(j)
        if ri == rj:
            return "schon"
        why = self.conflict(ri, rj)
        if why:
            return why
        if len(self.members[ri]) < len(self.members[rj]):
            ri, rj = rj, ri
        self.parent[rj] = ri
        self.members[ri] += self.members.pop(rj)
        A, B = self.info[ri], self.info.pop(rj)
        A["widow"] |= B["widow"]
        A["succ"] |= B["succ"]
        A["aks"] |= B["aks"]
        A["fns"] |= B["fns"]
        for slot, ys in B["slots"].items():
            A["slots"].setdefault(slot, []).extend(ys)
        return ""


@lru_cache(maxsize=None)
def _contradicts(x: tuple, y: tuple) -> bool:
    return compare_forenames(list(x), list(y)) == "widerspruch"


def block_edges(block: list[int], recs: list[dict]) -> list[tuple[int, int, int, list[str]]]:
    out = []
    block = sorted(block, key=lambda i: recs[i]["year"])
    for x, i in enumerate(block):
        a = recs[i]
        for j in block[x + 1:]:
            b = recs[j]
            if b["year"] - a["year"] > MAX_GAP:
                break
            if a["source"] != b["source"]:
                continue  # Telefonbuch ↔ Adressbuch kommt aus M2
            e = edge(a, b)
            if e:
                out.append((e[0], i, j, e[1]))
    return out


def entity_id(ids: list[str]) -> str:
    return "e" + hashlib.sha1(min(ids).encode()).hexdigest()[:10]


def summarise(eid: str, rs: list[dict]) -> dict:
    rs = sorted(rs, key=lambda r: (r["year"], r["source"]))
    ptt = [r for r in rs if r["source"] == "ptt"]

    def common(field: str, pool: list[dict]) -> str:
        c = Counter(r[field].strip() for r in pool if r[field].strip())
        return c.most_common(1)[0][0] if c else ""
    forenames = Counter(r["forename"].strip() for r in rs if r["forename"].strip())
    full = [f for f in forenames if not re.search(r"\b\w{1,2}\.", f)]
    forename = max(full, key=lambda f: (forenames[f], len(f))) if full else common("forename", rs)
    years = sorted({r["year"] for r in rs})
    return {
        "entity_id": eid, "kind": "firma" if rs[0]["firm"] else "person", "municipality": rs[0]["muni"],
        "bfs_today": common("bfs", rs), "canton": common("canton", rs),
        "name": common("name", ptt or rs) if rs[0]["firm"] else "",
        "surname": common("surname", ptt or rs), "forename": forename if not rs[0]["firm"] else "",
        "first_year": years[0], "last_year": years[-1], "years": " ".join(map(str, years)),
        "n_ptt": len(ptt), "n_ab": len(rs) - len(ptt),
        "phones": " ".join(sorted({r["phone"] for r in ptt if r["phone"]}, key=lambda p: (len(p), p))),
        "addresses": " | ".join(dict.fromkeys(r["address"] for r in reversed(rs) if r["address"]))[:300],
        "occupations": " | ".join(dict.fromkeys(r["occupation"] for r in rs if r["occupation"]))[:200],
    }


def main() -> None:
    cfg = config()
    recs = ptt_records(cfg) + ab_records(cfg)
    pos = {r["id"]: i for i, r in enumerate(recs)}
    blocks = defaultdict(list)
    for i, r in enumerate(recs):
        blocks[(r["muni"], r["sk"], r["firm"])].append(i)
    edges = []
    for block in blocks.values():
        if len(block) > 1:
            edges += block_edges(block, recs)
    for i, r in enumerate(recs):
        j = pos.get(r["same_as"])
        if j is not None:
            edges.append((9, j, i, ["derselbe"]))
    m2 = 0
    for l in csv.DictReader(open(LINKS / "ptt_ab.csv", encoding="utf-8")):
        if l["tier"] in ("sicher", "wahrscheinlich") and "firma-person" not in l["evidence"]:
            i, j = pos.get(l["ptt_id"]), pos.get(l["ab_id"])
            if i is not None and j is not None and recs[i]["firm"] == recs[j]["firm"]:
                edges.append((8 if l["tier"] == "sicher" else 5, i, j, ["m2:" + l["tier"]] + l["evidence"].split("+")))
                m2 += 1
    edges.sort(key=lambda e: (-e[0], recs[e[1]]["id"], recs[e[2]]["id"]))
    cl = Clusters(recs)
    outcome, kept = Counter(), []
    for s, i, j, ev in edges:
        why = cl.union(i, j)
        outcome[why or "vereinigt"] += 1
        if not why:
            kept.append({"a": recs[i]["id"], "b": recs[j]["id"],
                         "kind": f"{recs[i]['source']}-{recs[j]['source']}", "strength": s, "evidence": "+".join(ev)})
    groups = defaultdict(list)
    for i in range(len(recs)):
        groups[cl.find(i)].append(i)
    members, summaries = [], []
    for idxs in groups.values():
        rs = [recs[i] for i in idxs]
        eid = entity_id([r["id"] for r in rs])
        summaries.append(summarise(eid, rs))
        members += [{"record_id": r["id"], "entity_id": eid, "source": r["source"], "year": r["year"],
                     "municipality": r["muni"]} for r in rs]
    members.sort(key=lambda r: r["record_id"])
    summaries.sort(key=lambda r: (r["municipality"], r["surname"], r["forename"], r["entity_id"]))
    kept.sort(key=lambda r: (r["a"], r["b"]))
    write_csv(LINKS / "entities.csv.gz", ENTITY_FIELDS, members)
    write_csv(LINKS / "entity_edges.csv.gz", EDGE_FIELDS, kept)
    write_csv(NORM / "entities.csv.gz", SUMMARY_FIELDS, summaries)
    size = Counter(len(v) for v in groups.values())
    multi = [s for s in summaries if int(s["n_ptt"]) + int(s["n_ab"]) > 1]
    stats = {
        "records": len(recs), "entities": len(summaries), "entities_multi": len(multi),
        "records_in_multi": sum(int(s["n_ptt"]) + int(s["n_ab"]) for s in multi),
        "with_ptt_and_ab": sum(1 for s in summaries if int(s["n_ptt"]) and int(s["n_ab"])),
        "span_10y": sum(1 for s in summaries if int(s["last_year"]) - int(s["first_year"]) >= 10),
        "edges": dict(outcome), "m2_edges": m2,
        "by_kind": dict(Counter(s["kind"] for s in summaries)),
        "largest": max(size),
    }
    (NORM / "cluster_stats.json").write_text(json.dumps(stats, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(json.dumps(stats, ensure_ascii=False))


if __name__ == "__main__":
    main()

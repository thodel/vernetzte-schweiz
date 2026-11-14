"""M10 (experimentell): Wer zieht von einer Gemeinde in eine andere?

    python scripts/migration.py         # Kandidaten suchen → links/migration.csv, data/norm/migration_stats.json
    python scripts/migration.py site    # Daten für die Seite → site/data/wanderungen.json.gz

Die Bündelung (M3) arbeitet je Gemeinde: wer umzieht, wird zu zwei Einheiten. Hier werden
solche Paare gesucht. Eine Einheit A **verschwindet** aus ihrer Gemeinde (letztes Jahr t),
eine Einheit B mit gleichem Familiennamen und verträglichem Vornamen **erscheint** in einer
anderen Gemeinde zum ersten Mal (erstes Jahr t' mit t < t' ≤ t + MAX_GAP).

Belege und Gegenbelege (Regeln in `evidence`, Stufen in `tier`):
- Vorname: ausgeschrieben gleich, oder Abkürzung; nur Initialen genügen nie.
- Beruf: gleicher Wortstamm, sonst gleiche Berufsklasse (scripts/occupations.py);
  verschiedene Klassen gelten als schwacher Gegenbeleg (Berufswechsel kommt vor).
- Titel (Dr., Prof., Ing.) auf beiden Seiten.
- Seltenheit des Familiennamens (Personen-Einheiten in der ganzen Schweiz).
- Eindeutigkeit: A hat genau einen solchen Nachfolger und B genau einen Vorgänger.
- Ausgeschlossen: A erscheint am alten Ort später doch wieder (eine verträgliche Einheit
  dort beginnt nach t), oder B stand schon vorher am neuen Ort.

Ob A wirklich verschwand, lässt sich nur sagen, wenn die alte Gemeinde nach t noch einmal
mit ähnlich vielen Einträgen vorliegt (`left_seen`); ob B wirklich neu ist, nur wenn die neue
Gemeinde vor t' schon vorlag (`new_seen`). Die Telefonbücher nennen nur Abonnenten: neu im
Buch heisst oft «neu ein Telefon», nicht «neu zugezogen». Die Ergebnisse sind Kandidaten.
"""

from __future__ import annotations

import gzip
import json
import math
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import NORM, ROOT, open_csv, write_csv  # noqa: E402
from link_ptt_ab import RANK, compare_forenames, forename_tokens, nkey, skey, stems  # noqa: E402
from occupations import CLASSES, LABELS, classify  # noqa: E402

LINKS = ROOT / "links"
MAX_GAP = 6          # Jahre zwischen letztem Eintrag am alten und erstem am neuen Ort
SEEN_SHARE = 0.5     # alte/neue Gemeinde gilt als «vorliegend», wenn sie so viele Einträge hat wie …
NEAR_KM = 5          # Nachbarorte: Umzug oder nur andere Ortszuweisung derselben Zeile
WIDOW = re.compile(r"\b(Wwe|Witwe|Wittwe|Wb|Vve|Veuve|Ved|Frau|Fr\.|Mme|Mlle|Frl|Jgfr)\b", re.I)
# Firmen, Ämter und Institutionen, die die Zerlegung (M1) als Person führt: «Boéchat, les fils
# de Paul», «Richteramt, Schloss», «Kloster St. Scholastika», «Eilboten-Institut», «Eredi fu Giovanni».
# Sie ziehen nicht um, sie verlegen den Sitz; das ist eine andere Frage.
NOT_PERSON = re.compile(
    r"\b(fils|söhne|soehne|erben|eredi|héritiers|gebr|gebrüder|frères|freres|fratelli|cie|co|comp)\b|&"
    r"|amt\b|ämter|schloss|château|verwaltung|kanzlei|kloster|couvent|convento|stift\b|institut|istituto|anstalt"
    r"|verein|société|societa|gesellschaft|genossenschaft|spital|hôpital|ospedale|asyl|schule|école|scuola|seminar"
    r"|kirche|église|chiesa|pfarr|paroisse|bank|banque|banca|kasse|caisse|eilboten|bureau|büro|ufficio|direktion|direction"
    r"|gemeinde|commune|comune|municipio|kommission|commission|komitee|comité", re.I)
TITLE = re.compile(r"\b(Dr|Prof|Ing|Pfr|Pfarrer|Not|Fürspr|Architekt|Arch)\b\.?", re.I)
FIELDS = ["from_entity", "to_entity", "surname", "forename_from", "forename_to", "from_muni", "to_muni",
          "from_last", "to_first", "gap", "km", "occ_from", "occ_to", "class", "evidence", "score", "tier",
          "left_seen", "new_seen", "n_surname"]
TIERS = ("stark", "mittel", "schwach")
NEIGHBOURS = 10      # Zeilen davor und danach im selben Telefonbuch
LINES: dict[str, list[tuple[int, str]]] = defaultdict(list)   # Band → [(Zeile, Eintrag)]


STREET_TYPE = re.compile(
    r"^(r\.|rue|av\.?|avenue|ch\.?|chemin|rte\.?|route|pl\.?|place|bd\.?|boulevard|quai|q\.|ruelle|via|vicolo|piazza)\s+"
    r"(de la |de l'|de l’|des |du |de |d'|d’)?", re.I)


def street_of(addr: str) -> str:
    """Strassenschlüssel einer Adresse ohne Hausnummer, ohne «rue du», «av. de la» usw."""
    s = re.sub(r"[\s,]*\d+\s*[a-zA-Z]?\b.*$", "", addr or "").strip(" ,.")
    return skey(STREET_TYPE.sub("", s)) if len(s) >= 3 else ""


def coords() -> tuple[dict[str, tuple[float, float]], dict[str, Counter]]:
    """Mittelpunkt je Gemeinde 1914 aus den verorteten Telefonbuch-Einträgen (wie M6), und
    die Strassen je Gemeinde (Telefon- und Adressbuch) für die Prüfung der Ortszuweisung."""
    g: dict[str, list] = defaultdict(lambda: [0.0, 0.0, 0])
    streets: dict[str, Counter] = defaultdict(Counter)
    for r in open_csv(NORM / "ptt_entries.csv.gz"):
        LINES[r["refcode"]].append((int(r["seq"]), r["id"]))
        m = r["municipality_1914"]
        if r["lat"] and m and r["place_confidence"] in ("hoch", "mittel"):
            x = g[m]
            x[0] += float(r["lat"]); x[1] += float(r["lon"]); x[2] += 1
            if r["street_name"]:
                streets[m][street_of(r["street_name"])] += 1
    for r in open_csv(NORM / "ab_entries.csv"):
        if r["street"] and r["municipality"]:
            streets[r["municipality"]][street_of(r["street"])] += 1
    return {m: (v[0] / v[2], v[1] / v[2]) for m, v in g.items() if v[2]}, streets


def misplaced(a: dict, b: dict, streets: dict[str, Counter]) -> str:
    """Grund, das Paar für einen Fehler der Ortszuweisung (M1) statt einen Umzug zu halten.

    Wer umzieht, bekommt eine neue Nummer und eine neue Adresse. Steht B an einer Strasse,
    die es am alten Ort gibt und am neuen kaum, oder an derselben Adresse bzw. Nummer wie A,
    ist meist dieselbe Zeile einem anderen Ort zugewiesen worden (Lausanne 1911–1914 unter
    «Genève», M1). Ein Gasthaus mit gleichem Namen ist ortsfest."""
    if a["phones"] & b["phones"]:
        return "gleiche_nummer"
    if a["addrs"] & b["addrs"]:
        return "gleiche_adresse"
    sa, sb = streets.get(a["muni"], Counter()), streets.get(b["muni"], Counter())
    for s in b["streets"]:
        if s and sa[s] >= 3 and sb[s] < sa[s] / 2:
            return "strasse_des_alten_orts"
    fa, fb = (nkey(re.sub(r"^(Le|La|Les|St\.?|Ste\.?|Saint|Sainte|San|Santa)\s+", "", m))
              for m in (a["muni"], b["muni"]))
    if fa[:2] == fb[:2] and a.get("km", 99) >= NEAR_KM:
        return "ähnlicher_ortsname"  # Charge B: Läufe unter der Überschrift des Nachbarn im Alphabet
    if a["cls"] == "gast" and a["occ"] and a["occ"].lower() == b["occ"].lower():
        return "gleicher_betrieb"
    return ""


def km(a: tuple[float, float], b: tuple[float, float]) -> float:
    la1, lo1, la2, lo2 = map(math.radians, (*a, *b))
    h = math.sin((la2 - la1) / 2) ** 2 + math.cos(la1) * math.cos(la2) * math.sin((lo2 - lo1) / 2) ** 2
    return 6371 * 2 * math.asin(math.sqrt(h))


def coverage() -> tuple[dict[str, dict[int, int]], dict[str, str]]:
    """Einträge je Gemeinde und Jahr (beide Quellen): wann eine Gemeinde «vorliegt»; dazu
    je Telefonbuch-Eintrag die Einheit."""
    c: dict[str, Counter] = defaultdict(Counter)
    ent: dict[str, str] = {}
    for r in open_csv(LINKS / "entities.csv.gz"):
        c[r["municipality"]][int(r["year"])] += 1
        if r["source"] == "ptt":
            ent[r["record_id"]] = r["entity_id"]
    return c, ent


def seen_after(cov: dict[int, int], year: int) -> bool:
    need = SEEN_SHARE * cov.get(year, 0)
    return any(n >= need for y, n in cov.items() if year < y <= year + MAX_GAP)


def seen_before(cov: dict[int, int], year: int) -> bool:
    need = SEEN_SHARE * cov.get(year, 0)
    return any(n >= need for y, n in cov.items() if year - MAX_GAP <= y < year)


def prepare(r: dict) -> dict | None:
    if r["kind"] != "person" or NOT_PERSON.search(r["surname"] + " " + r["forename"]) or WIDOW.search(r["forename"]) or WIDOW.search(r["occupations"][:40]):
        return None
    fn = forename_tokens(r["forename"])
    if not fn or all(len(k) == 1 for k, _ in fn):
        return None  # nur Initialen: kein Beleg für dieselbe Person anderswo
    occ = r["occupations"]
    addrs = [x.strip() for x in r["addresses"].split("|") if x.strip()]
    return {
        "phones": set(r["phones"].split()),
        "addrs": {nkey(x) for x in addrs if re.search(r"[A-Za-z]{3}.*\d", x)},
        "streets": {street_of(x) for x in addrs} - {""},
        "id": r["entity_id"], "muni": r["municipality"], "sk": nkey(r["surname"]), "surname": r["surname"],
        "forename": r["forename"], "fn": fn, "first": int(r["first_year"]), "last": int(r["last_year"]),
        "occ": occ, "stems": stems(occ), "cls": classify(occ),
        "title": {m.lower().rstrip(".") for m in TITLE.findall(r["forename"] + " " + occ)},
    }


def evidence(a: dict, b: dict) -> tuple[int, list[str]] | None:
    """Punkte und Belege für «A ist B an einem anderen Ort», None bei Widerspruch."""
    f = compare_forenames(a["fn"], b["fn"])
    if RANK.get(f, 0) < 2:
        return None  # Widerspruch, nur Initiale oder kein Vorname
    pts, ev = (2, ["vorname:gleich"]) if f == "gleich" else (1, ["vorname:abkürzung"])
    if a["stems"] & b["stems"]:
        pts += 2; ev.append("beruf:wort")
    elif a["cls"] and a["cls"] == b["cls"]:
        pts += 1; ev.append("beruf:klasse")
    elif a["cls"] and b["cls"]:
        pts -= 1; ev.append("beruf:anders")
    if a["title"] & b["title"]:
        pts += 1; ev.append("titel")
    return pts, ev


def tier(pts: int, ev: list[str], n_surname: int) -> str:
    if n_surname <= 10:
        pts += 2
    elif n_surname <= 40:
        pts += 1
    beruf = any(e.startswith("beruf:wort") or e == "beruf:klasse" or e == "titel" for e in ev)
    if pts >= 6 and beruf:
        return "stark"
    if pts >= 4 and beruf:
        return "mittel"
    if pts >= 4:
        return "schwach"
    return ""


def find() -> None:
    rows = open_csv(NORM / "entities.csv.gz")
    n_surname = Counter(nkey(r["surname"]) for r in rows if r["kind"] == "person")
    ents = [e for e in map(prepare, rows) if e and e["sk"]]
    by_sk: dict[str, list[dict]] = defaultdict(list)
    for e in ents:
        by_sk[e["sk"]].append(e)
    cov, rec_ent = coverage()
    geo, streets = coords()
    # Zeilen eines Bandes in Folge; je Einheit ihre Telefonbuch-Einträge
    where: dict[str, tuple[str, int]] = {}
    for ref, lines in LINES.items():
        lines.sort()
        for i, (_, rid) in enumerate(lines):
            where[rid] = (ref, i)
    recs_of: dict[str, list[str]] = defaultdict(list)
    for rid, eid in rec_ent.items():
        recs_of[eid].append(rid)

    cand: list[tuple[dict, dict, int, list[str]]] = []
    blocked_back = blocked_before = 0
    for sk, es in by_sk.items():
        if len(es) < 2:
            continue
        # Vorname-Initiale als Unterblock (verträgliche Vornamen haben dieselbe)
        sub: dict[str, list[dict]] = defaultdict(list)
        for e in es:
            for k, _ in e["fn"]:
                sub[k[:1].replace("k", "c").replace("j", "i")].append(e)
        pairs, block = set(), []
        for group in sub.values():
            group.sort(key=lambda e: e["first"])
            for a in group:
                for b in group:
                    if a is b or a["muni"] == b["muni"] or not (a["last"] < b["first"] <= a["last"] + MAX_GAP):
                        continue
                    if (a["id"], b["id"]) in pairs:
                        continue
                    pairs.add((a["id"], b["id"]))
                    r = evidence(a, b)
                    if r:
                        block.append((a, b, *r))
        # Gegenbelege: A am alten Ort später wieder, B am neuen Ort schon vorher
        same_place = defaultdict(list)
        for e in es:
            same_place[e["muni"]].append(e)
        for a, b, pts, ev in block:
            if any(x is not a and x["first"] > a["last"] and RANK.get(compare_forenames(a["fn"], x["fn"]), 0) >= 2
                   for x in same_place[a["muni"]]):
                blocked_back += 1
                continue
            if any(x is not b and x["last"] < b["first"] and RANK.get(compare_forenames(b["fn"], x["fn"]), 0) >= 2
                   for x in same_place[b["muni"]]):
                blocked_before += 1
                continue
            cand.append((a, b, pts, ev))

    # Ganze Läufe falsch verortet (M1): Stehen um die erste Zeile von B weitere Einträge, die
    # ebenfalls vom alten Ort A «gekommen» wären, ist der Lauf A zugehörig, nicht B.
    # (Nachbarn mit demselben Familiennamen zählen nicht: Geschwister stehen untereinander.)
    arrivals = defaultdict(dict)  # alter Ort → {Einheit am neuen Ort, die von dort käme: Namensschlüssel}
    for a, b, _, _ in cand:
        arrivals[a["muni"]][b["id"]] = b["sk"]

    def run_from_old_place(a: dict, b: dict) -> int:
        n = 0
        for rid in recs_of.get(b["id"], []):
            if rid not in where:
                continue
            ref, i = where[rid]
            lines = LINES[ref]
            for _, other in lines[max(0, i - NEIGHBOURS): i + NEIGHBOURS + 1]:
                e = rec_ent.get(other)
                if e and e != b["id"] and arrivals[a["muni"]].get(e, b["sk"]) != b["sk"]:
                    n += 1
        return n

    # Eindeutigkeit in beide Richtungen
    outs, ins = Counter(c[0]["id"] for c in cand), Counter(c[1]["id"] for c in cand)
    out_rows, stats = [], Counter()
    stats["kandidaten_vor_eindeutigkeit"] = len(cand)
    for a, b, pts, ev in cand:
        if outs[a["id"]] > 1 or ins[b["id"]] > 1:
            stats["mehrdeutig"] += 1
            continue
        d = round(km(geo[a["muni"]], geo[b["muni"]]), 1) if a["muni"] in geo and b["muni"] in geo else ""
        why = misplaced({**a, "km": d if d != "" else 99}, b, streets) or ("nachbarzeilen_vom_alten_ort" if run_from_old_place(a, b) >= 2 else "")
        if why:
            stats["ortszuweisung:" + why] += 1
            continue
        n_s = n_surname[a["sk"]]
        t = tier(pts, ev, n_s)
        if not t:
            stats["zu_schwach"] += 1
            continue
        left = seen_after(cov[a["muni"]], a["last"])
        new = seen_before(cov[b["muni"]], b["first"])
        cls = a["cls"] if a["cls"] == b["cls"] else (b["cls"] or a["cls"]) if not (a["cls"] and b["cls"]) else ""
        if d != "" and d < NEAR_KM:
            ev = ev + ["nachbarort"]
        out_rows.append({
            "from_entity": a["id"], "to_entity": b["id"], "surname": a["surname"],
            "forename_from": a["forename"], "forename_to": b["forename"],
            "from_muni": a["muni"], "to_muni": b["muni"], "from_last": a["last"], "to_first": b["first"],
            "gap": b["first"] - a["last"], "km": d, "occ_from": a["occ"][:120], "occ_to": b["occ"][:120],
            "class": cls, "evidence": "+".join(ev), "score": pts, "tier": t,
            "left_seen": int(left), "new_seen": int(new), "n_surname": n_s,
        })
        stats[t] += 1
        stats["beide_vorliegend"] += left and new
    out_rows.sort(key=lambda r: (TIERS.index(r["tier"]), r["from_last"], r["surname"]))
    write_csv(LINKS / "migration.csv", FIELDS, out_rows)
    stats.update({"personen_einheiten": len(rows), "geprueft": len(ents),
                  "später_am_alten_ort": blocked_back, "vorher_am_neuen_ort": blocked_before})
    (NORM / "migration_stats.json").write_text(json.dumps(dict(stats), ensure_ascii=False, indent=1) + "\n")
    print(json.dumps(dict(stats), ensure_ascii=False))


def site() -> None:
    """site/data/wanderungen.json.gz für #/wanderungen.

    - `places`: [Name, Kanton, Breite, Länge] (nur Orte, die vorkommen)
    - `classes`: [Schlüssel, Bezeichnung]
    - `moves`: [von, nach (Index in places), letztes Jahr alt, erstes Jahr neu, Klasse (-1 keine),
      Stufe (0 stark, 1 mittel, 2 schwach), km, Name, Beruf alt, Beruf neu, entity alt, entity neu,
      beide Seiten vorliegend (0/1)]
    """
    rows = open_csv(LINKS / "migration.csv")
    geo, _ = coords()
    canton = {r["municipality"]: r["canton"] for r in open_csv(NORM / "entities.csv.gz")}
    names = sorted({m for r in rows for m in (r["from_muni"], r["to_muni"]) if m in geo})
    idx = {m: i for i, m in enumerate(names)}
    ckey = {k: i for i, (k, _, _) in enumerate(CLASSES)}
    moves = []
    for r in rows:
        if r["from_muni"] not in idx or r["to_muni"] not in idx:
            continue
        moves.append([idx[r["from_muni"]], idx[r["to_muni"]], int(r["from_last"]), int(r["to_first"]),
                      ckey.get(r["class"], -1), TIERS.index(r["tier"]), float(r["km"] or 0),
                      f"{r['surname']}, {r['forename_to'] or r['forename_from']}", r["occ_from"][:60], r["occ_to"][:60],
                      r["from_entity"], r["to_entity"], int(r["left_seen"] == "1" and r["new_seen"] == "1")])
    out = {"places": [[m, canton.get(m, ""), round(geo[m][0], 4), round(geo[m][1], 4)] for m in names],
           "classes": [[k, LABELS[k]] for k, _, _ in CLASSES], "moves": moves}
    path = ROOT / "site" / "data" / "wanderungen.json.gz"
    path.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(path, "wt", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, separators=(",", ":"))
    print(f"{path.relative_to(ROOT)}: {len(moves)} Wanderungen zwischen {len(names)} Gemeinden")


if __name__ == "__main__":
    site() if sys.argv[1:] == ["site"] else find()

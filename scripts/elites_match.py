"""Elites suisses ↔ Einheiten über Name und Lebensjahre (ohne Wikidata-Kennung).

    python scripts/elites_match.py      # → data/norm/elites_candidates.csv.gz, elites_candidates.json

Grundlage: data/norm/elites_suisses_personen.csv.gz und _mitglied.csv.gz
(scripts/elites_suisses.py, alle Personen bis Jahrgang 1896) und die Einheiten aus M3
(data/norm/entities.csv.gz). Beschreibung und Messung: docs/elites_suisses.md.

**Bedingungen** (alle nötig):
- gleicher Familienname (Schlüssel wie in M2; bei «Heusler-Sarasin» zählt «Heusler»);
- verträglicher Vorname, mindestens als Abkürzung; haben beide Seiten zwei ausgeschriebene
  Vornamen, müssen sie übereinstimmen;
- kein Widerspruch im Geschlecht (scripts/migration.py: Vorname, Berufsform, «geb.»);
- die Einheit steht in Jahren im Buch, in denen die Person 16 Jahre alt und noch am Leben war,
  und zum ersten Mal, bevor sie 75 war;
- haben beide Seiten zwei Vornamen, stimmen ihre Anfangsbuchstaben Stelle für Stelle überein
  («Konr. Otto» ≠ «(Friedrich) Otto», «Hans Jak.» ≠ «Hans Heinrich»); «Mme», «Vve», «Wwe» gelten als Frau (Messung 1).

**Belege** (Punkte):
- Vorname ausgeschrieben gleich 2, als Abkürzung 1;
- ein Gremium der Person nennt den Ort der Einheit («Grosser Rat BS» → Basel? nein: nur
  Kanton; «Lausanne», «Genève», «Zürcher Handelskammer» → Ort) 3, nur den Kanton 2;
- eine Mitgliedschaft in diesem Kanton oder Ort fällt in die Jahre der Einheit: 1 dazu;
- Familienname selten (höchstens 10 Personen-Einheiten in der Schweiz) 2, höchstens 40: 1.

**Stufen** (nach Eindeutigkeit in beide Richtungen: je Person der beste Ort, je Einheit die
beste Person; Gleichstand an verschiedenen Orten → mehrdeutig, fällt weg):
- `wahrscheinlich`: ≥ 6 Punkte, mit Ort oder Kanton;
- `möglich`: ≥ 4 Punkte, mit Ort, Kanton oder seltenem Namen;
- `schwach`: der Rest mit ≥ 3 Punkten.
Personen, die über Wikidata schon mit einer Einheit verknüpft sind (links/authority.csv),
werden übersprungen.
"""

from __future__ import annotations

import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import NORM, ROOT, open_csv, write_csv  # noqa: E402
from link_ptt_ab import RANK, compare_forenames, forename_tokens, nkey  # noqa: E402
from migration import WIDOW, sex  # noqa: E402

OUT = NORM / "elites_candidates.csv.gz"
FIELDS = ["entity_id", "es_id", "tier", "score", "why", "es_name", "birth", "death", "es_qid", "municipality", "years"]
CANTONS = "ZH BE LU UR SZ OW NW GL ZG FR SO BS BL SH AR AI SG GR AG TG TI VD VS NE GE JU".split()
CANTON_RE = re.compile(r"(?:^|[\s(/])(" + "|".join(CANTONS) + r")(?:$|[\s)/,])")
# Orte in Gremien (deutsch, französisch, italienisch) → (Gemeinde wie in den Einheiten, Kanton)
PLACES = {
    "zürich": ("Zürich", "ZH"), "zurich": ("Zürich", "ZH"), "zürcher": ("Zürich", "ZH"), "winterthur": ("Winterthur", "ZH"),
    "bern": ("Bern", "BE"), "berne": ("Bern", "BE"), "berner": ("Bern", "BE"), "biel": ("Biel (BE)", "BE"), "bienne": ("Biel (BE)", "BE"),
    "basel": ("Basel", "BS"), "bâle": ("Basel", "BS"), "basler": ("Basel", "BS"),
    "genève": ("Genève", "GE"), "genf": ("Genève", "GE"), "genevois": ("Genève", "GE"), "genevoise": ("Genève", "GE"),
    "lausanne": ("Lausanne", "VD"), "lausannois": ("Lausanne", "VD"), "vevey": ("Vevey", "VD"), "montreux": ("Montreux", "VD"),
    "luzern": ("Luzern", "LU"), "lucerne": ("Luzern", "LU"), "luzerner": ("Luzern", "LU"),
    "st. gallen": ("St. Gallen", "SG"), "st-gall": ("St. Gallen", "SG"), "st. galler": ("St. Gallen", "SG"),
    "neuchâtel": ("Neuchâtel", "NE"), "la chaux-de-fonds": ("La Chaux-de-Fonds", "NE"), "le locle": ("Le Locle", "NE"),
    "fribourg": ("Fribourg", "FR"), "freiburg": ("Fribourg", "FR"), "aarau": ("Aarau", "AG"), "aargauer": ("", "AG"),
    "baden": ("Baden", "AG"), "schaffhausen": ("Schaffhausen", "SH"), "chur": ("Chur", "GR"), "lugano": ("Lugano", "TI"),
    "solothurn": ("Solothurn", "SO"), "zug": ("Zug", "ZG"), "sion": ("Sion", "VS"), "thun": ("Thun", "BE"),
    "vaudois": ("", "VD"), "vaud": ("", "VD"), "valais": ("", "VS"), "tessin": ("", "TI"), "ticino": ("", "TI"),
    "thurgau": ("", "TG"), "thurgauer": ("", "TG"), "glarus": ("", "GL"), "glarner": ("", "GL"),
}
PLACE_RE = re.compile(r"\b(" + "|".join(sorted(map(re.escape, PLACES), key=len, reverse=True)) + r")\b", re.I)


def places_of(groups: list[tuple[str, int, int]]) -> tuple[dict, dict]:
    """Orte und Kantone aus den Gremien einer Person, je mit den Jahren der Mitgliedschaft."""
    muni: dict[str, list] = defaultdict(list)
    cant: dict[str, list] = defaultdict(list)
    for g, a, z in groups:
        for m in CANTON_RE.findall(g):
            cant[m].append((a, z))
        for m in PLACE_RE.findall(g):
            place, c = PLACES[m.lower()]
            if place:
                muni[place].append((a, z))
            cant[c].append((a, z))
    return muni, cant


def ini(k: str) -> str:
    """Anfangsbuchstabe eines Vornamens, Karl = Carl, Jakob = Iacob (wie in migration.py)."""
    return k[:1].replace("k", "c").replace("j", "i")


def overlaps(spans: list, y0: int, y1: int) -> bool:
    return any((a or 0) <= y1 and (z or 9999) >= y0 for a, z in spans)


def main() -> None:
    persons = {r["es_id"]: r for r in open_csv(NORM / "elites_suisses_personen.csv.gz")}
    groups: dict[str, list] = defaultdict(list)
    for m in open_csv(NORM / "elites_suisses_mitglied.csv.gz"):
        if m["group"]:
            groups[m["es_id"]].append((m["group"], int(m["start"] or 0), int(m["end"] or 0)))
    linked_qids = {a["qid"] for a in open_csv(ROOT / "links" / "authority.csv")}

    ents = [e for e in open_csv(NORM / "entities.csv.gz") if e["kind"] == "person"]
    n_surname = Counter(nkey(e["surname"]) for e in ents)
    by_sk: dict[str, list] = defaultdict(list)
    for e in ents:
        fn = forename_tokens(e["forename"])
        if fn and not all(short for _, short in fn):  # nur Initialen genügen nicht
            e["fn"] = fn
            e["sex"] = "f" if WIDOW.search(e["forename"] + " " + e["occupations"][:40]) else sex(e["forename"], e["occupations"])
            by_sk[nkey(e["surname"])].append(e)

    found: dict[str, list] = defaultdict(list)   # es_id → [(Punkte, Einheit, Belege)]
    stats = Counter()
    for pid, p in persons.items():
        if p["qid"] and p["qid"] in linked_qids:
            stats["schon_über_wikidata"] += 1
            continue
        fam, _, given = p["name"].partition(",")
        sk = nkey(re.split(r"[\s\-]+", fam.strip())[0]) if fam.strip() else ""
        given = re.sub(r"[()]", " ", given)
        fn = forename_tokens(given)
        if not sk or not fn or sk not in by_sk:
            continue
        b = int(p["birth"])
        d = int(p["death"]) if p["death"] else b + 95
        psex = {"male": "m", "female": "f"}.get(p["gender"], "")
        muni, cant = places_of(groups.get(pid, []))
        for e in by_sk[sk]:
            y0, y1 = int(e["first_year"]), int(e["last_year"])
            if y0 < b + 16 or y1 > d or y0 > b + 75:
                continue  # zu jung, schon tot, oder erst mit über 75 zum ersten Mal im Buch
            f = compare_forenames(fn, e["fn"])
            if RANK.get(f, 0) < 2:
                continue
            full_p, full_e = ({k for k, short in x if not short} for x in (fn, e["fn"]))
            if len(full_p) >= 2 and len(full_e) >= 2 and not (full_p <= full_e or full_e <= full_p):
                continue
            if len(fn) >= 2 and len(e["fn"]) >= 2 and any(ini(x) != ini(y) for (x, _), (y, _) in zip(fn, e["fn"])):
                continue  # zweiter Vorname anders: «Konr. Otto» ≠ «(Friedrich) Otto», «Hans Jak.» ≠ «Hans Heinrich»
            if psex and e["sex"] and psex != e["sex"]:
                continue
            pts, why = (2, ["vorname:gleich"]) if f == "gleich" else (1, ["vorname:abkürzung"])
            if e["municipality"] in muni:
                pts += 3; why.append("ort")
                if overlaps(muni[e["municipality"]], y0, y1):
                    pts += 1; why.append("zeitgleich")
            elif e["canton"] in cant:
                pts += 2; why.append("kanton")
                if overlaps(cant[e["canton"]], y0, y1):
                    pts += 1; why.append("zeitgleich")
            ns = n_surname[sk]
            if ns <= 10:
                pts += 2; why.append("name:selten")
            elif ns <= 40:
                pts += 1; why.append("name:eher_selten")
            found[pid].append((pts, e, why))

    # Eindeutigkeit: je Person der beste Ort (Gleichstand an verschiedenen Orten → mehrdeutig),
    # je Einheit die beste Person
    best_e: dict[str, tuple] = {}
    for pid, cs in found.items():
        cs.sort(key=lambda c: -c[0])
        top = cs[0][0]
        tied = [c for c in cs if c[0] == top]
        if len({c[1]["municipality"] for c in tied}) > 1 or len(tied) > 1:
            stats["mehrdeutig_person"] += 1
            continue
        pts, e, why = cs[0]
        if e["entity_id"] in best_e and best_e[e["entity_id"]][0] >= pts:
            best_e[e["entity_id"]] = (max(pts, best_e[e["entity_id"]][0]), None, None)  # Gleichstand → keiner
            continue
        best_e[e["entity_id"]] = (pts, pid, (e, why))
    rows = []
    for eid, (pts, pid, ew) in best_e.items():
        if not pid:
            stats["mehrdeutig_einheit"] += 1
            continue
        e, why = ew
        place = "ort" in why or "kanton" in why
        rare = "name:selten" in why
        tier = ("wahrscheinlich" if pts >= 6 and place else
                "möglich" if pts >= 4 and (place or rare) else
                "schwach" if pts >= 3 else "")
        if not tier:
            stats["zu_schwach"] += 1
            continue
        p = persons[pid]
        rows.append({"entity_id": eid, "es_id": pid, "tier": tier, "score": pts, "why": "+".join(why),
                     "es_name": p["name"], "birth": p["birth"], "death": p["death"], "es_qid": p["qid"],
                     "municipality": e["municipality"], "years": f"{e['first_year']}–{e['last_year']}"})
        stats[tier] += 1
    rows.sort(key=lambda r: (["wahrscheinlich", "möglich", "schwach"].index(r["tier"]), r["es_name"]))
    write_csv(OUT, FIELDS, rows)
    stats.update({"personen": len(persons), "mit_kandidat": len(found)})
    (NORM / "elites_candidates.json").write_text(json.dumps(dict(stats), ensure_ascii=False, indent=1) + "\n")
    print(json.dumps(dict(stats), ensure_ascii=False))


if __name__ == "__main__":
    main()

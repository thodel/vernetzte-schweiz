"""Umgekehrte Prüfung: Wie viele Personen des HLS müssten in den Telefon- und Adressbüchern
1880–1914 stehen, und wie viele finden wir?

    python scripts/hls_coverage.py [Pfad zur HLS-CSV]

Grundlage ist der HLS-Export, aus dem auch hls_mcp gebaut wird (`hls_articles.csv`,
Biografien). Die Orte einer Person kommen aus Wikidata (Wohn-, Wirkungs-, Sterbeort mit
BFS-Nummer, `data/ref/wikidata_persons.csv.gz`, über die HLS-Nummer); fehlt die Person dort,
gilt der Sterbeort aus dem Kopf des HLS-Artikels, über den Gemeindenamen.

**Erwartet** ist eine Person, wenn sie 1880–1914 mindestens ein Jahr erwachsen (25–80) war
und an einem ihrer Orte in einem dieser Jahre ein Telefon- oder Adressbuch vorliegt. Die Orte
haben kein Datum: Ein Sterbeort von 1940 zählt, auch wenn die Person 1900 anderswo lebte.
Darum wird «gelebt» (Wohn- oder Wirkungsort) getrennt von «nur Sterbeort» ausgewiesen.

**Gefunden** in Stufen:
- `normdaten`: eine Einheit trägt die HLS-Nummer (links/authority.csv);
- `name_ort_vorname`: Einheit am Ort, gleicher Familienname, Vorname gleich oder abgekürzt,
  in einem Jahr, in dem die Person erwachsen war;
- `name_ort_initiale`: wie oben, aber nur die Initiale passt;
- `name_ort`: Familienname am Ort ohne Vornamen in der Einheit;
- sonst `nicht_gefunden`.
Die Namensstufen sind Kandidaten, keine Identifikation: siehe die Stichprobe in
docs/hls_abdeckung.md.

Schreibt data/norm/hls_coverage.csv.gz (je Person), data/norm/hls_candidates.csv.gz (je
Person und Einheit, mit Stufe; bei «nicht gefunden» die gleichnamigen Einheiten anderswo)
und data/norm/hls_coverage.json. Aus dem Artikeltext wird nichts übernommen, nur Orte und
Jahre.
"""

from __future__ import annotations

import ast
import csv
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from common import NORM, ROOT, open_csv, write_csv  # noqa: E402
from authority import OCC_GROUPS  # noqa: E402
from link_ptt_ab import compare_forenames, forename_tokens, nkey  # noqa: E402
from occupations import _PATTERNS as OCC_PATTERNS  # noqa: E402

HLS_CSV = Path("/Users/TH_1/Documents/HLS/hls_articles.csv")
Y0, Y1 = 1880, 1914
LIVED = {"wohnort", "wirkungsort"}
# «Wirkungsort Bern» steht in Wikidata für jedes Mitglied der Bundesversammlung und der
# Bundesbehörden; gewohnt haben die meisten anderswo. Bern zählt darum nur als Wohn- oder
# Sterbeort.
IGNORE = {("351", "wirkungsort")}
PARTICLES = {"von", "de", "du", "la", "le", "di", "da", "van", "zum", "zur"}
DATE = r"(?:\d{1,2}\.\d{1,2}\.)?(?:\d{4})"
HEAD = re.compile(rf"(?:^|\s)(?:um |vor |nach |getauft )?{DATE} ([^,]+?),\s+(?:(?:um |vor |nach |begraben )?{DATE} ([^,]+?),)?")


def year(s: str) -> int | None:
    m = re.match(r"-?(\d{4})", s or "")
    return int(m.group(1)) if m else None


def surname_keys(fam: str) -> set[str]:
    """«Schmid von Grüneck» → schmid, schmidvongruneck; «de Pury» → pury, depury."""
    words = [w for w in re.split(r"[\s\-]+", fam) if w]
    keys = {nkey(fam)}
    core = [w for w in words if w.lower() not in PARTICLES]
    if core:
        keys.add(nkey(core[0]))
        keys.add(nkey(core[-1]))
    return {k for k in keys if len(k) >= 2}


def clean_place(s: str) -> str:
    s = re.sub(r"\(.*?\)", "", s or "").strip()
    return re.sub(r"\s+bei\s+.*$", "", s).strip()


# Deutsche Namen im HLS für Gemeinden, die in den Telefonbüchern anders heissen
EXONYMS = {"genf": "Genève", "neuenburg": "Neuchâtel", "freiburg": "Fribourg", "pruntrut": "Porrentruy",
           "delsberg": "Delémont", "sitten": "Sion", "siders": "Sierre", "biel": "Biel (BE)", "bellenz": "Bellinzona",
           "neuenstadt": "La Neuveville", "vivis": "Vevey", "peterlingen": "Payerne", "iferten": "Yverdon",
           "milden": "Moudon", "murten": "Murten", "st. moritz": "St. Moritz", "lauis": "Lugano",
           "münster (be)": "Moutier", "st-imier": "Saint-Imier", "st. immer": "Saint-Imier", "dachsfelden": "Tavannes",
           "neuenburg (ne)": "Neuchâtel"}
# Gemeindenamen, die im Text meist etwas anderes meinen
PLACE_STOP = {"wald", "stein", "horn", "egg", "au", "berg", "buch", "feld", "ried", "grub", "matt", "moos", "dorf",
              "hof", "holz", "boden", "rain", "kirche", "schule", "basel-land", "land", "see"}
YEARS = re.compile(r"\b(ab|seit|bis|um|nach|vor|Ab|Seit|Bis|Um)?\s?(1[789]\d\d)(?:\s?[-–]\s?(\d{2,4}))?\b")
IN_PLACE = re.compile(r"\b(?:in|nach|In)\s+((?:St\.\s|Ste\.\s|La\s|Le\s|Les\s)?[A-ZÀ-Ý][\w'’\-]*(?:[\s-](?:sur|de|la|le|les|am|an|im)[\s-][A-ZÀ-Ý][\w'’\-]*)?)(\s\((?:[A-Z]{2})\))?")


def gazetteer(names: set[str]) -> dict[str, str]:
    """Gemeindename (klein) → Name in den Telefonbüchern. Mit Kantonszusatz immer; ohne nur,
    wenn der Name einmalig ist; dazu die deutschen Namen aus EXONYMS."""
    gaz = {n.lower(): n for n in names}
    bare = Counter(n.split(" (")[0].lower() for n in names)
    for n in names:
        b = n.split(" (")[0].lower()
        if bare[b] == 1:
            gaz.setdefault(b, n)
    for k, v in EXONYMS.items():
        if v in names:
            gaz[k] = v
    return {k: v for k, v in gaz.items() if k not in PLACE_STOP and len(k) >= 3}


def year_span(m: re.Match, death: int | None) -> tuple[int, int]:
    """«1889-1894» → 1889–1894, «1909-45» → 1909–1945, «ab 1897» → 1897 bis Tod,
    «bis 1880» → 1875–1880, «1901» → 1901–1910 (eine Jahreszahl nennt meist einen Anfang)."""
    pre, y, to = (m.group(1) or "").lower(), int(m.group(2)), m.group(3)
    if to:
        y2 = int(to) if len(to) == 4 else int(str(y)[: 4 - len(to)] + to)
        return (y, y2) if y2 >= y else (y, y)
    if pre in ("ab", "seit"):
        return y, death or y + 40
    if pre == "bis":
        return y - 5, y
    return y, y + 9


def text_places(text: str, gaz: dict[str, str], death: int | None) -> dict[str, list[tuple[int, int, str]]]:
    """Orte mit Jahren aus dem Artikeltext: «1892-1894 Gemeinderat in Baar» → Baar 1892–1894.
    Die Jahreszahl muss im selben Satzteil (bis Komma oder Strichpunkt) vor dem Ort stehen;
    Lebensdaten (Tag.Monat.Jahr) zählen nicht. Ein Ort ohne solche Jahreszahl fällt weg
    («Gymnasium in Zürich, ab 1852 Stud. in Basel» gibt nur Basel ab 1852)."""
    body = re.sub(r"\(heute [^)]*\)", "", text.split("Autor:", 1)[-1])
    body = re.sub(r"\d{1,2}\.\d{1,2}\.\d{4}", "", body)
    out: dict[str, list] = defaultdict(list)
    for sent in re.split(r"(?<=[a-zäöü\)])\.\s+(?=[A-ZÄÖÜ0-9])", body):
        for part in re.split(r"[,;]\s", sent):
            years = list(YEARS.finditer(part))
            for m in IN_PLACE.finditer(part):
                prev = [y for y in years if y.start() < m.start()]
                if not prev:
                    continue
                name = (m.group(1) + (m.group(2) or "")).strip()
                hit = gaz.get(name.lower()) or gaz.get(m.group(1).lower())
                if hit:
                    out[hit].append((*year_span(prev[-1], death), part.strip()[:200]))
    return out


# Berufsgruppen aus dem Abgleich in M3, ergänzt um die Wörter, mit denen das HLS Berufe nennt
GROUPS = {**OCC_GROUPS, "jurist": OCC_GROUPS["jurist"] + r"|anwalt|avvocat|notaio",
          "presse": r"redaktor|redakteur|rédacteur|redattore|redaktion|rédaction|verleger|éditeur"}


def occ_evidence(text: str) -> set[str]:
    """Berufsgruppen und Berufsklassen (M6) eines Textes."""
    t = text or ""
    return {g for g, pat in GROUPS.items() if re.search(pat, t, re.I)} | \
           {k for k, pat in OCC_PATTERNS if k != "privat" and pat.search(t)}


def main(path: Path = HLS_CSV) -> None:
    csv.field_size_limit(10**9)
    # Telefonbücher: Jahre je BFS-Nummer; Gemeindename → BFS
    editions: dict[str, set[int]] = defaultdict(set)
    bfs_of: dict[str, str] = {}
    size: Counter = Counter()
    for r in open_csv(NORM / "ptt_entries.csv.gz"):
        if r["bfs_today"] and r["place_confidence"] in ("hoch", "mittel"):
            editions[r["bfs_today"]].add(int(r["year"]))
            bfs_of.setdefault(r["municipality_1914"], r["bfs_today"])
            size[r["municipality_1914"]] += 1
    for m in open_csv(ROOT / "links" / "entities.csv.gz"):
        if m["source"] == "ab" and m["municipality"] in bfs_of:
            editions[bfs_of[m["municipality"]]].add(int(m["year"]))
    gaz = gazetteer(set(bfs_of))
    by_name = {k: bfs_of[v] for k, v in gaz.items()}
    # BFS-Nummer → Gemeinde mit den meisten Einträgen (Zürich, nicht Witikon)
    muni_of = {}
    for k, v in sorted(bfs_of.items(), key=lambda kv: size[kv[0]]):
        muni_of[v] = k
    # Einheiten je BFS und Familienname
    idx: dict[tuple[str, str], list[dict]] = defaultdict(list)
    by_surname: dict[str, list[dict]] = defaultdict(list)
    for s in open_csv(NORM / "entities.csv.gz"):
        if s["kind"] != "person" or not s["bfs_today"]:
            continue
        s["_years"] = {int(y) for y in s["years"].split() if y.isdigit()} or {int(s["first_year"]), int(s["last_year"])}
        s["_fn"] = forename_tokens(s["forename"])
        s["_occ"] = occ_evidence(s["occupations"] + " " + s["forename"])
        idx[(s["bfs_today"], nkey(s["surname"]))].append(s)
        by_surname[nkey(s["surname"])].append(s)
    linked: dict[str, list[str]] = defaultdict(list)
    for a in open_csv(ROOT / "links" / "authority.csv"):
        if a["hls_id"]:
            linked[a["hls_id"]].append(a["entity_id"])
    wd = {c["hls_id"]: c for c in open_csv(ROOT / "data" / "ref" / "wikidata_persons.csv.gz") if c["hls_id"]}

    rows, stats, cand_rows = [], Counter(), []
    for row in csv.DictReader(open(path, encoding="utf-8", errors="replace")):
        if row["category"] != "bio" or not row["bio.family_name"].strip():
            continue
        hid = row["id"].strip()
        b, d = year(row["bio.birth_date"]), year(row["bio.death_date"])
        if b is None:
            continue
        a0, a1 = max(Y0, b + 25), min(Y1, d if d is not None else b + 80, b + 80)
        if a0 > a1:
            continue
        stats["erwachsen_1880_1914"] += 1
        text = row["content_text"]
        # Orte: (BFS) → {Quelle: [(von, bis, Beleg)]}; Text mit Jahren, Wikidata und Sterbeort ohne
        places: dict[str, dict[str, list]] = defaultdict(lambda: defaultdict(list))
        for muni, spans in text_places(text, gaz, d).items():
            for y0, y1, ev in spans:
                lo, hi = max(y0, a0), min(y1, a1)
                if lo <= hi:
                    places[bfs_of[muni]]["text"].append((lo, hi, ev))
        if hid in wd:
            for pc in wd[hid]["places"].split("|"):
                rel, _, bfs = pc.partition(":")
                if bfs and (bfs, rel) not in IGNORE and rel in LIVED | {"sterbeort"}:
                    places[bfs]["wikidata_" + rel].append((a0, a1, ""))
        m = HEAD.search(text[:600])
        death = clean_place(m.group(2)) if m and m.group(2) else ""
        if death.lower() in by_name:
            places[by_name[death.lower()]]["hls_sterbeort"].append((a0, a1, ""))
        if not places:
            stats["ohne_ort"] += 1
            continue
        covered = {}
        for bfs, srcs in places.items():
            yrs = editions.get(bfs, set())
            spans = [(lo, hi, ev, src) for src, lst in srcs.items() for lo, hi, ev in lst
                     if any(lo <= y <= hi for y in yrs)]
            if spans:
                covered[bfs] = spans
        if not covered:
            stats["ohne_abgedeckten_ort"] += 1
            continue
        srcs_all = {sp[3] for spans in covered.values() for sp in spans}
        basis = ("text" if "text" in srcs_all else
                 "gelebt" if srcs_all & {"wikidata_wohnort", "wikidata_wirkungsort"} else "nur_sterbeort")
        fns = forename_tokens(row["bio.first_name"])
        hls_occ_all = occ_evidence(text[:2500])
        cands = []
        for bfs, spans in covered.items():
            text_spans = [(lo, hi, ev) for lo, hi, ev, src in spans if src == "text"]
            occ_here = set().union(*(occ_evidence(ev) for _, _, ev in text_spans)) | \
                {g for g in hls_occ_all if g in GROUPS}
            for k in surname_keys(row["bio.family_name"]):
                for s in idx.get((bfs, k), ()):
                    if not any(a0 <= y <= a1 for y in s["_years"]):
                        continue
                    level = compare_forenames(s["_fn"], fns) if fns else ""
                    if level == "widerspruch":
                        continue
                    in_text = any(lo - 2 <= y <= hi + 2 for lo, hi, _ in text_spans for y in s["_years"])
                    job = bool(s["_occ"] & occ_here)
                    cands.append((s, level, in_text, job))
        found = tier_of(cands, bool(linked.get(hid)))
        best = [c for c in cands if cand_tier(c) == found] if found not in ("normdaten", "nicht_gefunden") else []
        ents = linked[hid] if found == "normdaten" else [c[0]["entity_id"] for c in best]
        stats[f"{basis}:{found}"] += 1
        # alle Kandidaten mit ihrer Stufe (je Einheit die beste), dazu die Normdaten
        per_ent: dict[str, tuple] = {}
        for c in cands:
            eid, tier = c[0]["entity_id"], cand_tier(c)
            if eid not in per_ent or TIERS.index(tier) > TIERS.index(per_ent[eid][0]):
                per_ent[eid] = (tier, why_of(c))
        for eid in linked.get(hid, ()):
            per_ent[eid] = ("normdaten", "hls-nummer")
        for eid, (tier, why) in per_ent.items():
            cand_rows.append({"hls_id": hid, "entity_id": eid, "tier": tier, "why": why, "where": "ort"})
        reason = ""
        if found == "nicht_gefunden":
            keys = surname_keys(row["bio.family_name"])
            pool = [s for k in keys for s in by_surname.get(k, ())]
            far = [s for s in pool if any(a0 <= y <= a1 for y in s["_years"]) and fns
                   and compare_forenames(s["_fn"], fns) in ("gleich", "abkürzung")]
            for s in far[:10]:
                cand_rows.append({"hls_id": hid, "entity_id": s["entity_id"], "tier": "anderswo",
                                  "why": compare_forenames(s["_fn"], fns), "where": "anderswo"})
            reason = ("name_anderswo" if far else "name_ohne_vorname" if any(s["bfs_today"] in covered for s in pool)
                      else "name_nicht_am_ort" if pool else "name_fehlt")
        rows.append({"hls_id": hid, "name": f"{row['bio.first_name']} {row['bio.family_name']}".strip(),
                     "birth": b, "death": d or "", "gender": row["bio.gender"], "adult_from": a0, "adult_to": a1,
                     "places": ";".join(place_cell(muni_of.get(bfs, bfs), v, editions.get(bfs, set()))
                                        for bfs, v in sorted(covered.items())),
                     "fields": "|".join(fields_of(row["lexical_class"])),
                     "basis": basis, "found": found, "reason": reason, "n_hits": len(set(ents)),
                     "entities": " ".join(sorted(set(ents))[:20]),
                     "why": " ".join(sorted({why_of(c) for c in best}))})
    # Eine Einheit, die für zwei HLS-Personen «wahrscheinlich» ist (Vater und Sohn gleichen
    # Namens), bleibt für beide nur «möglich».
    shared = Counter(e for r in rows if r["found"] == "wahrscheinlich" for e in r["entities"].split())
    for r in rows:
        if r["found"] == "wahrscheinlich" and any(shared[e] > 1 for e in r["entities"].split()):
            stats[f"{r['basis']}:wahrscheinlich"] -= 1
            stats[f"{r['basis']}:möglich"] += 1
            r["found"], r["why"] = "möglich", r["why"] + " mehrdeutig"
            for c in cand_rows:
                if c["hls_id"] == r["hls_id"] and c["tier"] == "wahrscheinlich":
                    c["tier"], c["why"] = "möglich", c["why"] + " mehrdeutig"
    write_csv(NORM / "hls_candidates.csv.gz", list(cand_rows[0]), cand_rows)
    write_csv(NORM / "hls_coverage.csv.gz", list(rows[0]), rows)
    (NORM / "hls_coverage.json").write_text(json.dumps(dict(sorted(stats.items())), ensure_ascii=False, indent=1))
    print(json.dumps(dict(sorted(stats.items())), ensure_ascii=False, indent=1))


def place_cell(muni: str, spans: list, eds: set[int]) -> str:
    """«Gemeinde|von|bis|Quellen|Jahre mit Buch in dieser Spanne»."""
    lo, hi = min(sp[0] for sp in spans), max(sp[1] for sp in spans)
    yrs = ",".join(str(y) for y in sorted(eds) if lo <= y <= hi)
    return f"{muni}|{lo}|{hi}|{'+'.join(sorted({sp[3] for sp in spans}))}|{yrs}"


def fields_of(lexical: str) -> list[str]:
    """Fachgebiete des HLS-Artikels: zweite Stufe der Klassen («Personen -> Wirtschaft -> …»)."""
    try:
        paths = ast.literal_eval(lexical) if lexical.startswith("[") else [lexical]
    except (ValueError, SyntaxError):
        return []
    return sorted({p.split(" -> ")[1].split(" (")[0] for p in paths if p.count(" -> ") >= 1})


def why_of(c: tuple) -> str:
    return f"{c[1] or 'ohne_vorname'}{'+text' if c[2] else ''}{'+beruf' if c[3] else ''}"


TIERS = ["nicht_gefunden", "schwach", "möglich", "wahrscheinlich", "normdaten"]


def cand_tier(c: tuple) -> str:
    """Stufe eines Kandidaten (Einheit, Vornamenvergleich, Ort+Jahr aus dem Text, Beruf).
    Gemessen in docs/hls_abdeckung.md: Der Beruf trägt, der Ort aus dem Text allein nicht
    (er nennt oft das Studium, und am selben Ort leben Namensvettern)."""
    _, level, in_text, job = c
    full = level in ("gleich", "abkürzung")
    if (full and job) or (level == "initiale" and job and in_text):
        return "wahrscheinlich"
    if full:
        return "möglich"
    return "schwach"


def tier_of(cands: list[tuple], linked: bool) -> str:
    if linked:
        return "normdaten"
    return max((cand_tier(c) for c in cands), key=TIERS.index, default="nicht_gefunden")


if __name__ == "__main__":
    main(Path(sys.argv[1]) if len(sys.argv) > 1 else HLS_CSV)

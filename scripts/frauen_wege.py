"""Experiment (M10b): Wege von Frauen über den Zivilstand — von «Frl. X» über «Y-X» / «geb. X»
zu «Wwe.» (docs/frauen_wege.md).

    python scripts/frauen_wege.py          # → links/frauen_wege.csv, data/norm/frauen_wege_stats.json

Frauen wechseln mit der Heirat den Familiennamen; die Wanderungen (M10) finden sie darum nicht.
Hier werden Einträge über den Zivilstand verbunden. Grundlage sind alle Einträge (Adress- und
Telefonbücher), nicht die Einheiten aus M3, weil M3 nach Familiennamen bündelt.

**Spuren.** Einträge mit gleicher Gemeinde, gleichem Zivilstand und gleichem Namen werden zu einer
Spur zusammengefasst (Jahre, Nummern, Adressen, Berufe). Zivilstand je Eintrag:
- `witwe`: Wwe., Witwe, Wittwe, Wb., Vve, veuve;
- `verheiratet`: Frau, Mme, geb., née, oder eine Frau mit Allianzname («Wächter-Lindenmann»: der
  zweite Name ist ihr Geburtsname);
- `ledig`: Frl., Fräulein, Mlle, Jgfr. (ausdrücklich); `ledig?`: Frau nach Vorname oder Berufsform
  (Näherin), ohne jedes Zeichen einer Ehe (vermutet);
- `mann`: Mann nach Vorname, für den Übergang Ehemann → Witwe.
Steht bei einer Witwe ein Männername («Suter, Jakob, Becks Wittwe»), ist er der Vorname des Mannes.

**Übergänge** (je mit Punkten, eindeutig in beide Richtungen, sonst mehrdeutig):
- `ledig→verheiratet`: Familienname der Ledigen = Geburtsname der Verheirateten, Vorname
  verträglich, später. Auch zur Witwe, wenn diese den Geburtsnamen nennt (`ledig→witwe`).
- `verheiratet→witwe`: gleicher Ehename, Vorname verträglich, Geburtsname gleich oder nicht genannt
  (verschieden → kein Paar); die Witwe erst nach der letzten Nennung als Ehefrau.
Vornamen: verträglich wie in M2; haben beide Seiten zwei, beginnen sie Stelle für Stelle gleich.
- `mann→witwe`: Ehename gleich; Vorname des Mannes = Männername bei der Witwe, oder Allianzname
  gleich; die Witwe erscheint im letzten Jahr des Mannes oder bis 5 Jahre danach; gleiche Gemeinde.
Belege: gleiche Telefonnummer (+3), gleiche Adresse (+2), gleiche Gemeinde (+2), gleicher Beruf
(+1), Vorname ausgeschrieben gleich (+2) bzw. abgekürzt (+1), seltener Name (+1).
Übergänge zwischen Gemeinden werden mitgerechnet (Stufe höchstens `möglich`), um zu prüfen, ob
das trägt.
"""

from __future__ import annotations

import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import NORM, ROOT, open_csv, write_csv  # noqa: E402
from link_ptt_ab import RANK, compare_forenames, forename_tokens, nkey, skey, stems  # noqa: E402
from migration import FEMALE_NAMES, FEMALE_OCC, GEB, MALE_NAMES, NOT_PERSON  # noqa: E402
from occupations_fine import fine  # noqa: E402

OUT = ROOT / "links" / "frauen_wege.csv"
WIDOW = re.compile(r"\b(Wwe|Witwe|Wittwe|Wb|Vve|Veuve)\b\.?", re.I)
SINGLE = re.compile(r"\b(Frl|Fräulein|Mlle|Mademoiselle|Jgfr|Jungfer|Demoiselle)\b\.?", re.I)
MARRIED = re.compile(r"\b(Frau|Mme|Madame|geb|née)\b\.?", re.I)
FIELDS = ["typ", "stufe", "punkte", "belege", "von_spur", "nach_spur", "von_gemeinde", "nach_gemeinde",
          "von_jahre", "nach_jahre", "von_name", "nach_name", "von_text", "nach_text", "von_einheiten", "nach_einheiten"]


def first_name(forename: str) -> tuple[str, str]:
    """Erster ausgeschriebener Vorname und sein Geschlecht (f/m/'')."""
    for w in re.findall(r"[A-Za-zÀ-ÿ]+\.?", forename or ""):
        if w.endswith(".") or len(w) <= 3:
            continue
        lw = w.lower()
        if lw in FEMALE_NAMES:
            return lw, "f"
        if lw in MALE_NAMES:
            return lw, "m"
    return "", ""


def record(src: str, rid: str, muni: str, year: int, surname: str, alliance: str, maiden: str, forename: str,
           marks: str, occ: str, phone: str, addr: str, text: str) -> dict | None:
    if not surname or not muni or NOT_PERSON.search(surname + " " + forename):
        return None
    sk = nkey(re.split(r"[\s\-]+", surname.strip())[0])
    if len(sk) < 2:
        return None
    fn, fsex = first_name(forename)
    female_occ = bool(FEMALE_OCC.search(occ.split("|")[0])) if occ else False
    if WIDOW.search(marks):
        status = "witwe"
    elif SINGLE.search(marks):
        status = "ledig"
    elif MARRIED.search(marks) or maiden:
        status = "verheiratet"
    elif fsex == "f" or (female_occ and fsex != "m"):
        status = "verheiratet" if alliance else "ledig?"
    elif fsex == "m":
        status = "mann"
    else:
        return None
    husband_fn = fn if status == "witwe" and fsex == "m" else ""
    birth = nkey(maiden) if maiden else (nkey(alliance) if alliance and status in ("verheiratet", "witwe") else "")
    return {"src": src, "id": rid, "muni": muni, "year": year, "sk": sk, "birth": birth, "alli": nkey(alliance),
            "fn": forename_tokens(forename) if not husband_fn else [], "hfn": husband_fn, "status": status,
            "occ": occ, "phone": phone, "addr": addr, "text": text, "surname": surname, "forename": forename}


def load() -> list[dict]:
    recs = []
    for r in open_csv(NORM / "ab_entries.csv"):
        maiden = r["maiden_name"] or ((GEB.search(r["text"]) or [None, ""])[1])
        rec = record("ab", r["id"], r["municipality"] or r["city"], int(r["volume"][:4]), r["surname"], r["alliance_name"],
                     maiden, r["forename"], f"{r['civil_status']} {r['forename']} {r['text'][:120]}", r["occupation"], "",
                     skey(r["street"]) + " " + (r["building_no"] or "") if r["street"] else "", r["text"][:140])
        if rec:
            recs.append(rec)
    for r in open_csv(NORM / "ptt_entries.csv.gz"):
        if r["entity_type"] != "person" or r["place_confidence"] not in ("hoch", "mittel"):
            continue
        marks = f"{r['name1']} {r['name2']} {r['supplement']}"
        maiden = (GEB.search(marks) or [None, ""])[1]
        rec = record("ptt", r["id"], r["municipality_1914"], int(r["year"]), r["surname"], r["alliance_name"], maiden,
                     r["forename"], marks, r["occupation"], r["phone_norm"],
                     f"{r['street_key']} {r['house_no']}".strip() if r["street_key"] else "",
                     f"{r['year']} TB " + " | ".join(x for x in (r["name1"], r["name2"], r["supplement"], r["street"]) if x))
        if rec:
            recs.append(rec)
    return recs


def traces(recs: list[dict]) -> dict[str, dict]:
    """Spuren: gleiche Gemeinde, gleicher Zivilstand, gleicher Name (Familien-, Geburts-, Vorname)."""
    sp: dict[str, dict] = {}
    for r in recs:
        fkey = r["hfn"] or (r["fn"][0][0] if r["fn"] else "")
        key = "|".join((r["muni"], r["status"], r["sk"], r["birth"], fkey))
        s = sp.setdefault(key, {"key": key, "muni": r["muni"], "status": r["status"], "sk": r["sk"], "birth": r["birth"],
                                "alli": set(), "fn": r["fn"], "hfn": r["hfn"], "years": set(), "phones": set(),
                                "addrs": set(), "occ": set(), "texts": [], "ids": set(),
                                "name": f"{r['surname']}, {r['forename']}".strip(", ")})
        s["ids"].add(r["id"])
        s["years"].add(r["year"])
        if r["alli"]:
            s["alli"].add(r["alli"])
        if r["phone"]:
            s["phones"].add(r["phone"])
        if r["addr"]:
            s["addrs"].add(r["addr"])
        s["occ"] |= fine(r["occ"])
        if len(s["texts"]) < 3:
            s["texts"].append(r["text"])
        if len(r["fn"]) > len(s["fn"]):
            s["fn"] = r["fn"]
    for s in sp.values():
        s["first"], s["last"] = min(s["years"]), max(s["years"])
    return sp


def ini(k: str) -> str:
    return k[:1].replace("k", "c").replace("j", "i")


def names_fit(fa: list, fb: list) -> str:
    """Vornamen verträglich (wie M2) und, wo beide zwei haben, Stelle für Stelle gleich anfangend
    («Paule Elis.» ≠ «Maria Elisab.»). Rückgabe: gleich, abkürzung oder ''."""
    f = compare_forenames(fa, fb)
    if RANK.get(f, 0) < 2:
        return ""
    if len(fa) >= 2 and len(fb) >= 2 and any(ini(x) != ini(y) for (x, _), (y, _) in zip(fa, fb)):
        return ""
    return "gleich" if f == "gleich" else "abkürzung"


def score(a: dict, b: dict, n_name: Counter) -> tuple[int, list[str]] | None:
    pts, ev = 0, []
    if a["muni"] == b["muni"]:
        pts += 2; ev.append("gemeinde")
    if a["phones"] & b["phones"]:
        pts += 3; ev.append("nummer")
    if a["addrs"] & b["addrs"]:
        pts += 2; ev.append("adresse")
    if a["occ"] & b["occ"] - {"privat"}:
        pts += 1; ev.append("beruf")
    if n_name[a["sk"]] <= 20:
        pts += 1; ev.append("name:selten")
    return pts, ev


def main() -> None:
    recs = load()
    sp = traces(recs)
    n_name = Counter(s["sk"] for s in sp.values())
    by_status: dict[str, list] = defaultdict(list)
    for s in sp.values():
        by_status[s["status"]].append(s)
    # Indizes
    married_by_birth = defaultdict(list)
    for s in by_status["verheiratet"] + by_status["witwe"]:
        if s["birth"]:
            married_by_birth[s["birth"]].append(s)
    by_sk = defaultdict(lambda: defaultdict(list))
    for st in ("verheiratet", "witwe", "mann"):
        for s in by_status[st]:
            by_sk[st][s["sk"]].append(s)

    cand = []
    # ledig → verheiratet / witwe: Familienname der Ledigen = Geburtsname
    for st in ("ledig", "ledig?"):
        for a in by_status[st]:
            for b in married_by_birth.get(a["sk"], []):
                if b["first"] <= a["last"] or b["first"] - a["last"] > 20 or not a["fn"] or not b["fn"]:
                    continue
                f = names_fit(a["fn"], b["fn"])
                if not f:
                    continue
                pts, ev = score(a, b, n_name)
                pts += 2 if f == "gleich" else 1
                ev.insert(0, "vorname:" + f)
                if st == "ledig":
                    pts += 1; ev.append("frl.")
                cand.append((f"ledig→{b['status']}", a, b, pts, ev))
    # verheiratet → witwe: gleicher Ehename, Vorname der Frau verträglich, Geburtsname nicht verschieden
    for a in by_status["verheiratet"]:
        for b in by_sk["witwe"].get(a["sk"], []):
            if b["first"] <= a["last"] or not a["fn"] or not b["fn"]:
                continue  # Witwe erst nach der letzten Nennung als Ehefrau (im selben Band: zwei Frauen)
            if a["birth"] and b["birth"] and a["birth"][:5] != b["birth"][:5]:
                continue
            f = names_fit(a["fn"], b["fn"])
            if not f:
                continue
            pts, ev = score(a, b, n_name)
            pts += 2 if f == "gleich" else 1
            ev.insert(0, "vorname:" + f)
            if a["birth"] and b["birth"]:
                pts += 3; ev.append("geburtsname")
            cand.append(("verheiratet→witwe", a, b, pts, ev))
    # Ehemann → Witwe: Vorname des Mannes bei der Witwe, oder gleicher Allianzname; gleiche Gemeinde
    for a in by_status["mann"]:
        if not a["fn"]:
            continue
        mfn = a["fn"][0][0]
        for b in by_sk["witwe"].get(a["sk"], []):
            if b["muni"] != a["muni"] or not (a["last"] <= b["first"] <= a["last"] + 5):
                continue
            if b["first"] == a["last"] and not (a["phones"] & b["phones"]):
                continue  # Mann und «Witwe» im selben Band: nicht seine Witwe (Messung: Ott/Klein 1914)
            hit_fn = b["hfn"] and b["hfn"][:4] == mfn[:4]
            hit_alli = a["alli"] and (a["alli"] & ({b["birth"]} | b["alli"]))
            if not (hit_fn or hit_alli):
                continue
            pts, ev = score(a, b, n_name)
            if hit_fn:
                pts += 2; ev.insert(0, "vorname_des_mannes")
            if hit_alli:
                pts += 3; ev.insert(0, "allianzname")
            cand.append(("mann→witwe", a, b, pts, ev))

    # eindeutig in beide Richtungen, je Übergangstyp
    outs, ins = Counter((c[0][:5], c[1]["key"]) for c in cand), Counter((c[0][:5], c[2]["key"]) for c in cand)
    rows, stats = [], Counter()
    for typ, a, b, pts, ev in cand:
        stats["kandidaten:" + typ] += 1
        if outs[(typ[:5], a["key"])] > 1 or ins[(typ[:5], b["key"])] > 1:
            stats["mehrdeutig:" + typ] += 1
            continue
        same = a["muni"] == b["muni"]
        strong = {"nummer", "adresse", "geburtsname", "allianzname"} & set(ev)
        tier = ("wahrscheinlich" if same and pts >= 6 and strong else
                "möglich" if pts >= 5 or (same and pts >= 4) else "schwach")
        if not same and tier == "wahrscheinlich":
            tier = "möglich"
        stats[f"{typ}:{tier}"] += 1
        stats[f"{typ}:{'gleiche_gemeinde' if same else 'andere_gemeinde'}"] += 1
        rows.append({"typ": typ, "stufe": tier, "punkte": pts, "belege": "+".join(ev),
                     "von_spur": a["key"], "nach_spur": b["key"], "von_gemeinde": a["muni"], "nach_gemeinde": b["muni"],
                     "von_jahre": f"{a['first']}–{a['last']}", "nach_jahre": f"{b['first']}–{b['last']}",
                     "von_name": a["name"], "nach_name": b["name"],
                     "von_text": " ‖ ".join(a["texts"]), "nach_text": " ‖ ".join(b["texts"])})
    # Einheiten (M3) der beiden Spuren, für die Seite einer Einheit
    need = {i for r in rows for i in (sp[r["von_spur"]]["ids"] | sp[r["nach_spur"]]["ids"])}
    rec_ent = {m["record_id"]: m["entity_id"] for m in open_csv(ROOT / "links" / "entities.csv.gz") if m["record_id"] in need}
    for r in rows:
        for side in ("von", "nach"):
            ents = sorted({rec_ent[i] for i in sp[r[f"{side}_spur"]]["ids"] if i in rec_ent})
            r[f"{side}_einheiten"] = " ".join(ents[:5])
    rows.sort(key=lambda r: (r["typ"], ["wahrscheinlich", "möglich", "schwach"].index(r["stufe"]), r["von_name"]))
    write_csv(OUT, FIELDS, rows)
    stats.update({"einträge": len(recs), "spuren": len(sp), **{f"spuren:{k}": len(v) for k, v in by_status.items()}})
    (NORM / "frauen_wege_stats.json").write_text(json.dumps(dict(sorted(stats.items())), ensure_ascii=False, indent=1) + "\n")
    print(json.dumps(dict(sorted(stats.items())), ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()

"""BERNHIST als Referenz für den Kanton Bern: Orte an die Gemeinden von 1914 binden, verwendete Reihen ablegen.

    python scripts/ref_bernhist.py --bernhist <sqlite>     # liest den lokal geladenen Dump
    BERNHIST_SQLITE=<sqlite> python scripts/ref_bernhist.py
    python scripts/ref_bernhist.py                         # rechnet nur aus data/ref/bernhist/werte.csv neu

BERNHIST (Historisch-statistische Datenbank des Kantons Bern, Projekt Christian Pfister, heute bei der
Universitätsbibliothek Bern, https://www.bernhist.ch) kennt weder BFS-Nummern noch Koordinaten. Die Bindung geht
über den Namen (ort_schluessel) und eine Handtabelle (config/bernhist_orte.csv). Im Repo liegt nicht der Dump,
sondern nur, was gebraucht wird:

    data/ref/bernhist/werte.csv          verwendete Einzelwerte mit Ort, Thema, Jahr und Nummer im Dump
    data/ref/bernhist/orte.csv           jeder BERNHIST-Ort (Einwohnergemeinde) → Gemeinde von 1914 und Einheit
    data/ref/bernhist/gemeinden_1914.csv jede Berner Gemeinde von 1914 → BERNHIST-Ort, Einheit oder «nicht in BERNHIST»
    data/ref/bernhist/einheiten.csv      je Einheit: Bevölkerung 1880–1910, Haushalte 1888, Erwerbstätige nach Sektor 1910
    data/ref/bernhist/vergleich_bfs.csv  Bevölkerung 1900 und 1910 gegen data/ref/population_1850_2000.csv

Einheit: BERNHIST führt die Bevölkerung nicht im Gebietsstand von 1914. Tramelan, Konolfingen und Linden gibt es
nur als spätere Gemeinden, Strättligen steckt in Thun. Eine Einheit ist darum der BERNHIST-Ort, der die
Bevölkerung trägt, mit allen Gemeinden von 1914, die darin aufgehen (meist genau eine).

Erwerbstätige 1910: BERNHIST hat zwei Reihen. Reihe A (zuerst erfasst) steht im Gebietsstand von 1910 und nennt
den 1. und 2. Sektor; der 3. ist der Rest. Reihe B nennt alle drei Sektoren, steht aber in einem späteren
Gebietsstand (Bern mit Bümpliz, Biel mit Bözingen, Mett und Madretsch). sektoren() wählt je Einheit die Reihe,
die zum Gebiet der Bevölkerung passt, und schreibt die Wahl in die Spalte sektor_quelle.
"""

from __future__ import annotations

import argparse
import os
import re
import sqlite3
import sys
import unicodedata
from collections import defaultdict
from pathlib import Path

from common import ROOT, open_csv, write_csv
from infrastruktur import unit_2000

OUT = ROOT / "data" / "ref" / "bernhist"
HAND = ROOT / "config" / "bernhist_orte.csv"
QUELLE = "BERNHIST, Dump ub-unibe-ch/bernhist (Stand 22.03.2024)"
STADT_BERN = 457
EINWOHNERGEMEINDE = 6
CENSUS = (1880, 1888, 1900, 1910)
NICHT_IN_BERNHIST = ("District de Porrentruy", "District de Delémont", "District des Franches-Montagnes")

# Reihen je Gemeinde: Schlüssel → (Thema, Jahr)
GEMEINDE_REIHEN = {
    **{f"bev_{y}": (990, y) for y in CENSUS},
    "haushalte_1888": (543, 1888),
    "erw_1910": (342, 1910), "erw_s1_1910": (305, 1910), "erw_s2_1910": (314, 1910), "erw_s3_1910": (327, 1910),
}
# Nur für die Stadt Bern (Nenner der Gruppen; dieselben Werte wie adressbuecher-bern, ref/bernhist/werte.csv)
STADT_REIHEN = {
    "bev_1856": (990, 1856), "bev_1930": (990, 1930), "haushalte_1860": (543, 1860), "bev_1860": (990, 1860),
    "frauen_1856": (362, 1856), "maenner_1856": (696, 1856), "frauen_1930": (362, 1930), "maenner_1930": (696, 1930),
    "verwitwet_1856": (988, 1856), "verwitwet_1910": (988, 1910), "ledig_1910": (984, 1910),
    "verheiratet_1910": (986, 1910), "geschieden_1910": (982, 1910),
    "witwen_1846": (360, 1846), "witwer_1846": (694, 1846),
    "erw_1856": (342, 1856), "selbstaendige_1856": (341, 1856), "selbstaendige_1930": (341, 1930),
    "dienstboten_1856": (344, 1856), "dienstboten_1910": (344, 1910),
    "erw_frauen_1910": (345, 1910), "erw_maenner_1910": (346, 1910),
    "aerzte_1856": (1713, 1856), "aerzte_1910": (1713, 1910),
    "spezerei_1901": (1690, 1901), "spezerei_1909": (1690, 1909),
    "handel_1910": (330, 1910), "gastgewerbe_1910": (329, 1910), "verwaltung_1910": (336, 1910),
    "verkehr_1910": (335, 1910), "bau_1910": (316, 1910), "nahrung_1910": (323, 1910),
    "bekleidung_1910": (317, 1910), "druck_1910": (325, 1910), "maschinen_1910": (322, 1910),
}
WERTE_FELDER = ["reihe", "rang", "bernhist_id", "ort", "thema_id", "thema", "jahr", "wert", "data_entry_id"]


# ── Namen ────────────────────────────────────────────────────────────────────────────────────────────
def ort_schluessel(name: str) -> str:
    """Vergleichsform eines Ortsnamens: ohne Zusätze in Klammern, Artikel nach vorn, ohne Akzente, th = t."""
    s = re.sub(r"\s*\((?:bis|ab|mit)\b[^)]*\)", "", name)
    s = re.sub(r"\s*\(BE\)", "", s).strip()
    if m := re.match(r"(.+), (La|Le|Les)$", s):
        s = f"{m[2]} {m[1]}"
    s = unicodedata.normalize("NFKD", s.lower())
    s = "".join(c for c in s if not unicodedata.combining(c))
    return re.sub(r"[^a-z]+", " ", s.replace("th", "t")).strip()


def ort_varianten(name: str) -> list[str]:
    """«Interlaken / Aarmühle» trägt zwei Namen: der ganze Name zuerst, dann jeder Teil."""
    s = re.sub(r"\s*\((?:bis|ab|mit)\b[^)]*\)", "", name)
    out = []
    for p in [s] + s.split(" / "):
        k = ort_schluessel(p)
        if k and k not in out:
            out.append(k)
    return out


# ── Dump lesen ───────────────────────────────────────────────────────────────────────────────────────
def werte_aus_dump(pfad: Path) -> tuple[list[dict], list[dict]]:
    """Orte (Einwohnergemeinden) und die verwendeten Werte. Doppelte Werte bekommen einen Rang nach data_entry.id."""
    db = sqlite3.connect(f"file:{pfad}?mode=ro", uri=True)
    orte = [{"bernhist_id": i, "bernhist_name": n} for i, n in
            db.execute("select id, name from location where type_id = ? order by id", (EINWOHNERGEMEINDE,))]
    thema = dict(db.execute("select id, name from topic"))
    name = {o["bernhist_id"]: o["bernhist_name"] for o in orte}
    rows = []

    def lies(reihe: str, tid: int, jahr: int, nur: int | None) -> None:
        q = ("select d.location_id, d.value, d.id from data_entry d join location l on l.id = d.location_id "
             "where l.type_id = ? and d.topic_id = ? and d.year_from = ?")
        args: list = [EINWOHNERGEMEINDE, tid, jahr]
        if nur is not None:
            q += " and d.location_id = ?"
            args.append(nur)
        rang: dict = defaultdict(int)
        for loc, wert, did in db.execute(q + " order by d.location_id, d.id", args):
            rows.append({"reihe": reihe, "rang": rang[loc], "bernhist_id": loc, "ort": name[loc], "thema_id": tid,
                         "thema": thema[tid], "jahr": jahr, "wert": int(wert) if wert == int(wert) else wert,
                         "data_entry_id": did})
            rang[loc] += 1

    for reihe, (tid, jahr) in GEMEINDE_REIHEN.items():
        lies(reihe, tid, jahr, None)
    for reihe, (tid, jahr) in STADT_REIHEN.items():
        lies(reihe, tid, jahr, STADT_BERN)
    rows.sort(key=lambda r: (r["reihe"], r["bernhist_id"], r["rang"]))
    return orte, rows


def werte_index(rows: list[dict]) -> dict:
    """(reihe, bernhist_id) → Werte nach Rang."""
    out: dict = defaultdict(list)
    for r in sorted(rows, key=lambda r: (r["reihe"], int(r["bernhist_id"]), int(r["rang"]))):
        out[(r["reihe"], int(r["bernhist_id"]))].append(float(r["wert"]))
    return out


# ── Zuordnung ────────────────────────────────────────────────────────────────────────────────────────
def zuordnen(orte: list[dict], gemeinden: list[dict], hand: list[dict], hat_bev: set[int]) -> tuple[list[dict], list[dict]]:
    """BERNHIST-Orte ↔ Gemeinden von 1914 (Kanton BE). Gibt (orte.csv, gemeinden_1914.csv) zurück."""
    nach_schluessel = {}
    for g in gemeinden:
        nach_schluessel.setdefault(ort_schluessel(g["name"]), g)
    nach_name = {g["name"]: g for g in gemeinden}
    bh_name = {o["bernhist_name"]: o for o in orte}
    umbenannt = {h["bernhist_name"]: h for h in hand if h["art"] == "name"}
    teil = {h["bernhist_name"]: h for h in hand if h["art"] == "einheit"}
    for h in hand:
        if h["bernhist_name"] not in bh_name:
            raise SystemExit(f"Handtabelle: BERNHIST-Ort «{h['bernhist_name']}» gibt es nicht")
        if h["art"] == "name" and h["ziel"] not in nach_name:
            raise SystemExit(f"Handtabelle: Gemeinde von 1914 «{h['ziel']}» gibt es nicht")
        if h["art"] == "einheit" and h["ziel"] not in bh_name:
            raise SystemExit(f"Handtabelle: Einheit «{h['ziel']}» gibt es nicht")
    out, vergeben = [], {}
    for o in orte:
        n, i = o["bernhist_name"], o["bernhist_id"]
        g, methode = None, ""
        if n in umbenannt:
            g, methode = nach_name[umbenannt[n]["ziel"]], "hand"
        elif n in nach_name:
            g, methode = nach_name[n], "exakt"
        else:
            for k in ort_varianten(n):
                if k in nach_schluessel:
                    g, methode = nach_schluessel[k], "normalisiert"
                    break
        if g and g["hist_code"] in vergeben:
            raise SystemExit(f"{g['name']} doppelt zugeordnet: {vergeben[g['hist_code']]} und {n}")
        if g:
            vergeben[g["hist_code"]] = n
        if n in teil:
            einheit, bem = bh_name[teil[n]["ziel"]], teil[n]["grund"]
        elif i in hat_bev:
            einheit, bem = o, ""
        else:
            einheit = None
            bem = ("in BERNHIST ohne Wohnbevölkerung 1910" if g else
                   "vor 1914 aufgelöst oder ohne Werte 1880–1910" if re.search(r"\(bis 1[89]", n) else
                   "ohne Wohnbevölkerung 1910, keine Gemeinde von 1914")
        if not g and einheit is o:
            bem = "spätere Gemeinde: trägt die Bevölkerung ihrer Vorgänger"
        out.append({"bernhist_id": i, "bernhist_name": n, "hist_code": g["hist_code"] if g else "",
                    "gemeinde_1914": g["name"] if g else "", "einheit_id": einheit["bernhist_id"] if einheit else "",
                    "einheit_name": einheit["bernhist_name"] if einheit else "", "methode": methode, "bemerkung": bem})
    nach_code = {r["hist_code"]: r for r in out if r["hist_code"]}
    gem = []
    for g in sorted(gemeinden, key=lambda g: g["name"]):
        r = nach_code.get(g["hist_code"])
        if r and r["einheit_id"] != "":
            status = "zugeordnet" if r["einheit_id"] == r["bernhist_id"] else "Teil einer Einheit"
        elif r:
            status = "ohne Bevölkerung in BERNHIST"
        else:
            status = "nicht in BERNHIST" + (" (Nordjura, seit 1979 Kanton Jura)" if g["district"] in NICHT_IN_BERNHIST else "")
        gem.append({"hist_code": g["hist_code"], "name": g["name"], "district": g["district"],
                    "bernhist_id": r["bernhist_id"] if r else "", "einheit_id": r["einheit_id"] if r else "",
                    "einheit_name": r["einheit_name"] if r else "", "status": status})
    return out, gem


# ── Erwerbstätige nach Sektor 1910 ───────────────────────────────────────────────────────────────────
def sektoren(traeger: int, teile: list[int], w: dict) -> dict:
    """Erwerbstätige 1910 einer Einheit im Gebiet ihrer Bevölkerung: {erw, s1, s2, s3, quelle, pruefung}.

    traeger: BERNHIST-Ort mit der Bevölkerung; teile: Orte ohne eigene Bevölkerung, die in ihr stecken.
    """
    def a(i: int, k: str) -> float | None:      # Reihe A: erster Wert
        v = w.get((k, i), [])
        return v[0] if v else None

    def b(i: int, k: str) -> float | None:      # Reihe B: zweiter Wert, beim 3. Sektor der einzige
        v = w.get((k, i), [])
        return v[0] if k == "erw_s3_1910" and v else v[1] if len(v) > 1 else None

    leer = {"erw": "", "s1": "", "s2": "", "s3": "", "quelle": "fehlt", "pruefung": ""}
    erw_a = a(traeger, "erw_1910")
    if erw_a is None:
        return leer
    s3_b = b(traeger, "erw_s3_1910")
    if len(w.get(("erw_1910", traeger), [])) == 1:
        # ein einziger Wert: Gemeinde ohne spätere Gebietsänderung in Reihe B oder spätere Gemeinde (Summe der Teile)
        s1, s2 = a(traeger, "erw_s1_1910"), a(traeger, "erw_s2_1910")
        if s1 is None or s2 is None or s1 + s2 > erw_a:
            return {**leer, "erw": int(erw_a), "pruefung": "1. und 2. Sektor fehlen oder übersteigen die Summe"}
        s3 = erw_a - s1 - s2
        pr = "" if s3_b is None or s3_b == s3 else f"3. Sektor in BERNHIST {int(s3_b)}, als Rest {int(s3)}"
        summe = sum(a(t, "erw_1910") or 0 for t in teile)
        if teile and summe != erw_a:
            pr = (pr + "; " if pr else "") + f"Summe der Teile {int(summe)}"
        return {"erw": int(erw_a), "s1": int(s1), "s2": int(s2), "s3": int(s3),
                "quelle": "einzige Reihe" + (", 3. Sektor als Rest" if s3_b is None else ""), "pruefung": pr}
    erw_b, s1_b, s2_b = b(traeger, "erw_1910"), b(traeger, "erw_s1_1910"), b(traeger, "erw_s2_1910")
    b_ganz = None not in (erw_b, s1_b, s2_b, s3_b) and s1_b + s2_b + s3_b == erw_b
    s1, s2 = a(traeger, "erw_s1_1910"), a(traeger, "erw_s2_1910")
    quelle = "Reihe A, 3. Sektor als Rest"
    erw = erw_a
    if teile and erw_b != erw_a:                 # A = Gebiet von 1910 ohne die Teile (Thun ohne Strättligen)
        erw += sum(a(t, "erw_1910") or 0 for t in teile)
        s1 += sum(a(t, "erw_s1_1910") or 0 for t in teile)
        s2 += sum(a(t, "erw_s2_1910") or 0 for t in teile)
        quelle = "Reihe A mit Teilen, 3. Sektor als Rest"
    if s1 + s2 > erw or (s1 == 0 and b_ganz and s1_b > 0):
        if not b_ganz:
            return {**leer, "erw": int(erw), "pruefung": "Reihe A lückenhaft, Reihe B nicht schlüssig"}
        return {"erw": int(erw_b), "s1": int(s1_b), "s2": int(s2_b), "s3": int(s3_b), "quelle": "Reihe B (Reihe A lückenhaft)",
                "pruefung": f"Reihe A: {int(erw_a)} Erwerbstätige, 1. Sektor {int(s1)}"}
    s3 = erw - s1 - s2
    if erw_b == erw and b_ganz:
        pr = "" if (s1_b, s2_b, s3_b) == (s1, s2, s3) and s3_b == s3 else (
            "" if s3_b == s3 else f"Reihe B verteilt anders: {int(s1_b)}/{int(s2_b)}/{int(s3_b)}")
    elif erw_b == erw:
        pr = "Reihe B nicht schlüssig"
    else:
        pr = f"Reihe B anderes Gebiet oder lückenhaft ({int(erw_b)} Erwerbstätige)"
    return {"erw": int(erw), "s1": int(s1), "s2": int(s2), "s3": int(s3), "quelle": quelle, "pruefung": pr}


def einheiten(orte: list[dict], w: dict) -> list[dict]:
    glieder: dict = defaultdict(list)
    for o in orte:
        if o["einheit_id"] != "":
            glieder[int(o["einheit_id"])].append(o)
    out = []
    for e, gs in sorted(glieder.items()):
        selbst = next(o for o in gs if int(o["bernhist_id"]) == e)
        teile = [int(o["bernhist_id"]) for o in gs if int(o["bernhist_id"]) != e]
        codes = [o["hist_code"] for o in gs if o["hist_code"]]
        row = {"einheit_id": e, "name": selbst["bernhist_name"],
               "hist_codes": ";".join(codes), "gemeinden_1914": ";".join(o["gemeinde_1914"] for o in gs if o["hist_code"]),
               "n_gemeinden_1914": len(codes)}
        for y in CENSUS:
            v = w.get((f"bev_{y}", e), [])
            row[f"bev_{y}"] = int(v[0]) if v and v[0] > 0 else ""
        v = w.get(("haushalte_1888", e), [])
        row["haushalte_1888"] = int(v[0]) if v and v[0] > 0 else ""
        s = sektoren(e, teile, w)
        row.update({"erw_1910": s["erw"], "s1_1910": s["s1"], "s2_1910": s["s2"], "s3_1910": s["s3"],
                    "sektor_quelle": s["quelle"], "sektor_pruefung": s["pruefung"]})
        out.append(row)
    return out


# ── Abgleich mit der BFS-Tabelle ─────────────────────────────────────────────────────────────────────
def vergleich_bfs(einh: list[dict], gemeinden: list[dict], bfs: list[dict], schwelle: float = 2.0) -> list[dict]:
    """Bevölkerung 1900 und 1910: BERNHIST gegen die BFS-Tabelle (Gebietsstand 2000).

    Verglichen wird, was dasselbe Gebiet meint: die BFS-Gemeinde von 2000 gegen die Summe der Einheiten, deren
    Gemeinden von 1914 alle in ihr liegen. Fehlt eine Gemeinde von 1914 in BERNHIST, steht das in der Bemerkung.
    """
    pop = {r["bfs"]: r for r in bfs}
    code = {g["hist_code"]: g for g in gemeinden}
    ziel = {g["hist_code"]: unit_2000(g, set(pop)) for g in gemeinden}
    erwartet: dict = defaultdict(set)            # BFS-Gemeinde → Gemeinden von 1914
    for c, u in ziel.items():
        if u:
            erwartet[u].add(c)
    gruppen: dict = defaultdict(list)
    for e in einh:
        us = {ziel[c] for c in e["hist_codes"].split(";") if c}
        gruppen[tuple(sorted(us))].append(e)
    out = []
    for us, es in sorted(gruppen.items(), key=lambda kv: kv[1][0]["name"]):
        if len(us) != 1 or not us[0]:
            for e in es:
                out.append({"bfs": "/".join(us), "name_bfs": "", "einheiten": e["name"], "bemerkung":
                            "nicht vergleichbar: Einheit liegt in mehreren BFS-Gemeinden oder in keiner"})
            continue
        u = us[0]
        da = {c for e in es for c in e["hist_codes"].split(";") if c}
        fehlt = sorted(code[c]["name"] for c in erwartet[u] - da)
        row = {"bfs": u, "name_bfs": pop[u]["name"], "einheiten": ";".join(e["name"] for e in es),
               "bemerkung": ("in BERNHIST ohne Bevölkerung: " + ", ".join(fehlt)) if fehlt else ""}
        if fehlt:
            row["bemerkung"] = "nicht vergleichbar: " + row["bemerkung"]
            out.append(row)
            continue
        for y in (1900, 1910):
            bh = sum(e[f"bev_{y}"] or 0 for e in es)
            ref = int(pop[u][str(y)]) if pop[u][str(y)] else 0
            row[f"bernhist_{y}"], row[f"bfs_{y}"] = bh, ref
            row[f"abw_{y}_prozent"] = round(100 * (bh - ref) / ref, 1) if ref else ""
        row["ueber_schwelle"] = "ja" if any(row[f"abw_{y}_prozent"] != "" and abs(row[f"abw_{y}_prozent"]) > schwelle
                                            for y in (1900, 1910)) else ""
        row["identisch"] = "ja" if all(row[f"bernhist_{y}"] == row[f"bfs_{y}"] for y in (1900, 1910)) else ""
        out.append(row)
    return out


# ── Ablauf ───────────────────────────────────────────────────────────────────────────────────────────
def gemeinden_be() -> list[dict]:
    return [r for r in open_csv(ROOT / "data" / "ref" / "municipalities_1914.csv") if r["canton"] == "BE"]


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--bernhist", default=os.environ.get("BERNHIST_SQLITE", ""), help="lokal geladener Dump (SQLite)")
    args = ap.parse_args()
    if args.bernhist:
        orte, rows = werte_aus_dump(Path(args.bernhist))
        write_csv(OUT / "werte.csv", WERTE_FELDER, rows)
    else:
        rows = open_csv(OUT / "werte.csv")
        orte = [{"bernhist_id": int(r["bernhist_id"]), "bernhist_name": r["bernhist_name"]} for r in open_csv(OUT / "orte.csv")]
    w = werte_index(rows)
    hat_bev = {i for (k, i), v in w.items() if k == "bev_1910" and v and v[0] > 0}
    gem = gemeinden_be()
    o, g = zuordnen(orte, gem, open_csv(HAND), hat_bev)
    e = einheiten(o, w)
    v = vergleich_bfs(e, gem, open_csv(ROOT / "data" / "ref" / "population_1850_2000.csv"))
    write_csv(OUT / "orte.csv", list(o[0]), o)
    write_csv(OUT / "gemeinden_1914.csv", list(g[0]), g)
    write_csv(OUT / "einheiten.csv", list(e[0]), e)
    write_csv(OUT / "vergleich_bfs.csv", ["bfs", "name_bfs", "einheiten", "bernhist_1900", "bfs_1900", "abw_1900_prozent",
                                          "bernhist_1910", "bfs_1910", "abw_1910_prozent", "identisch", "ueber_schwelle", "bemerkung"], v)
    from collections import Counter
    print(f"BERNHIST-Orte {len(o)}, davon an eine Gemeinde von 1914 gebunden {sum(1 for r in o if r['hist_code'])}",
          dict(Counter(r["methode"] or "–" for r in o)))
    print("Gemeinden von 1914 (BE):", len(g), dict(Counter(r["status"] for r in g)))
    print("Einheiten:", len(e), "mit Sektoren", sum(1 for r in e if r["s1_1910"] != ""), dict(Counter(r["sektor_quelle"] for r in e)))
    print("Sektor-Prüfung:", [(r["name"], r["sektor_pruefung"]) for r in e if r["sektor_pruefung"]])
    vv = [r for r in v if r.get("bfs_1910")]
    print(f"BFS-Abgleich: {len(vv)} vergleichbar, in beiden Jahren identisch {sum(1 for r in vv if r['identisch'])}, "
          f"über 2 %: {sum(1 for r in vv if r['ueber_schwelle'])}")
    for r in sorted((r for r in vv if r["ueber_schwelle"]), key=lambda r: -abs(r["abw_1910_prozent"] or 0)):
        print("  ", r["name_bfs"], r["bernhist_1900"], r["bfs_1900"], r["abw_1900_prozent"], "|",
              r["bernhist_1910"], r["bfs_1910"], r["abw_1910_prozent"], "|", r["einheiten"], "|", r["bemerkung"])


if __name__ == "__main__":
    sys.exit(main())

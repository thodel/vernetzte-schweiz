"""M3, Teil 2: Einheiten mit Normdaten verbinden (Wikidata, HLS, GND).

    python scripts/authority.py fetch   # Kandidaten aus Wikidata → data/ref/wikidata_persons.csv.gz
    python scripts/authority.py link    # Abgleich → links/authority.csv

**Übernahme.** Die Städte haben ihre Adressbuch-Einträge selbst abgeglichen
(`data/norm/ab_authority.csv`, bis «möglich»). Gehört ein solcher Eintrag zu einer Einheit
(M3, `cluster.py`), erhält die ganze Einheit diese Normdaten (`source = stadt`).

**Zweiter Abgleich** für Personen ohne Normdaten der Stadt, meist solche, die nur im
Telefonbuch stehen. Kandidaten sind Menschen in Wikidata, geboren 1790–1895, gestorben 1880
oder später (oder ohne Sterbedatum), mit HLS-Artikel (P902) oder mit Wohn-, Wirkungs- oder
Sterbeort in einer Schweizer Gemeinde. Den Ort verbindet die **BFS-Gemeindenummer** (P771
des Ortes = `bfs_today` der Einheit), nicht der Ortsname; HLS-Nummer und GND kommen aus
demselben Wikidata-Eintrag, nicht aus einer Namenssuche.

Bedingungen: gleicher Familienname, verträglicher Vorname, die Person lebte im ersten Jahr
der Einheit und war 25–80 Jahre alt, und Wohn-, Wirkungs- oder Sterbeort in der Gemeinde
der Einheit (der Geburtsort allein genügt nicht).
- `wahrscheinlich`: ausgeschriebener oder abgekürzter Vorname und ein passender Beruf
  (gleicher Wortstamm oder gleiche Berufsgruppe: Arzt = médecin, Advokat = avocat …);
  nur ein solcher Kandidat;
- `möglich`: Initiale mit passendem Beruf, oder ausgeschriebener Vorname mit Wohn- bzw.
  Wirkungsort in der Gemeinde (ohne Beruf); nur ein solcher Kandidat.
Name und Sterbeort allein genügen nicht: In den Städten gibt es zu viele Namensvettern
(gemessen: etwa 4 von 10 richtig).
Witwen und Einträge mit «Frau» bleiben ohne Abgleich: Wikidata nennt meist den Mann.
Firmen bleiben in diesem Schritt ohne Abgleich.
"""

from __future__ import annotations

import csv
import gzip
import json
import re
import sys
import time
import urllib.parse
import urllib.request
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from common import NORM, ROOT, open_csv, write_csv  # noqa: E402
from link_ptt_ab import LINKS, compare_forenames, forename_tokens, nkey, stems  # noqa: E402

REF = ROOT / "data" / "ref" / "wikidata_persons.csv.gz"
SPARQL = "https://query.wikidata.org/sparql"
UA = "vernetzte-schweiz/0.1 (https://github.com/thodel/vernetzte-schweiz)"
WINDOW = "FILTER(YEAR(?b) >= 1790 && YEAR(?b) <= 1895 && (!BOUND(?d) || YEAR(?d) >= 1880))"
ID_QUERIES = {
    "hls": "SELECT DISTINCT ?p WHERE { ?p wdt:P902 ?h; wdt:P31 wd:Q5; wdt:P569 ?b . OPTIONAL { ?p wdt:P570 ?d } "
           + WINDOW + " }",
    "ort": "SELECT DISTINCT ?p WHERE { VALUES ?rel { wdt:P551 wdt:P937 wdt:P20 } ?p ?rel ?pl . ?pl wdt:P771 ?bfs . "
           "?p wdt:P31 wd:Q5; wdt:P569 ?b . OPTIONAL { ?p wdt:P570 ?d } " + WINDOW + " }",
}
DETAIL = """SELECT ?p (SAMPLE(?lbl) AS ?label) (MIN(?b) AS ?birth) (MIN(?d) AS ?death) (SAMPLE(?hls) AS ?hls)
  (SAMPLE(?gnd) AS ?gnd) (SAMPLE(?sex) AS ?sex)
  (GROUP_CONCAT(DISTINCT ?gn; separator="|") AS ?given) (GROUP_CONCAT(DISTINCT ?fn; separator="|") AS ?family)
  (GROUP_CONCAT(DISTINCT ?occ; separator="|") AS ?occupations) (GROUP_CONCAT(DISTINCT ?pc; separator="|") AS ?places)
WHERE {
  VALUES ?p { %s }
  OPTIONAL { ?p wdt:P569 ?b } OPTIONAL { ?p wdt:P570 ?d } OPTIONAL { ?p wdt:P21 ?sex }
  OPTIONAL { ?p rdfs:label ?lbl FILTER(LANG(?lbl) IN ("de", "fr", "it", "mul")) }
  OPTIONAL { ?p wdt:P902 ?hls } OPTIONAL { ?p wdt:P227 ?gnd }
  OPTIONAL { ?p wdt:P735 ?g . ?g rdfs:label ?gn FILTER(LANG(?gn) IN ("de", "fr", "mul", "en")) }
  OPTIONAL { ?p wdt:P734 ?f . ?f rdfs:label ?fn FILTER(LANG(?fn) IN ("de", "fr", "mul", "en")) }
  OPTIONAL { ?p wdt:P106 ?o . ?o rdfs:label ?occ FILTER(LANG(?occ) IN ("de", "fr")) }
  OPTIONAL { VALUES (?rel ?code) { (wdt:P551 "wohnort") (wdt:P937 "wirkungsort") (wdt:P20 "sterbeort") (wdt:P19 "geburtsort") }
             ?p ?rel ?pl . ?pl wdt:P771 ?bfs . BIND(CONCAT(?code, ":", ?bfs) AS ?pc) }
} GROUP BY ?p"""
FIELDS = ["qid", "label", "birth", "death", "sex", "hls_id", "gnd", "given", "family", "occupations", "places"]
AUTH_FIELDS = [
    "entity_id", "qid", "label", "birth", "death", "hls_id", "gnd", "tier", "source", "evidence", "hls_check", "via",
]
STRONG = ("wohnort", "wirkungsort", "sterbeort")
LIVED = ("wohnort", "wirkungsort")
# Berufsgruppen über Sprachen und Titel hinweg (kurze Wörter wie «Arzt» fallen bei den
# Wortstämmen sonst weg)
OCC_GROUPS = {
    "arzt": r"\barzt|ärzt|médecin|medecin|docteur|dr\.? ?med|chirurg|mediziner|internist",
    "jurist": r"advokat|fürsprech|notar|jurist|avocat|rechtsanwalt|richter|juge|dr\.? ?jur",
    "pfarrer": r"pfarrer|pasteur|theolog|pfr\.|curé|prediger|dekan",
    "professor": r"\bprof\b|prof\.|professor|hochschullehrer|professeur",
    "ingenieur": r"ingenieur|ingénieur|ing\.",
    "architekt": r"architekt|architecte",
    "fabrikant": r"fabrikant|fabricant|industriell|industriel|unternehmer|entrepreneur",
    "bankier": r"bankier|banquier|bankdirektor|bankverein",
    "apotheker": r"apothek|pharmac",
    "lehrer": r"lehrer|instituteur|enseignant|pädagog",
    "politiker": r"regierungsrat|nationalrat|ständerat|stadtrat|grossrat|bürgerrat|politiker|politique|conseiller",
    "musiker": r"musik|musicien|komponist|dirigent|organist",
    "maler": r"kunstmaler|artiste peintre|\bmaler\b",
    "uhrmacher": r"horlog|uhrmacher|uhrenfabr",
}
FEMALE = re.compile(r"\b(Frau|Fräulein|Frl|Mme|Mlle|Madame|Mademoiselle|Wwe|Witwe|Vve|Veuve|Wb)\b", re.I)


def sparql(q: str) -> list[dict]:
    data = urllib.parse.urlencode({"query": q}).encode()
    for attempt in range(5):
        try:
            req = urllib.request.Request(SPARQL, data=data, headers={
                "User-Agent": UA, "Accept": "application/sparql-results+json"})
            with urllib.request.urlopen(req, timeout=300) as r:
                return json.loads(r.read().decode("utf-8"))["results"]["bindings"]
        except Exception as e:  # noqa: BLE001 — Wikidata drosselt; erneut versuchen
            print(f"  Wikidata: {e}; neuer Versuch", file=sys.stderr)
            time.sleep(20 * (attempt + 1))
    raise RuntimeError("Wikidata antwortet nicht")


def fetch() -> None:
    ids: set[str] = set()
    for name, q in ID_QUERIES.items():
        got = {b["p"]["value"].rsplit("/", 1)[1] for b in sparql(q)}
        print(f"{name}: {len(got)} Personen")
        ids |= got
    ids_sorted = sorted(ids, key=lambda q: int(q[1:]))
    rows = []
    for k in range(0, len(ids_sorted), 250):
        batch = ids_sorted[k:k + 250]
        for b in sparql(DETAIL % " ".join(f"wd:{q}" for q in batch)):
            v = {key: b[key]["value"] for key in b}
            rows.append({
                "qid": v["p"].rsplit("/", 1)[1], "label": v.get("label", ""),
                "birth": v.get("birth", "")[:10], "death": v.get("death", "")[:10],
                "sex": {"Q6581097": "m", "Q6581072": "f"}.get(v.get("sex", "").rsplit("/", 1)[-1], ""),
                "hls_id": v.get("hls", ""), "gnd": v.get("gnd", ""),
                "given": v.get("given", ""), "family": v.get("family", ""),
                "occupations": v.get("occupations", ""), "places": v.get("places", ""),
            })
        print(f"  {min(k + 250, len(ids_sorted))}/{len(ids_sorted)}", file=sys.stderr)
        time.sleep(1)
    rows.sort(key=lambda r: int(r["qid"][1:]))
    write_csv(REF, FIELDS, rows)
    print(f"{len(rows)} Kandidaten → {REF.relative_to(ROOT)}")


# ── Abgleich ──────────────────────────────────────────────────────────────

def year(s: str) -> int | None:
    m = re.match(r"-?(\d{4})", s or "")
    return int(m.group(1)) if m else None


def candidates() -> dict[str, list[dict]]:
    """{Familienname-Schlüssel: [Kandidat]} mit Vornamen-Schlüsseln und Orten."""
    idx: dict[str, list[dict]] = defaultdict(list)
    for c in open_csv(REF):
        fam = {nkey(f) for f in c["family"].split("|") if f}
        words = c["label"].split()
        if len(words) >= 2:
            fam.add(nkey(words[-1]))
        given = " ".join(g for g in c["given"].split("|") if g) or " ".join(words[:-1])
        c["_fn"] = forename_tokens(given)
        c["_b"], c["_d"] = year(c["birth"]), year(c["death"])
        places = defaultdict(set)
        for pc in c["places"].split("|"):
            if ":" in pc:
                rel, bfs = pc.split(":", 1)
                places[bfs].add(rel)
        c["_places"] = places
        c["_occ"] = stems(c["occupations"].replace("|", " "))
        c["_grp"] = occ_groups(c["occupations"].replace("|", " ") + " " + c["label"])
        for f in fam - {""}:
            idx[f].append(c)
    return idx


def entity_profiles() -> dict[str, dict]:
    """Je Personen-Einheit: Familienname, Vornamen, Gemeinde (BFS), Jahre, Berufe."""
    import cluster  # noqa: PLC0415 — teuer, nur für den Abgleich
    recs = {r["id"]: r for r in cluster.ptt_records(cluster.config())}
    summ = {s["entity_id"]: s for s in open_csv(NORM / "entities.csv.gz")}
    prof: dict[str, dict] = {}
    for m in open_csv(LINKS / "entities.csv.gz"):
        s = summ[m["entity_id"]]
        if s["kind"] != "person":
            continue
        p = prof.setdefault(m["entity_id"], {"sk": set(), "fns": set(), "occ": set(), "female": False, "summary": s,
                                              "text": s["occupations"]})
        r = recs.get(m["record_id"])
        if r is None:
            continue
        p["sk"].add(r["sk"])
        if r["fn"]:
            p["fns"].add(r["fn"])
        p["occ"] |= r["occ"]
        p["text"] += " " + r["name"]
        p["female"] |= r["widow"] or bool(FEMALE.search(r["name"] + " " + r["occupation"]))
    return prof


def occ_groups(text: str) -> set[str]:
    t = (text or "").lower()
    return {g for g, pat in OCC_GROUPS.items() if re.search(pat, t)}


def best_forename(fns: set[tuple]) -> tuple:
    """Der ausführlichste Vorname der Einheit (ausgeschrieben vor abgekürzt)."""
    return max(fns, key=lambda t: (sum(not short for _, short in t), sum(len(k) for k, _ in t)), default=())


def match(p: dict, idx: dict) -> tuple[dict, str, list[str]] | None:
    s = p["summary"]
    first, bfs = int(s["first_year"]), s["bfs_today"]
    fn = best_forename(p["fns"])
    if not fn or not bfs or p["female"]:
        return None
    p["groups"] = occ_groups(p["text"])
    found = []
    for c in {id(c): c for k in p["sk"] for c in idx.get(k, ())}.values():
        level = compare_forenames(list(fn), c["_fn"])
        if level in ("", "widerspruch"):
            continue
        if any(compare_forenames(list(f), c["_fn"]) == "widerspruch" for f in p["fns"]):
            continue
        if c["_b"] is None or c["_b"] > first - 25 or c["_b"] < first - 80 or (c["_d"] is not None and c["_d"] < first):
            continue
        rels = c["_places"].get(bfs, set())
        strong = sorted(rels & set(STRONG))
        if not strong:
            continue  # Geburtsort allein: zu schwach
        ev = [f"vorname:{level}"] + strong
        job = bool(p["occ"] & c["_occ"]) or bool(p["groups"] & c["_grp"])
        if job:
            ev.append("beruf")
        lived = bool(rels & set(LIVED))
        full = level in ("gleich", "abkürzung")
        if full and job:
            tier = "wahrscheinlich"
        elif job or (full and lived):
            tier = "möglich"
        else:
            continue  # Sterbeort und Name allein: in den Städten zu viele Namensvettern
        found.append((tier, c, ev))
    if not found:
        return None
    for tier in ("wahrscheinlich", "möglich"):
        top = [f for f in found if f[0] == tier]
        if len(top) == 1:
            return top[0][1], tier, top[0][2]
        if len(top) > 1:
            return None  # mehrdeutig
    return None


def link() -> None:
    members = defaultdict(list)
    for m in open_csv(LINKS / "entities.csv.gz"):
        members[m["record_id"]].append(m["entity_id"])
    rows, stats = [], Counter()
    # 1. Normdaten der Städte übernehmen
    city: dict[str, list[dict]] = defaultdict(list)
    for a in open_csv(NORM / "ab_authority.csv"):
        for eid in members.get(a["id"], ()):
            city[eid].append(a)
    rank = {"wahrscheinlich": 2, "möglich": 1}
    for eid, links in city.items():
        qids = Counter(a["qid"] for a in links)
        best = max(links, key=lambda a: (rank.get(a["tier"], 0), qids[a["qid"]], int(a["score"] or 0)))
        tier = best["tier"]
        if len(qids) > 1:
            stats["stadt:mehrere_qids"] += 1
            tier = "möglich"  # Einträge derselben Einheit nennen verschiedene Personen
        rows.append({**{k: best[k] for k in ("qid", "label", "birth", "death", "hls_id", "gnd", "hls_check")},
                     "entity_id": eid, "tier": tier, "source": "stadt", "evidence": best["evidence"], "via": best["id"]})
        stats["stadt"] += 1
    # 2. zweiter Abgleich über die Gemeindenummer
    idx = candidates()
    for eid, p in entity_profiles().items():
        if eid in city:
            continue
        hit = match(p, idx)
        if hit is None:
            continue
        c, tier, ev = hit
        rows.append({"entity_id": eid, "qid": c["qid"], "label": c["label"], "birth": c["birth"], "death": c["death"],
                     "hls_id": c["hls_id"], "gnd": c["gnd"], "tier": tier, "source": "telefonbuch",
                     "evidence": "+".join(ev), "hls_check": "", "via": ""})
        stats[f"telefonbuch:{tier}"] += 1
    rows.sort(key=lambda r: (r["source"], r["entity_id"]))
    write_csv(LINKS / "authority.csv", AUTH_FIELDS, rows)
    (NORM / "authority_stats.json").write_text(json.dumps(dict(stats), ensure_ascii=False, indent=1) + "\n",
                                               encoding="utf-8")
    print(dict(stats))


if __name__ == "__main__":
    {"fetch": fetch, "link": link}[sys.argv[1] if len(sys.argv) > 1 else "link"]()

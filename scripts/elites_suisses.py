"""Elites suisses (UNIL, LESSH/LOD4HSS): Personen mit Wikidata-Kennung aus dem SPARQL-Endpunkt.

    python scripts/elites_suisses.py     # → data/norm/elites_suisses.csv.gz (mit Wikidata-Kennung)
                                         #   und elites_suisses_personen.csv.gz, _mitglied.csv.gz (bis Jahrgang 1896)

Beschreibung, Endpunkt und Beispielabfragen: docs/elites_suisses.md.

Abgefragt werden alle Personen (`crm:E21`) mit `owl:sameAs` auf Wikidata, dazu Name
(`sdh-short:P9`), Geburts- und Todesjahr (`sdh-short:P2`, `P13`). Verknüpft wird nur über die
Wikidata-Kennung (links/authority.csv); Namen und Jahre dienen der Anzeige und der Prüfung.
Der Endpunkt nimmt nur GET-Abfragen an.
"""

from __future__ import annotations

import json
import sys
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import NORM, write_csv  # noqa: E402

ENDPOINT = "https://swiss-elites.lod4hss.cloud/wisski/endpoint/default_wisski_distillery_adapter"
PROFILE = "https://elitessuisses.unil.ch/p/{id}"   # Personenseite; die Ressourcen-URI selbst löst nicht auf
QUERY = """
PREFIX crm: <http://www.cidoc-crm.org/cidoc-crm/>
PREFIX owl: <http://www.w3.org/2002/07/owl#>
PREFIX sdh-short: <https://sdhss.org/ontology/shortcuts/>
SELECT ?s ?q ?name ?b ?d WHERE {
  ?s a crm:E21 ; owl:sameAs ?q ; sdh-short:P9 ?name .
  FILTER(STRSTARTS(STR(?q), "http://www.wikidata.org/entity/"))
  OPTIONAL { ?s sdh-short:P2 ?b }
  OPTIONAL { ?s sdh-short:P13 ?d }
}
LIMIT 50000
"""
OUT = NORM / "elites_suisses.csv.gz"
FIELDS = ["es_id", "qid", "name", "birth", "death"]
# Für den Abgleich über Name und Lebensjahre (scripts/elites_match.py): alle Personen, die 1914
# erwachsen waren (Jahrgang bis 1896), mit Geschlecht und Mitgliedschaften (Gremium, Jahre)
MAX_BIRTH = 1896
OUT_P = NORM / "elites_suisses_personen.csv.gz"
OUT_M = NORM / "elites_suisses_mitglied.csv.gz"
Q_PERSONS = f"""
PREFIX crm: <http://www.cidoc-crm.org/cidoc-crm/>
PREFIX owl: <http://www.w3.org/2002/07/owl#>
PREFIX sdh-short: <https://sdhss.org/ontology/shortcuts/>
PREFIX sdh-slc: <https://sdhss.org/ontology/social-life-core/>
SELECT ?s ?name ?b ?d ?g ?q WHERE {{
  ?s a crm:E21 ; sdh-short:P9 ?name ; sdh-short:P2 ?b . FILTER(?b <= {MAX_BIRTH})
  OPTIONAL {{ ?s sdh-short:P13 ?d }} OPTIONAL {{ ?s sdh-slc:P23/sdh-short:P9 ?g }}
  OPTIONAL {{ ?s owl:sameAs ?q FILTER(STRSTARTS(STR(?q), "http://www.wikidata.org/entity/")) }}
}} LIMIT 100000
"""
Q_MEMBERS = f"""
PREFIX crm: <http://www.cidoc-crm.org/cidoc-crm/>
PREFIX sdh-short: <https://sdhss.org/ontology/shortcuts/>
PREFIX sdh-slc: <https://sdhss.org/ontology/social-life-core/>
SELECT ?s ?group ?role ?start ?end WHERE {{
  ?s a crm:E21 ; sdh-short:P2 ?b . FILTER(?b <= {MAX_BIRTH})
  ?m a sdh-slc:C5 ; sdh-slc:P1 ?s .
  OPTIONAL {{ ?m sdh-slc:P2/sdh-short:P9 ?group }} OPTIONAL {{ ?m sdh-slc:P63/sdh-short:P9 ?role }}
  OPTIONAL {{ ?m sdh-short:P4 ?start }} OPTIONAL {{ ?m sdh-short:P7 ?end }}
}} LIMIT 200000
"""


def sparql(query: str) -> list[dict]:
    url = ENDPOINT + "?" + urllib.parse.urlencode({"query": query})
    req = urllib.request.Request(url, headers={"Accept": "application/sparql-results+json",
                                               "User-Agent": "vernetzte-schweiz (research; github.com/thodel/vernetzte-schweiz)"})
    with urllib.request.urlopen(req, timeout=300) as r:
        return json.load(r)["results"]["bindings"]


def main() -> None:
    rows = {}
    for b in sparql(QUERY):
        es_id = b["s"]["value"].rsplit("/p", 1)[-1]
        qid = b["q"]["value"].rsplit("/", 1)[-1]
        rows.setdefault((es_id, qid), {"es_id": es_id, "qid": qid, "name": b["name"]["value"],
                                       "birth": b.get("b", {}).get("value", ""), "death": b.get("d", {}).get("value", "")})
    out = sorted(rows.values(), key=lambda r: int(r["es_id"]) if r["es_id"].isdigit() else 0)
    write_csv(OUT, FIELDS, out)
    stamp = datetime.now(timezone.utc).astimezone().strftime("%Y-%m-%d")
    (NORM / "elites_suisses.json").write_text(json.dumps(
        {"endpoint": ENDPOINT, "abgefragt": stamp, "personen_mit_qid": len(out),
         "qids": len({r["qid"] for r in out})}, ensure_ascii=False, indent=1) + "\n")
    print(f"{OUT.relative_to(NORM.parent.parent)}: {len(out)} Personen mit Wikidata-Kennung")

    v = lambda b, k: b.get(k, {}).get("value", "")  # noqa: E731
    pid = lambda b: v(b, "s").rsplit("/p", 1)[-1]  # noqa: E731
    persons = {}
    for b in sparql(Q_PERSONS):
        persons.setdefault(pid(b), {"es_id": pid(b), "name": v(b, "name"), "birth": v(b, "b"), "death": v(b, "d"),
                                    "gender": v(b, "g"), "qid": v(b, "q").rsplit("/", 1)[-1]})
    write_csv(OUT_P, ["es_id", "name", "birth", "death", "gender", "qid"], sorted(persons.values(), key=lambda r: int(r["es_id"])))
    members = sorted({(pid(b), v(b, "group"), v(b, "role"), v(b, "start"), v(b, "end")) for b in sparql(Q_MEMBERS)},
                     key=lambda x: (int(x[0]), x[3], x[1]))
    write_csv(OUT_M, ["es_id", "group", "role", "start", "end"],
              [dict(zip(["es_id", "group", "role", "start", "end"], m)) for m in members])
    meta = json.loads((NORM / "elites_suisses.json").read_text())
    meta.update({"personen_bis_jahrgang": MAX_BIRTH, "personen": len(persons), "mitgliedschaften": len(members)})
    (NORM / "elites_suisses.json").write_text(json.dumps(meta, ensure_ascii=False, indent=1) + "\n")
    print(f"{OUT_P.name}: {len(persons)} Personen bis Jahrgang {MAX_BIRTH}; {OUT_M.name}: {len(members)} Mitgliedschaften")


if __name__ == "__main__":
    main()

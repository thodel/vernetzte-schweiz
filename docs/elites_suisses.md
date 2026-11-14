# Elites suisses (SPARQL)

Die Datenbank der Schweizer Eliten der Universität Lausanne steht als Wissensgraph im Projekt LESSH von LOD4HSS bereit:
[lod4hss-projects/elites-suisses](https://github.com/lod4hss-projects/elites-suisses), mit einer
[Versuchsseite](https://lod4hss-projects.github.io/elites-suisses/). Vernetzte Schweiz nutzt
den Graphen, um Personen mit Normdaten auf ihre Seite in der Elitendatenbank zu verlinken.

## Endpunkt

| | |
|---|---|
| SPARQL-Endpunkt | `https://swiss-elites.lod4hss.cloud/wisski/endpoint/default_wisski_distillery_adapter` |
| Methode | nur GET (`?query=…`), Antwort mit `Accept: application/sparql-results+json` |
| Graph mit den Daten | `https://swiss-elites.lod4hss.cloud/resource/`; die übrigen Graphen braucht WissKI |
| Personen-URI | `https://elites-suisses.lod4hss.org/resource/p<Nummer>`; löst nicht auf (404) |
| Personenseite | `https://elitessuisses.unil.ch/p/<Nummer>` |
| Ontologie | CIDOC CRM mit den SDHSS-Erweiterungen (`sdh-short:` für Abkürzungen) |

Die Dokumentation im Repo nennt noch `…/wisski/endpoint/default`. Am 14.11.2026 antwortete
dieser Pfad mit «No such adapter: 'default'». Die Versuchsseite selbst fragt
`default_wisski_distillery_adapter` ab (`docs/sparql-queries/address.js`).

**Was der Graph über Personen enthält** (Stand 14.11.2026):

| Eigenschaft | Bedeutung | Personen |
|---|---|---|
| `rdf:type crm:E21` | Person | 58 729 |
| `sdh-short:P9` | Name («Conrad, Peter») | 58 729 |
| `sdh-slc:P23` | Geschlecht | 58 534 |
| `sdh-short:P2` | Geburtsjahr | 45 333 |
| `sdh-short:P13` | Todesjahr | 22 577 |
| `owl:sameAs` | Wikidata (10 629) und WissKI-Ansicht (92) | 10 721 |

Ämter, Mitgliedschaften und Ausbildung hängen an eigenen Knoten; Beispiele dazu stehen im
Repo unter `llm_documentation/SPARQL_queries_examples/`.

## Beispielabfragen

Personen mit Wikidata-Kennung, Namen und Lebensjahren. Diese Abfrage nutzt
[scripts/elites_suisses.py](../scripts/elites_suisses.py):

```sparql
PREFIX crm: <http://www.cidoc-crm.org/cidoc-crm/>
PREFIX owl: <http://www.w3.org/2002/07/owl#>
PREFIX sdh-short: <https://sdhss.org/ontology/shortcuts/>
SELECT ?s ?q ?name ?b ?d WHERE {
  ?s a crm:E21 ; owl:sameAs ?q ; sdh-short:P9 ?name .
  FILTER(STRSTARTS(STR(?q), "http://www.wikidata.org/entity/"))
  OPTIONAL { ?s sdh-short:P2 ?b }
  OPTIONAL { ?s sdh-short:P13 ?d }
}
```

Eine Person zu einer Wikidata-Kennung:

```sparql
PREFIX owl: <http://www.w3.org/2002/07/owl#>
PREFIX sdh-short: <https://sdhss.org/ontology/shortcuts/>
SELECT ?s ?name WHERE {
  ?s owl:sameAs <http://www.wikidata.org/entity/Q2074388> ; sdh-short:P9 ?name .
}
```

Mit `curl`:

```bash
curl -G 'https://swiss-elites.lod4hss.cloud/wisski/endpoint/default_wisski_distillery_adapter' -H 'Accept: application/sparql-results+json' --data-urlencode 'query=PREFIX crm: <http://www.cidoc-crm.org/cidoc-crm/> SELECT (COUNT(DISTINCT ?p) AS ?n) WHERE { ?p a crm:E21 }'
```

## Wie Vernetzte Schweiz den Graphen nutzt

1. `python scripts/elites_suisses.py` fragt alle Personen mit Wikidata-Kennung ab und
   schreibt `data/norm/elites_suisses.csv.gz` (Nummer, QID, Name, Geburts- und Todesjahr).
   `data/norm/elites_suisses.json` hält Endpunkt und Abfragedatum fest. Der Abzug liegt im
   Repo; der Pages-Workflow fragt den Endpunkt nicht ab.
2. **Verknüpft wird nur über die Wikidata-Kennung.** Hat eine Einheit Normdaten
   (`links/authority.csv`, [einheiten.md](einheiten.md)) und steht dieselbe QID im Graphen,
   zeigt die Seite der Einheit unter «Normdaten» den Link «Elites suisses <Nummer>». Namen
   und Jahre werden nicht verglichen; eine Zuordnung über den Namen allein gibt es nicht.
3. **Live auf der Seite einer Person** ([angaben.md](angaben.md)): Ein Rahmen fragt Ämter und Mitgliedschaften beim Endpunkt ab, mit der Stufe der Zuordnung.
4. **Wanderungen** ([wanderungen.md](wanderungen.md)): Normdaten der einen Seite eines Paars
   kommen mit, auch der Link zu den Elites suisses.

**Umfang** (14.11.2026): 452 der 1 552 Einheiten mit Normdaten haben eine Personenseite bei
den Elites suisses. Die Qualität dieser Links ist die der Normdaten: Die Stufen
«wahrscheinlich» und «möglich» bleiben stehen.

## Grenzen

- Der Graph ist ein Versuch («Experimental website»); Endpunkt und Pfade können sich ändern.
  Darum steht das Abfragedatum bei den Daten.
- Nur rund ein Sechstel der Personen im Graphen hat eine Wikidata-Kennung. Wer dort keine
  hat, wird nicht gefunden, auch wenn er in den Adress- und Telefonbüchern steht.
- Lizenz der Daten: Das Repo steht unter MIT, eine eigene Datenlizenz ist nicht genannt.
  Vernetzte Schweiz übernimmt nur Nummer, QID, Name und Lebensjahre und verlinkt auf die
  Personenseite.

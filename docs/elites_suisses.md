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

## Abgleich über Name und Lebensjahre

Die meisten Personen im Graphen haben keine Wikidata-Kennung. Sie sucht
[scripts/elites_match.py](../scripts/elites_match.py) über Name und Lebensjahre in den
Einheiten. Grundlage ist ein zweiter Abzug: alle 17 804 Personen bis Jahrgang 1896
(1914 erwachsen) mit Geschlecht und ihren Mitgliedschaften (Gremium, Rolle, Jahre),
`data/norm/elites_suisses_personen.csv.gz` und `_mitglied.csv.gz`.

**Bedingungen:**
- Der Familienname ist gleich. Bei «Heusler-Sarasin» zählt «Heusler».
- Der Vorname ist verträglich, mindestens als Abkürzung. Haben beide Seiten zwei Vornamen,
  stimmen die Anfangsbuchstaben Stelle für Stelle überein.
- Das Geschlecht widerspricht sich nicht. «Mme», «Vve» und «Wwe» gelten als Frau.
- Die Einheit steht in Jahren im Buch, in denen die Person mindestens 16 und noch am Leben
  war, und zum ersten Mal, bevor sie 75 war.

**Belege:**
- ein Gremium am Ort der Einheit («Lausanne», «Zürcher Handelskammer»), sonst eines im
  Kanton («Grosser Rat BS», «Kantonsrat ZH»);
- die Mitgliedschaft fällt in dieselben Jahre;
- ein seltener Familienname;
- ein ausgeschriebener statt abgekürzter Vorname.

Gilt die Person an mehreren Orten gleich gut, fällt sie weg (mehrdeutig). Personen, die schon
über Wikidata verknüpft sind, sind übersprungen.

**Stufen:** `wahrscheinlich` braucht ≥ 6 Punkte mit Ort oder Kanton, `möglich` ≥ 4 mit Ort,
Kanton oder seltenem Namen, `schwach` ≥ 3.

**Ergebnis** (15.11.2026):
- 463 Einheiten `wahrscheinlich`, 750 `möglich`, 417 `schwach`;
- 3 030 Personen hatten mehrere gleich gute Einheiten und fallen weg.

**Messung** (beurteilt von Claude, nicht von den Projektmitarbeitenden;
[scripts/measure_elites.py](../scripts/measure_elites.py)):
- Zu jedem Paar standen die Gremien der Person und das Berufsfeld der Einheit.
- «richtig» heisst: Beruf oder Amt bestätigen die Person. Beispiele: Camille Decoppet,
  procureur général und Conseiller d'État in Lausanne; der Seidenfabrikant Alfred
  Schwarzenbach; der Kantonschemiker Hans Kreis.
- «falsch» heisst: etwas widerspricht. Beispiele: der Geiger Wilhelm Brückner in Lausanne
  gegen den Germanisten Wilhelm Bruckner; ein Priester Enrico Pellegrini gegen den Maler
  Alfred Heinrich Pellegrini.

| Stufe | Messung 1 (`data/review/elites_kandidaten.csv`) | Messung 2, nach den Korrekturen (`elites_kandidaten_2.csv`) |
|---|---|---|
| `wahrscheinlich` | 7 richtig, 1 falsch, 12 unklar: 35–95 % | 5 richtig, 0 falsch, 15 unklar: 25–100 % |
| `möglich` | 6 / 2 / 12: 30–90 % | 3 / 2 / 15: 15–90 % |
| `schwach` | 3 / 7 / 10: 15–65 % | 4 / 3 / 13: 20–85 % |

**Korrekturen nach Messung 1:**
- Ausgeschlossen werden seither ein anderer zweiter Vorname («Konr. Otto» ≠ «(Friedrich)
  Otto»), eine Witwe unter dem Namen eines Mannes und ein erster Eintrag nach dem 75.
  Altersjahr.
- An Messung 1 nachgerechnet fallen dadurch 5 falsche Paare weg, kein richtiges.

**Lesart:**
- `wahrscheinlich` hat in 39 beurteilten Paaren (nach den Korrekturen) keines, das falsch
  ist.
- Die meisten bleiben aber unklar: Die Bücher nennen oft keinen Beruf, und Gremien wie «Grosser
  Rat BS» passen zu vielen Berufen. Die Untergrenze der Präzision ist darum niedrig.
- `schwach` ist zu einem Viertel bis zur Hälfte falsch.

**Auf der Seite:** Die Seite einer Einheit zeigt Kandidaten der Stufen `wahrscheinlich` und
`möglich` in einem eigenen Rahmen Elites suisses (live abgefragt, [angaben.md](angaben.md)).
Dazu stehen der Hinweis «über Name und Lebensjahre gefunden, nicht über Normdaten», die
Stufe, die Belege und das Messergebnis. Hat die Person im Graphen eine Wikidata-Kennung,
kommt der Rahmen Wikidata dazu. `schwach` wird nicht gezeigt.

## Grenzen

- Der Graph ist ein Versuch («Experimental website»); Endpunkt und Pfade können sich ändern.
  Darum steht das Abfragedatum bei den Daten.
- Nur rund ein Sechstel der Personen im Graphen hat eine Wikidata-Kennung. Die übrigen findet
  nur der Abgleich über Name und Lebensjahre, und nur, wenn sie bis 1896 geboren sind.
- Lizenz der Daten: Das Repo steht unter MIT, eine eigene Datenlizenz ist nicht genannt.
  Vernetzte Schweiz übernimmt Nummer, QID, Name, Lebensjahre und Geschlecht, für den Abgleich
  auch Gremien und Jahre der Mitgliedschaften, und verlinkt auf die Personenseite.

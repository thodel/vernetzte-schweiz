# Angaben aus anderen Projekten

Die Seite einer Person (`#/e/<entity_id>`) zeigt unter «Angaben aus anderen Projekten», was
Wikidata, das Historische Lexikon der Schweiz (HLS) und die Elites suisses (OBELIS,
Universität Lausanne) über sie wissen. Je Projekt gibt es einen Rahmen. Jeder Rahmen nennt,
**wie sicher die Zuordnung ist** und woher sie stammt.

## Woher die Zuordnung kommt

Je Einheit gelten diese Quellen, die sicherste zuerst. Jede ergibt eine Reihe von Rahmen.

| Quelle | Zuordnung | Stufe im Rahmen |
|---|---|---|
| Normdaten der Einheit (`links/authority.csv`, [einheiten.md](einheiten.md)) | Wikidata-Kennung, oft mit HLS und GND | die Stufe der Normdaten: «wahrscheinlich» oder «möglich», mit den Belegen |
| Möglicher HLS-Eintrag (M9, [hls_abdeckung.md](hls_abdeckung.md)) | HLS-Nummer | «wahrscheinlich», mit dem Grund («gleich+text+beruf») |
| Wanderung (M10, [wanderungen.md](wanderungen.md)) | Normdaten der anderen Einheit des Paars | höchstens «möglich», mit Stufe der Wanderung und der Normdaten |

## Die Rahmen

| Rahmen | Wie abgefragt | Inhalt |
|---|---|---|
| **Wikidata** | live, `query.wikidata.org/sparql` (SPARQL, beim Öffnen der Seite) | Bezeichnung und Beschreibung in der Sprache der Seite, Geburt und Tod (Datum, Ort), Berufe (P106), Ämter mit Jahren (P39), Ausbildung (P69), Mitgliedschaft und Partei (P463, P102), HLS- und GND-Nummer |
| **HLS** | aus unseren Daten (`site/data/hls/`, M9); das HLS hat keine offene Schnittstelle | Name, Lebensjahre, Orte mit Jahren; Link zum Artikel und zur Prüfung gegen die Bücher. Kein Artikeltext |
| **Elites suisses (OBELIS)** | live, SPARQL-Endpunkt von LESSH/LOD4HSS ([elites_suisses.md](elites_suisses.md)) | Name, Lebensjahre, Ämter und Mitgliedschaften mit Jahren (Gremium, Rolle, Art); Link zur Personenseite |

**Verkettung:**
- Hat eine Einheit nur eine HLS-Nummer, sucht der Wikidata-Rahmen die Person über die
  HLS-Nummer (P902).
- Die Wikidata-Kennung, die er dabei findet, verknüpft die Elites suisses.
- Fehlt die HLS-Nummer in den Normdaten, nimmt der HLS-Rahmen die aus Wikidata.
- Bei jeder dieser Verkettungen gilt die Stufe der ursprünglichen Zuordnung.

**Beispiele:**
- [Peter Conrad, Aarau](https://thodel.github.io/vernetzte-schweiz/#/e/e00164e17c7): Die
  Normdaten haben die Stufe «wahrscheinlich». Die Elites suisses nennen Grosser Rat AG
  1880–1885 und Regierungsrat AG 1885–1914.
- [John Syz, Zürich](https://thodel.github.io/vernetzte-schweiz/#/e/ea216156713): Hier gibt
  es nur einen HLS-Kandidaten. Wikidata wird über die HLS-Nummer gefunden, und darüber die
  Elites suisses mit 11 Ämtern und Mitgliedschaften.
- [James Siordet, Chexbres](https://thodel.github.io/vernetzte-schweiz/#/e/eb21e194db8):
  Die Angaben kommen über die Wanderung von der Einheit in Genève; die Stufe ist darum
  «möglich».

## Grenzen

- Live abgefragte Angaben sind die der Projekte, mit ihren Fehlern. Sie werden nicht
  gespeichert. Ist ein Dienst nicht erreichbar, sagt der Rahmen das.
- Eine Zuordnung ist nur so sicher wie ihre Quelle. Die Rahmen übernehmen keine Angaben in
  die Einheit; sie stehen daneben.
- Personen ohne Normdaten, ohne HLS-Kandidaten und ohne Wanderung mit Normdaten bekommen
  keine Rahmen.

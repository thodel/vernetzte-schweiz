# HLS → Telefon- und Adressbuch: umgekehrte Prüfung

Stand 11.11.2026, `scripts/hls_coverage.py`, Ergebnis in `data/norm/hls_coverage.csv.gz`
und `data/norm/hls_coverage.json`.

Die Frage: Wie viele Personen des Historischen Lexikons der Schweiz müssten wir in den
Telefon- und Adressbüchern 1880–1914 finden, wenn sie eingetragen waren, und wie viele
finden wir?

Das Skript liest den HLS-Export, aus dem auch hls_mcp gebaut ist (`hls_articles.csv`, nicht
im Repo). Es läuft darum lokal, und sein Ergebnis wird eingecheckt.

## Grundgesamtheit

| Schritt | Personen |
|---|---:|
| HLS-Biografien mit Familienname und Geburtsjahr, 1880–1914 mindestens ein Jahr 25–80 Jahre alt | 7 879 |
| ohne Schweizer Ort aus Text, Wikidata oder Sterbeort | − 872 |
| Ort bekannt, dort aber kein Telefon- oder Adressbuch in ihren Jahren | − 835 |
| **erwartet** | **6 172** |

### Woher die Orte kommen

1. **Ort mit Jahr aus dem Artikeltext** (2 253 Personen). «1892-1894 Gemeinderat in Baar»
   ergibt Baar 1892–1894.
   - Die Jahreszahl muss im selben Satzteil vor dem Ort stehen.
   - «ab 1897» gilt bis zum Tod, eine einzelne Jahreszahl für zehn Jahre.
   - Deutsche Namen werden übersetzt (Genf → Genève, Pruntrut → Porrentruy).
   - Stichprobe: 26 von 30 Fundstellen nennen einen Ort, an dem die Person damals war.
     Die übrigen nennen ein Ereignis (Promotion, Kongress) statt eines Wohnorts.
2. **Wikidata:** Wohn- und Wirkungsort, nur wenn der Text keinen Ort liefert (263).
   - «Wirkungsort Bern» zählt nicht. Wikidata setzt ihn für alle Mitglieder der
     Bundesversammlung, und die meisten wohnten anderswo.
3. **Nur Sterbeort** (3 656): aus Wikidata oder aus dem Kopf des Artikels. Wer 1940 in
   Zürich starb, kann 1900 in Winterthur gelebt haben; diese Gruppe ist darum die
   unsicherste.

## Stufen und Messung

Eine Einheit ist Kandidat, wenn sie an einem dieser Orte steht, den gleichen Familiennamen
hat (auch ohne Partikel: «de Pury» = Pury) und in einem Jahr eingetragen ist, in dem die
Person erwachsen war. Der Vorname darf nicht widersprechen. «Beruf» heisst, dass Einheit und
Artikel dieselbe Berufsgruppe nennen (Arzt, Jurist, Redaktor …; Gruppen aus M3 und Klassen
aus M6).

| Stufe | Regel | Personen | richtig in der Stichprobe |
|---|---|---:|---|
| normdaten | Einheit trägt die HLS-Nummer (M3) | 683 | 97–100 % bzw. 70–95 % (M3) |
| wahrscheinlich | Vorname ausgeschrieben oder abgekürzt **und** Beruf; oder Initiale, Beruf **und** Ort mit Jahr aus dem Text | 261 | 22–23 von 25, dazu 21 von 22 aus der ersten Runde |
| möglich | Vorname ausgeschrieben oder abgekürzt, ohne Beruf | 453 | 23 von 36 (64 %) |
| schwach | nur Initiale, oder Einheit ohne Vornamen | 1 169 | 7 von 20 |
| nicht gefunden | | 3 606 | |

Was die Messung gezeigt hat:
- **Der Beruf trägt die Zuordnung, der Ort aus dem Text allein nicht.** Ausgeschriebener
  Vorname plus Ort mit Jahr war nur zu etwa 50 % richtig. Der Ort nennt oft das Studium,
  und am selben Ort leben Namensvettern.
- **Vater und Sohn gleichen Namens:** Ist eine Einheit für zwei HLS-Personen
  «wahrscheinlich», bleibt sie für beide nur «möglich». Beispiel: Joseph Albert und Albert
  Hautle, Advokat in Appenzell.
- **Typische Fehler** in «möglich» und «schwach»:
  - der Vater im Geschäft (Irlet, Negotiant in Twann);
  - Namensvettern in den Städten (Karl Schneider, Redaktor in Bern 1900, als die
    HLS-Person 14 war);
  - Witwen («Frau Wwe.») und Firmen («Gebr.»).

## Quote

Gewichtet mit den gemessenen Anteilen: 683 × 0,9 + 261 × 0,9 + 453 × 0,64 + 1 169 × 0,35
≈ **1 550 von 6 172, rund 25 %** (grob 20–30 %; «schwach» ist mit 20 Fällen am
schlechtesten gemessen).

- **Mit Ort und Jahr aus dem Text** (die belastbarste Grundgesamtheit): etwa 700 von 2 253,
  rund **31 %**.
- **Frauen:** etwa 47 von 333, rund 14 %. Die Telefonbücher nennen meist den Mann oder die
  Firma.

Gelesen: Die Bücher erfassen Gewerbe, freie Berufe und Behörden mit Telefon. Eine
HLS-Person, die fehlt, hatte oft kein Telefon, lebte nicht am Sterbeort oder steht unter
einem Lesefehler. Die Quote ist darum keine Fehlerquote der Verknüpfung, sondern eine
Untergrenze dessen, was die Bücher über die HLS-Personen sagen.

Die beurteilten Fälle liegen mit Begründung in `data/review/m9_hls.csv`.

## In der Ansicht (M9, `#/hls`)

- **Übersicht:** Stufen insgesamt und nach Kanton, Geburtsjahrzehnt, Geschlecht,
  Grundlage der Orte und Fachgebiet des HLS-Artikels; Liste mit Suche nach Name oder
  HLS-Nummer.
- **Personenseite `#/hls/<Nummer>`:** Orte × erwachsene Jahre (Buch vorhanden, Eintrag
  gefunden), Kandidaten mit Stufe und Begründung, bei «nicht gefunden» der Grund und
  gleichnamige Einheiten anderswo.
- **«wahrscheinlich»:** als Kandidat mit Begründung, auf der Seite der Einheit als
  «wahrscheinlicher HLS-Eintrag».
- **«möglich» und «schwach»:** nur auf der HLS-Seite, als Liste zum Prüfen.
- **Daten:** `scripts/build_hls.py` → `site/data/hls.json.gz` (Index) und
  `site/data/hls/<xx>.json.gz` (64 Teile).
- **Keine Stufe wird zu Normdaten:** Normdaten bleiben, was M3 verknüpft hat.

# Volltext und Telefonbücher (M8)

`scripts/build_entries.py` macht alle 638 701 Telefonbuch-Einträge bis 1914 durchsuchbar
und zum Blättern zugänglich, nicht nur die gebündelten Personen und Firmen (M3). Vorbild
für die Funktionen (nicht die Gestaltung) ist [historic.localsearch](https://historic.localsearch.ch/search).

## Telefonbücher zum Blättern (`#/buch?kt=…&y=…`)

Jede Zelle der Übersicht «Telefonbücher bis 1914» (Kanton × Jahr) ist ein Link auf alle
Einträge dieses Kantons und Jahrgangs, in Lesereihenfolge, 200 je Seite. Filter: Text (Name,
Beruf, Strasse, Nummer), Gemeinde, Telefonbuch (Signatur). «–» = Einträge ohne aufgelösten
Ort, wie in der Übersicht.

## Volltextsuche (`#/suche?v=ft`)

Wie historic.localsearch:
- **ein Suchfeld** über alle Felder; jedes Wort muss vorkommen;
- **genau oder ungefähr**: «ungefähr» nimmt alle Wörter des Wortschatzes, deren
  Namensschlüssel innerhalb der Schwelle aus M7 liegt (Schreibvarianten und Lesefehler:
  «Mttler» findet «Müller»; die gefundenen Formen werden genannt);
- **Jahre** (Regler);
- **Felder**: Name, Vorname/Namenzusatz, Beruf/Zusatz, Strasse, Ort, Telefonnummer. Die
  Felder stammen aus der Zerlegung (M1) und sind nicht immer richtig getrennt;
- **Treffer nach Jahr**, die ältesten zuerst, drei Jahre auf einmal, «Weitere Jahre»; je Jahr
  bis 100 Einträge; gefundene Wörter hervorgehoben;
- **je Treffer**: Gemeinde, Telefonbuch (Signatur), Seite, Seitenbild, Link zur Person/Firma.

## Seitenbilder

Der IIIF-Server des PTT-Archivs liefert jede Seite als
`https://iiif.ptt-archiv.ch/iiif/3/<Signatur>_<Bild-Nr., 4-stellig>.jp2/full/max/0/default.jpg`
(dieselben Adressen verlinkt historic.localsearch).
- **Charge A (bis 1910):** Die Bild-Nummer steht in den Daten (`telefonbuch_136` → `0136`).
  Geprüft an zwei Seiten: «Böhme-Asal, Jacques» (Basel 1907, Bild 136, gedruckte Seite 56)
  und «Schnider-Bloch, Wwe. K.» (Basel 1907, Bild 24, gedruckte Seite 123) stehen auf dem
  verlinkten Bild. Bild-Reihenfolge und gedruckte Seiten laufen nicht parallel.
- **Charge B (1911–1914):** Die Seitenangabe der Daten ist keine Bild-Nummer
  («Rigatiti, Charles», Genève 1913: Seite 120 in den Daten, Bild 134 bei historic.localsearch).
  Ohne den Versatz je Band verlinkt die Seite hier kein Bild.

## Dateien

| Datei | Inhalt |
|---|---|
| `books.json` | Signaturen; je Zelle Kanton, Jahr, Zahl der Einträge, Telefonbücher, Gemeinden |
| `r/<Kanton>-<Jahr>.json.gz` | Einträge der Zelle: Signatur, Seite, Bild-Nr., Name, Namenzusatz, Zusatz, Strasse, Nummer, Gemeinde, Einheit |
| `ft/<xx>.json.gz` | «Feld:Wort» → Fundstellen (Zelle × 100 000 + Zeile), 64 Teile nach FNV des Wortes |
| `vocab.json.gz` | alle Wörter mit ihren Feldern (für «ungefähr») |

## Zahl der Dateien

Der Pages-Deploy bricht nach 10 Minuten ab, auch wenn ein längeres `timeout` gesetzt ist;
mit rund 3 500 Dateien wurde er nicht fertig (10.11.2026), mit 2 300 schon. Die Teile von
Volltext, Namen- und Gemeindekarten und Gemeinden sind deshalb auf 64 Hash-Teile, die
Berufswörter auf den ersten Buchstaben zusammengelegt: rund 1 800 Dateien, 79 MB.

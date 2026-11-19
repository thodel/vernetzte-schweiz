# Neulesung von Band 2c (Tessin) 1911 und 1912

Der gesamtschweizerische Band 2c deckt das Tessin und das Misox ab. In der Quelle
(DHBern/PTT_phonebook_data_tsv, Charge B) ist er schlecht zerlegt:

- Für 1911 kommen nur 22 verschiedene Seitennummern vor, der Band hat 71 Verzeichnisseiten.
- Alle Einträge stehen unter dem Netzort («Acquarossa»); die Ortschaften innerhalb eines Netzes
  (Castro, Corzoneso) sind in die Einträge hineingelesen.
- Taxspalten, Führungspunkte und mehrere Einträge stehen im selben Namensfeld. Nur 36 % der Einträge
  wurden als Person erkannt (übrige Bände: 51–71 %).

Darum sind beide Bände aus den Seitenbildern des PTT-Archivs neu gelesen. Die Tabellen liegen unter
`data/override/ptt/P-260-1_2c_<Jahr>.tsv`; `scripts/ingest_ptt.py` nimmt sie anstelle der Zeilen der
Quelle. Die Quelle selbst bleibt unverändert.

## Vorgehen

1. Seitenbilder: `https://iiif.ptt-archiv.ch/iiif/3/P-260-1_2c_<Jahr>_<NNNN>.jp2/full/max/0/default.jpg`
   (1911: 127 Bilder, Verzeichnis auf den Bildern 53–124; 1912: 139 Bilder, Verzeichnis 53–134).
2. `scripts/neulesung/read_2c.py`: jede Seite geht ganz an qwen3.8-27b (GPUStack der Universität Bern),
   mit dem Auftrag im Skript. Ausgabe je Eintrag: Ortschaft (die fett gesetzte Ortsangabe vor dem
   Gedankenstrich), Zwischentitel, Rufnummer, Name (fett), Zusatz, Strasse.
3. `scripts/neulesung/convert_2c.py`: die Ortschaft über den Seitenwechsel weitertragen, Verweise ohne
   Nummer («Hôtel vedi Alberghi») weglassen und Wiederholungszeichen » aus dem Eintrag darüber auflösen:
   - Wort für Wort an derselben Stelle, auch in der Mitte und am Ende («» credito »» unter «Banca
     cantonale Ticinese» → «Banca credito Ticinese»);
   - ein einzelnes » unter einem Gattungswort (Albergo, Caffè, Pension, Società, Banca, Ufficio …) steht
     nur für dieses Wort, der Rest der Zeile ist der Name («»  Flora» → «Albergo Flora»);
   - « Corriere del Ticino » ist ein Titel, kein Wiederholungszeichen.

Gelesen ist jede Seite dreimal: mit Massstab 1,6 (Lauf A), 1,25 (Lauf B) und 2,0 (Lauf C). Lauf A gibt
Reihenfolge und Bestand vor. Je Feld (Name, Zusatz, Strasse, Ort) gilt, was zwei von drei Läufen gleich
lesen, sonst A; zugeordnet wird über die Rufnummer auf derselben Seite. Die Spalte `Check` nennt:

- `uneins` (35 Einträge): alle drei Läufe lesen den Namen verschieden; es gilt A.
- `ergänzt` (39 Einträge): der Eintrag fehlt in A und steht in B und C. 38 davon stehen auf einer Seite
  (1911, Bild 114, Mendrisio), die Lauf A nach dem ersten Drittel abbrach.

Die Mehrheit überstimmte Lauf A bei 109 Namen, 156 Zusätzen, 9 Strassen und 23 Orten.

## Ergebnis

| | Quelle | Neulesung |
|---|---|---|
| Einträge 1911 | 1 554 | 1 903 |
| Einträge 1912 | 1 720 | 2 102 |
| Ortsangaben 1911 | Netzort | 257 Ortschaften |
| als Person erkannt | 36 % | 48 % (1911), 50 % (1912) |
| Namen in Lauf A und B gleich | – | 93 % (1911), 94 % (1912) |

In Lugano stehen damit 638 (1911) und 681 (1912) Einträge, zwischen 529 (1909) und 685 (1913); mit den
Zeilen der Quelle brach die Reihe «Personen je 100 Haushalte» in diesen beiden Jahren ein.

## Prüfung am Seitenbild

Zwei zufällig gezogene Seiten (Zufallszahl 20261118: 1911 Bild 96, Lugano; 1912 Bild 58, Bellinzona),
zusammen 78 Einträge, von Hand mit dem Bild verglichen (geprüft von Claude, nicht von Projektmitarbeitenden):

- Rufnummer: 78 von 78 richtig.
- Ortschaft: 78 von 78 richtig.
- Name buchstabengenau: 73 von 78 nach Lauf A. Die Fehler sind einzelne Buchstaben («Carmin» statt
  «Carmine», «Bossbard» statt «Bossard»). Nach der dritten Lesung sind auf diesen beiden Seiten zwei der
  fünf behoben (beide «Carmine»), «Bossbard» bleibt und trägt den Merker `uneins`. Eine neue Stichprobe
  nach der Abstimmung gibt es nicht.
- Strasse: 5 von 78 mit einem falschen Buchstaben oder einem fehlenden Wort.

Die Stichprobe ist klein; die Spanne für «Name buchstabengenau» reicht bei 73 von 78 etwa von 86 bis 97 %.

## Was das für die Auswertung heisst

- Die Bände nennen Name und Vorname im selben Feld («Tami Fulgenzio»). `parse_ptt.py` erkennt solche Bände
  am Anteil der Namenszeilen mit bekanntem Vornamen und liest dort auch einen unbekannten Vornamen nach
  bekanntem Familiennamen als Vornamen.
- Der Ort steht je Eintrag, wie in den Regionalbüchern. Die Prüfungen für übertragene Überschriften
  (Jahresabgleich, Namensabgleich) laufen über diese Bände nicht.
- Eine Ortschaft erhält ihre Gemeinde von 1914, wenn ihre heutige Gemeinde aus genau einer Gemeinde von
  1914 hervorgeht (Tenero → Tenero-Contra), sonst über `data/ref/place_aliases.csv` (Cassarate, Ambrì,
  Paradiso). Die erste Regel gilt für alle Telefonbücher (17 417 Einträge) und greift erst nach der
  Ortszuordnung: Vorgezogen gab sie verlesenen Überschriften eine Gemeinde, und der Namensabgleich
  stellte die Seiten von Einsiedeln, Payerne und Kriens nicht mehr richtig. 4–5 % der Einträge von Band
  2c bleiben ohne Gemeinde (Weiler, die weder im Ortschaftenverzeichnis noch in der Liste stehen).
- Einen eigenen Band 2c gibt es 1913 und 1914 nicht; das Tessin steht dann in Band 2b. Dieser ist ab dem
  Block Luzern ebenfalls neu gelesen: [neulesung_2b.md](neulesung_2b.md).

# Neulesung von Band 2b 1913 und 1914 (ab dem Block Luzern)

Band 2b deckt Basel, Aargau, Baselland, Solothurn, die Innerschweiz und 1913/14 auch das Tessin und das
Misox ab (einen eigenen Band 2c gibt es nur 1911 und 1912). Er beginnt mit Basel und Luzern als eigenen
Blöcken und ordnet danach alle übrigen Orte in einem Alphabet, mit Überschriften wie «Melide (Bissone) ER».

In der Quelle (DHBern/PTT_phonebook_data_tsv, Charge B) fehlen viele dieser Überschriften:

- Der Block Luzern steht unter «Basel».
- Die Einträge von Altdorf stehen unter «Altbüron», die von Melchthal, Melide und Mellingen unter «Melano».
- Aarau hat 1914 128 Einträge (Regionalbuch 1910: 530), Liestal 10, Olten 117.

Darum ist für beide Jahre alles ab dem Block Luzern aus den Seitenbildern des PTT-Archivs neu gelesen. Der
Block Basel bleibt aus der Quelle. Die Quelle selbst bleibt unverändert.

## Vorgehen

1. Seitenbilder: `https://iiif.ptt-archiv.ch/iiif/3/P-260-1_2b_<Jahr>_<NNNN>.jp2/full/max/0/default.jpg`
   (1913: 267 Bilder, neu gelesen ab Bild 101; 1914: 291 Bilder, neu gelesen ab Bild 111).
2. `scripts/neulesung/read_2b.py`: jede Seite geht ganz an qwen3.8-27b (GPUStack der Universität Bern), mit
   dem Auftrag im Skript. Ausgabe: Kolumnentitel der Seite, dann je Eintrag Ort (Überschrift), Zentrale
   (Klammer der Überschrift), Rufnummer, Name (fett) und Rest.
3. `scripts/neulesung/convert_2b.py`:
   - Der Ort gilt über den Seitenwechsel weiter. Nennt der Kolumnentitel eine einzelne Stadt («M-N Luzern»),
     gilt sie für die Einträge am Seitenkopf; ein als Ort gelesener Kolumnentitel («Gersau-Giubiasco») zählt nicht.
   - Aus der Klammer der Überschrift bleibt die Zentrale. Kürzel der Dienststunden («C-n», «ER»),
     Betriebszeiten («April—Okt.») und Kantonszusätze («Aarg.», zum Ortsnamen gestellt) fallen weg.
   - Wiederholungszeichen » werden aus dem Eintrag darüber aufgelöst, wie in Band 2c. Neu: Zwei Zeichen unter
     «Gasthaus z. Adler» stehen für «Gasthaus z.», der Rest der Zeile ist der Name («» » Kreuz (Widmer)» →
     «Gasthaus z. Kreuz»).
   - Die Einträge des Blocks Basel am Anfang des gelesenen Bereichs fallen weg.

Gelesen ist jede Seite dreimal: mit Massstab 1,3 (Lauf A), 1,0 (Lauf B) und 1,6 (Lauf C). Lauf A gibt
Reihenfolge und Bestand vor. Je Feld (Name, Rest, Ort) gilt, was zwei von drei Läufen gleich lesen, sonst A;
zugeordnet wird über die Rufnummer auf derselben Seite. Die Spalte `Check` nennt:

- `uneins` (62 Einträge 1913, 112 Einträge 1914): alle drei Läufe lesen den Namen verschieden; es gilt A.
- `ergänzt` (4 und 1): der Eintrag fehlt in A und steht in B und C.
- `zwei-lesungen` (1 und 6), `nur-A` (2 und 0): eine oder beide weiteren Lesungen haben den Eintrag nicht.

Die Mehrheit überstimmte Lauf A bei 539 Namen, 914 Resten und 293 Orten (beide Jahre zusammen).

## Teil-Neulesung in `ingest_ptt.py`

Die Tabellen liegen unter `data/override/ptt/P-260-1_2b_<Jahr>.tsv`. Daneben nennt
`P-260-1_2b_<Jahr>.ersetzt.txt` die Zeilen der Quelle, die sie ersetzen (1913: 5867–16604, 1914: 6107–17262,
gezählt je Band in der Reihenfolge der Quelle). Anders als bei Band 2c ersetzt die Tabelle also nicht den
ganzen Band:

- Die übrigen Zeilen der Quelle (Block Basel) behalten ihre Nummern und damit ihre Bezeichner.
- Die neu gelesenen Zeilen zählen ab 100 001 (`PARTIAL_START`); ihre Bezeichner sind neu.
- Jede Zeile trägt ihr Seitenbild; der Ort steht je Eintrag und gilt als verlässlich. Die Prüfungen für
  übertragene Überschriften (Jahresabgleich, Namensabgleich) laufen über diese Zeilen nicht.

## Ergebnis

| | Quelle 1913 | Neulesung 1913 | Quelle 1914 | Neulesung 1914 |
|---|---|---|---|---|
| Einträge im ersetzten Bereich | 10 724 | 10 877 | 11 142 | 11 512 |
| verschiedene Ortsangaben | 652 | 1 051 | 682 | 1 078 |
| Gemeinden von 1914 | 496 | 721 | 500 | 731 |
| Einträge ohne Gemeinde | 363 | 36 | 371 | 35 |
| als Person erkannt | 64 % | 65 % | 64 % | 64 % |

Einträge je Gemeinde, 1914 (Quelle → Neulesung): Luzern 1 366 → 2 167, Aarau 128 → 543, Olten 117 → 346,
Liestal 10 → 200, Zofingen 1 → 158, Altdorf 0 → 115, Baden 381 → 415, Lugano 784 → 795, Bellinzona 194 → 195,
Locarno 216 → 194. Unter «Basel» standen im ersetzten Bereich 1 334 Einträge, jetzt 9.

Je Kanton, 1914: Luzern 2 524 → 3 355, Aargau 2 249 → 2 993, Tessin 2 468 → 2 375, Baselland 734 → 920,
Solothurn 532 → 612, Schwyz 299 → 383, Uri 136 → 289, Nidwalden 64 → 163, Obwalden 162 → 148,
Basel-Stadt 1 342 → 115 (Riehen und Bettingen stehen im Alphabet). Das Laufental zählt 1914 zu Bern.

Folgen ausserhalb der beiden Bände:

- Rund 1 400 Einträge anderer Bände wechseln die Gemeinde. Der Jahresabgleich stützt sich auf die
  Nachbarjahre: Einträge von Luzern, die 1911 und 1912 unter «Basel» standen, und solche von Olten
  («Olsberg») und Zofingen («Ziefen») liegen jetzt richtig.
- `places.series()` unterschied die Bände der Charge B nach dem Jahr statt nach dem Band. Die
  Kantonsvorliebe galt damit für alle Bände eines Jahres gemeinsam: «Brugg» im Band 2b wurde Brügg BE,
  «Romont (F.)» im Band 1 Romont BE, Altdorf Schaffhausen. Jetzt gilt sie je Band und Jahr («2b:1914»).
- `data/ref/place_aliases.csv` nennt 19 weitere Ortschaften (Emmenbrücke-Gerliswil → Emmen, Neu-Allschwil →
  Allschwil, Neuewelt → Münchenstein, Schinznach-Bad → Birrenlauf …). Acquarossa bleibt ohne Gemeinde: Es
  liegt in mehreren Gemeinden von 1914.
- Eine öffentliche Sprechstelle haben bis 1914 1 773 statt 1 816 Gemeinden. Im Band 2b 1914 sind es 339
  statt 272; weggefallen sind solche, die nur durch eine fehlende Überschrift entstanden (die
  «Gemeindestation» von Balzenwil stand unter Ballwil).

## Prüfung am Seitenbild

Sechs zufällig gezogene Seiten (Zufallszahl 20261119: 1913 Bilder 224, 233, 257; 1914 Bilder 146, 191, 247),
je zehn zufällig gezogene Einträge, zusammen 60, von Hand mit dem Bild verglichen (geprüft von Claude,
nicht von Projektmitarbeitenden), nach der Abstimmung der drei Lesungen:

- Rufnummer: 60 von 60 richtig.
- Ort: 60 von 60 richtig, auch über den Seitenwechsel (Reigoldswil) und mit Dienststunden in der
  Überschrift (Faido).
- Name und Rest buchstabengenau: 56 von 60. Drei Lesefehler («Siegfried» statt «Siegrist», «Litzli» statt
  «Litzi», «Haushaltsartikel» statt «Haushaltungsartikel») und ein falsch aufgelöstes Wiederholungszeichen
  («Gasthaus z. Adler, Schlüssel» statt «Gasthaus z. Schlüssel»). Das letzte ist seither in
  `convert_2b.py` behoben (72 Einträge in beiden Jahren); eine neue Stichprobe danach gibt es nicht.

Die Stichprobe ist klein: Bei 56 von 60 reicht die Spanne für «buchstabengenau» etwa von 84 bis 98 %.

## Was offen bleibt

- Unterzeilen eines Betriebs («Bauleitung», «Bureau» unter «Elektrizitätswerk u. Wasserversorgung») stehen
  als eigene Einträge ohne den Namen des Betriebs, wo der Band diesen nicht als Titel über die Zeilen setzt.
- 71 Einträge bleiben ohne Gemeinde (Weiler im Tessin und im Luzerner Hinterland).
- Der Block Basel ist nicht neu gelesen.
- Die Bände 2b 1911 und 1912 sind nicht neu gelesen; dort greifen weiter Jahres- und Namensabgleich.

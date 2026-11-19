# Neulesung von Band 2b 1913 und 1914

Band 2b deckt Basel, Aargau, Baselland, Solothurn, die Innerschweiz und 1913/14 auch das Tessin und das
Misox ab (einen eigenen Band 2c gibt es nur 1911 und 1912). Er beginnt mit Basel und Luzern als eigenen
Blöcken und ordnet danach alle übrigen Orte in einem Alphabet, mit Überschriften wie «Melide (Bissone) ER».

In der Quelle (DHBern/PTT_phonebook_data_tsv, Charge B) fehlen viele dieser Überschriften:

- Der Block Luzern steht unter «Basel».
- Die Einträge von Altdorf stehen unter «Altbüron», die von Melchthal, Melide und Mellingen unter «Melano».
- Aarau hat 1914 128 Einträge (Regionalbuch 1910: 530), Liestal 10, Olten 117.

Darum sind beide Bände ganz aus den Seitenbildern des PTT-Archivs neu gelesen: zuerst alles ab dem Block Luzern,
danach auch der Block Basel. Dort stimmt der Ort in der Quelle, aber viele Einträge sind zerlegt oder
zusammengezogen («Kanderner Thonwarenfabrik | E.Kammüller. Drahtzugstr. 14 13.361 1.77) Kantonalbank»), und
Unterzeilen einer Firma stehen ohne deren Namen. Die Quelle selbst bleibt unverändert; sie dient als vierte
Lesung (unten).

## Vorgehen

1. Seitenbilder: `https://iiif.ptt-archiv.ch/iiif/3/P-260-1_2b_<Jahr>_<NNNN>.jp2/full/max/0/default.jpg`
   (1913: 267 Bilder, gelesen ab Bild 15, Block Luzern ab Bild 101; 1914: 291 Bilder, gelesen ab Bild 17, Block
   Luzern ab Bild 111).
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
     Das gilt nur unter einem Gattungswort: «» » Güterbahnhof» unter «Hediger & Co.» bleibt «Hediger & Co.».
   - Trennstriche am Zeilenende vor dem Grundwort einer Strasse fallen weg («Sevogel-strasse 60» →
     «Sevogelstrasse 60», 1 192 Einträge in beiden Jahren). Andere Trennstriche bleiben («Gas-glühlicht»),
     weil sie sich von echten Bindestrichen («medico-chirurgo») nicht sicher trennen lassen.
   - Mit `--ganz` bleibt der Block Basel in der Tabelle; ohne den Schalter beginnt sie mit dem Block Luzern.

Gelesen ist jede Seite dreimal: mit Massstab 1,3 (Lauf A), 1,0 (Lauf B) und 1,6 (Lauf C). Lauf A gibt
Reihenfolge und Bestand vor. Je Feld (Name, Rest, Ort) gilt, was zwei von drei Läufen gleich lesen, sonst A;
zugeordnet wird über die Rufnummer auf derselben Seite. Die Spalte `Check` nennt:

- `uneins` (61 Einträge 1913, 70 Einträge 1914): alle drei Läufe lesen den Namen verschieden und die Quelle
  stützt keinen; es gilt A.
- `ergänzt` (13 und 13): der Eintrag fehlt in A und steht in B und C.
- `zwei-lesungen` (4 und 10), `nur-A` (2 und 4): eine oder beide weiteren Lesungen haben den Eintrag nicht.
- `nummer-quelle` (0 und 40): die Rufnummer stammt aus der Quelle (nächster Abschnitt).

Die Mehrheit überstimmte Lauf A bei 999 Namen, 1 459 Resten und 293 Orten (beide Jahre zusammen).

## Die Quelle als vierte Stimme

Die Tabelle der Quelle ist eine eigene, unabhängige Texterkennung. `convert_2b.py --quelle <tsv/>` ordnet ihre
Zeilen den neu gelesenen über Seite und Rufnummer zu (die Quelle nennt die gedruckte Seite; der Versatz zum
Bild wird je Bild aus den gemeinsamen Nummern bestimmt, Seiten mit weniger als der Hälfte gemeinsamer Nummern
bleiben aus):

- Liest die Quelle den Namen wie einer der drei Läufe, gilt diese Lesart, auch gegen die beiden anderen: 336
  Namen 1913, 419 Namen 1914. Beispiel: zwei Läufe lesen «Bruder-Nyferer», einer «Bruder-Nyfeler» wie die
  Quelle; im Druck steht «Bruder-Nyfeler».
- Stimmt die Quelle mit dem gewählten Namen überein, fällt ein Vermerk `uneins`, `zwei-lesungen` oder `nur-A`
  weg (24 und 48).
- Liest kein Lauf wie die Quelle, bleibt die Neulesung. Die Lesart der Quelle allein wird nie übernommen, weil
  sie Einträge oft falsch zerlegt.
- Verrutschte Rufnummern: Steht der Name in der Quelle bei einer anderen Nummer und trägt die Nummer der
  Neulesung dort den Namen einer Nachbarzeile, sind die Nummern der Neulesung um eine Zeile verschoben. Trifft
  das auf mindestens zwei Zeilen einer Seite zu, gilt die Nummer der Quelle (1914: 40 Einträge auf den Bildern
  21, 30 und 45; am Bild 21 für elf Einträge geprüft, alle richtig).

Die vierte Stimme greift im ganzen Band, nicht nur im Block Basel. Von den Zeilen ab dem Block Luzern, die
zuerst allein veröffentlicht waren (Commit a6db42d), ändern sich dadurch und durch die Trennstriche 379 (1913)
und 427 (1914).

## Übernahme in `ingest_ptt.py`

Die Tabellen liegen unter `data/override/ptt/P-260-1_2b_<Jahr>.tsv` und ersetzen den ganzen Band, wie bei
Band 2c:

- Die Zeilen zählen in der Reihenfolge der Tabelle ab 1; alle Bezeichner `ptt:P-260-1_2b_1913:<n>` und
  `…_1914:<n>` sind neu. Die Bezeichner des ersten Stands (ab 100 001, Teil-Neulesung ab dem Block Luzern) gibt es
  nicht mehr; die Liste `<Band>.ersetzt.txt` und der Teil-Ersatz in `ingest_ptt.py` sind entfernt.
- Als Seite steht die Nummer des Seitenbilds, nicht die gedruckte Seitenzahl.
- Jede Zeile trägt ihr Seitenbild; der Ort steht je Eintrag und gilt als verlässlich. Die Prüfungen für
  übertragene Überschriften (Jahresabgleich, Namensabgleich) laufen über diese Zeilen nicht.

## Ergebnis ab dem Block Luzern

Stand der ersten Übernahme (ohne vierte Stimme und Trennstriche; die Zahl der Einträge ist seither gleich):

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
je zehn zufällig gezogene Einträge, zusammen 60, von Hand mit dem Bild verglichen (Stand der ersten Übernahme) (geprüft von Claude,
nicht von Projektmitarbeitenden), nach der Abstimmung der drei Lesungen:

- Rufnummer: 60 von 60 richtig.
- Ort: 60 von 60 richtig, auch über den Seitenwechsel (Reigoldswil) und mit Dienststunden in der
  Überschrift (Faido).
- Name und Rest buchstabengenau: 56 von 60. Drei Lesefehler («Siegfried» statt «Siegrist», «Litzli» statt
  «Litzi», «Haushaltsartikel» statt «Haushaltungsartikel») und ein falsch aufgelöstes Wiederholungszeichen
  («Gasthaus z. Adler, Schlüssel» statt «Gasthaus z. Schlüssel»). Das letzte ist seither in
  `convert_2b.py` behoben (72 Einträge in beiden Jahren); eine neue Stichprobe danach gibt es nicht.

Die Stichprobe ist klein: Bei 56 von 60 reicht die Spanne für «buchstabengenau» etwa von 84 bis 98 %.

## Der Block Basel

| | Quelle 1913 | Neulesung 1913 | Quelle 1914 | Neulesung 1914 |
|---|---|---|---|---|
| Zeilen im Block Basel | 5 866 | 5 980 | 6 106 | 6 341 |
| Rufnummern, die nur eine Seite hat | 136 | 250 | 102 | 337 |

Vergleich über die Rufnummer (Nummern, die in beiden Tabellen genau einmal stehen; 9 294 Paare in beiden
Jahren): Vor der vierten Stimme wich der Name (erstes Feld) in 1 551 Paaren ab, danach in 1 283. Zwei
Stichproben aus diesen Abweichungen, am Seitenbild beurteilt (geprüft von Claude):

- vor der vierten Stimme (24 Paare, 22 beurteilbar): Neulesung richtig 15, Quelle richtig 6, gleichwertig 1;
- danach (24 Paare, 23 beurteilbar): Neulesung richtig 15, Quelle richtig 5, gleichwertig 3.

Wo die Quelle recht behält, lesen alle drei Läufe denselben Fehler («Hetzcl» statt «Hetzel»,
«Maschinenaustellung», «VonderMühl» statt «VonderMühll»; den letzten macht das Modell regelmässig).

Unverzerrte Stichprobe nach allen Schritten: 32 zufällig gezogene Einträge des Blocks Basel (Zufallszahl
20261119), 29 davon am Ausschnitt des Seitenbilds auffindbar:

- Rufnummer: 29 von 29 richtig.
- Name (erstes Feld): 26 von 29. Fehler: «Scharli» statt «Schärli», «VonderMühl-Christ» statt
  «VonderMühll-Christ», «Hediger & Güterbahnhof» statt «Hediger & Co.» (falsch aufgelöstes
  Wiederholungszeichen, seither in `convert_2b.py` behoben, 23 Einträge in beiden Jahren).
- Ganzer Eintrag buchstabengenau: 22 von 29. Dazu kommen «Peffingerstr.» statt «Pfeffingerstr.»,
  «Grenzachstr.» statt «Grenzacherstr.», «Photograph» für gedrucktes «Photogr.» und zwei stehen gebliebene
  Trennstriche («Bewilligungs-beamter», «Gas-glühlicht»).

Die Stichprobe ist klein: Bei 26 von 29 reicht die Spanne für den Namen etwa von 73 bis 98 %.

Folgen:

- Basel zählt 1913 5 968 statt 5 873 und 1914 6 329 statt 6 115 Einträge (12,9 statt 12,8 je 100 Einwohner).
- In der Berufsgruppe Bahn steigt Basel 1914 von 56 auf 80 Einträge: Unterzeilen wie «Versandbureau» tragen
  jetzt den Namen des Betriebs («Bahnhof S. B. B.»).
- Die Verknüpfung mit den Basler Adressbüchern ändert sich kaum (4 193 statt 4 192 verknüpfte Einträge). Zum Historischen Grundbuch führen 16 001 statt 15 997 Paare.
- In den übrigen Bänden wechseln vier Einträge die Gemeinde.

## Was offen bleibt

- Unterzeilen eines Betriebs («Bauleitung», «Bureau» unter «Elektrizitätswerk u. Wasserversorgung») stehen
  als eigene Einträge ohne den Namen des Betriebs, wo der Band diesen nicht als Titel über die Zeilen setzt.
  Im Block Basel betrifft das die Filialen des Consumvereins und die Listen der Wirtschaften («Rest. „ …»): Die
  drei Läufe geben das Wiederholungszeichen dort uneinheitlich wieder, ein Teil der Wirtschaften steht ohne
  «Rest.».
- 71 Einträge bleiben ohne Gemeinde (Weiler im Tessin und im Luzerner Hinterland).
- Trennstriche am Zeilenende ausserhalb von Strassennamen bleiben stehen.
- Die Bände 2b 1911 und 1912 sind nicht neu gelesen (die Lesung läuft); dort greifen weiter Jahres- und
  Namensabgleich.

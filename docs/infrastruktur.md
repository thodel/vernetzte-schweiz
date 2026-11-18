# Infrastruktur (Versuch)

Was zeigen Telefon- und Adressbücher vom Ausbau der Infrastruktur zwischen 1880 und 1914?
`scripts/infrastruktur.py` misst drei Dinge und einige weitere Spuren; die Seite zeigt sie unter
`#/infrastruktur`.

```bash
make infrastruktur                      # data/norm/infrastruktur.json
python scripts/infrastruktur.py site    # site/data/infrastruktur.json.gz (läuft im Pages-Workflow)
```

## Die Quellen und ihre Lücken

Die Telefonbücher beginnen **1880** (Zürich, 99 Einträge) und decken die ganze Schweiz erst ab
**1911** (gesamtschweizerische Bände 1, 2a–2c, 3). Dazwischen liegen Regionalbücher vor, je Jahr ein bis
sieben Netze (Basel, Bern, St. Gallen, Zürich, Genève, Lausanne, Chur, Bellinzona …); 1891 fehlt
ganz, 1907 liegt nur ein Netz vor. Ein Ort, der erst 1911 erscheint, kann früher ein Telefon gehabt
haben, wenn sein Regionalbuch fehlt (vor allem Waadt und Wallis). Auch in den gesamtschweizerischen Bänden ist nicht jeder
Band ganz gelesen (Band 2c fehlt 1913 und 1914; Lausanne 1912–1914 und Winterthur 1913 sind dünn),
und vielen Orten fehlt die Überschrift (siehe unten und `scripts/places.py`, Schritt 3).

Daraus folgen zwei Regeln für alles, was über die Jahre verglichen wird:

- **Verläufe zählen «bis zum Jahr mindestens einmal belegt»** (`verlauf` in der Ausgabe, Funktion
  `cumulative`). Ein fehlender Jahrgang oder ein schlecht gelesener Band senkt die Zahl nicht. Vor
  1911 wächst sie auch, weil Bücher dazukommen; die Seite nennt darum daneben den Anteil an den
  Gemeinden, die bis dahin überhaupt in einem Buch stehen.
- **Jahre der gesamtschweizerischen Bände werden nur mit den Bänden verglichen, die jedes Jahr vorliegen**
  (1, 2a, 2b, 3).

Die Seite zeigt den Bestand selbst («Was die Bücher abdecken»): Einträge und Gemeinden je Jahrgang
und die Gemeinden bisher (1890: 220, 1900: 1'319, 1910: 2'192, 1914: 2'697).

## 1. Telefonnetz

**Reihen je Stadt.** Einträge je Stadt und Jahr. Liegen für ein Jahr mehrere Bände vor (Basel 1899),
zählt der mit den meisten Einträgen. Ein Jahr mit weniger als 90 % des bisher höchsten Jahrs gilt
als unvollständig gelesen und fällt weg (ein Netz schrumpft in dieser Zeit nicht). Gezeigt sind 21 Städte mit mindestens acht Jahrgängen
vor 1911 und mindestens 150 Einträgen im letzten Jahr. Basel wächst von 145 Einträgen
(1881) auf 7'440 (1914), Bern von 74 auf 6'191. (Basel stand vorher bei 8'813: Darunter waren 1'350
Einträge von Luzern, die im Band unter der Überschrift «Basel» stehen.)
Ein Eintrag ist nicht ein Anschluss: Firmen stehen unter mehreren Namen, Geschäftsleute mit
Wohnungsanschluss zweimal.

**Telefon in der Wohnung.** Anteil der Einträge mit einem Wohnungsanschluss («Wohnung», «Privat»,
«domicile», «appartement», «abitazione»), nur Jahre mit mindestens 100 Einträgen (`HOME_MIN`):
darunter entscheiden einzelne Fälle (Bern 1881: vier Wohnungen unter 74 Einträgen). Basel steigt von
0 % (1881) auf 4,0 % (1914), Bern auf 9,7 % (1909), St. Gallen auf 6,8 % (1910). Der Anteil hängt
auch davon ab, wie ein Buch Wohnungen kennzeichnet. Der Anteil der Einträge unter Personennamen
taugt dafür nicht: «Weitnauer, Cigarrenhandlung» ist eine Person mit Geschäft.

**Gemeinden.** Erstes Jahr, in dem eine Gemeinde in einem Telefonbuch steht, Einträge 1914 und
öffentliche Sprechstellen (`CALL_OFFICE`: «Gemeindestation», «Gemeindesprechstation», «Station
communale», «Station publique», «Stazione pubblica», «Stazione consortile»). Von den 3'151 Gemeinden
am 1.1.1914 (BFS) haben 2'697 bis 1914 mindestens einen Eintrag (86 %), 2'192 schon bis 1910. Eine
öffentliche Sprechstelle haben bis 1914 1'816 Gemeinden, zwei von drei mit Telefon. Die Karte färbt
nach Jahrzehnten (1880–1889, 1890–1899, 1900–1910, 1911–1914); die Kantonstabelle nennt den Stand
1890, 1900, 1910 und 1914.

## 2. Berufe der Infrastruktur

Sieben Gruppen nach Stichwörtern im Beruf, bei Firmen und Ämtern auch im Namen (`GROUPS` im Skript):
Bahn; Post, Telegraf, Telefon; Elektrizität; Gas und Wasser; Auto und Velo; Tram, Schiff, Omnibus;
Ingenieure und Bau.

- Gaststätten, die nach Bahnhof oder Post heissen («Hôtel de la Gare», «Wirtschaft z. Post»,
  «Bahnhofbuffet»), zählen nicht zu Bahn oder Post.
- Die Bahnen vor der Verstaatlichung 1902 stehen abgekürzt im Buch: N.O.B. (Nordostbahn), J.-S.
  (Jura-Simplon), S.C.B. (Centralbahn), V.S.B., J.-B.-L.; ohne sie fehlte Lausanne 1896 fast jede
  Bahnstelle (0,5 statt 14,8 je 1000 Einträge). Danach S.B.B. / C.F.F.
- «Postkondukteur» (Postkutsche) zählt zur Post, «Tramkondukteur» zum Tram.

**Adressbücher, je 1000 Einträge** (Einwohner- und Gebäudelisten), Zürich:

| Gruppe | 1867 | 1875 | 1885 | 1900 | 1914 |
|---|---|---|---|---|---|
| Bahn | 5.4 | 32.7 | 18.1 | 20.5 | 33.7 |
| Post, Telegraf, Telefon | 9.9 | 11.3 | 9.3 | 12.3 | 16.3 |
| Elektrizität | 0.3 | 0.0 | 0.1 | 1.5 | 3.9 |
| Gas und Wasser | 1.0 | 0.5 | 0.3 | 0.6 | 1.3 |
| Auto und Velo | 0.0 | 0.0 | 0.0 | 0.5 | 3.3 |
| Tram, Schiff, Omnibus | 2.0 | 1.9 | 1.7 | 3.0 | 6.1 |
| Ingenieure und Bau | 6.5 | 8.3 | 7.2 | 8.6 | 13.5 |

Zürich 1867 umfasst fast nur die Altstadt, 1875–1885 auch die Ausgemeinden (Bahnhof und Werkstätten
in Aussersihl). Weitere Reihen: Aarau 1867–1899, Bern 1883/1900, Lausanne 1896/1907, Baden 1900/1910.

**Telefonbücher einer Stadt, je 1000 Einträge**, für die Städte mit langen Reihen ab ihrem ersten
Buch (je Jahr der Band mit den meisten Einträgen, mindestens 100 Einträge). Basel:

| Gruppe | 1885 | 1900 | 1914 |
|---|---|---|---|
| Bahn | 11.5 | 7.5 | 8.6 |
| Post, Telegraf, Telefon | 1.0 | 0.9 | 3.6 |
| Elektrizität | 0.0 | 3.6 | 4.2 |
| Gas und Wasser | 8.6 | 4.8 | 1.9 |
| Auto und Velo | 0.0 | 1.5 | 5.0 |
| Tram, Schiff, Omnibus | 1.9 | 1.8 | 1.6 |
| Ingenieure und Bau | 3.8 | 10.2 | 15.5 |

**Gesamtschweizerische Bände 1911–1914**, Einträge (Gemeinden), nur Bände 1, 2a, 2b und 3 (Band 2c mit dem Tessin
fehlt 1913 und 1914):

| Gruppe | 1911 | 1912 | 1913 | 1914 |
|---|---|---|---|---|
| Bahn | 393 (163) | 438 (165) | 477 (177) | 495 (183) |
| Post, Telegraf, Telefon | 721 (301) | 802 (319) | 903 (374) | 963 (396) |
| Elektrizität | 541 (191) | 556 (221) | 636 (239) | 664 (244) |
| Gas und Wasser | 267 (86) | 289 (94) | 310 (94) | 331 (106) |
| Auto und Velo | 357 (61) | 454 (74) | 540 (80) | 588 (90) |
| Tram, Schiff, Omnibus | 135 (45) | 152 (47) | 161 (45) | 161 (47) |
| Ingenieure und Bau | 1'341 (242) | 1'332 (256) | 1'326 (265) | 1'368 (278) |
| Einträge insgesamt | 71'849 | 77'496 | 86'262 | 91'339 |

Die Telefonbücher nennen nur Abonnenten: ein Elektrizitätswerk oder eine Garage mit Telefon, nicht
jeden Elektriker oder Chauffeur.

## 3. Weitere Spuren

**Sprechstellen, Ämter und Werke am Netz.** Gemeinden, in denen bis zum Jahr mindestens einmal ein
solcher Eintrag steht; in Klammern der Anteil an den Gemeinden mit Telefon bis dahin:

| Art | bis 1890 | bis 1900 | bis 1910 | bis 1914 |
|---|---|---|---|---|
| Öffentliche Sprechstelle | 8 (4 %) | 475 (36 %) | 1'105 (50 %) | 1'816 (67 %) |
| Gemeindekanzlei | 18 (8 %) | 70 (5 %) | 290 (13 %) | 788 (29 %) |
| Post- und Telegrafenbüro | 7 (3 %) | 115 (9 %) | 361 (16 %) | 485 (18 %) |
| Bahnhof, Station | 11 (5 %) | 42 (3 %) | 112 (5 %) | 286 (11 %) |
| Elektrizitätswerk | 0 | 25 (2 %) | 136 (6 %) | 330 (12 %) |
| Gaswerk | 7 (3 %) | 15 (1 %) | 51 (2 %) | 124 (5 %) |
| Wasserversorgung | 7 (3 %) | 16 (1 %) | 43 (2 %) | 100 (4 %) |
| Bahnhofstrasse in einer Adresse | 15 (7 %) | 38 (3 %) | 90 (4 %) | 173 (6 %) |
| Gemeinden mit Telefon | 220 | 1'319 | 2'192 | 2'697 |

- Werke (`WORKS`): nach dem Namen eines Betriebs oder Amts, nicht nach dem Beruf einer Person. Ein
  «Gas-, Wasser- u. Elektrizitätswerk» zählt dreifach; «Mineralwasser- und Colonialwarenhandlung»
  ist kein Wasserwerk. Das erste Elektrizitätswerk steht 1893 im Buch.
- Ämter (`OFFICES`): eigener Eintrag einer Gemeindekanzlei, eines Bahnhofs, eines Post- oder
  Telegrafenbüros, Gaststätten ausgenommen. **Kein Bahnhof** sind «Station communale», «Station
  publique», «Stazione pubblica» und «Stazione consortile»: Das sind Gemeindesprechstellen (rund
  2'300 von 4'166 Einträgen, die das Muster zuerst als Bahnhof zählte). **Keine Post** sind «Poste
  de gendarmerie» und «Poste de police» (`NOT_OFFICE`).
- Die Sprechstellen waren vorher um mehr als die Hälfte unterzählt (447 statt 998 Gemeinden im Jahr
  1914), weil «Gemeindestation» und «Station communale» im Muster fehlten.

**Städte: was wann im Buch steht.** Für die 21 Städte mit langen Reihen das erste Jahr mit
Sprechstelle, Amt oder Werk. Jede Jahreszahl führt auf der Seite zum Eintrag
(`#/buch?kt=…&y=…&g=…&q=…`; das Suchwort ist der Anfang des Namens, Funktion `term`). Kein Jahr liegt
vor dem ersten gelesenen Buch der Stadt.

**Rufnummern.** Verschiedene Nummern je Stadt und Jahr zählen die Anschlüsse (eine Firma unter
mehreren Namen hat eine Nummer); die höchste Nummer zeigt, wie weit die Zentrale ihre Nummern
vergeben hat. Höchste Nummer = Ende des geschlossenen Bereichs um die mittlere Nummer; ein Block nach
einer Lücke über 300 zählt nicht (Bern 1914 hat einen Block 8000–9999, St. Gallen 1911 einen um 5000–6000).
Nur Jahre mit mindestens 80 % lesbaren Nummern. Basel springt 1896 von höchstens 2'200 auf 4'302 bei
2'146 Nummern (belegt 50 %), bleibt bis 1905 bei rund 4'300 und füllt den Bereich auf (88 % im Jahr 1905).
Basel 1914: 7'440 Einträge, 5'674 Nummern.

**Fremdenverkehr.** Hotels, Kurhäuser, Pensionen (`HOTEL`) unter den Einträgen im ersten Jahr einer
Gemeinde: 6 % (1880–1899), 9 % (1900–1914). In 25 Gemeinden stellen sie mindestens die Hälfte
(mindestens 5 Einträge), darunter Grindelwald 1893 (8 von 8), Beatenberg 1895 (11/13), Lenk 1898
(10/10), Adelboden 1900 (20/30), Kandersteg 1900 (18/21), Salvan 1911 (11/12).

**Telefon je Einwohner und Haushalt** (`durchdringung()`).

*Einwohner.* Grundlage sind die Gemeindeartikel des HLS (`scripts/hls_population.py` →
`data/ref/hls_population.csv`): die Reihe im Kopf des Artikels («1850 2253; 1900 2390; 1950 2831») oder
die Zeile «Einwohner» der Tabelle «Bevölkerungsstruktur». Das ergibt Zahlen für 1'753 Gemeinden von
1914, fast immer für 1850, 1900 und 1950, selten für 1880, 1888 oder 1910. Im HLS-Bestand (derselbe
Export wie hls_mcp, 3'867 Ortsartikel) fehlen aber die Gemeindeartikel fast aller Städte: Von 27
geprüften Städten ist nur St. Gallen dabei. Für sie und für die übrigen Zähljahre dient die BFS-Tabelle
px-x-4004000000_101 (Eidgenössische Volkszählungen, Gebietsstand 5.12.2000; Lizenz OPEN-BY-ASK),
Auszug in `data/ref/population_1850_2000.csv`. Beide nennen dieselben Zählungen: 1'694 von 1'714
vergleichbaren Werten sind gleich. HLS-Werte gelten für 1'499 Gemeinden, BFS allein für 1'176.
Zwischen den Zähljahren wird geometrisch interpoliert. Eine Gemeinde von 1914 zählt zu ihrer Gemeinde
von 2000; was bis 2000 zusammenging, wird zusammengezählt.

*Haushalte.* Das HLS nennt keine Haushalte. Haushalte = Einwohner / Personen je Haushaltung im Kanton
(`data/ref/household_size.csv`; Statistisches Bureau, «Die Verteilung der Bevölkerung auf die
bewohnten Häuser und auf die Haushaltungen», Zeitschrift für schweizerische Statistik 1914, S. 222,
vom Scan abgelesen: Schweiz 4,66 (1880), 4,57 (1888), 4,55 (1900), 4,53 (1910); Genf 3,52, Luzern
5,03 im Jahr 1910).

*Zähler.* Einträge; verschiedene Rufnummern; «Personen» = Einträge unter einem Personennamen, jede
Person je Ort einmal (Geschäft und Wohnung zählen nicht doppelt). Der Anteil der Personen an den
Haushalten ist eine **Obergrenze** für Haushalte mit eigenem Anschluss: Viele sind Handwerker,
Händler oder Ärzte mit dem Telefon im Geschäft.

*Schweiz* (gesamtschweizerische Bände, jeder Eintrag, auch ohne aufgelösten Ort):

| Jahr | Einwohner | Einträge | Rufnummern | Personen | Einträge je 100 Einwohner | Personen je 100 Haushalte |
|---|---|---|---|---|---|---|
| 1911 | 3'765'806 | 73'752 | 63'388 | 44'333 | 1,96 | 5,3 % |
| 1912 | 3'778'361 | 79'598 | 65'725 | 50'034 | 2,11 | 6,0 % |
| 1913 | 3'790'958 | 86'262 | 70'446 | 53'468 | 2,28 | 6,4 % |
| 1914 | 3'803'597 | 91'339 | 74'359 | 56'789 | 2,40 | 6,8 % |

1913 und 1914 fehlt Band 2c (Tessin, 1'900–2'100 Einträge); die Zahlen dieser Jahre liegen darum um
etwa 2 % zu tief. Band 2c ist für 1911 und 1912 neu gelesen ([neulesung_2c.md](neulesung_2c.md)); die
Zeile «Personen» stieg am 18.11.2026 in allen Jahren um 2'200–3'300, weil die Namenszeilen besser
zerlegt werden (Partikel, Doppelnamen, italienische Firmenwörter).

*Städte* (je Jahr der Band mit den meisten Einträgen, ab 100 Einträgen), Personen je 100 Haushalte:
Basel 0,7 (1881), 9,6 (1900), 15,3 (1914); Bern 1,0 (1882), 9,7 (1900), 16,2 (1914);
St. Gallen 1,5 (1886), 6,6 (1900), 15,2 (1914); Interlaken 19,2 (1900), 38,7 (1914);
Lugano 4,3 (1900), 13,5 (1914).

*Nach Gemeindegrösse, um 1910.* **In den gesamtschweizerischen Bänden 1911–1914 fehlen vielen Orten die
Überschriften**: Burgdorf steht unter «Büren zum Hof», Olten unter «Olsberg», Luzern 1912–1914 mitten
unter «Basel». `places.py` findet diese Einträge über die Familiennamen des Regionalbuchs wieder
(19'846 Zeilen), aber nicht vollständig: Burgdorf hat 239 Einträge im Regionalbuch 1910 und danach
220, 154, 5 und 47; Aarau 530 und danach 347, 283, 204 und 129. Orte ohne Regionalbuch zum Vergleich
(Vevey, Montreux) bleiben leer. Ein einzelnes Jahr taugt darum nicht. Gezählt wird je Gemeinde das
Jahr 1909–1914 mit den meisten Einträgen (`END_YEARS`), nur sicher verortete Einträge, und gezeigt wird
der Median der Klasse, nicht die Summe: Ein Lauf, der in ein Dorf gerutscht ist, verzerrt die Summe,
nicht den Median.

| Einwohner 1910 | Gemeinden | mit Telefon | Einträge je 100 Einwohner (Median) | Personen je 100 Haushalte (Median) |
|---|---|---|---|---|
| unter 500 | 1'242 | 74 % | 0,64 | 1,0 % |
| 500–999 | 623 | 92 % | 0,68 | 1,7 % |
| 1'000–1'999 | 465 | 95 % | 0,89 | 2,6 % |
| 2'000–4'999 | 266 | 96 % | 1,24 | 3,8 % |
| 5'000–19'999 | 67 | 96 % | 1,91 | 6,0 % |
| ab 20'000 | 12 | 100 % | 5,23 | 15,3 % |

Die Werte der kleinen und mittleren Gemeinden sind Untergrenzen: Wo weder ein Regionalbuch von
1909/1910 vorliegt noch die Überschrift im gesamtschweizerischen Band gelesen ist, fehlen die Einträge. Eine Tabelle
nach Kantonen gibt es aus demselben Grund nicht. Die Rangliste der Seite nennt nur Gemeinden ab 5'000
Einwohnern (`TOWN`): Genève 25,6 %, Frauenfeld 18,3 %, St. Gallen 16,4 %, Bern 16,2 %, Aarau 16,0 %,
Zürich 15,5 %.

Die Karte «Einträge je 1000 Einwohner» zeigt ebenfalls das beste Jahr 1909–1914; 38 Gemeinden mit
mehr als 250 je 1000 bleiben weg, dort ist die Ortszuordnung falsch (z. B. Kammersrohr, Bettens).

**Bahn und Telefon.** Bahnhöfe aus Wikidata (`P31 Q55488`, `P17 Q39`, Eröffnung `P1619`; CC0),
Auszug in `data/ref/stations_wikidata.csv`; nur 728 von 1'811 haben ein Eröffnungsjahr. Ein Bahnhof
gehört zur nächsten Gemeinde im Umkreis von 3 km. Gemeinden gleicher Grösse (Einwohner 1910, Gebiet
bis 2000 unverändert), Anteil mit Telefon bis 1911:

| Einwohner 1910 | mit Bahnhof (bis 1910) | ohne |
|---|---|---|
| unter 500 | 75 % (91) | 61 % (1'133) |
| 500–999 | 91 % (90) | 89 % (497) |
| 1'000–1'999 | 95 % (93) | 91 % (321) |
| 2'000–4'999 | 100 % (93) | 94 % (149) |
| ab 5'000 | 100 % (42) | 100 % (15) |

Der Bahnhof macht 2–14 Punkte aus, die Grösse den Rest des Unterschieds (91 % gegen 75 % insgesamt).
Eine öffentliche Sprechstelle bis 1914 haben mit Bahnhof 59–98 % je Grössenklasse, ohne 52–87 %.

Abfrage der Bahnhöfe (CSV von https://query.wikidata.org/sparql):

```sparql
SELECT ?s ?sLabel ?d ?c WHERE { ?s wdt:P31 wd:Q55488; wdt:P17 wd:Q39; wdt:P625 ?c.
  OPTIONAL { ?s wdt:P1619 ?d. } SERVICE wikibase:label { bd:serviceParam wikibase:language "de,fr,it". } }
```

```bash
python scripts/infrastruktur.py ref bfs_px-x-4004000000_101.px stations.csv
python scripts/hls_population.py        # data/ref/hls_population.csv, braucht den HLS-Export (lokal)
```

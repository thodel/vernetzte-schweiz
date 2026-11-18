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
**1911** (Landesbuch, Bände 1, 2a–2c, 3). Dazwischen liegen Regionalbücher vor, je Jahr ein bis
sieben Netze (Basel, Bern, St. Gallen, Zürich, Genève, Lausanne, Chur, Bellinzona …); 1891 fehlt
ganz, 1907 liegt nur ein Netz vor. Ein Ort, der erst 1911 erscheint, kann früher ein Telefon gehabt
haben, wenn sein Regionalbuch fehlt (vor allem Waadt und Wallis). Auch im Landesbuch ist nicht jeder
Band ganz gelesen (Band 2c fehlt 1913 und 1914, Lausanne 1912–1914, Luzern 1914 und Winterthur 1913
sind dünn).

Daraus folgen zwei Regeln für alles, was über die Jahre verglichen wird:

- **Verläufe zählen «bis zum Jahr mindestens einmal belegt»** (`verlauf` in der Ausgabe, Funktion
  `cumulative`). Ein fehlender Jahrgang oder ein schlecht gelesener Band senkt die Zahl nicht. Vor
  1911 wächst sie auch, weil Bücher dazukommen; die Seite nennt darum daneben den Anteil an den
  Gemeinden, die bis dahin überhaupt in einem Buch stehen.
- **Jahre der Landesbücher werden nur mit den Bänden verglichen, die jedes Jahr vorliegen**
  (1, 2a, 2b, 3).

Die Seite zeigt den Bestand selbst («Was die Bücher abdecken»): Einträge und Gemeinden je Jahrgang
und die Gemeinden bisher (1890: 209, 1900: 1'284, 1910: 2'145, 1914: 2'631).

## 1. Telefonnetz

**Reihen je Stadt.** Einträge je Stadt und Jahr. Liegen für ein Jahr mehrere Bände vor (Basel 1899),
zählt der mit den meisten Einträgen. Ein Jahr mit weniger als 60 % des vorigen behaltenen Jahrs gilt
als unvollständig gelesen und fällt weg. Gezeigt sind 19 Städte mit mindestens acht Jahrgängen
vor 1911 und mindestens 150 Einträgen im letzten Jahr. Basel wächst von 145 Einträgen
(1881) auf 8'813 (1914), Bern von 74 auf 6'159.
Ein Eintrag ist nicht ein Anschluss: Firmen stehen unter mehreren Namen, Geschäftsleute mit
Wohnungsanschluss zweimal.

**Telefon in der Wohnung.** Anteil der Einträge mit einem Wohnungsanschluss («Wohnung», «Privat»,
«domicile», «appartement», «abitazione»), nur Jahre mit mindestens 100 Einträgen (`HOME_MIN`):
darunter entscheiden einzelne Fälle (Bern 1881: vier Wohnungen unter 74 Einträgen). Basel steigt von
0 % (1881) auf 4,1 % (1914), Bern auf 9,7 % (1909), St. Gallen auf 6,8 % (1910). Der Anteil hängt
auch davon ab, wie ein Buch Wohnungen kennzeichnet. Der Anteil der Einträge unter Personennamen
taugt dafür nicht: «Weitnauer, Cigarrenhandlung» ist eine Person mit Geschäft.

**Gemeinden.** Erstes Jahr, in dem eine Gemeinde in einem Telefonbuch steht, Einträge 1914 und
öffentliche Sprechstellen (`CALL_OFFICE`: «Gemeindestation», «Gemeindesprechstation», «Station
communale», «Station publique», «Stazione pubblica», «Stazione consortile»). Von den 3'151 Gemeinden
am 1.1.1914 (BFS) haben 2'631 bis 1914 mindestens einen Eintrag (83 %), 2'145 schon bis 1910. Eine
öffentliche Sprechstelle haben bis 1914 1'739 Gemeinden, zwei von drei mit Telefon. Die Karte färbt
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
| Bahn | 11.5 | 7.5 | 8.5 |
| Post, Telegraf, Telefon | 1.0 | 0.9 | 4.5 |
| Elektrizität | 0.0 | 3.6 | 4.5 |
| Gas und Wasser | 8.6 | 4.8 | 2.3 |
| Auto und Velo | 0.0 | 1.5 | 5.6 |
| Tram, Schiff, Omnibus | 1.9 | 1.8 | 1.5 |
| Ingenieure und Bau | 3.8 | 10.2 | 16.1 |

**Landesbücher 1911–1914**, Einträge (Gemeinden), nur Bände 1, 2a, 2b und 3 (Band 2c mit dem Tessin
fehlt 1913 und 1914):

| Gruppe | 1911 | 1912 | 1913 | 1914 |
|---|---|---|---|---|
| Bahn | 397 (142) | 444 (155) | 481 (160) | 501 (165) |
| Post, Telegraf, Telefon | 721 (269) | 802 (293) | 904 (346) | 963 (362) |
| Elektrizität | 541 (175) | 556 (197) | 636 (214) | 664 (215) |
| Gas und Wasser | 269 (76) | 289 (82) | 310 (84) | 331 (93) |
| Auto und Velo | 357 (55) | 454 (66) | 542 (67) | 590 (78) |
| Tram, Schiff, Omnibus | 135 (40) | 153 (44) | 163 (43) | 163 (44) |
| Ingenieure und Bau | 1'341 (209) | 1'335 (232) | 1'327 (242) | 1'369 (250) |
| Einträge insgesamt | 71'849 | 77'496 | 86'262 | 91'339 |

Die Telefonbücher nennen nur Abonnenten: ein Elektrizitätswerk oder eine Garage mit Telefon, nicht
jeden Elektriker oder Chauffeur.

## 3. Weitere Spuren

**Sprechstellen, Ämter und Werke am Netz.** Gemeinden, in denen bis zum Jahr mindestens einmal ein
solcher Eintrag steht; in Klammern der Anteil an den Gemeinden mit Telefon bis dahin:

| Art | bis 1890 | bis 1900 | bis 1910 | bis 1914 |
|---|---|---|---|---|
| Öffentliche Sprechstelle | 8 (4 %) | 465 (36 %) | 1'058 (49 %) | 1'739 (66 %) |
| Gemeindekanzlei | 17 (8 %) | 67 (5 %) | 278 (13 %) | 745 (28 %) |
| Post- und Telegrafenbüro | 6 (3 %) | 111 (9 %) | 348 (16 %) | 465 (18 %) |
| Bahnhof, Station | 11 (5 %) | 42 (3 %) | 105 (5 %) | 260 (10 %) |
| Elektrizitätswerk | 0 | 25 (2 %) | 127 (6 %) | 314 (12 %) |
| Gaswerk | 7 (3 %) | 15 (1 %) | 49 (2 %) | 124 (5 %) |
| Wasserversorgung | 7 (3 %) | 15 (1 %) | 41 (2 %) | 92 (3 %) |
| Bahnhofstrasse in einer Adresse | 15 (7 %) | 38 (3 %) | 88 (4 %) | 167 (6 %) |
| Gemeinden mit Telefon | 209 | 1'284 | 2'145 | 2'631 |

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

**Städte: was wann im Buch steht.** Für die 19 Städte mit langen Reihen das erste Jahr mit
Sprechstelle, Amt oder Werk. Jede Jahreszahl führt auf der Seite zum Eintrag
(`#/buch?kt=…&y=…&g=…&q=…`; das Suchwort ist der Anfang des Namens, Funktion `term`). Kein Jahr liegt
vor dem ersten gelesenen Buch der Stadt.

**Rufnummern.** Verschiedene Nummern je Stadt und Jahr zählen die Anschlüsse (eine Firma unter
mehreren Namen hat eine Nummer); die höchste Nummer zeigt, wie weit die Zentrale ihre Nummern
vergeben hat. Höchste Nummer = Ende des geschlossenen Bereichs um die mittlere Nummer; ein Block nach
einer Lücke über 300 zählt nicht (Bern 1914 hat einen Block 8000–9999, St. Gallen 1911 einen um 5000–6000).
Nur Jahre mit mindestens 80 % lesbaren Nummern. Basel springt 1896 von höchstens 2'200 auf 4'302 bei
2'146 Nummern (belegt 50 %), bleibt bis 1905 bei rund 4'300 und füllt den Bereich auf (88 % im Jahr 1905).
Basel 1914: 8'813 Einträge, 5'643 Nummern.

**Fremdenverkehr.** Hotels, Kurhäuser, Pensionen (`HOTEL`) unter den Einträgen im ersten Jahr einer
Gemeinde: 6 % (1880–1899), 8 % (1900–1914). In 22 Gemeinden stellen sie mindestens die Hälfte
(mindestens 5 Einträge), darunter Grindelwald 1893 (8 von 8), Beatenberg 1895 (11/13), Lenk 1898
(10/10), Adelboden 1900 (20/30), Kandersteg 1900 (18/21), Salvan 1911 (11/12).

**Je 1000 Einwohner.** Einwohner aus der BFS-Tabelle px-x-4004000000_101 (Eidgenössische
Volkszählungen 1850–2000, Gebietsstand 5.12.2000; Lizenz OPEN-BY-ASK: freie nichtkommerzielle
Nutzung mit Quellenangabe), Auszug in `data/ref/population_1850_2000.csv`. Eine Gemeinde von 1914
zählt zu ihrer Gemeinde von 2000 (eigene Nummer, sonst die heutige). Städte mit späteren
Eingemeindungen fallen aus der Städtetabelle (der Nenner wäre zu gross). Die Karte zeigt 1911 je
Gemeinde von 2000, nur sicher verortete Einträge (`place_confidence` ≠ `unsicher`); 10 Gemeinden mit
mehr als 250 je 1000 bleiben weg, dort ist die Ortszuordnung falsch (z. B. Kammersrohr, Fiez).
Städte: Basel 2 (1880), 23 (1888), 31 (1900), 40 (1910); 1910 Aarau 55, Solothurn 43, Interlaken 104,
St. Moritz 77 Einträge je 1000 Einwohner.

**Bahn und Telefon.** Bahnhöfe aus Wikidata (`P31 Q55488`, `P17 Q39`, Eröffnung `P1619`; CC0),
Auszug in `data/ref/stations_wikidata.csv`; nur 728 von 1'811 haben ein Eröffnungsjahr. Ein Bahnhof
gehört zur nächsten Gemeinde im Umkreis von 3 km. Gemeinden gleicher Grösse (Einwohner 1910, Gebiet
bis 2000 unverändert), Anteil mit Telefon bis 1911:

| Einwohner 1910 | mit Bahnhof (bis 1910) | ohne |
|---|---|---|
| unter 500 | 71 % (91) | 58 % (1'133) |
| 500–999 | 92 % (86) | 86 % (501) |
| 1'000–1'999 | 92 % (89) | 87 % (325) |
| 2'000–4'999 | 99 % (95) | 90 % (147) |
| ab 5'000 | 100 % (41) | 100 % (16) |

Der Bahnhof macht 5–13 Punkte aus, die Grösse den Rest des Unterschieds (91 % gegen 71 % insgesamt).
Eine öffentliche Sprechstelle bis 1914 haben mit Bahnhof 63–98 % je Grössenklasse, ohne 50–75 %.

Abfrage der Bahnhöfe (CSV von https://query.wikidata.org/sparql):

```sparql
SELECT ?s ?sLabel ?d ?c WHERE { ?s wdt:P31 wd:Q55488; wdt:P17 wd:Q39; wdt:P625 ?c.
  OPTIONAL { ?s wdt:P1619 ?d. } SERVICE wikibase:label { bd:serviceParam wikibase:language "de,fr,it". } }
```

```bash
python scripts/infrastruktur.py ref bfs_px-x-4004000000_101.px stations.csv
```

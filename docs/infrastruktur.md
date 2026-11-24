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
Band ganz gelesen (einen eigenen Band 2c gibt es 1913 und 1914
nicht, das Tessin steht dann in Band 2b),
und vielen Orten fehlt die Überschrift (siehe unten und `scripts/places.py`, Schritt 3).

Daraus folgen zwei Regeln für alles, was über die Jahre verglichen wird:

- **Verläufe zählen «bis zum Jahr mindestens einmal belegt»** (`verlauf` in der Ausgabe, Funktion
  `cumulative`). Ein fehlender Jahrgang oder ein schlecht gelesener Band senkt die Zahl nicht. Vor
  1911 wächst sie auch, weil Bücher dazukommen; die Seite nennt darum daneben den Anteil an den
  Gemeinden, die bis dahin überhaupt in einem Buch stehen.
- **Jahre der gesamtschweizerischen Bände werden nur mit den Bänden verglichen, die jedes Jahr vorliegen**
  (1, 2a, 2b, 3).

Die Seite zeigt den Bestand selbst («Was die Bücher abdecken»): Einträge und Gemeinden je Jahrgang
und die Gemeinden bisher (1890: 220, 1900: 1'322, 1910: 2'196, 1914: 2'786).

## 1. Telefonnetz

**Reihen je Stadt.** Einträge je Stadt und Jahr. Liegen für ein Jahr mehrere Bände vor (Basel 1899),
zählt der mit den meisten Einträgen. Ein Jahr mit weniger als 90 % des bisher höchsten Jahrs gilt
als unvollständig gelesen und fällt weg (ein Netz schrumpft in dieser Zeit nicht). Gezeigt sind 25 Städte mit mindestens acht Jahrgängen
vor 1911 und mindestens 150 Einträgen im letzten Jahr. Basel wächst von 145 Einträgen
(1881) auf 6'327 (1914), Bern von 74 auf 6'355. (Basel stand vorher bei 8'813 und dann bei 7'440: Darunter
waren Einträge von Luzern, die in der Quelle unter der Überschrift «Basel» stehen. Seit der Neulesung von
Band 2b, [neulesung_2b.md](neulesung_2b.md), sind sie getrennt.)
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
am 1.1.1914 (BFS) haben 2'786 bis 1914 mindestens einen Eintrag (88 %), 2'196 schon bis 1910. Eine
öffentliche Sprechstelle haben bis 1914 1'629 Gemeinden, knapp sechs von zehn mit Telefon. Die Karte färbt
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
| Bahn | 11.5 | 7.5 | 12.6 |
| Post, Telegraf, Telefon | 1.0 | 0.9 | 2.8 |
| Elektrizität | 0.0 | 3.6 | 4.3 |
| Gas und Wasser | 8.6 | 4.8 | 1.1 |
| Auto und Velo | 0.0 | 1.5 | 5.4 |
| Tram, Schiff, Omnibus | 1.9 | 1.8 | 2.1 |
| Ingenieure und Bau | 3.8 | 10.2 | 14.1 |

**Gesamtschweizerische Bände 1911–1914**, Einträge (Gemeinden), nur Bände 1, 2a, 2b und 3 (Band 2c mit dem Tessin
gibt es nur 1911 und 1912; 1913 und 1914 steht das Tessin in Band 2b und zählt hier mit):

| Gruppe | 1911 | 1912 | 1913 | 1914 |
|---|---|---|---|---|
| Bahn | 408 (166) | 460 (175) | 492 (182) | 527 (191) |
| Post, Telegraf, Telefon | 760 (324) | 810 (341) | 922 (394) | 1'000 (423) |
| Elektrizität | 561 (203) | 562 (225) | 659 (248) | 689 (258) |
| Gas und Wasser | 291 (89) | 295 (97) | 325 (96) | 345 (112) |
| Auto und Velo | 358 (61) | 455 (75) | 542 (82) | 588 (92) |
| Tram, Schiff, Omnibus | 143 (48) | 151 (48) | 162 (46) | 169 (47) |
| Ingenieure und Bau | 1'362 (251) | 1'335 (264) | 1'341 (276) | 1'382 (288) |
| Einträge insgesamt | 73'362 | 78'261 | 86'867 | 92'283 |

Die Telefonbücher nennen nur Abonnenten: ein Elektrizitätswerk oder eine Garage mit Telefon, nicht
jeden Elektriker oder Chauffeur.

## 3. Weitere Spuren

**Sprechstellen, Ämter und Werke am Netz.** Gemeinden, in denen bis zum Jahr mindestens einmal ein
solcher Eintrag steht; in Klammern der Anteil an den Gemeinden mit Telefon bis dahin:

| Art | bis 1890 | bis 1900 | bis 1910 | bis 1914 |
|---|---|---|---|---|
| Öffentliche Sprechstelle | 8 (4 %) | 476 (36 %) | 1'113 (51 %) | 1'629 (58 %) |
| Gemeindekanzlei | 18 (8 %) | 70 (5 %) | 293 (13 %) | 589 (21 %) |
| Post- und Telegrafenbüro | 7 (3 %) | 117 (9 %) | 365 (17 %) | 420 (15 %) |
| Bahnhof, Station | 11 (5 %) | 42 (3 %) | 113 (5 %) | 240 (9 %) |
| Elektrizitätswerk | 0 | 26 (2 %) | 139 (6 %) | 223 (8 %) |
| Gaswerk | 7 (3 %) | 15 (1 %) | 52 (2 %) | 88 (3 %) |
| Wasserversorgung | 7 (3 %) | 16 (1 %) | 43 (2 %) | 69 (2 %) |
| Bahnhofstrasse in einer Adresse | 15 (7 %) | 38 (3 %) | 91 (4 %) | 112 (4 %) |
| Gemeinden mit Telefon | 220 | 1'322 | 2'196 | 2'786 |

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

**Städte: was wann im Buch steht.** Für die 25 Städte mit langen Reihen das erste Jahr mit
Sprechstelle, Amt oder Werk. Jede Jahreszahl führt auf der Seite zum Eintrag
(`#/buch?kt=…&y=…&g=…&q=…`; das Suchwort ist der Anfang des Namens, Funktion `term`). Kein Jahr liegt
vor dem ersten gelesenen Buch der Stadt.

**Rufnummern.** Verschiedene Nummern je Stadt und Jahr zählen die Anschlüsse (eine Firma unter
mehreren Namen hat eine Nummer); die höchste Nummer zeigt, wie weit die Zentrale ihre Nummern
vergeben hat. Höchste Nummer = Ende des geschlossenen Bereichs um die mittlere Nummer; ein Block nach
einer Lücke über 300 zählt nicht (Bern 1914 hat einen Block 8000–9999, St. Gallen 1911 einen um 5000–6000).
Nur Jahre mit mindestens 80 % lesbaren Nummern. Basel springt 1896 von höchstens 2'200 auf 4'302 bei
2'146 Nummern (belegt 50 %), bleibt bis 1905 bei rund 4'300 und füllt den Bereich auf (88 % im Jahr 1905).
Basel 1914: 6'327 Einträge, 5'551 Nummern.

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
Auszug in `data/ref/population_1850_2000.csv`. Beide nennen dieselben Zählungen: 1'762 von 1'791
vergleichbaren Werten sind gleich. HLS-Werte gelten für 1'565 Gemeinden, BFS allein für 1'226.
Zwischen den Zähljahren wird geometrisch interpoliert. Eine Gemeinde von 1914 zählt zu ihrer Gemeinde
von 2000; was bis 2000 zusammenging, wird zusammengezählt. Ob eine Gemeinde 2000 noch bestand, sagt die BFS-Tabelle,
nicht das Feld `valid_to`: Ein Datum vor 2000 steht dort auch bei Umbenennungen und neuen Bezirken (Kanton Bern
31.12.1978). Bis 23.11.2026 las `unit_2000()` das als Fusion; 116 Gemeinden zählten darum zur heutigen Gemeinde oder
fielen weg (Ilanz, Maienfeld). Die Summen für die Schweiz ändern sich dadurch nicht, die Mediane der Klassen um
höchstens 0,3 Punkte.

*Kanton Bern.* Für die Berner Gemeinden gibt es mit BERNHIST eine zweite Referenz, die auch die Erwerbstätigen
nach Sektor 1910 nennt. Dichte gegen Grösse und Erwerbsstruktur und die Stadt Bern nach Gruppen (Sektoren, Ärzte,
Frauen, neben dem Adressbuch) stehen in [durchdringung_bern.md](durchdringung_bern.md)
(`scripts/ref_bernhist.py`, `scripts/durchdringung_bern.py`).

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
| 1911 | 3'765'806 | 77'155 | 67'966 | 47'848 | 2,05 | 5,8 % |
| 1912 | 3'778'361 | 82'127 | 73'231 | 51'604 | 2,17 | 6,2 % |
| 1913 | 3'790'958 | 88'196 | 77'958 | 55'526 | 2,33 | 6,6 % |
| 1914 | 3'803'597 | 93'937 | 82'427 | 58'567 | 2,47 | 7,0 % |

Einen eigenen Band 2c (Tessin) gibt es nur 1911 und 1912; 1913 und 1914 steht das Tessin in Band 2b
(2'200–2'400 Einträge). Band 2c ist für 1911 und 1912 neu gelesen ([neulesung_2c.md](neulesung_2c.md)),
die Bände 1, 2a, 2b und 3 für 1911–1914 ganz ([neulesung_13.md](neulesung_13.md), [neulesung_2a.md](neulesung_2a.md), [neulesung_2b.md](neulesung_2b.md)); die
Zeile «Personen» stieg am 18.11.2026 in allen Jahren um 2'200–3'300, weil die Namenszeilen besser
zerlegt werden (Partikel, Doppelnamen, italienische Firmenwörter).

*Städte* (je Jahr der Band mit den meisten Einträgen, ab 100 Einträgen), Personen je 100 Haushalte:
Basel 0,7 (1881), 9,6 (1900), 12,9 (1914); Bern 1,0 (1882), 9,7 (1900), 17,1 (1914);
St. Gallen 1,5 (1886), 6,6 (1900), 14,4 (1914); Interlaken 19,2 (1900), 36,0 (1914);
Lugano 4,4 (1900), 13,4 (1914).

*Nach Gemeindegrösse, um 1910.* **In den gesamtschweizerischen Bänden 1911–1914 fehlen vielen Orten die
Überschriften**: In Band 2a stand Burgdorf unter «Büren zum Hof», in Band 2b standen Olten unter «Olsberg» und Luzern mitten
unter «Basel», in Band 1 der Lausanner Block 1914 unter «Genève» und Aigle 1913 unter «Aclens», in Band 3 Winterthur unter «Winterberg», bis zur Neulesung der Bände (1911–1914, [neulesung_2b.md](neulesung_2b.md), [neulesung_2a.md](neulesung_2a.md), [neulesung_13.md](neulesung_13.md)). `places.py` findet diese Einträge über die Familiennamen des Regionalbuchs wieder
(9'714 Zeilen), aber nicht vollständig. Zum Vergleich: Burgdorf hat 239 Einträge im Regionalbuch 1910 und nach der Neulesung
von Band 2a 259, 285, 305 und 316 (vorher 218, 152, 5 und 46); Aarau 530 und nach der Neulesung von Band 2b 510, 522, 528
und 544 (vorher 1911 und 1912: 347 und 283). Orte ohne Regionalbuch zum Vergleich
(Montreux, auf zwei Gemeinden verteilt) bleiben leer. Ein einzelnes Jahr taugt darum nicht. Gezählt wird je Gemeinde das
Jahr 1909–1914 mit den meisten Einträgen (`END_YEARS`), nur sicher verortete Einträge, und gezeigt wird
der Median der Klasse, nicht die Summe: Ein Lauf, der in ein Dorf gerutscht ist, verzerrt die Summe,
nicht den Median.

| Einwohner 1910 | Gemeinden | mit Telefon | Einträge je 100 Einwohner (Median) | Personen je 100 Haushalte (Median) |
|---|---|---|---|---|
| unter 500 | 1'326 | 82 % | 0,51 | 0,0 % |
| 500–999 | 642 | 96 % | 0,49 | 1,2 % |
| 1'000–1'999 | 473 | 97 % | 0,77 | 2,3 % |
| 2'000–4'999 | 269 | 99 % | 1,36 | 3,9 % |
| 5'000–19'999 | 69 | 100 % | 2,24 | 6,5 % |
| ab 20'000 | 12 | 100 % | 5,25 | 15,1 % |

Die Werte der kleinen und mittleren Gemeinden sind Untergrenzen: Wo weder ein Regionalbuch von
1909/1910 vorliegt noch die Überschrift im gesamtschweizerischen Band gelesen ist, fehlen die Einträge. Eine Tabelle
nach Kantonen gibt es aus demselben Grund nicht. Die Rangliste der Seite nennt nur Gemeinden ab 5'000
Einwohnern (`TOWN`): Genève 18,7 %, Davos 18,6 %, Lausanne 18,2 %, Bern 17,1 %, Zürich 16,3 %, Aarau 16,1 %, Luzern 16,0 %. Vor der Neulesung der Bände 1 und 3 stand Genève mit 25,6 % vorn: In Band 1 1914 zählte der Lausanner Block mit.

Die Karte «Einträge je 1000 Einwohner» zeigt ebenfalls das beste Jahr 1909–1914; 27 Gemeinden mit
mehr als 250 je 1000 bleiben weg, dort ist die Ortszuordnung falsch (z. B. Kammersrohr, Bettens).

**Bahn und Telefon.** Bahnhöfe aus Wikidata (`P31 Q55488`, `P17 Q39`, Eröffnung `P1619`; CC0),
Auszug in `data/ref/stations_wikidata.csv`; nur 728 von 1'811 haben ein Eröffnungsjahr. Ein Bahnhof
gehört zur nächsten Gemeinde im Umkreis von 3 km. Gemeinden gleicher Grösse (Einwohner 1910, Gebiet
bis 2000 unverändert), Anteil mit Telefon bis 1911:

| Einwohner 1910 | mit Bahnhof (bis 1910) | ohne |
|---|---|---|
| unter 500 | 75 % (93) | 63 % (1'220) |
| 500–999 | 91 % (93) | 89 % (515) |
| 1'000–1'999 | 95 % (97) | 92 % (333) |
| 2'000–4'999 | 100 % (96) | 94 % (154) |
| ab 5'000 | 100 % (43) | 100 % (17) |

Der Bahnhof macht 2–12 Punkte aus, die Grösse den Rest des Unterschieds (91 % gegen 75 % insgesamt).
Eine öffentliche Sprechstelle bis 1914 haben mit Bahnhof 56–95 % je Grössenklasse, ohne 49–76 %.

Abfrage der Bahnhöfe (CSV von https://query.wikidata.org/sparql):

```sparql
SELECT ?s ?sLabel ?d ?c WHERE { ?s wdt:P31 wd:Q55488; wdt:P17 wd:Q39; wdt:P625 ?c.
  OPTIONAL { ?s wdt:P1619 ?d. } SERVICE wikibase:label { bd:serviceParam wikibase:language "de,fr,it". } }
```

```bash
python scripts/infrastruktur.py ref bfs_px-x-4004000000_101.px stations.csv
python scripts/hls_population.py        # data/ref/hls_population.csv, braucht den HLS-Export (lokal)
```

# Infrastruktur (Versuch)

Was zeigen Telefon- und Adressbücher vom Ausbau der Infrastruktur? `scripts/infrastruktur.py` misst
drei Dinge und einige weitere Spuren; die Seite zeigt sie unter `#/infrastruktur`.

```bash
make infrastruktur                      # data/norm/infrastruktur.json
python scripts/infrastruktur.py site    # site/data/infrastruktur.json.gz (läuft im Pages-Workflow)
```

## Die Quellen und ihre Lücken

Die Telefonbücher decken die ganze Schweiz erst ab **1911** (Landesbuch, Bände 1, 2a–2c, 3). Vorher
liegen Regionalbücher vor, je nach Jahr für Basel, Bern, St. Gallen, Aarau, Chur, Bellinzona, Genève,
Zürich (1909–1910) und ihre Netze. Ein Ort, der erst 1911 erscheint, kann früher ein Telefon gehabt
haben, wenn sein Regionalbuch fehlt (vor allem Waadt und Wallis). Auch im Landesbuch ist nicht jeder
Band ganz gelesen (Band 2c fehlt 1913 und 1914, Lausanne 1912–1914 und Chur 1911–1914 sind dünn).

## 1. Telefonnetz

**Reihen je Stadt.** Einträge je Stadt und Jahr. Liegen für ein Jahr mehrere Bände vor (Basel 1899),
zählt der mit den meisten Einträgen. Ein Jahr mit weniger als 60 % des vorigen behaltenen Jahrs gilt
als unvollständig gelesen und fällt weg. Gezeigt sind 19 Städte mit mindestens acht Jahrgängen
vor 1911 und mindestens 150 Einträgen im letzten Jahr. Basel wächst von 145 Einträgen
(1881) auf 8'813 (1914), Bern von 74 auf 6'159.
Ein Eintrag ist nicht ein Anschluss: Firmen stehen unter mehreren Namen, Geschäftsleute mit
Wohnungsanschluss zweimal.

**Telefon in der Wohnung.** Anteil der Einträge mit einem Wohnungsanschluss («Wohnung», «Privat»,
«domicile», «appartement», «abitazione»). Basel steigt von 0 % (1881–1886) auf 4,1 % (1914), Bern
von 0,1–0,2 % (1890er Jahre) auf 9,7 % (1909), St. Gallen auf 6,8 % (1910). Der Anteil der Einträge
unter Personennamen taugt dafür nicht: «Weitnauer, Cigarrenhandlung» ist eine Person mit Geschäft.
Der frühe Gipfel in Bern (1881–1884, 2–5 %) beruht auf vier bis sechs Wohnungen unter 74 bis 192
Einträgen.

**Gemeinden.** Erstes Jahr, in dem eine Gemeinde in einem Telefonbuch steht, Einträge 1914 und
öffentliche Sprechstellen («Gemeindesprechstation», «station téléphonique publique», «posto
telefonico»). Von den 3'151 Gemeinden am 1.1.1914 (BFS) haben 2'626 bis 1914 mindestens einen
Eintrag (83%), 2'330 schon bis 1911. Eine öffentliche Sprechstelle haben 1911–1914 zusammen
733 Gemeinden, im Jahr 1914 allein 457.

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

**Landesbücher 1911–1914**, Einträge (Gemeinden):

| Gruppe | 1911 | 1912 | 1913 | 1914 |
|---|---|---|---|---|
| Bahn | 398 (141) | 444 (154) | 481 (165) | 501 (164) |
| Post, Telegraf, Telefon | 753 (275) | 838 (298) | 904 (349) | 963 (365) |
| Elektrizität | 583 (180) | 600 (207) | 636 (219) | 664 (216) |
| Gas und Wasser | 269 (75) | 289 (82) | 310 (84) | 331 (88) |
| Auto und Velo | 363 (53) | 459 (66) | 542 (73) | 590 (78) |
| Tram, Schiff, Omnibus | 139 (36) | 156 (42) | 163 (44) | 163 (43) |
| Ingenieure und Bau | 1'350 (211) | 1'345 (230) | 1'327 (241) | 1'369 (247) |
| Einträge insgesamt | 73'403 | 79'216 | 86'262 | 91'339 |

Die Telefonbücher nennen nur Abonnenten: ein Elektrizitätswerk oder eine Garage mit Telefon, nicht
jeden Elektriker oder Chauffeur.

## 3. Weitere Spuren

**Bahnhofstrasse:** Gemeinden mit Einträgen an einer Bahnhofstrasse, Rue de la Gare, Via Stazione:
52 (1911), 65 (1914).

**Rufnummern.** Verschiedene Nummern je Stadt und Jahr zählen die Anschlüsse (eine Firma unter
mehreren Namen hat eine Nummer); die höchste Nummer zeigt, wie weit die Zentrale ihre Nummern
vergeben hat. Höchste Nummer = Ende des geschlossenen Bereichs um die mittlere Nummer; ein Block nach
einer Lücke über 300 zählt nicht (Bern 1914 hat einen Block 8000–9999, St. Gallen 1911 einen um 5000–6000).
Nur Jahre mit mindestens 80 % lesbaren Nummern. Basel springt 1896 von höchstens 2'200 auf 4'302 bei
2'146 Nummern (belegt 50 %), bleibt bis 1905 bei rund 4'300 und füllt den Bereich auf (88 % im Jahr 1905).
Basel 1914: 8'813 Einträge, 5'643 Nummern.

**Gemeindewerke.** Elektrizitäts-, Gas- und Wasserwerke unter ihrem eigenen Namen (`WORKS`), nicht
der Beruf einer Person. Gemeinden mit mindestens einem Werk: Strom 106 (1911) → 148 (1914), Gas
28 → 45, Wasser 26 → 35; vor 1911 schon 127 / 32 / 37, wo Regionalbücher vorliegen. 1914 liegt unter
1913, weil Band 2c fehlt.

**Ämter am Netz.** Eigener Eintrag einer Gemeindekanzlei, eines Bahnhofs, eines Post- oder
Telegrafenbüros (`OFFICES`, Gaststätten ausgenommen). 1911: 278 / 257 / 111 Gemeinden, 1914:
374 / 393 / 151, je etwa ein Fünftel der Gemeinden mit Einträgen im selben Jahr (Post 8–9 %: sie
ist oft die öffentliche Sprechstelle).

**Fremdenverkehr.** Hotels, Kurhäuser, Pensionen (`HOTEL`) unter den Einträgen im ersten Jahr einer
Gemeinde: 6 % (1880–1899), 8 % (1900–1914). In 22 Gemeinden stellen sie mindestens die Hälfte
(mindestens 5 Einträge), darunter Grindelwald 1893 (8 von 8), Beatenberg 1895 (11/13), Lenk 1898
(10/10), Adelboden 1900 (20/30), Kandersteg 1900 (18/21), Salvan 1911 (11/12).

**Je 1000 Einwohner.** Einwohner aus der BFS-Tabelle px-x-4004000000_101 (Eidgenössische
Volkszählungen 1850–2000, Gebietsstand 5.12.2000; Lizenz OPEN-BY-ASK: freie nichtkommerzielle
Nutzung mit Quellenangabe), Auszug in `data/ref/population_1850_2000.csv`. Eine Gemeinde von 1914
zählt zu ihrer Gemeinde von 2000 (eigene Nummer, sonst die heutige). Städte mit späteren
Eingemeindungen fallen aus der Städtetabelle (der Nenner wäre zu gross). Die Karte zeigt 1911 je
Gemeinde von 2000, nur sicher verortete Einträge (`place_confidence` ≠ `unsicher`); 12 Gemeinden mit
mehr als 250 je 1000 bleiben weg, dort ist die Ortszuordnung falsch (z. B. Kammersrohr, Betten).
Städte, 1910: Basel 40, Aarau 55, Solothurn 42, Interlaken 104, St. Moritz 77 Einträge je 1000
Einwohner.

**Bahn und Telefon.** Bahnhöfe aus Wikidata (`P31 Q55488`, `P17 Q39`, Eröffnung `P1619`; CC0),
Auszug in `data/ref/stations_wikidata.csv`; nur 728 von 1'811 haben ein Eröffnungsjahr. Ein Bahnhof
gehört zur nächsten Gemeinde im Umkreis von 3 km. Gemeinden gleicher Grösse (Einwohner 1910, Gebiet
bis 2000 unverändert), Anteil mit Telefon bis 1911:

| Einwohner 1910 | mit Bahnhof (bis 1910) | ohne |
|---|---|---|
| unter 500 | 71 % (91) | 58 % (1'133) |
| 500–999 | 92 % (87) | 86 % (500) |
| 1'000–1'999 | 93 % (88) | 87 % (326) |
| 2'000–4'999 | 99 % (95) | 91 % (147) |
| ab 5'000 | 100 % (40) | 100 % (17) |

Der Bahnhof macht 6–13 Punkte aus, die Grösse den Rest des Unterschieds (91 % gegen 71 % insgesamt).

Abfrage der Bahnhöfe (CSV von https://query.wikidata.org/sparql):

```sparql
SELECT ?s ?sLabel ?d ?c WHERE { ?s wdt:P31 wd:Q55488; wdt:P17 wd:Q39; wdt:P625 ?c.
  OPTIONAL { ?s wdt:P1619 ?d. } SERVICE wikibase:label { bd:serviceParam wikibase:language "de,fr,it". } }
```

```bash
python scripts/infrastruktur.py ref bfs_px-x-4004000000_101.px stations.csv
```

# Durchdringung des Telefons im Kanton Bern, gemessen an BERNHIST

Stand 23.11.2026. Zwei Fragen: Hängt die Telefondichte der Berner Gemeinden um 1910 an der Erwerbsstruktur oder
nur an der Grösse? Und wer hat in der Stadt Bern 1885, 1900 und 1910 ein Telefon? Die Nenner kommen aus BERNHIST
(Historisch-statistische Datenbank des Kantons Bern, Projekt Christian Pfister, heute Universitätsbibliothek
Bern, <https://www.bernhist.ch>), die Zähler aus den Telefonbüchern (`data/norm/ptt_entries.csv.gz`).

Nachrechnen:

```bash
python scripts/ref_bernhist.py --bernhist <sqlite>   # nur mit dem Dump: Referenz neu aus BERNHIST lesen
python scripts/ref_bernhist.py                       # ohne Dump: Zuordnung und Abgleich aus werte.csv neu rechnen
python scripts/durchdringung_bern.py                 # Messung; schreibt die Tabellen und den Block unten
python -m unittest tests.test_durchdringung_bern
```

`durchdringung_bern.py` liest nur und baut keine abgeleiteten Daten neu. Es schreibt
`data/norm/durchdringung_bern_gemeinden.csv` (je Einheit), `data/norm/durchdringung_bern_stadt.csv` (Stadt Bern,
je Jahr und Gruppe mit Nenner und Herleitung) und `data/norm/durchdringung_bern.json` (Kreuztabellen).

## Befund in Kürze

**Gemeinden.** Die Telefondichte hängt an der Erwerbsstruktur; die Grösse wirkt fast nur über sie.

- Nach Grösse allein steigt die Dichte von 0,56 Einträgen je 100 Einwohner (Median der Einheiten unter 500
  Einwohnern) auf 1,1 (2000–4999) und 1,7 (ab 5000).
- Teilt man jede Grössenklasse in die Hälfte mit weniger und die mit mehr Erwerbstätigen im 3. Sektor, so hat die
  zweite Hälfte ab 1000 Einwohnern rund die dreifache Dichte: 0,59 gegen 1,6 Einträge je 100 Einwohner bei
  1000–1999, 0,65 gegen 2,2 bei 2000–4999, 1,2 gegen 5,8 ab 5000.
- Bäuerliche Gemeinden (1. Sektor ab 60 %) bleiben in jeder Grösse bei 0,3 bis 0,5 Einträgen je 100 Einwohner
  (Median 0,47; 0,47; 0,28; 0,40). Unter ihnen bringt Grösse nichts.
- Gemeinden mit mindestens einem Viertel der Erwerbstätigen im 3. Sektor liegen ab 500 Einwohnern bei 1,8 bis
  2,5, ab 5000 bei 4,0. Auch hier gibt es zwischen 500 und 4999 Einwohnern kein Gefälle nach Grösse.
- Gewerblich-industrielle Gemeinden (2. Sektor ab 50 %) liegen dazwischen (0,5 bis 1,1) und nahe bei den
  gemischten. Der 2. Sektor allein hebt die Dichte kaum.
- Unter 500 Einwohnern unterscheidet nichts: Dort besteht das Telefon aus einem bis drei Einträgen, oft nur der
  Gemeindestation, und 91 % dieser Gemeinden haben einen.
- Die Stadt Bern steht für sich (7,4 Einträge je 100 Einwohner 1914); die 13 übrigen Einheiten ab 5000 Einwohnern
  kommen zusammen auf 2,6.

**Stadt Bern.** Das Telefon ist ein Werkzeug des Handels, der Verwaltung und der freien Berufe, bevor es ein
Anschluss der Haushalte wird.

- 1885 stehen 151 Personen, 76 Firmen und 45 Ämter im Buch: 0,34 % der Bevölkerung, 1,6 Personen je 100
  Haushalte. 1900 sind es 1 227 Personen (8,9 je 100 Haushalte), 1910 2 269 (12,3 je 100 Haushalte). Das ist
  eine Obergrenze für den Anteil der Haushalte mit Telefon: Die meisten Personen stehen mit ihrem Geschäft im
  Buch, und nur 361 nennen 1910 eine Wohnung (2,0 je 100 Haushalte).
- Der 3. Sektor hat in jedem Jahr die doppelte Quote des 2.: 1,4 gegen 0,61 Anschlussinhaber je 100
  Erwerbstätige 1885, 6,7 gegen 3,3 im Jahr 1900, 9,6 gegen 4,5 im Jahr 1910 (1910 mit gezählten Nennern, davor
  geschätzt).
- Ärzte sind die am dichtesten angeschlossene Gruppe mit Nenner: 11 von rund 84 im Jahr 1885 (13 %), 58 von rund
  103 im Jahr 1900 (56 %), 96 von 116 im Jahr 1910 (83 %).
- Frauen sind fast nicht vertreten: 3, 106 und 265 erkannte Frauen (0,56 % der Frauen 1910), darunter 1, 35 und
  71 Witwen (2,1 % der geschätzten Witwen 1910).
- Neben dem Adressbuch: 1900 nennt das Einwohnerverzeichnis 102 Personen je 100 Haushalte, das Telefonbuch 8,9.
  Auf 100 Personen des Adressbuchs im 3. Sektor kommen 13,2 Personen und Firmen im Telefonbuch, im 2. Sektor 8,4,
  bei den Ärzten 48, bei den Frauen 3,3. Firmen stehen häufiger im Telefonbuch als im Adressbuch (400 gegen 262).
- Über die Verknüpfung gezählt (Untergrenze): 6,7 % der Personen im Einwohnerverzeichnis 1900 haben 1900 oder
  1901 ein Telefon; im 3. Sektor 8,4 %, im 2. Sektor 5,7 %, Ärzte 45,5 %, Spezereihändler 25,4 %, Witwen 3,7 %.
  1883–84 sind es 1,4 % (3. Sektor 2,0 %, 2. Sektor 1,0 %, Ärzte 14 %).

## Adressbuch und Telefon in der Stadt Bern, 1795–1914

Zusammenführung mit den beiden Adressbuch-Repos, die dieselben BERNHIST-Nenner verwenden:
[adressbuecher-bern-frueh](https://thodel.github.io/adressbuecher-bern-frueh/abdeckung.html) (1795–1848, Commit
d134c15) und [adressbuecher-bern](https://thodel.github.io/adressbuecher-bern/abdeckung.html) (1883–84 und 1900,
Commit 8692f31). Die Zahlen sind dort hergeleitet; hier stehen sie nebeneinander. Haushalte vor 1847 und nach
1888 sind geschätzt (Haushaltsgrösse eines Stichjahrs), Nenner für Gruppen vor 1856 mit der Bevölkerung
umgerechnet; die Werte sind darum Grössenordnungen.

**Wie viele stehen im Buch?** Verschiedene Personen je 100 Einwohner und je 100 Haushalte:

| Jahr | Verzeichnis | je 100 Einwohner | je 100 Haushalte |
|---|---|---:|---:|
| 1795 | Address-Handbuch der Handelshäuser | 0,9 | 4 |
| 1810 | Livre d'adresses | 3,1 | 13 |
| 1822 | Adressbuch der Stadt Bern | 6,5 | 28 |
| 1836 | Adressenbuch der Republik Bern (Einwohnerschaft der Stadt) | 13,7 | 58 |
| 1848 | Verzeichnis der Einsassen (ohne Burger) | 8,6 | 38 |
| 1883–84 | Adressbuch der Stadt Bern | 18,0 | 83 |
| 1885 | Telefonbuch | 0,3 | 1,6 |
| 1900 | Adressbuch der Stadt Bern | 22,1 | 102 |
| 1900 | Telefonbuch | 1,9 | 8,9 |
| 1910 | Telefonbuch | 2,6 | 12,3 |

Das Adressbuch erreicht um 1900 rechnerisch jeden Haushalt (über 100 heisst: mehr als eine genannte Person je
Haushalt, etwa Witwen und erwerbstätige Kinder mit eigener Zeile). Das Telefonbuch steht 1910 dort, wo das
Adressbuch 1810 stand. 1848 ist kein Rückgang: Das Verzeichnis nennt nur Einsassen, und von ihnen steht ein
Drittel der Köpfe in den verzeichneten Haushalten.

**Wer steht drin?** Anteil der Gruppe, der im Buch steht (in %):

| Gruppe | 1822 | 1836 | 1848 | 1883–84 | 1900 | Telefon 1885 | Telefon 1900 | Telefon 1910 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Ärzte | 81 | 93 | 17 | 26–63 | 80 | 13 | 56 | 83 |
| Erwerbstätige 3. Sektor | 31 | 64 | 35 | 38 | 50 | 1,4 | 6,7 | 9,6 |
| Erwerbstätige 2. Sektor | 22 | 27 | 27 | 31 | 37 | 0,6 | 3,3 | 4,5 |
| Frauen (alle Alter) | 1,1 | 3,2 | 3,3 | 6,6 | 9,0 | 0,01 | 0,3 | 0,6 |
| Witwen | 2,8 | 3,9 | 5,0 | 20 | 45 | 0,05 | 1,3 | 2,1 |
| Dienstboten | 0,4 | 0,4 | 1,0 | 0,3 | 0,3 | | | |

- **Die Reihenfolge der Gruppen ist in beiden Büchern dieselbe** und über 120 Jahre stabil: Ärzte vor Handel und
  Verwaltung (3. Sektor) vor Handwerk und Gewerbe (2. Sektor), Frauen und Dienstboten fast gar nicht. Das Telefon
  wiederholt die Rangfolge des Adressbuchs auf tieferem Niveau; nur die Ärzte holen bis 1910 ganz auf.
- **Das Adressbuch öffnet sich für Frauen erst nach 1850,** und zwar über die Witwen (von 5 % auf 45 % zwischen
  1848 und 1900); Frauen insgesamt bleiben unter 10 %. Im Telefonbuch sind Frauen 1910 so selten wie im
  Adressbuch von 1822.
- **Dienstboten fehlen in jedem Verzeichnis** (unter 1 %): Sie wohnen im Haushalt der Herrschaft und haben keine
  eigene Zeile. Das ist eine Grenze der Quelle, nicht der Lesung.
- **Ärzte 1848 und 1883–84 sind kein Einbruch:** 1848 fehlen die Burger, 1883–84 nennt das Einwohnerverzeichnis
  den Beruf oft nur als «Dr.» (26 % mit Beruf «Arzt», 63 % mit «Dr. med.» im Titel).

## Referenz: BERNHIST an den Gemeinden von 1914

`scripts/ref_bernhist.py` liest den lokal geladenen Dump (Repo `ub-unibe-ch/bernhist`, Stand 22.03.2024) und legt
unter `data/ref/bernhist/` nur ab, was gebraucht wird. BERNHIST kennt weder BFS-Nummern noch Koordinaten; die
Bindung an `data/ref/municipalities_1914.csv` geht über den Namen.

| Datei | Inhalt |
|---|---|
| `werte.csv` | 5 011 verwendete Einzelwerte mit Ort, Thema, Jahr und Nummer im Dump (`data_entry_id`) |
| `orte.csv` | jeder der 450 BERNHIST-Orte vom Typ Einwohnergemeinde: Gemeinde von 1914 (`hist_code`), Einheit, Methode |
| `gemeinden_1914.csv` | jede der 503 Berner Gemeinden von 1914: BERNHIST-Ort, Einheit oder «nicht in BERNHIST» |
| `einheiten.csv` | je Einheit Wohnbevölkerung 1880, 1888, 1900, 1910, Haushalte 1888, Erwerbstätige nach Sektor 1910 |
| `vergleich_bfs.csv` | Bevölkerung 1900 und 1910 gegen `data/ref/population_1850_2000.csv` |
| `adressbuch_bern.csv` | Zähler und Quoten aus `adressbuecher-bern` (Commit 8692f31), zum Vergleich |

**Zuordnung.** 421 der 450 Orte sind an eine Gemeinde von 1914 gebunden: 388 mit gleichem Namen, 29 nach
Normalisierung (Zusätze wie «(bis 1919)» und «(BE)» weg, «Ferrière, La» = «La Ferrière», «Interlaken / Aarmühle»
= beide Namen, th = t, ohne Akzente), 4 über die Handtabelle `config/bernhist_orte.csv`. Die 29 übrigen Orte sind
vor 1914 aufgelöste Gemeinden («Riedtwil (bis 1851)») oder spätere Gemeinden, die es 1914 noch nicht gab (Tramelan,
Konolfingen, Linden); jede steht mit Begründung in `orte.csv`.

Von den 503 Berner Gemeinden von 1914 sind 409 direkt zugeordnet, 11 sind Teil einer Einheit, 1 hat in BERNHIST
keine Bevölkerung (Kandersteg: 0 statt 3 554), 82 fehlen: die 74 Gemeinden der Bezirke Porrentruy, Delémont und
Franches-Montagnes (seit 1979 Kanton Jura) und 8 des Bezirks Moutier, die später zum Kanton Jura kamen. BERNHIST
deckt den heutigen Kanton Bern und das Laufental.

**Einheit.** BERNHIST führt die Bevölkerung nicht durchgehend im Gebietsstand von 1914. Tramelan, Konolfingen
und Linden gibt es nur als spätere Gemeinden; Strättligen steckt in Thun, Gäserz in Brüttelen, Mullen in Tschugg,
Isenfluh in Lauterbrunnen. Eine Einheit ist darum der BERNHIST-Ort, der die Bevölkerung trägt, mit allen Gemeinden
von 1914, die darin aufgehen. Es gibt 412 Einheiten; 405 gehen in die Messung ein.

**Erwerbstätige 1910.** BERNHIST hat für 1910 zwei Reihen. Reihe A (zuerst erfasst) steht im Gebietsstand von
1910 und nennt den 1. und den 2. Sektor; der 3. ist der Rest. Reihe B nennt alle drei Sektoren, steht aber in
einem späteren Gebietsstand: Bern mit Bümpliz (37 247 statt 35 250), Biel mit Bözingen, Mett und Madretsch, Thun
mit Strättligen und Goldiwil. Verwendet wird je Einheit die Reihe, die zum Gebiet der Bevölkerung passt
(Spalte `sektor_quelle`): 396-mal Reihe A, 6-mal Reihe A mit den Teilen, 9-mal die einzige vorhandene Reihe,
einmal Reihe B (Kirchlindach: Reihe A ohne 1. Sektor). Wo beide Reihen dieselbe Summe nennen (394 Orte), stimmt
der 3. Sektor als Rest in 392 Fällen mit dem von Reihe B überein; was abweicht, steht in `sektor_pruefung`
(Moutier, Frutigen, Malleray, Tramelan, Büren an der Aare, Aarberg).

**Abgleich mit der BFS-Tabelle.** Verglichen wird die BFS-Gemeinde im Gebietsstand von 2000 gegen die Summe der
Einheiten, die darin liegen. 406 Gemeinden sind vergleichbar; 404 stimmen 1900 und 1910 auf den Kopf überein.
Über 2 % weichen zwei ab:

| Gemeinde | BERNHIST 1900 | BFS 1900 | BERNHIST 1910 | BFS 1910 | Abweichung 1910 | Erklärung |
|---|---:|---:|---:|---:|---:|---|
| Frutigen | 3 996 | 3 996 | 8 386 | 4 832 | +73,6 % | 8 386 = 4 832 + 3 554: BERNHIST zählt Kandersteg 1910 bei Frutigen mit (Kandersteg selbst: 0) |
| Kirchdorf (BE) mit Noflen | 812 | 605 | 813 | 602 | +35,0 % | nicht geklärt; vermutlich ein weiterer Gemeindeteil in BERNHIST |

Beide sind von der Messung ausgeschlossen. Nicht vergleichbar ist Vellerat (die BFS-Gemeinde Courrendlin
enthält Gemeinden, die in BERNHIST fehlen).

## Gemeinden: Grösse oder Erwerbsstruktur?

**Zähler.** Einträge im Telefonbuch je Einheit im besten Jahr 1909–1914: je Gemeinde und Jahr der Band mit den
meisten Einträgen, Einträge mit unsicherem Ort weggelassen, dann das Jahr mit den meisten Einträgen. Das ist die
Regel von `infrastruktur.durchdringung()`; ein einzelnes Jahr wäre für viele Orte zu tief, weil in den
gesamtschweizerischen Bänden 1911–1914 Überschriften fehlen. Für 263 Einheiten ist 1914 das beste Jahr.

**Nenner.** Wohnbevölkerung 1910 der Einheit aus BERNHIST; nicht auf das Jahr des Bands fortgeschrieben.

**Gruppen.** Grössenklassen wie in `infrastruktur.py`, die beiden obersten zusammengelegt (ab 5000 gibt es im
Kanton nur 14 Einheiten). Erwerbsstruktur nach den Anteilen der Sektoren an den Erwerbstätigen 1910, in dieser
Reihenfolge geprüft: Dienstleistung (3. Sektor ab 25 %), bäuerlich (1. Sektor ab 60 %), gewerblich-industriell
(2. Sektor ab 50 %), sonst gemischt. Die Schwellen sind gesetzt, nicht aus den Daten geschätzt; darum steht
daneben die Teilung jeder Grössenklasse am Median des Sektoranteils, die ohne Schwelle auskommt.

**Ausgeschlossen** sind 7 Einheiten: Frutigen, Kirchdorf und Noflen (Bevölkerung weicht von der BFS-Tabelle ab),
Kandergrund, Niederried bei Kallnach und Heiligenschwendi (Erwerbstätige über 60 % der Bevölkerung: Baustellen der
Lötschbergbahn und des Kraftwerks Kallnach, Heilstätte), Roches (33,6 Einträge je 100 Einwohner: ein Lauf des
Bands ist in das Dorf gerutscht). Kandersteg fehlt, weil BERNHIST dafür keine Bevölkerung hat.

## Stadt Bern: Wer hat ein Telefon?

**Bände.** 1885: `P-260-1_Bern_Biel_1885` (484 Einträge der Stadt), 1900: `P-260-1_Bern_1900_2` (2 322; der Band
mit mehr Einträgen von zweien), 1910: `P-260-1_Bern_1910` (4 304). Der Band 1885 hat einen alphabetischen und
einen Branchenteil; dieselbe Person steht darin mehrmals («Wetli, J., Tapezierer» dreimal) und zählt einmal.

**Art des Eintrags** (`art()`): Person, Firma, Amt oder Zusatz («Derselbe, Wohnung»). Ausgangspunkt ist
`entity_type`; berichtigt werden Ämter und Anstalten, die als Firma oder als Person ohne Vornamen gelesen sind
(«Direktion des Gemeindewesens», «Oberfeldarzt, eidg.», «Waldau, Irrenanstalt»), und Firmen, die als Person
gelesen sind («Weibel, Gebr.», «Schweizerhof, Hôtel»). Gezählt werden Anschlussinhaber: eine Person einmal
(Familienname und erster Buchstabe des Vornamens), eine Firma oder ein Amt einmal je Name.

**Frau, Witwe** (`frau()`): nach Stand («Frau», «Frl.», «Wwe.», «Mme»), sonst nach ausgeschriebenem Vornamen oder
Berufsform (Hebamme). «Fr.» ist im Telefonbuch Fritz oder Friedrich und zählt nicht. Viele Vornamen sind
abgekürzt; die Zahl der Frauen ist eine Untergrenze.

**Sektor** (`sektor()`): die Wortlisten von `adressbuecher-bern` (`scripts/85_abdeckung.py`, Commit 8692f31),
unverändert, damit Telefon und Adressbuch dieselben Gruppen messen. Die Einteilung folgt BERNHIST für 1910:
1 = Landwirtschaft, Gärtnerei, Forst; 2 = Gewerbe und Industrie mit Bau-, Nahrungsmittel-, Bekleidungs- und
Reinigungsgewerbe und Druck; 3 = Handel, Banken, Gastgewerbe, Verkehr, Verwaltung, Schule, Kirche, Gesundheit.
Es gilt die erste Angabe; «Privatier» und «alt Oberrichter» zählen als ohne Erwerb. Das Telefonbuch nennt oft
ein Geschäft statt eines Berufs («Comestibles», «Eisenlager», «Graphische Anstalt»); dafür gibt es Ergänzungen
(`TEL_*`), und drei Regeln gelten nur dort: «Wohnung» ist keine Angabe; bei «-handlung» gilt der Handel, auch
wenn die Ware zuerst steht; bei «Direktor der Möbelfabrik» gilt der Betrieb. Bei Firmen entscheidet die erste
Angabe mit Sektor, sonst der Name («Café Ratskeller»), aber nie ein Name aus Familiennamen («Hirter &
Werthmüller» ist kein Müller). Ämter haben keinen Sektor und stehen als eigene Zeile.

**Einzelne Gruppen** (`gruppe()`): Ärzte ohne Zahn- und Tierärzte, einmal nach der Angabe, einmal mit allen, die
«Dr. med.» im Titel führen; Spezereihandlungen; für 1910 drei Branchen, für die BERNHIST Erwerbstätige nennt
(Gastgewerbe, Nahrungs- und Genussmittel, Druck). Bei den Branchen stehen Betriebe gegen Beschäftigte: Die Zahl
sagt, wie viele Anschlüsse auf 100 Erwerbstätige kommen, nicht welcher Teil der Betriebe ein Telefon hat.

**Nenner.** Dieselbe Herleitung wie in `adressbuecher-bern` (`nenner()`): Bevölkerung 1885 linear zwischen den
Volkszählungen 1880 und 1888; Haushalte = Bevölkerung durch die Haushaltsgrösse von 1888 (4,63); Erwerbstätige
= Bevölkerung mal Erwerbsquote, zwischen 1856 und 1910 interpoliert; Sektoren = Erwerbstätige mal Anteil des
Sektors 1910; Witwen = Verwitwete mal Frauenanteil der Verwitweten 1846 (75 %); Ärzte linear zwischen 1856 (47)
und 1910 (116). Für 1910 sind Bevölkerung, Erwerbstätige, Sektoren, Ärzte und Verwitwete gezählt, nicht
geschätzt. Jede Zeile von `durchdringung_bern_stadt.csv` nennt Art und Herleitung des Nenners.

Ein Unterschied zu `adressbuecher-bern`: Dort sind die Erwerbstätigen 1910 die der Reihe B (37 247, mit
Bümpliz), hier die der Stadt im Gebiet von 1910 (35 250). Die Anteile der Sektoren sind damit 1,9 %, 49,0 % und
49,1 % statt 2,8 %, 49,4 % und 47,8 %. In der Tabelle «Telefon neben Adressbuch» stehen die Adressbuchquoten so,
wie `adressbuecher-bern` sie ausweist; vergleichbar ohne diesen Unterschied ist die Spalte «Telefon je 100 im
Adressbuch», die keinen Nenner aus BERNHIST braucht.

**Verknüpfte Personen.** Die dritte Tabelle zählt Personen im Einwohnerverzeichnis 1883–84 und 1900, die über
`links/ptt_ab.csv` (Stufen `sicher` und `wahrscheinlich`) in einem Telefonbuch der Jahre 1884–1886 oder 1900–1901
stehen. Gruppen nach der Berufsangabe des Adressbuchs, mit derselben Regel.

**Stichproben.** Je 60 Einträge (20 je Jahr), zufällig mit festem Startwert gezogen, beurteilt nach Art des
Eintrags, Frau/Witwe und Sektor (`data/review/durchdringung_bern_stichprobe*.csv`). Wie in `docs/verknuepfung.md`
sind die Regeln nach den ersten beiden Stichproben angepasst worden; die dritte ist danach gezogen und seither
unverändert und gibt die gültige Trefferquote: 56 von 60 ganz richtig (93,3 %), Art 57, Frau/Witwe 60, Sektor 56.
Die vier Fehler: drei Anstalten und Amtsstellen, die als Person oder Firma zählen (städtische Lehrwerkstätten,
ein Institut der Universität, eine Inspektion des Bundes), und «Sohn, Fabrikant» als ohne Erwerb. «Unbestimmt»
und leer gelten beide als «kein Sektor erkennbar». Beurteilt hat Claude, nicht eine zweite Person, und geprüft
ist die Zuordnung der gelesenen Angabe, nicht die Lesung selbst.

## Ergebnis

<!-- TABELLEN:START -->
Stand der Daten: `data/norm/ptt_entries.csv.gz` mit 659 296 Einträgen, davon 67 314 im Kanton Bern 1909–1914.

**Gemeinden um 1910: Grössenklasse**

| Einwohner 1910 | Einheiten | mit Telefon | Einwohner | Einträge | Einträge je 100 Einw. | Median der Einheiten |
|---|---:|---:|---:|---:|---:|---:|
| 0–499 | 161 | 146 (91 %) | 46 995 | 364 | 0,77 | 0,56 |
| 500–999 | 99 | 95 (96 %) | 71 177 | 706 | 0,99 | 0,57 |
| 1000–1999 | 73 | 71 (97 %) | 103 092 | 1 112 | 1,1 | 0,73 |
| 2000–4999 | 58 | 58 (100 %) | 158 999 | 2 388 | 1,5 | 1,1 |
| ab 5000 | 14 | 14 (100 %) | 193 878 | 9 207 | 4,8 | 1,7 |
| alle | 405 | 384 (95 %) | 574 141 | 13 777 | 2,4 | 0,65 |

Ab 5000 Einwohnern ohne die Stadt Bern: 13 Einheiten, 2,6 Einträge je 100 Einwohner (Median 1,5).

**Gemeinden um 1910: Erwerbsstruktur**

| Erwerbsstruktur 1910 | Einheiten | mit Telefon | Einwohner | Einträge je 100 Einw. | Median der Einheiten |
|---|---:|---:|---:|---:|---:|
| bäuerlich (1. Sektor ab 60 %) | 170 | 157 (92 %) | 122 109 | 0,62 | 0,44 |
| gemischt | 124 | 119 (96 %) | 137 497 | 0,97 | 0,67 |
| gewerblich-industriell (2. Sektor ab 50 %) | 66 | 63 (95 %) | 101 739 | 1,2 | 0,80 |
| Dienstleistung (3. Sektor ab 25 %) | 45 | 45 (100 %) | 212 796 | 4,9 | 2,1 |

**Grösse × Erwerbsstruktur: Median der Einträge je 100 Einwohner (Zahl der Einheiten); in Klammern nichts, wenn weniger als 5**

| Einwohner 1910 | bäuerlich | gemischt | gewerblich-industriell | Dienstleistung |
|---|---:|---:|---:|---:|
| 0–499 | 0,47 (93) | 0,65 (48) | 0,50 (15) | 0,35 (5) |
| 500–999 | 0,47 (41) | 0,54 (36) | 0,74 (15) | 1,8 (7) |
| 1000–1999 | 0,28 (22) | 0,67 (19) | 0,75 (21) | 2,5 (11) |
| 2000–4999 | 0,40 (13) | 0,94 (18) | 1,1 (11) | 1,8 (16) |
| ab 5000 | – (1) | – (3) | – (4) | 4,0 (6) |

**Grösse × Erwerbsstruktur: Einträge je 100 Einwohner, alle Einheiten der Zelle zusammen**

| Einwohner 1910 | bäuerlich | gemischt | gewerblich-industriell | Dienstleistung |
|---|---:|---:|---:|---:|
| 0–499 | 0,65 | 0,98 | 0,56 | 1,1 |
| 500–999 | 0,77 | 0,69 | 1,5 | 2,6 |
| 1000–1999 | 0,59 | 0,81 | 1,0 | 2,6 |
| 2000–4999 | 0,47 | 1,0 | 1,2 | 2,9 |
| ab 5000 | – | – | – | 6,0 |

**Innerhalb der Grössenklasse: Hälfte unter und ab dem Median des Sektoranteils (Einträge je 100 Einwohner, zusammen / Median)**

| Einwohner 1910 | 3. Sektor: Median | darunter | ab Median | 1. Sektor: Median | darunter | ab Median |
|---|---:|---:|---:|---:|---:|---:|
| 0–499 | 8,3 % | 0,63 / 0,46 | 0,89 / 0,65 | 64,7 % | 0,84 / 0,64 | 0,68 / 0,47 |
| 500–999 | 11,6 % | 0,78 / 0,47 | 1,2 / 0,76 | 52,7 % | 1,2 / 0,70 | 0,73 / 0,45 |
| 1000–1999 | 12,2 % | 0,59 / 0,44 | 1,6 / 1,2 | 41,5 % | 1,4 / 0,92 | 0,73 / 0,49 |
| 2000–4999 | 13,4 % | 0,65 / 0,64 | 2,2 / 1,6 | 41,5 % | 2,1 / 1,4 | 0,84 / 0,65 |
| ab 5000 | 21,7 % | 1,2 / 1,1 | 5,8 / 3,8 | 16,1 % | 5,8 / 3,8 | 1,3 / 1,1 |

**Rangkorrelation (Spearman) der Einträge je 100 Einwohner mit Grösse und Sektoranteilen**

| Einwohner 1910 | Einwohner | 1. Sektor | 2. Sektor | 3. Sektor |
|---|---:|---:|---:|---:|
| 0–499 | -0,11 | -0,07 | 0,08 | 0,12 |
| 500–999 | 0,28 | -0,36 | 0,30 | 0,41 |
| 1000–1999 | 0,11 | -0,43 | 0,25 | 0,65 |
| 2000–4999 | 0,31 | -0,65 | 0,32 | 0,85 |
| ab 5000 | 0,82 | -0,64 | 0,07 | 0,87 |
| alle | 0,27 | -0,40 | 0,29 | 0,46 |

**Stadt Bern: Telefon nach Gruppen**

| Gruppe | 1885: Buch | Nenner | Quote | 1900: Buch | Nenner | Quote | 1910: Buch | Nenner | Quote |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Einträge im Telefonbuch | 484 | 44 954 | 1,1 % | 2 322 | 64 227 | 3,6 % | 4 304 | 85 651 | 5,0 % |
| Personen mit Eintrag je Einwohner | 151 | 44 954 | 0,34 % | 1 227 | 64 227 | 1,9 % | 2 269 | 85 651 | 2,6 % |
| Personen mit Eintrag je Haushalt | 151 | 9 703 | 1,6 % | 1 227 | 13 863 | 8,9 % | 2 269 | 18 488 | 12,3 % |
| Personen mit Wohnungsanschluss | 4 | 9 703 | 0,04 % | 159 | 13 863 | 1,1 % | 361 | 18 488 | 2,0 % |
| Firmen | 76 | – | – | 400 | – | – | 768 | – | – |
| Ämter und Anstalten | 45 | – | – | 348 | – | – | 405 | – | – |
| Frauen | 3 | 24 718 | 0,01 % | 106 | 35 316 | 0,30 % | 265 | 47 099 | 0,56 % |
| Witwen | 1 | 2 097 | 0,05 % | 35 | 2 721 | 1,3 % | 71 | 3 384 | 2,1 % |
| Fräulein | 0 | – | – | 15 | – | – | 49 | – | – |
| Personen und Firmen mit Sektor je Erwerbstätige | 191 | 19 171 | 1,0 % | 1 330 | 26 816 | 5,0 % | 2 460 | 35 250 | 7,0 % |
| 1. Sektor | 2 | 368 | 0,54 % | 17 | 514 | 3,3 % | 21 | 676 | 3,1 % |
| 2. Sektor | 57 | 9 396 | 0,61 % | 433 | 13 143 | 3,3 % | 778 | 17 277 | 4,5 % |
| 3. Sektor | 132 | 9 407 | 1,4 % | 880 | 13 158 | 6,7 % | 1 661 | 17 297 | 9,6 % |
| ohne Erwerb (Privatier, Rentier) | 1 | – | – | 22 | – | – | 33 | – | – |
| Angabe ohne Sektor | 16 | – | – | 92 | – | – | 161 | – | – |
| keine Angabe (nur Name, «Wohnung») | 19 | – | – | 183 | – | – | 383 | – | – |
| Ärzte (Angabe nennt «Arzt») | 11 | 84 | 13,1 % | 3 | 103 | 2,9 % | 31 | 116 | 26,7 % |
| Ärzte (dazu Titel «Dr. med.») | 11 | 84 | 13,1 % | 58 | 103 | 56,2 % | 96 | 116 | 82,8 % |
| verschiedene Rufnummern | – | – | – | 1 785 | 64 227 | 2,8 % | 3 464 | 85 651 | 4,0 % |
| Spezereihandlungen | – | – | – | 35 | 243 | 14,4 % | 52 | 289 | 18,0 % |
| Gastgewerbe: Anschlüsse je 100 Erwerbstätige | – | – | – | – | – | – | 238 | 2 441 | 9,8 % |
| Nahrungs- und Genussmittel: Anschlüsse je 100 Erwerbstätige | – | – | – | – | – | – | 235 | 1 804 | 13,0 % |
| Druck und Buchbinderei: Anschlüsse je 100 Erwerbstätige | – | – | – | – | – | – | 101 | 1 284 | 7,9 % |

**Stadt Bern: Telefon neben Adressbuch**

| Gruppe | Adressbuch 1883–84 | Quote | Telefon 1885 | Quote | Telefon je 100 im Adressbuch | Adressbuch 1900 | Quote | Telefon 1900 | Quote | Telefon je 100 im Adressbuch |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Personen je Einwohner | 7 969 | 18,0 % | 151 | 0,34 % | 1,9 | 14 184 | 22,1 % | 1 227 | 1,9 % | 8,7 |
| Personen je Haushalt | 7 969 | 83,4 % | 151 | 1,6 % | 1,9 | 14 184 | 102,3 % | 1 227 | 8,9 % | 8,7 |
| Firmen | 151 | – | 76 | – | 50,3 | 262 | – | 400 | – | 152,7 |
| Frauen | 1 611 | 6,6 % | 3 | 0,01 % | 0,20 | 3 189 | 9,0 % | 106 | 0,30 % | 3,3 |
| Witwen | 425 | 20,3 % | 1 | 0,05 % | 0,20 | 1 217 | 44,7 % | 35 | 1,3 % | 2,9 |
| 1. Sektor | 118 | 21,4 % | 2 | 0,54 % | 1,7 | 218 | 27,5 % | 17 | 3,3 % | 7,8 |
| 2. Sektor | 2 954 | 30,8 % | 57 | 0,61 % | 1,9 | 5 132 | 37,1 % | 433 | 3,3 % | 8,4 |
| 3. Sektor | 3 493 | 37,6 % | 132 | 1,4 % | 3,8 | 6 651 | 49,6 % | 880 | 6,7 % | 13,2 |
| Ärzte (mit Titel «Dr. med.») | 51 | 62,6 % | 11 | 13,1 % | 21,6 | 121 | 117,2 % | 58 | 56,2 % | 47,9 |
| Spezereihandlungen | 119 | 71,1 % | – | – | – | 215 | 88,5 % | 35 | 14,4 % | 16,3 |

**Stadt Bern: Personen des Adressbuchs mit Telefon (über die Verknüpfung, Stufen sicher und wahrscheinlich)**

| Gruppe | 1883–84: Personen | mit Telefon 1884–86 | Anteil | 1900: Personen | mit Telefon 1900–01 | Anteil |
|---|---:|---:|---:|---:|---:|---:|
| Personen im Einwohnerverzeichnis | 7 681 | 111 | 1,4 % | 13 987 | 941 | 6,7 % |
| 1. Sektor | 118 | 0 | 0,00 % | 218 | 13 | 6,0 % |
| 2. Sektor | 2 862 | 28 | 0,98 % | 4 897 | 281 | 5,7 % |
| 3. Sektor | 3 259 | 64 | 2,0 % | 6 228 | 523 | 8,4 % |
| ohne Erwerb (Privatier, Rentier) | 366 | 3 | 0,82 % | 785 | 37 | 4,7 % |
| Angabe ohne Sektor | 208 | 6 | 2,9 % | 357 | 40 | 11,2 % |
| keine Angabe | 868 | 10 | 1,2 % | 1 502 | 47 | 3,1 % |
| Frauen | 1 600 | 10 | 0,62 % | 3 142 | 81 | 2,6 % |
| Witwen | 426 | 6 | 1,4 % | 1 219 | 45 | 3,7 % |
| Ärzte (mit Titel «Dr. med.») | 50 | 7 | 14,0 % | 121 | 55 | 45,5 % |
| Spezereihandlungen | 53 | 5 | 9,4 % | 134 | 34 | 25,4 % |

**Stichproben zur Zuordnung (Art des Eintrags, Frau/Witwe, Sektor)**

| Stichprobe | Einträge | Art richtig | Frau/Witwe richtig | Sektor richtig | alle drei | Quote |
|---|---:|---:|---:|---:|---:|---:|
| 1, mit den Regeln beim Ziehen | 60 | 56 | 60 | 53 | 52 | 86,7 % |
| 2, mit den Regeln beim Ziehen | 60 | 53 | 58 | 49 | 45 | 75,0 % |
| 3, mit den Regeln beim Ziehen (gültige Messung) | 60 | 57 | 60 | 56 | 56 | 93,3 % |
| 1, mit den heutigen Regeln | 60 | 59 | 60 | 59 | 59 | 98,3 % |
| 2, mit den heutigen Regeln | 60 | 59 | 60 | 56 | 55 | 91,7 % |
| 3, mit den heutigen Regeln | 60 | 57 | 60 | 56 | 56 | 93,3 % |
<!-- TABELLEN:ENDE -->

Lesehilfe: «Buch» ist die Zahl der Anschlussinhaber im Band, «Nenner» der Wert aus BERNHIST für das Jahr,
«Quote» der Anteil in Prozent. «Zusammen / Median» nennt zuerst die Einträge aller Einheiten der Gruppe geteilt
durch ihre Einwohner, dann den Median der Einheiten; der Median ist die robustere Zahl, weil ein falsch
verorteter Lauf eines Bands die Summe verzerrt.

## Grenzen

- **Einträge, nicht Anschlüsse und nicht Haushalte.** Ein Eintrag ist eine Zeile im Buch. Ein Anschluss kann
  mehrere Zeilen haben (Geschäft und Wohnung), ein Amt viele Anschlüsse. In der Stadt Bern sind 1910 4 304
  Einträge 3 464 verschiedene Nummern und 3 442 Inhaber.
- **Ortszuordnung.** Die Dichte kleiner Gemeinden ruht auf einer Handvoll Einträgen; ein falsch verorteter Lauf
  hebt sie sofort (Roches, ausgeschlossen; Pohlern mit 24 Einträgen bei 229 Einwohnern ist nicht ausgeschlossen
  und vermutlich ebenfalls falsch). Darum steht überall der Median. Die Bände 1911–1914 werden laufend neu
  gelesen; die Zahlen gelten für den Stand der Daten, der über der Tabelle steht.
- **Bevölkerung 1910, Einträge bis 1914.** Für wachsende Orte ist die Dichte damit etwas zu hoch (Bern 1914:
  7,4 je 100 Einwohner von 1910; mit der Bevölkerung von 1914 wären es rund 7,0).
- **Erwerbsstruktur.** Der 3. Sektor ist bis auf 9 Einheiten der Rest aus Summe, 1. und 2. Sektor. Wo eine
  Reihe lückenhaft ist, ist der Rest falsch; geprüft ist das nur dort, wo Reihe B dasselbe Gebiet meint. Die
  Erwerbstätigen sind Wohnbevölkerung: Hotelpersonal der Saison (Zählung am 1. Dezember) fehlt, Bauarbeiter der
  Lötschbergbahn zählen mit.
- **Zusammenhang, keine Ursache.** Der 3. Sektor umfasst genau die Betriebe, die ein Telefon brauchen (Handel,
  Gasthöfe, Post, Verwaltung), und ein Teil der Einträge sind diese Betriebe selbst. Gemessen ist, wo das
  Telefon steht, nicht warum.
- **Stadt Bern: Nenner vor 1910 geschätzt.** Die Berufsstruktur gibt es nur für 1856 und 1910. Die Quoten für
  1885 überbrücken 25 bis 29 Jahre; ihr Verhältnis untereinander (3. gegen 2. Sektor) trägt, ihre Höhe nicht.
- **Ämter.** `AMT` trifft auch die Kantonalbank und die Eidgenössische Bank (rund ein Dutzend Einträge); sie
  zählen als Amt statt als Firma im 3. Sektor. Umgekehrt bleiben einzelne Anstalten Firmen (Stichprobe 3).
- **Sektor der Personen.** 383 von 3 037 Personen und Firmen haben 1910 keine Angabe (nur Name oder «Wohnung»),
  161 eine ohne Sektor. Diese 18 % fehlen im Zähler der Sektoren; die Quoten sind Untergrenzen.
- **Ärzte 1900.** Der Band 1900 nennt den Beruf selten («Dr. med.» steht im Titel); die Zeile «Angabe nennt
  Arzt» ist dort nicht zu gebrauchen. Woher BERNHIST die Zahl der Ärzte nimmt, ist nicht bekannt.
- **Verknüpfung.** Die dritte Tabelle ist eine Untergrenze: Nicht jede Person wird wiedergefunden, und die Stufe
  `wahrscheinlich` war in der Berner Stichprobe zu 7 von 10 richtig (`docs/verknuepfung.md`).
- **Was sich nicht messen liess.** Selbständige (BERNHIST nennt sie 1856 und 1930, das Telefonbuch die Stellung
  im Beruf nicht), Burger und Einsassen (im Telefonbuch nicht genannt), Dienstboten und Taglöhner (keine
  Einträge), die Stadt Bern 1881–1884 und 1886–1899 (kein Nenner in der Nähe und nur drei Stichjahre gerechnet),
  der Nordjura (nicht in BERNHIST), Kandersteg (keine Bevölkerung in BERNHIST).
- **Rechte.** Die Nutzungsrechte an BERNHIST sind nicht ausgewiesen. `data/ref/bernhist/` enthält nur die
  verwendeten Werte mit Ort, Thema, Jahr und Nummer im Dump und steht nicht unter der CC0-Freigabe von `data/`
  (`data/ref/bernhist/README.md`).

## Auf der Seite

Unter «Infrastruktur» (`#/infrastruktur`, Abschnitt «Kanton Bern: Grösse oder Erwerbsstruktur?») stehen die
Kreuztabelle Grösse × Erwerbsstruktur (Median, Zahl der Einheiten) und die Stadt Bern nach Gruppen, mit Verweis
auf diesen Bericht. `python scripts/durchdringung_bern.py site` schreibt dafür
`site/data/durchdringung_bern.json.gz` aus den abgelegten Ergebnissen; der Pages-Lauf rechnet nichts neu.
Zeichenketten: `inf_be_*` in `site/i18n/de.json`, `fr.json` und `en.json`. Fehlt die Datei, fällt der Abschnitt weg.

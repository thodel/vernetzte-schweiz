# Wanderungen (M10, experimentell)

Wer verschwindet an einem Ort aus Telefon- und Adressbuch und taucht kurz danach an einem
anderen zum ersten Mal auf? `scripts/migration.py` sucht solche Paare. Die Seite zeigt sie
unter `#/karten?v=wanderungen`. Es sind **Kandidaten**, keine geprüften Umzüge.

```bash
make wanderungen   # links/migration.csv, data/norm/migration_stats.json
python scripts/migration.py site   # site/data/wanderungen.json.gz (läuft im Pages-Workflow)
make check-wanderungen   # sind alle Daten drin? (scripts/check_migration.py --upstream)
```

### Sind alle Daten drin?

Jeder Lauf von `migration.py` schreibt einen Stempel, `data/norm/migration_inputs.json`: je Eingabe
(Einheiten, Einträge beider Quellen, Normdaten, HLS-Kandidaten und die Skripte mit den Regeln) eine
Prüfsumme über den Inhalt und je Gemeinde die Jahrgänge mit der Zahl der Einträge.
`scripts/check_migration.py` vergleicht den Stand damit und nennt, was seit dem letzten Lauf neu ist
(Gemeinden, Jahrgänge, geänderte Dateien), dazu Einheiten in `links/migration.csv`, die es nicht mehr
gibt. `--update` rechnet dann neu. `--upstream` schaut eine Stufe weiter vorn: ob die Quell-Repos in
`config/sources.toml` seit dem gepinnten Commit eine übernommene Datei geändert haben; neue Bände
kommen über `commit` neu setzen und `make ingest link entities` in die Einheiten, dann mit
`--update` in die Wanderungen. Der Pages-Workflow ruft `--ci` auf: veraltet heisst dort neu rechnen
(die Seite zeigt so immer alle Daten) und eine Warnung im Lauf, `links/migration.csv` nachzuführen.

## Ausgangslage

Die Bündelung (M3, [einheiten.md](einheiten.md)) arbeitet je Gemeinde: Wer umzieht, wird
zu zwei Einheiten. Hier werden die zwei Einheiten wieder zusammengeführt, aber nur als
Hinweis. Die Bündelung selbst ändert sich nicht.

## Regeln

Gesucht sind Paare aus einer Einheit **A** (alter Ort, letztes Jahr *t*) und einer Einheit
**B** (neuer Ort, erstes Jahr *t'*):

- Beide sind Personen. Ausgenommen sind Witwen und Einträge mit «Frau», «Mme» usw., weil
  der Vorname dort oft der des Mannes ist. Ausgenommen sind auch Firmen, Ämter und
  Institutionen, die als Person zerlegt wurden («les fils de …», «Richteramt, Schloss»,
  «Kloster St. Scholastika», «Eilboten-Institut», «Eredi fu Giovanni»). Sie verlegen den Sitz,
  das ist eine andere Frage.
- Gleicher Familienname (Namensschlüssel wie in M2).
- *t* < *t'* ≤ *t* + 6.
- Verträglicher Vorname, mindestens als Abkürzung («Friedr.» = «Friedrich»). Nur eine
  Initiale genügt nie. Haben beide Seiten zwei ausgeschriebene Vornamen, müssen sie
  übereinstimmen: «Karl Friedrich» ≠ «Karl Johann».
- Verschiedene Allianznamen widersprechen («Spörry-Streiff» ≠ «Spœrri-Duport»). Verglichen
  werden die ersten fünf Buchstaben, so ist «Tröndli» = «Tröndle».
- Verschiedenes Geschlecht widerspricht («Jos. Anton» ≠ «Maria Josepha»). Das Geschlecht
  kommt aus dem ersten ausgeschriebenen Vornamen (Listen in `migration.py`), sonst aus der
  Berufsform («Lehrerin», «couturière»), «geb.» oder «Witwe».
- Verschiedene Geburtsnamen zweier Frauen widersprechen. Bei einer Frau ist der Allianzname
  der Geburtsname («Wächter-Lindenmann» ≠ «geb. Sandmeier»). Steht B als «geb. X» und A
  früher als Dienstmagd, Köchin, Lehrerin, Glätterin … unter dem eigenen Familiennamen,
  war A ledig und hiess von Geburt so; B ist dann eine andere Frau («Streit, Anna, dom.»
  ≠ «Anna geb. Wyss»).
- **Gegenbelege:**
  - Am alten Ort beginnt nach *t* eine verträgliche Einheit. Dann ist A nicht verschwunden,
    die Bündelung hat nur getrennt (17 962 Fälle).
  - Am neuen Ort gab es vor *t'* schon eine verträgliche Einheit (35 454 Fälle).
- **Eindeutigkeit:** A hat genau einen solchen Nachfolger, und B hat genau einen Vorgänger.
  23 037 Paare fallen hier weg.

### Punkte und Stufen

| Beleg | Punkte |
|---|---|
| Vorname ausgeschrieben gleich | 2 |
| Vorname als Abkürzung | 1 |
| Beruf mit gleichem Wortstamm, anders formuliert | 2 |
| Beruf mit gleichem Wortlaut (meist dieselbe Zeile, nicht derselbe Mensch anderswo); ohne neue Nummer oder Adresse höchstens `schwach` | 1 |
| derselbe Beruf in der feinen Liste, anders geschrieben («Charcuterie» = «Metzger», «tapissier» = «Tapezierer») | 2 |
| derselbe allgemeine Beruf (Commis, Kaufmann, Handlanger, Privat …) | 1 |
| verwandter Beruf (Bäcker ↔ Konditor, Fürsprecher ↔ Richter, Wirt ↔ Hotel) | 1 |
| verschiedene Berufe in der feinen Liste (Metzger ≠ Bäcker), auch bei gleichem Wort | −2 |
| sonst, wenn eine Seite keinen Beruf der feinen Liste hat: gleiche Berufsklasse ([occupations.py](../scripts/occupations.py)) | 1 |
| … verschiedene Berufsklassen | −2 |
| gleicher Titel (Dr., Prof., Ing. …) | 1 |
| gleicher Allianzname | 1 |
| neue Rufnummer (beide Seiten haben eine) | 1 |
| neue Adresse (beide Seiten haben eine) | 1 |
| Familienname mit höchstens 10 Personen-Einheiten in der Schweiz | 2 |
| Familienname mit höchstens 40 Personen-Einheiten | 1 |

| Stufe | Bedingung |
|---|---|
| `stark` | ≥ 6 Punkte, ein Beleg aus Beruf, Titel oder Allianzname, **und** neue Nummer oder Adresse |
| `mittel` | ≥ 4 Punkte und ein Beleg aus Beruf, Titel oder Allianzname |
| `schwach` | ≥ 4 Punkte, ohne solchen Beleg, aber mit neuer Nummer oder Adresse |

Die **feine Berufsliste** ([occupations_fine.py](../scripts/occupations_fine.py), seit Messung 3)
führt 129 Berufe deutsch, französisch und italienisch mit Abkürzungen, jeder mit einer
Gruppe verwandter Berufe. Die Berufsklassen der Karten sind zu grob, um Personen zu trennen:
«Metzger» und «Bäcker» stehen beide unter Lebensmittel, «cordonnier» und «Küfer» beide unter
Handwerk. Vor dem Vergleich werden Strassen aus dem Berufsfeld entfernt («Zinngiesserei,
Schneiderg. 30» ist kein Schneider) und Nachbarzeilen abgeschnitten, die die Zerlegung im
Berufsfeld gelassen hat («archit.-métreur; av. de Lancy; 15 Fontana; Léon-P; architecte»).

Wer umzieht, bekommt eine neue Nummer und eine neue Adresse. Gleicher Wortlaut ist dagegen
meist dieselbe Zeile unter einem anderen Ort (Messung 1, unten).

## Fehler der Ortszuweisung

Der erste Lauf ergab 1 598 Paare. Die meisten waren keine Umzüge, sondern dieselbe Zeile
unter einem anderen Ort. Das sind die Fehler aus M1: Charge B überträgt die Ortsüberschrift.
Ein Beispiel ist Lausanne 1911–1914 unter «Genève», mit 321 Paaren und Strassen wie
«r. Pépinet» und «Lion d'Or» am neuen Ort. Darum gelten folgende Paare als Fehler und fallen
weg. Die Gründe stehen je Paar in `data/norm/migration_dropped.csv.gz`.

| Grund | Paare |
|---|---|
| dieselbe Rufnummer an beiden Orten, auch die im Adressbuch gedruckte («T 535») | 1 034 |
| um die erste Zeile von B stehen mindestens zwei weitere Einträge, die ebenfalls vom Ort A «gekommen» wären (der ganze Lauf gehört zu A; Nachbarn mit demselben Familiennamen zählen nicht) | 328 |
| die Ortsnamen beginnen gleich und liegen mindestens 5 km auseinander («Fleurier» → «Finhaut», «Altstätten» → «Alt St. Johann»: Nachbarn im Alphabet des Telefonbuchs) | 168 |
| ein Orts- oder Strassenwort des alten Eintrags steht im neuen («Direktor, auf Robersten» unter Brügg, «voiturier, Unterseen» unter Interlaken), oder der neue Ort heisst wie die alte Adresse («Oberdorf» → Oberdorf (SO), «Liesbergmühle» → Liesberg, «Bertigny» → Burtigny). Die Wörter stammen nur aus der Strasse und dem Zusatz nach dem ersten Glied, das meist der Beruf ist | 159 |
| vierstellige Stadtnummer an einem Ort mehr als 15 km vom nächsten Stadtnetz («36.86» unter Prez-vers-Siviriez); Vororte wie Versoix oder Renens liegen im Netz der Stadt | 78 |
| ortsfester Betrieb oder Posten auf beiden Seiten (Gasthaus, Mühle, Villa, Postablage, Sindaco, Richter …) mit gleichem Wortlaut oder gleichem Eigenwort («Löwenburg», «Ochsen») | 48 |
| B steht an einer Strasse, die es am Ort A gibt und an seinem eigenen Ort kaum | 48 |
| eine solche Strasse steht im Zusatz von B («boulanger, r. des Deux-Marchés», «past., Valentin») | 18 |
| Strassenangabe in der Sprache des alten Orts («Via alla Stazione» unter Luzern) | 8 |
| gleiche Adresse | 9 |

Ein Paar zählt beim ersten zutreffenden Grund in der Reihenfolge des Codes; die Zahlen der späteren Gründe sanken darum mit der Regel «Ortswort».

Übrig bleiben **313 Paare**: 42 `stark`, 149 `mittel`, 122 `schwach` (mit 129 Berufen in der feinen Liste: Glaser, Viehhändler, Graveur, Färber eigene Berufe, «arbeiter», «commis», «privat» nur als eigenes Wort; davor 41, 149, 123; vor dem Vergleich von Geschlecht und Geburtsname 319: 42, 154, 123; vor der Regel «Ortswort» und der Grenze für gleichen Wortlaut 332: 43, 193, 96; vor der feinen Berufsliste 339: 33, 172, 134).

## Was «verschwunden» und «neu» heissen

- Die Telefonbücher nennen nur Abonnenten. «Neu im Buch» heisst oft «neu ein Telefon»,
  «nicht mehr im Buch» oft «kein Telefon mehr». Ein Paar ist erst dann ein Hinweis auf
  einen Umzug, wenn dieselbe Person am einen Ort aufhört und am anderen beginnt.
- Vor 1911 liegen nur einzelne Ausgaben vor (Charge A). Darum häufen sich die Paare
  1911–1914, rund die Hälfte.
- Ob A wirklich verschwand, lässt sich nur sagen, wenn der alte Ort nach *t* noch einmal
  mit mindestens halb so vielen Einträgen vorliegt (Spalte `left_seen`). Ob B wirklich neu
  ist, nur wenn der neue Ort vor *t'* so vorliegt (`new_seen`). Beides trifft auf 89 Paare
  zu. Die Seite kann auf sie einschränken.
- Nachbarorte unter 5 km sind oft dieselbe Adresse unter anderem Ortsnamen
  (Lugano/Massagno, Locarno/Muralto). Die Seite blendet sie anfangs aus.

## Ergebnis

`links/migration.csv`, eine Zeile je Paar:

| Spalte | Inhalt |
|---|---|
| `from_entity`, `to_entity` | Einheit am alten und am neuen Ort (M3) |
| `surname`, `forename_from`, `forename_to` | Name, wie die Einheiten ihn führen |
| `from_muni`, `to_muni` | Gemeinde 1914 |
| `from_last`, `to_first`, `gap` | letztes Jahr alt, erstes Jahr neu, Abstand |
| `km` | Luftlinie zwischen den Gemeindemittelpunkten |
| `occ_from`, `occ_to`, `class` | Berufe und gemeinsame Berufsklasse |
| `evidence`, `score`, `tier` | Belege, Punkte, Stufe |
| `left_seen`, `new_seen` | alter bzw. neuer Ort danach bzw. davor belegt (0/1) |
| `n_surname` | Personen-Einheiten mit diesem Familiennamen in der Schweiz |

## Die Ansicht

Die Ansicht liegt unter `#/wanderungen?a=…&b=…&t=0|1|2&c=…&d=linien|saldo&n=ohne|mit&g=alle|ja`.
Die frühere Adresse `#/karten?v=wanderungen` leitet dorthin weiter.

- **Linien:** Bögen vom alten zum neuen Ort, Breite nach Zahl der Paare. Ein blauer Punkt
  steht am Ausgangsort, ein roter am Ziel; die Fläche zählt die Weg- bzw. Zuzüge.
- **Saldo:** je Ort ein Kreis nach Zu- plus Wegzügen, grün bei mehr Zuzügen, rot bei mehr
  Wegzügen.
- **Klicken öffnet einen neuen Tab**, mit denselben Filtern und einem Ort dazu:
  - eine Linie → die Fälle dieses Ortspaars (`vo=<alter Ort>&na=<neuer Ort>`);
  - ein blauer Punkt → alle Wegzüge von dort (`vo=`);
  - ein roter Punkt → alle Zuzüge dorthin (`na=`);
  - ein Kreis der Saldo-Ansicht → Zu- und Wegzüge des Orts (`ort=`).

  Ist ein Ort gewählt, zählen auch Nachbarorte unter 5 km. Oben steht, welcher Ort gilt,
  mit Links auf die Gemeinde und «alle Orte zeigen».
- **Seitenleiste:**
  - Zahl nach Berufsklasse mit Median der Entfernung;
  - Verteilung der Entfernungen und erstes Jahr am neuen Ort;
  - häufigste Ortspaare;
  - Fälle mit Links auf beide Einheiten, dazu Normdaten (Wikidata, HLS, GND, Elites suisses)
    und HLS-Kandidaten, wo eine Seite welche hat.

## Normdaten

Normdaten (`links/authority.csv`, [einheiten.md](einheiten.md)) gehören zu einer Einheit,
also zu einem Ort. Ist ein Paar richtig, gelten sie für beide Seiten. Deshalb:

- **Als Beleg:** Haben beide Seiten eine Wikidata-Kennung, zählt dieselbe 2 Punkte
  (`normdaten:gleich`) und eine verschiedene schliesst das Paar aus. Dasselbe gilt für
  verschiedene HLS-Artikel. Ein gemeinsamer HLS-Kandidat aus der umgekehrten Prüfung (M9,
  Stufen «wahrscheinlich» und «möglich») zählt 1 Punkt (`hls:gleich`).
- **Mitgenommen:** `links/migration.csv` führt die Normdaten der Seite, die welche hat (QID,
  Bezeichnung, HLS, GND, Stufe, `auth_side` = `von`, `nach` oder `beide`), und die
  HLS-Kandidaten beider Seiten. Die Seite einer Einheit zeigt unter «Wanderung (Versuch)»
  das Gegenstück, und ob die Normdaten von dieser oder der anderen Einheit kommen. Der Link
  zu den Elites suisses ([elites_suisses.md](elites_suisses.md)) kommt über die QID mit.
- **Umfang** (14.11.2026): 2 der 313 Paare haben Normdaten auf einer Seite (Siordet, Straub),
  5 einen HLS-Kandidaten; keines hat Normdaten auf beiden Seiten. Die Stufen ändern sich
  dadurch nicht. Normdaten gibt es vor allem in Aarau und Basel (Adressbücher) und für
  Personen des HLS. Die Wanderungen finden vor allem Telefonbuch-Paare.
- Mitgenommene Normdaten sind so sicher wie das Paar **und** wie die Normdaten selbst.

## Messung

Beurteilt hat Claude, nicht die Projektmitarbeitenden (`scripts/measure_migration.py`).
Grundlage waren die letzten zwei Einträge am alten und die ersten zwei am neuen Ort, wie
gedruckt.
- `richtig`: dieselbe Person an einem anderen Wohn- oder Geschäftsort.
- `falsch`: eine andere Person, dieselbe Zeile unter einem falschen Ort, oder eine Firma.
- `unklar`: meist ein Berufswechsel ohne weiteren Beleg (Taglöhner → Geometergehilfe),
  oder Vater und Sohn.

**Stichprobe 1** (`data/review/m10_wanderungen.csv`, Seed 10) wurde nach den ersten Regeln
gezogen, 40 Paare je Stufe. Die Regeln wurden danach angepasst; sie zählt nicht als
Messung.

| Stufe | n | richtig | unklar | falsch | Präzision |
|---|---|---|---|---|---|
| `stark` | 40 | 20 | 5 | 15 | 50–62 % |
| `mittel` | 40 | 27 | 6 | 7 | 68–82 % |
| `schwach` | 40 | 13 | 9 | 18 | 32–55 % |

Sie zeigte, dass gleicher Wortlaut und seltener Name eher für dieselbe Zeile unter einem
anderen Ort sprechen als für einen Umzug. 13 der 15 Fehler in `stark` waren solche Fehler:
- Lausanne unter Genève;
- Luzern unter Basel;
- Uster unter Bauma;
- Stadtnummern unter Dörfern;
- ortsfeste Betriebe.

Daraus folgten die Regeln oben: Wortlaut zählt weniger, neue Nummer und Adresse zählen mehr,
dazu Stadtnummer, Strasse im Zusatz, Sprache, Allianzname und zweiter Vorname.

**Stichprobe 2** (`data/review/m10_wanderungen_2.csv`, Seed 11) wurde nach dem letzten
Regelwechsel gezogen und ist die Messung. Sie enthält nur Paare, die nicht in Stichprobe 1
standen. Von den 33 `stark`-Paaren waren 18 schon beurteilt, es blieben 15.

| Stufe | n | richtig | unklar | falsch | Präzision |
|---|---|---|---|---|---|
| `stark` | 15 | 13 | 1 | 1 | 87–93 % |
| `mittel` | 40 | 18 | 13 | 9 | 45–78 % |
| `schwach` | 40 | 11 | 19 | 10 | 28–75 % |

**Lesart:**

- **`stark`** ist jetzt brauchbar, aber klein: 33 Paare in der ganzen Schweiz. Typisch sind
  Ärzte, Ingenieure, Instruktoren, Direktoren und Allianznamen, mit neuer Adresse und neuer
  Nummer. Der eine Fehler ist eine Konditorei «Calprino» (Lugano) unter Hochdorf.
- **`mittel`** hat viele `unklar`. Häufig wechselt der Beruf ohne weiteren Beleg, oder das
  Adressbuch nennt keinen Beruf. Die Fehler sind noch Ortszuweisungen (Pont de Chailly,
  Huprächtigen, «Echo de la Montagne»), Namensvettern (Paul Piccard) und Berufe ohne
  Klasse (Zinngiesser ≠ Schneider, Metzger ≠ Bäcker).
- **`schwach`** ist zur Hälfte offen. Fehler sind meist Namensvettern mit anderem Beruf.
- **Stichprobe 1 unter den neuen Regeln** (nur als Prüfung, nicht als Messung): `stark` 15
  richtig, 2 falsch, 1 unklar; `mittel` 31 / 5 / 6.

**Stichprobe 3** (`data/review/m10_wanderungen_3.csv`, Seed 12) wurde nach Einführung der
feinen Berufsliste gezogen, nur aus Paaren, die nicht in Stichprobe 1 oder 2 standen. Danach
wurde nur noch Nr. 003 behoben (Nachbarzeilen im Berufsfeld); das Paar fällt jetzt weg.

| Stufe | n | richtig | unklar | falsch | Präzision |
|---|---|---|---|---|---|
| `stark` | 8 | 6 | 1 | 1 | 75–88 % |
| `mittel` | 40 | 17 | 15 | 8 | 42–80 % |
| `schwach` | 40 | 6 | 28 | 6 | 15–85 % |

**Lesart:**

- Die feine Liste tut, wofür sie gedacht ist: In Stichprobe 2 waren 4 der 9 Fehler in
  `mittel` Berufsverwechslungen (Metzger/Bäcker, Zinngiesser/Schneider, cordonnier/Küfer,
  Mineralwasser/Wein), in Stichprobe 3 ist es keiner. Auf die schon beurteilten Paare
  angewandt, steigt `mittel` in Stichprobe 2 von 45–78 % auf 59–83 % (29 Paare bleiben).
- Die Präzision von `mittel` steigt in der frischen Stichprobe trotzdem nicht. Alle 8
  Fehler sind Ortszuweisungen, bei denen ein Ortsname oder eine Strasse des alten Orts in
  der Zeile steht: «auf Robersten», «Oberdorf», «Unterseen», «Seefahrtstrasse»,
  «Collonges», «Bertigny», «Liesbergmühle». 6 der 8 haben gleichen Wortlaut und weder neue
  Nummer noch neue Adresse.
- `unklar` bleibt gross: Berufswechsel ohne weiteren Beleg und Adressbuch-Einträge ohne
  Beruf.

Daraus folgten zwei Regeln: Steht ein Orts- oder Strassenwort des alten Eintrags im neuen,
oder heisst der neue Ort wie die alte Adresse, fällt das Paar weg (159 Paare). Gleicher
Wortlaut ohne neue Nummer oder Adresse ergibt höchstens `schwach`. Auf die Stichproben 2
und 3 angewandt (Prüfung, keine Messung): Die Regel trifft dort 10 Paare, alle `falsch`;
`mittel` steht in Stichprobe 2 bei 59–85 % (27 Paare), in Stichprobe 3 bei 55–100 % (29).

**Stichprobe 4** (`data/review/m10_wanderungen_4.csv`, Seed 13) wurde danach gezogen, aus
Paaren, die in keiner früheren Stichprobe standen. In `stark` war keines mehr übrig, in
`schwach` nur 29.

| Stufe | n | richtig | unklar | falsch | Präzision |
|---|---|---|---|---|---|
| `mittel` | 40 | 12 | 20 | 8 | 30–80 % |
| `schwach` | 29 | 15 | 10 | 4 | 52–86 % |

**Lesart:**

- Die Ortszuweisungen sind aus `mittel` verschwunden: keiner der 8 Fehler ist mehr dieselbe
  Zeile unter einem anderen Ort.
- Die Präzision von `mittel` steigt trotzdem nicht. Die 8 Fehler sind jetzt fast alle
  Adressbuch-Paare mit verschiedenen Menschen: andere Frau (geb. Sandmeier statt
  Wächter-Lindenmann, ledige Anna Streit gegen Anna geb. Wyss), anderes Geschlecht
  (Jos. Anton gegen Maria Josepha, Joseph gegen Marie Jos.), anderer zweiter Vorname
  (Oskar Edmund gegen Edmund Th.), Portier gegen Gerber, dazu ein Institut unter einem
  anderen Familiennamen. Viele Adressbuch-Zeilen drucken den Familiennamen nicht («—»).
- `unklar` ist in `mittel` die Hälfte: Adressbuch-Einträge ohne Beruf, Frauen, die
  inzwischen verheiratet sind, häufige Namen.
- `schwach` ist in dieser Stichprobe besser als `mittel`. Dorthin fallen jetzt Tierärzte,
  Apotheker und Droguisten mit gleichem Wortlaut an einem neuen Ort (Guetg, Bouvier,
  Henauer, Barras), die meist richtig sind. Die Grenze für gleichen Wortlaut ist für
  Telefonbuch-Paare mit seltenem Beruf also zu streng.

Daraus folgte der Vergleich von Geschlecht und Geburtsname (oben unter den Bedingungen).
Auf Stichprobe 4 angewandt (Prüfung, keine Messung) fallen 7 Paare aus `mittel`: 4
`falsch` und 3 `unklar`, kein `richtig`. Die 3 `unklar` sind Dienstmägde und eine
Sommelière, die später als «geb. X» erscheinen; nach der Regel waren sie ledig unter einem
anderen Geburtsnamen, also andere Frauen. `mittel` steht dann bei 36–88 % (33 Paare).
Stichproben 2 und 3 ändern sich nicht.

**Stichprobe 5** (`data/review/m10_wanderungen_5.csv`, Seed 14) wurde danach gezogen, aus
Paaren, die in keiner früheren Stichprobe standen. In `mittel` waren nur noch 32 übrig, in
`stark` und `schwach` keine.

| Stufe | n | richtig | unklar | falsch | Präzision |
|---|---|---|---|---|---|
| `mittel` | 32 | 14 | 15 | 3 | 44–91 % |

**Lesart:**

- Nur noch 3 von 32 Paaren in `mittel` sind falsch, so wenige wie in keiner Stichprobe
  zuvor (Stichprobe 4: 8 von 40). Die drei: eine Witwe «geb. Burkhardt» gegen
  «Frl. Bertha Kummer» (Fräulein gegen verheiratet wird noch nicht verglichen), ein Beamter
  des Bundesgerichts in Chamblandes (Pully), unter «Genève» eingeordnet, und eine Firma mit
  Hauptsitz in Rorschach und Filiale in Zürich.
- Die Hälfte bleibt `unklar`, vor allem Adressbuch-Paare mit Berufswechsel (Knecht →
  Fabrikarbeiter, Schmied → Monteur) und häufige Namen.
- Die Stichproben sind jetzt aufgebraucht: Jedes Paar in `stark` und `schwach` und fast
  jedes in `mittel` wurde schon einmal beurteilt. Weitere Regeln lassen sich an diesen
  Paaren nicht mehr unabhängig messen.

**Verfeinerung (17.11.2026).** Drei Regeln kamen dazu:

- **Zivilstand:** Wer früher verheiratet oder verwitwet war, steht später nicht als «Frl.» im
  Buch. Wer früher «Frl. X» war, heisst später nicht «geb. Y». Der Zivilstand kommt aus dem
  Feld `civil_status` der Adressbücher und aus Zusatz und Namenszeile der Telefonbücher
  (Frl., Mlle; Frau, Mme, Wwe., Vve, geb.). Das Paar «Witwe geb. Burkhardt» / «Frl. Bertha
  Kummer» aus Stichprobe 5 fällt damit weg.
- **Seltene Berufe:** Gleicher Wortlaut ohne neue Nummer oder Adresse ergibt nicht mehr nur
  `schwach`, wenn beide Seiten einen Beruf mit Patent oder Wahl nennen (Tierarzt, Apotheker,
  Arzt, Zahnarzt, Notar, Fürsprecher, Pfarrer, Hebamme, Geometer, Architekt, Ingenieur,
  Photograph, Optiker, Drogist, Förster; Beleg `beruf:selten`). An den beurteilten Paaren
  steigen 7 von `schwach` nach `mittel`: 5 richtig, 2 unklar, keines falsch.
- **Mehrdeutig, aber klar vorn:** Ein Paar, das nicht eindeutig ist, bleibt, wenn auf jeder
  Seite höchstens drei Kandidaten stehen und es mindestens 2 Punkte vor jedem anderen Paar mit
  A oder B liegt (Beleg `eindeutig:abstand`). Das nimmt 110 Paare auf.

Übrig bleiben **433 Paare**: 49 `stark`, 256 `mittel`, 128 `schwach`
(vorher 323: 42, 156, 125; dazwischen kamen neue Telefonbücher, Aarau 1867–1881 und Zürich
1867 dazu). Stand 18.11.2026, nach der neuen Ortszuordnung der Telefonbücher: **426 Paare**
(49 `stark`, 255 `mittel`, 122 `schwach`); am Abend desselben Tags, nach der besseren Zerlegung der
Namenszeilen und der Neulesung von Band 2c: **423 Paare** (50, 252, 121). Stand 19.11.2026, nach der
Neulesung von Band 2b 1913/14 ([neulesung_2b.md](neulesung_2b.md)): **430 Paare** (50, 258, 122). Stand 20.11.2026,
mit Zürich 1901: 482 Paare; nach der Neulesung von Band 2a 1911–1914 ([neulesung_2a.md](neulesung_2a.md)):
**480 Paare** (57, 298, 125); mit den Ortschaften aus `data/ref/place_aliases.csv` (Wengen, Ostermundigen,
Wabern …): **484 Paare** (56, 303, 125); mit Zürich 1902: **493 Paare** (58, 309, 126); mit Zürich 1903, 1904, 1907, 1909 und 1910: **524 Paare** (59, 336, 129); mit Zürich 1911: **526 Paare** (59, 336, 131); nach der Neulesung der Bände 1 und 3 1911–1914 ([neulesung_13.md](neulesung_13.md)): **557 Paare** (61, 367, 129); mit Montreux bei Le Châtelard-Montreux: **563 Paare** (62, 370, 131); mit Zürich 1913: **571 Paare** (66, 376, 129); mit Bern 1861 und 1862: **568 Paare** (66, 376, 126); mit Bern 1863 und 1865: **569 Paare** (65, 378, 126); mit Bern 1866, 1868, 1870, 1871, 1873, 1875, 1877 und 1879: **577 Paare** (65, 386, 126).

**Stichprobe 6** (`data/review/m10_wanderungen_6.csv`, Seed 15) prüft, was neu dazukommt:
30 der 110 Paare aus «klar vorn» und 3 Paare mit seltenem Beruf.

| Gruppe | n | richtig | unklar | falsch | Präzision |
|---|---|---|---|---|---|
| klar vorn, `stark` | 3 | 3 | 0 | 0 | 100 % |
| klar vorn, `mittel` | 25 | 6 | 17 | 2 | 24–92 % |
| klar vorn, `schwach` | 2 | 1 | 1 | 0 | 50–100 % |
| seltener Beruf, `mittel` | 3 | 3 | 0 | 0 | 100 % |

**Lesart:**
- Die neuen Paare in `mittel` sind so gut wie die übrigen: 2 von 25 falsch (Stichprobe 5:
  3 von 32).
- Die beiden falschen sind kein Namensvetter, den der Abstand gewählt hätte. Das eine ist ein
  anderer Beruf (Metzger und Wirt gegen Baumwollzwirnerei), das andere eine Genfer Zeile unter
  Rohr (AG).
- Unklar bleiben vor allem Wirte in Nachbarorten (Unterseen/Interlaken) und häufige Namen.

Die Seite zeigt anfangs `stark` und `mittel`. Die Linien sind Hinweise, keine
Wanderungsstatistik.

Frauen, die mit der Heirat den Namen wechseln, findet diese Suche kaum. Ihre Wege über den
Zivilstand (ledig → verheiratet → Witwe, Ehemann → Witwe) prüft ein eigener Versuch:
[frauen_wege.md](frauen_wege.md).

## Grenzen

- **Geschlecht, Geburtsname und Zivilstand** werden verglichen (Messung 5 und 6). Ein anderer zweiter Vorname («Oskar Edmund» ≠ «Edmund Th.»)
  wird nur erkannt, wenn beide Seiten zwei ausgeschriebene Vornamen haben.
- **Neue Stichproben** sind kaum mehr möglich: Fast alle Paare wurden schon einmal
  beurteilt.
- **Gleicher Wortlaut ohne neue Nummer oder Adresse** ergibt höchstens `schwach`, ausser bei
  seltenen Berufen mit Patent oder Wahl.
- **Berufe ausserhalb der feinen Liste** («Seiler», «Treillageur») fallen auf die grobe
  Klasse zurück.
- **Namensvettern** in grossen Städten (Paul Piccard, Lausanne/Genève) lassen sich ohne
  Lebensdaten nicht trennen.
- **Mehrdeutige Paare** (23 037) fallen ganz weg. Häufige Namen kommen darum fast nie vor.
  Rufnummer und Adresse helfen hier nicht, weil sie sich beim Umzug ändern. Allianzname,
  Geburtsjahr oder Heimatort (Adressbücher) könnten helfen.
- **Firmen und Institutionen**, die den Sitz verlegen, sind nicht gesucht.
- **Adressbücher allein** (Basel 1862, Zürich 1859–1914, Bern, Lausanne) zählen mit, wo sie
  vorliegen. Die meisten Orte stehen aber nur im Telefonbuch.

## Zuzüge mit Heimatort

Die Paarsuche oben sucht dieselbe Person an zwei Orten. Die Zuzüge fragen anders: Wer steht in
einem Band einer Stadt zum ersten Mal, und woher stammt er? Das geht nur, wo die Adressbücher den
Heimatort nennen und mehrere Bände vorliegen, im Zeitfenster nur in **Aarau 1867–1913**
(Gebäude- und Einwohnerlisten, bis 1899 rund 60 % der Personen mit Heimatort, 1901 24 %, 1913 35 %). **Zürich 1867–1914** hat
mehrere Bände, aber keinen Heimatort: dort nur die Zuzüge selbst, ebenso in **Bern 1861–1900** (15 Bände) sowie
**Baden und Lausanne** (je zwei Bände, 10 und 11 Jahre auseinander). **Basel 1862** kommt fertig gerechnet aus dem
Basler Repo, mit dem Vorband 1850 vor dem Zeitfenster (unten). Die Seite zeigt alle sechs unter `#/wanderungen?v=zuzug`
(Auswahl «Stadt»).

```bash
make zuzuege                    # links/zuzuege.csv.gz, data/norm/zuzuege_stats.json
python scripts/zuzuege.py site  # site/data/zuzuege.json.gz (läuft im Pages-Workflow)
python scripts/origins.py       # Auszählung: wie viele Heimatorte gehen auf?
python scripts/origins.py ref DIR   # data/ref/places_foreign.csv neu aus GeoNames-Dumps (DE, AT, FR, IT, LI)
```

### Heimatort auflösen (`scripts/origins.py`)

1. Klammerzusatz: Kanton → Schweiz («Küttigen (Bern)»), «Großh. Baden», «Wtbg.», «Preussen»,
   «Tirol» … → Ausland. «Grh. Baden» ohne Klammer gibt nur das Land, keinen Ort.
2. Gemeinden 1914 und Ortschaften (`data/ref`), alte Schreibungen (-wyl, ß, y), Orte vor Fusionen
   (Ryken, Fluntern …), erster Teil eines Doppelnamens («Langnau» → Langnau im Emmental), Kanton
   allein («soloth»).
3. Ausländische Orte aus `data/ref/places_foreign.csv`: nur die GeoNames-Namen, die als Heimatort
   vorkommen und nicht schon als Schweizer Ort aufgehen (348 Namen). Koordinaten vom grössten Ort
   dieses Namens; mehrdeutige Namen tragen mehrere Länder («AT/DE»).
4. Unscharf gegen die Schweizer Liste (≥ 0,86) → `CH?` (Zezwyl, Erlisbach).

Aarau bis 1899, 11 718 Einträge mit Heimatort: CH 9 674, CH? 383, Ausland 1 132, offen 283, leer 246.

### Zuzüge (`scripts/zuzuege.py`)

- Je Band eine Liste: die Einwohnerliste, sonst die Gebäudeliste. Fehlt der Einwohnerliste der
  Heimatort, kommt er aus der Gebäudeliste desselben Bandes (Name, Vorname, Haus; Vermerk
  «[Gebäudeliste]»). Firmen («&», Cie) und Gebäude («Scheune», «Holzschopf») zählen nicht.
- Paare über die Bände: gleicher Familienname, oder ähnlicher (≥ 0,85, mindestens 5 Buchstaben),
  oder im selben Haus ähnlich genug (≥ 0,6, «Udel»/«Adel»). Vorname und Heimatort dürfen sich nicht
  widersprechen. Punkte: Vorname gleich 3, Abkürzung 2, Initiale 1; Heimatort gleich 3; Beruf 2;
  Strasse 1; Haus 1. Nötig sind 3 Punkte, bei ähnlichem Namen 5 (und ein Punkt Abzug). Seit 24.11.2026
  reicht bei gleichem Familiennamen ein nur schwach passender Vorname (Initiale oder dieselbe Abkürzung, «R.»/«Rud.»,
  «Jak.»/«Jak.») auch mit derselben Strasse (2 Punkte), wenn die Vornamen Stelle für Stelle passen: «Joh. Heinr.»
  und «Joh. Bapt.» in derselben Strasse bleiben getrennt (Vater und Sohn). Das verknüpft 1'188 Paare mehr (Zürich
  1'065, Bern 52, Aarau 37, Lausanne 32, Baden 2). Stichprobe von 30 (Seed 2412): 21 wohl dieselbe Person, 8 unklar
  (häufige Namen mit Berufswechsel), 1 wohl falsch («Kunz, J. K., Vergolder» → «Kunz, Joh., Schneider»). Ohne die
  Bedingung «Stelle für Stelle» waren in einer ersten Stichprobe 5 von 30 falsch. 1:1 nach Punkten; eine Person
  darf in einem Band fehlen.
- Aarau hat die Gebäude zwischen 1869 und 1877 neu nummeriert: Bei verknüpften Paaren stimmt die
  Nummer über diese Grenze in 29 von 565 Fällen, sonst in rund 75 %. Hausnummern zählen über die
  Grenze nicht, für «haushalt» gilt dort die Strasse.
- 1900 hat Aarau ein zweites Mal neu nummeriert. Darüber hilft das «Verzeichnis der neuen Hausnumerierung 1900»
  (sources.toml `renumbering`): Eine neue Nummer steht für eine oder mehrere alte («96/1256»), jede Gruppe alter
  Nummern wird auf die erste zurückgeführt, die neuen Nummern auf dieselbe; Neubauten ohne alte Nummer bilden ein
  eigenes System. Bleibende 1899→1901 im selben Haus: 956 von 1'665 (57 %, 1896→1899 63 %); die rohe Nummer
  stimmt nur bei 25. Ohne Konkordanz wären es 1901 452 statt 427 Zuzüge, «haushalt» 99 statt 80.
- Status im späteren Band: `bleibt`, `haushalt` (gleicher Name im selben Haus vorher: Sohn, Witwe,
  Angehörige), `witwe`, `neu_familie` (Familien-, Geburts- oder Allianzname schon in der Stadt),
  `neu`. **Zuzüge** = `neu` + `neu_familie`.

| Band | Personen | Zuzüge | mit Heimatort | davon Ausland | Ausland unter Bleibenden |
|---|---|---|---|---|---|
| 1869 | 1'460 | 304 | 190 | 18 (9 %) | 27/437 (6 %) |
| 1877 | 1'664 | 637 | 414 | 56 (14 %) | 26/341 (8 %) |
| 1879 | 1'658 | 310 | 216 | 29 (13 %) | 60/581 (10 %) |
| 1881 | 1'795 | 289 | 205 | 28 (14 %) | 51/635 (8 %) |
| 1884 | 1'839 | 483 | 385 | 51 (13 %) | 36/639 (6 %) |
| 1888 | 1'836 | 377 | 292 | 32 (11 %) | 58/782 (7 %) |
| 1892 | 1'941 | 390 | 328 | 28 (9 %) | 69/847 (8 %) |
| 1896 | 2'119 | 541 | 244 | 47 (19 %) | 38/480 (8 %) |
| 1899 | 2'080 | 366 | 161 | 28 (17 %) | 47/563 (8 %) |
| 1901 | 2'192 | 427 | 249 | 41 (16 %) | 59/623 (9 %) |
| 1913 | 3'362 | 1'791 | 1'226 | 65 (5 %)¹ | 28/613 (5 %)¹ |

¹ 1913 steht der Heimatort ohne «von» und ohne Landeszusatz («Eisenach», «Bergamo», «Firenze»). Die Auslandsliste
(`data/ref/places_foreign.csv`) kennt nur die Namen, die beim letzten Aufbau als Heimatort vorkamen; 228 Zuzüger
1913 bleiben darum «offen», darunter viele ausländische Orte. Der Auslandanteil 1913 ist eine Untergrenze, bis die
Liste aus den GeoNames-Dumps neu gebaut ist (`python scripts/origins.py ref DIR`). Dazu kommen Reste des Parsers
im Heimatort («Postdienstchef», «Kaffeehalle»).

1901 und 1913 kommen aus der Deutschen Nationalbibliothek (adressbuecher-aarau #9): 1901 mit qwen3.8 gelesen
(Stichprobe am Seitenbild 34 von 40 Einträgen voll korrekt), 1913 die Einwohner mit Gemini (26 von 30). Zwischen 1901
und 1913 liegen zwölf Jahre; «Zuzug» heisst «neu seit 1901» und schliesst Söhne mit eigenem Eintrag ein.

Ausländische Zuzüger in Aarau 1869–1913: Deutschland 307, Österreich 27, Frankreich 23, Österreich oder
Deutschland 20, Italien 16.

### Zürich 1867–1914 (ohne Heimatort)

Die Zürcher Bände nennen keinen Heimatort (nur 1867 bei rund hundert Einträgen). Die Verknüpfung
läuft gleich, mit drei Unterschieden: Zürich nummeriert je Strasse (Haus = Strasse + Nummer), eine
Umnummerierung zeigt sich nicht (gleiche Nummer bei verknüpften Paaren in derselben Strasse 76–87 %),
und ähnliche Familiennamen werden über eine Liste der Namen gesucht statt Eintrag gegen Eintrag
(61 000 Einträge je Band; Lauf rund 4 Minuten).

| Band | Vorband | Personen | Zuzüge | davon Name neu | bleibt | Quartier im Vorband nicht erfasst |
|---|---|---|---|---|---|---|
| 1875 | 1867 | 15'088 | 4'265 (28 %) | 1'535 | 2'224 | 7'513 |
| 1885 | 1875 | 26'504 | 19'201 (72 %) | 4'328 | 6'051 |  |
| 1900 | 1885 | 59'263 | 44'829 (76 %) | 11'495 | 11'674 |  |
| 1901 | 1900 | 61'369 | 10'521 (17 %) | 3'130 | 49'457 |  |
| 1902 | 1901 | 53'897 | 4'648 (9 %) | 1'062 | 48'399 |  |
| 1903 | 1902 | 46'996 | 3'892 (8 %) | 896 | 42'685 |  |
| 1904 | 1903 | 45'517 | 4'747 (10 %) | 1'672 | 40'268 |  |
| 1907 | 1904 | 49'745 | 13'160 (26 %) | 2'792 | 35'149 |  |
| 1909 | 1907 | 51'934 | 9'805 (19 %) | 2'163 | 40'762 |  |
| 1910 | 1909 | 55'975 | 7'595 (14 %) | 2'015 | 47'645 |  |
| 1911 | 1910 | 58'011 | 6'656 (11 %) | 1'496 | 50'403 |  |
| 1913 | 1911 | 60'477 | 10'625 (18 %) | 2'315 | 48'750 |  |
| 1914 | 1913 | 61'562 | 6'496 (11 %) | 1'373 | 54'169 |  |

- **1867 umfasst fast nur die Altstadt** (Quartier leer; Riesbach 111 Einträge gegen 1 571 im Jahr
  1875). Ein Quartier mit weniger als einem Viertel der Einträge im Vorband gilt als nicht erfasst;
  wer dort neu ist, hat den Status `gebiet` und zählt nicht als Zuzug.
- **Bis 1900 liegen die Bände 8 bis 15 Jahre auseinander, ab 1901 ein bis drei Jahre.** «Zuzug» heisst
  «neu seit dem Vorband» und schliesst Söhne ein, die einen eigenen Eintrag bekommen, ebenso Frauen, die neu
  unter eigenem Namen stehen. Über zwei oder drei Jahre (1907, 1913) steigt der Anteil darum: 1913 nach 1911
  18 %, 1914 nach 1913 11 %.
- **Nach der Eingemeindung 1893** wurden Strassen umbenannt: 1885→1900 trägt die Strasse bei 9 % der
  verknüpften Paare bei (1 073 von 11 676), zwischen den Jahresbänden ab 1901 bei 61–81 % (1913→1914:
  42 388 von 54 169). Vor 1900 hängt die Verknüpfung an Name, Vorname und Beruf.
- **Abgeschnittene Strassen vor 1893** (seit 27.11.2026): «Hirschengr.», «Seilergr.», «Stüssihofst.», «Rinderm.»,
  «Limmatq.» werden vor dem Vergleich ausgeschrieben (`street_canon` mit `cut_only`, 40 Schlüssel, rund 600
  Strassenangaben der Bände 1867–1885). Anders als in Bern nur abgeschnittene Namen ohne Endung, mindestens fünf
  Buchstaben, auf einen Mitlaut endend, und nur wenn die ausgeschriebene Form so beginnt: Der freie Vergleich hätte
  Strassen eigenen Namens zusammengelegt («Seestr.» → «Seefeldstr.», «Baurstr.» → «Braurstr.», «Schlossg.» →
  «Schlosserg.», «Eisg.» → «Eiseng.», «Talstr.» → «Tonhallestr.»). Wirkung klein: Zuzüge 1875 −4, 1885 −20, 1900 −16;
  13 neue Verknüpfungen, davon 8 sichtlich dieselbe Person («Claus, Alb., Dr., Arzt, Hirschengr. 20» →
  «Hirschengraben 20»), 4 unklar (Vater oder Sohn im selben Haus), 1 wohl falsch («Dietrich, J., Mehlhandlung» →
  «— Arn. Jac. Georg, Sohn», Stüssihofstatt); dazu 11 Verschiebungen unter gleichnamigen Personen («Keller, Carl»).
- **Gelesen ohne Nachkorrektur:** Ein falsch gelesener Name oder Vorname macht aus einem Bleibenden
  einen Zuzug. Stichprobe (24 Zuzüge aus 1900 und 1914): meist anderer Vorname, Beruf und Strasse als
  jeder ähnliche Name im Vorband; einzelne Grenzfälle mit abgekürztem Vornamen («Kamer, Jos.» →
  «Kamer, Jos. Ad.», anderer Beruf).
- Firmen, Anstalten und Vereine im Namen («Petranit A. G.», «Eilboten-Institut», «— Söhne») zählen nicht.

### Basel 1862 (übernommen, Vorband 1850)

Seit 27.11.2026. Die Basler Bände 1841, 1850 und 1862 verknüpft das Basler Repo selbst
([`scripts/60_zuzuege.py`](https://github.com/thodel/adressbuecher-basel/blob/main/scripts/60_zuzuege.py), Befund in
[PLAN.md, Abschnitt 7](https://github.com/thodel/adressbuecher-basel/blob/main/PLAN.md)); Vernetzte Schweiz übernimmt
`60_zuzuege.csv` und `60_zuzuege_stats.csv` am gepinnten Commit (`zuzuege`, `zuzuege_stats` in `config/sources.toml`,
`imported()` in `scripts/zuzuege.py`). Übernommen werden die Personen von 1862; vom Vorband 1850, der vor dem
Zeitfenster liegt, nur die Personenzahl als Vergleich. Selbst gerechnet wird Basel hier nicht: Die Verknüpfung hängt an
der alten, stadtweiten Hausnummer, die für 1862 erst über das Häuserverzeichnis gefunden wird, und an den Bänden 1841
und 1850, die nicht eingelesen sind. Eine zweite Fassung der Regeln liefe auseinander.

| Band | Vorband | Personen | Zuzüge | davon Name neu | bleibt | witwe, haushalt |
|---|---|---|---|---|---|---|
| 1862 | 1850 | 7'463 | 6'205 (83 %) | 1'976 | 768 (435 aus 1850, 333 aus 1841) | 490 |

- **Die Regeln weichen leicht ab:** Die alte Hausnummer zählt 2 Punkte (sie steht für Strasse und Haus), die Strasse
  nur zwischen 1841 und 1862 (1850 nennt keine), und der Vorname allein verknüpft nicht (in der Stichprobe meist
  verschiedene Personen); ein anderer Allianzname schliesst aus. Die Vornamen vergleicht `81_baende.py` wie in der
  Spalte «Andere Bände».
- **«Zuzug» heisst «neu im Register»:** 1850 nennt 2'826 Personen, 1862 7'463. Der grösste Teil der Zuzüge 1862 kommt
  vom grösseren Umfang des Registers, nicht aus Zuwanderung.
- Alle 7'463 Einträge haben ein Gegenstück in den Adressbuch-Einträgen und eine Einheit. Stichprobe im Basler Repo
  (30 Paare, Seed 2711): 27 plausibel, 3 unklar.

### Bern 1861–1900 (ohne Heimatort)

Seit 26.11.2026 mit allen gelesenen Bänden: 1861–1879 in Fraktur (Gemini, ohne 1864), 1883/84 und 1900. Gerechnet wie
Zürich (Hausnummer je Strasse, keine Quartiere), mit einer Umnummerierung 1882 («Die Häuser-Nummerirung in Bern»):
Bei verknüpften Paaren stimmt die Hausnummer 1879→1883 in 9 von 2'640 Fällen, zwischen den Bänden 1861–1879 in
59–80 %. Über diese Grenze zählt die Hausnummer nicht, für «haushalt» gilt die Strasse (1883: 377 statt 3, mit den
ausgeschriebenen Strassen 449).
Der Heimatort steht bei rund 1 % der Einträge (1861 92 von 6'345); die Herkunft bleibt darum leer.

| Band | Vorband | Abstand | Personen | Zuzüge | davon Name neu | bleibt | witwe, haushalt | bleibt / Personen Vorband |
|---|---|---|---|---|---|---|---|---|
| 1862 | 1861 | 1 | 3'926 | 996 (25 %) | 242 | 2'599 | 331 | 66 % |
| 1863 | 1862 | 1 | 3'887 | 692 (18 %) | 151 | 2'968 | 227 | 76 % |
| 1865 | 1863 | 2 | 4'051 | 1'069 (26 %) | 263 | 2'733 | 249 | 70 % |
| 1866 | 1865 | 1 | 4'678 | 1'105 (24 %) | 277 | 3'283 | 290 | 81 % |
| 1867 | 1866 | 1 | 4'871 | 1'180 (24 %) | 288 | 3'417 | 274 | 73 % |
| 1868 | 1867 | 1 | 5'108 | 829 (16 %) | 162 | 3'923 | 356 | 81 % |
| 1870 | 1868 | 2 | 5'804 | 1'658 (29 %) | 345 | 3'835 | 311 | 75 % |
| 1871 | 1870 | 1 | 5'735 | 830 (14 %) | 177 | 4'634 | 271 | 80 % |
| 1873 | 1871 | 2 | 5'453 | 693 (13 %) | 129 | 4'449 | 311 | 78 % |
| 1875 | 1873 | 2 | 5'804 | 1'794 (31 %) | 410 | 3'695 | 315 | 68 % |
| 1877 | 1875 | 2 | 6'110 | 841 (14 %) | 221 | 4'925 | 344 | 85 % |
| 1879 | 1877 | 2 | 5'867 | 1'237 (21 %) | 276 | 4'253 | 377 | 70 % |
| 1883 | 1879 | 4 | 7'479 | 4'122 (55 %) | 1'125 | 2'679 | 678 | 46 % |
| 1900 | 1883 | 17 | 13'405 | 10'054 (75 %) | 2'551 | 2'211 | 1'140 | 30 % |

«bleibt» schliesst Personen ein, die im Vorband fehlen und zwei Bände zurück stehen; das letzte Verhältnis ist darum
leicht zu hoch.

- **Der Anteil springt** zwischen 13 und 31 %, auch bei gleichem Abstand (1871 14 %, 1873 13 %, 1875 31 %).
  1873→1875 stimmt auch die Hausnummer bei verknüpften Paaren am seltensten (61 %, sonst 73–85 %): Unterschiede
  in Lesung und Satz der einzelnen Bände tragen vermutlich bei. Einzelne Jahre sind darum keine Zeitreihe der
  Zuwanderung.
- **Abgekürzte Strassen** (seit 27.11.2026). Bis 1883 kürzen die Bände die Strassen unterschiedlich ab («Kramg.»,
  «Krmg.»; «Mezg.», «Metzgerg.»; «Gerechtg.», «Gerechtigkeitsg.»). Für Bern bringt `street_canon` eine Abkürzung
  vor dem Vergleich auf die ausgeschriebene Form, gewonnen aus den Berner Schlüsseln selbst: gleiche Endung
  (-gasse, -strasse …), gleicher Anfangsbuchstabe, die Abkürzung als Buchstabenfolge in der längeren Form, diese
  mindestens so häufig und mindestens 30 Mal, und nur wenn genau eine Form passt. Eine reine Verlängerung um mehr als
  vier Buchstaben gilt nicht («Lorraine» bleibt, «Lorraine, Quartierhof» ist eine Adresse darin). Das schreibt 464
  Schlüssel aus (15'565 von 137'456 Strassenangaben). Die Zuzüge 1862–1879 sinken von 13'436 auf 12'924; Aarau,
  Baden und Lausanne bleiben unverändert. Für Zürich vor 1893 gilt seit 27.11.2026 eine strengere Regel (oben).
  Stichprobe von 30 neuen Verknüpfungen (Seed 2711): 26 sichtlich dieselbe Person («Krmg. 169» → «Kramg. 169»,
  «Pstg. 30» → «Postg. 30»), 3 unklar (anderer Beruf im selben Haus), 1 wohl falsch («Steck C. F. R., Amtsnotar» →
  «— R., Pharm.», Gerechtigkeitsgasse 69).
- **Initialen.** Viele Berner Einträge nennen nur die Initiale oder eine Abkürzung des Vornamens; das gibt einen
  Punkt und verknüpft nur mit gleichem Beruf oder (seit 24.11.2026) gleicher Strasse. «Hügi, R., Heizer im
  Bahnhof» 1883 (Könizstrasse) und «Hügi, R., Lokomotivführer» 1900 (andere Strasse) bleiben getrennt, ebenso
  «Richard, F., Priv.» 1870 (Junkerng.) und 1871 (Gerechtg.). Bei 10–21 % der Zuzüge 1862–1879, 21 % 1883 und 26 %
  1900 steht im Vorband noch ein unverknüpfter Eintrag mit gleichem Familiennamen und passender Initiale
  (Zürich 1885→1900: 22 %; Lausanne 7 %; Baden 2 %). Die Zuzüge sind darum eine Obergrenze, in Bern wie in Zürich.
- Stichprobe 1875 (8 Zuzüge «Name schon in der Stadt», Seed 1126): 7 mit anderem Vornamen oder Beruf als jeder
  Eintrag gleichen Namens 1873, 1 wohl dieselbe Person ohne Vornamen («Petri, Papierneg.»).

### Baden und Lausanne (je zwei Bände, ohne Heimatort)

Seit 24.11.2026 (Entscheid vom selben Tag) gleich gerechnet wie Zürich: Hausnummer je Strasse, keine Umnummerierung,
keine Quartiere. Gezählt wird nur die Gemeinde selbst (Baden 1910 umfasst den Bezirk, Lausanne 1907 dazu die
übrigen Waadtländer Gemeinden). Kein Band nennt einen Heimatort.

| Stadt | Band | Vorband | Abstand | Personen | Zuzüge | davon Name neu | bleibt | witwe, haushalt |
|---|---|---|---|---|---|---|---|---|
| Baden | 1910 | 1900 | 10 Jahre | 1'937 | 1'508 (78 %) | 781 | 327 | 102 |
| Lausanne | 1907 | 1896 | 11 Jahre | 22'535 | 15'489 (69 %) | 3'664 | 6'670 | 376 |

Von den Personen des Vorbands finden sich wieder: Baden 29 % (327 von 1'112), Lausanne 37 % (6'670 von 18'080);
zum Vergleich Zürich 1885→1900 44 % (über 15 Jahre), Bern 1883→1900 29 % (über 17 Jahre).

- **Initialen** siehe Bern; Lausanne 7 %, Baden 2 % der Zuzüge mit einem unverknüpften Eintrag gleichen Namens und
  passender Initiale im Vorband.
- **Allianznamen.** Lausanne nennt verheiratete Frauen oft mit Allianznamen (1907 bei 53 % der Einträge); steht
  er schon im Vorband, zählt die Person als «Name schon in der Stadt» (11'857 der 15'521 Zuzüge).
- **Baden 1900** nennt fast keine Hausnummern (4 % der Einträge), die Adresse hilft dort wenig.
- Stichprobe (je 8 Zuzüge «Name schon in der Stadt», Seed 1124): Bern 1900 4 klar neu, 2 wohl dieselbe Person
  (Hügi R.; Fässler/Fasler F.), 2 ohne Vornamen nicht beurteilbar; Lausanne 5 klar neu, 1 wohl dieselbe Person
  (Cuérel Hélène), 2 nicht beurteilbar.

### Nationalität aus dem Namen? (gemessen, nicht eingebaut)

An den 3 822 Aarauer Personen mit Heimatort (464 Ausland, drei Viertel Deutsche) gemessen:
Ein Name, der nicht als Schweizer belegt ist, findet 62 % der Ausländer, aber zwei von drei
Treffern sind Schweizer. Endungen (-ini, -ski, -eau) finden 3 %. Ein naiver Bayes aus Name, Vorname
und Endung erreicht AUC 0,79, gpt-oss-120b 0,71. Für Städte ohne Heimatort taugen Namen höchstens für
einen geschätzten Anteil, nicht für die einzelne Person: Deutsche und Deutschschweizer tragen dieselben
Namen. Darum zeigt die Seite nur Zuzüge mit gelesenem Heimatort.

### Grenzen der Zuzüge

- **Lesefehler** im Familiennamen machen aus einem Bleibenden einen Zuzug, wenn kein gemeinsames Haus
  hilft («Nieding»/«Riding»). Zeilen mit «—» erben den Familiennamen der Zeile darüber, 1899 manchmal
  den falschen («— Abraham» unter «Erismann & Blattner»).
- **Rückkehrer**: Wer zwei Bände lang fehlt, zählt bei der Rückkehr als Zuzug.
- **Stichprobe** (24 Zuzüge aus 1881, 1892, 1899, vor dem letzten Fix): 11 klar neu, 1 Rückkehr nach
  zwei Bänden, 1 seither verknüpft, 4 Lesevarianten oder Witwe unter anderem Namen, 7 «—»-Zeilen
  nicht beurteilbar.
- **Heimatort ist Bürgerort**, nicht letzter Wohnort: Ein Schweizer aus Basel kann aus Paris
  zugezogen sein und umgekehrt.
- 1896 und 1899 tragen den Heimatort bei weniger Personen (1 119 und 1 027 Einträge gegen 2 177 im Band
  1892): die Anteile beruhen dort auf weniger Fällen.

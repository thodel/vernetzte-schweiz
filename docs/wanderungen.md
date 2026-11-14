# Wanderungen (M10, experimentell)

Wer verschwindet an einem Ort aus Telefon- und Adressbuch und taucht kurz danach an einem
anderen zum ersten Mal auf? `scripts/migration.py` sucht solche Paare. Die Seite zeigt sie
unter `#/karten?v=wanderungen`. Es sind **Kandidaten**, keine geprüften Umzüge.

```bash
make wanderungen   # links/migration.csv, data/norm/migration_stats.json
python scripts/migration.py site   # site/data/wanderungen.json.gz (läuft im Pages-Workflow)
```

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
  Initiale genügt nie.
- **Gegenbelege:**
  - Am alten Ort beginnt nach *t* eine verträgliche Einheit. Dann ist A nicht verschwunden,
    die Bündelung hat nur getrennt (19 898 Fälle).
  - Am neuen Ort gab es vor *t'* schon eine verträgliche Einheit (40 997 Fälle).
- **Eindeutigkeit:** A hat genau einen solchen Nachfolger, und B hat genau einen Vorgänger.
  24 353 Paare fallen hier weg.

### Punkte und Stufen

| Beleg | Punkte |
|---|---|
| Vorname ausgeschrieben gleich | 2 |
| Vorname als Abkürzung | 1 |
| Beruf mit gleichem Wortstamm | 2 |
| sonst gleiche Berufsklasse ([occupations.py](../scripts/occupations.py)) | 1 |
| verschiedene Berufsklassen | −1 |
| gleicher Titel (Dr., Prof., Ing. …) | 1 |
| Familienname mit höchstens 10 Personen-Einheiten in der Schweiz | 2 |
| Familienname mit höchstens 40 Personen-Einheiten | 1 |

| Stufe | Bedingung |
|---|---|
| `stark` | ≥ 6 Punkte und ein Beruf- oder Titelbeleg |
| `mittel` | ≥ 4 Punkte und ein Beruf- oder Titelbeleg |
| `schwach` | ≥ 4 Punkte ohne Berufsbeleg (meist seltener Name und gleicher Vorname) |

## Fehler der Ortszuweisung

Der erste Lauf ergab 1 598 Paare. Die meisten waren keine Umzüge, sondern dieselbe Zeile
unter einem anderen Ort. Das sind die Fehler aus M1: Charge B überträgt die Ortsüberschrift.
Ein Beispiel ist Lausanne 1911–1914 unter «Genève», mit 321 Paaren und Strassen wie
«r. Pépinet» und «Lion d'Or» am neuen Ort. Darum gelten folgende Paare als Fehler und fallen
weg:

| Grund | Paare |
|---|---|
| dieselbe Rufnummer an beiden Orten (wer umzieht, bekommt eine neue) | 965 |
| um die erste Zeile von B stehen mindestens zwei weitere Einträge, die ebenfalls vom Ort A «gekommen» wären (der ganze Lauf gehört zu A; Nachbarn mit demselben Familiennamen zählen nicht) | 512 |
| die Ortsnamen beginnen gleich und liegen mindestens 5 km auseinander («Fleurier» → «Finhaut», «Altstätten» → «Alt St. Johann»: Nachbarn im Alphabet des Telefonbuchs) | 213 |
| B steht an einer Strasse, die es am Ort A gibt und an seinem eigenen Ort kaum | 68 |
| Gasthaus mit gleichem Namen (ortsfest) | 16 |
| gleiche Adresse | 11 |

Übrig bleiben **285 Paare**: 44 `stark`, 166 `mittel`, 75 `schwach`.

## Was «verschwunden» und «neu» heissen

- Die Telefonbücher nennen nur Abonnenten. «Neu im Buch» heisst oft «neu ein Telefon»,
  «nicht mehr im Buch» oft «kein Telefon mehr». Ein Paar ist erst dann ein Hinweis auf
  einen Umzug, wenn dieselbe Person am einen Ort aufhört und am anderen beginnt.
- Vor 1911 liegen nur einzelne Ausgaben vor (Charge A). Darum häufen sich die Paare
  1911–1914, rund sechs von zehn.
- Ob A wirklich verschwand, lässt sich nur sagen, wenn der alte Ort nach *t* noch einmal
  mit mindestens halb so vielen Einträgen vorliegt (Spalte `left_seen`). Ob B wirklich neu
  ist, nur wenn der neue Ort vor *t'* so vorliegt (`new_seen`). Beides trifft auf 81 Paare
  zu (78 Paare). Die Seite kann auf sie einschränken.
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

Die Ansicht liegt unter `#/karten?v=wanderungen&a=…&b=…&t=0|1|2&c=…&d=linien|saldo&n=ohne|mit&g=alle|ja`.

- **Linien:** Bögen vom alten zum neuen Ort, Breite nach Zahl der Paare, roter Punkt am Ziel.
- **Saldo:** je Ort ein Kreis nach Zu- plus Wegzügen, grün bei mehr Zuzügen, rot bei mehr
  Wegzügen.
- **Seitenleiste:**
  - Zahl nach Berufsklasse mit Median der Entfernung;
  - Verteilung der Entfernungen und erstes Jahr am neuen Ort;
  - häufigste Ortspaare;
  - Fälle mit Links auf beide Einheiten.

## Messung

Je Stufe 40 zufällige Paare (`scripts/measure_migration.py`, Seed 10), gezogen nach dem
Festlegen der Regeln oben, vor der Ausnahme der Institutionen. Beurteilt hat Claude, nicht
die Projektmitarbeitenden. Grundlage waren die letzten zwei Einträge am alten und die ersten
zwei am neuen Ort, wie gedruckt (`data/review/m10_wanderungen.csv`).
- `richtig`: dieselbe Person an einem anderen Wohn- oder Geschäftsort.
- `falsch`: eine andere Person, oder dieselbe Zeile unter einem falschen Ort.

| Stufe | n | richtig | unklar | falsch | Präzision |
|---|---|---|---|---|---|
| `stark` | 40 | 20 | 5 | 15 | 50–62 % |
| `mittel` | 40 | 27 | 6 | 7 | 68–82 % |
| `schwach` | 40 | 13 | 9 | 18 | 32–55 % |

**Was die Messung zeigt:**

- **`stark` ist schlechter als `mittel`.** Gleicher Berufstext und seltener Name sprechen
  eher für dieselbe Zeile unter einem anderen Ort als für einen Umzug. 13 der 15 Fehler in
  `stark` sind Ortszuweisungen:
  - Lausanne unter Genève (Deux-Marchés, Valentin, Chauderon);
  - Luzern unter Basel (Bruchstrasse);
  - Uster unter Bauma (Brunnen- und Florastrasse);
  - eine Stadtnummer wie 36.86 unter einem Dorf;
  - ortsfeste Betriebe und Ämter (Gasthaus, Mühle, Sindaco, Kreisrichter).
- **Echte Umzüge** zeigen fast immer eine neue Adresse und eine neue Nummer. Oft stimmen
  Beruf oder Allianzname überein, der Wortlaut aber nicht.
- **`schwach`** ist bei Personen ohne Berufsbeleg meist falsch: Maurer ≠ Ingenieur,
  Possidente ≠ Maurer, verschiedene Allianznamen.
- 4 Fehler der Stichprobe (Kloster, Eilboten-Institut, Erben, «Klosterhof») fallen mit der
  Ausnahme der Institutionen weg.

**Folgerungen (noch nicht umgesetzt; danach neue Stichprobe):**

- **Gleicher Wortlaut** des Zusatzes (nicht nur gleicher Stamm) bei ortsgebundenen Angaben
  wird ein Gegenbeleg: Gasthaus, Mühle, Villa, Hofname, Amt.
- **Rufnummer im Stadtformat** (xx.xx, vierstellig) unter einem Dorf deutet auf einen
  falsch verorteten Stadtlauf.
- **Strassen des alten Orts** sollen auch im Zusatz gesucht werden, nicht nur in der
  Strassenspalte («Chauderon», «Valentin», «au Day»).
- **Verschiedene Allianznamen** gelten als Widerspruch. Verschiedene Berufsklassen ohne
  Übergang (Arzt → Kellner) zählen stärker gegen das Paar.
- **Stufen neu ordnen:** Neue Adresse **und** neue Nummer werden Pluspunkte; gleicher
  Wortlaut zählt nicht mehr.

Bis dahin zeigt die Seite anfangs `stark` + `mittel`. Die Linien sind Hinweise, keine
Wanderungsstatistik.

## Grenzen

- **Sprachwechsel als Prüfung:** Eine italienische Berufsangabe in Luzern ist eher ein Fehler
  der Ortszuweisung als ein Umzug. Das wird noch nicht genutzt.
- **Mehrdeutige Paare** (24 353) fallen ganz weg. Häufige Namen kommen darum fast nie vor.
  Rufnummer und Adresse helfen hier nicht, weil sie sich beim Umzug ändern. Allianzname,
  Geburtsjahr oder Heimatort (Adressbücher) könnten helfen.
- **Firmen und Institutionen**, die den Sitz verlegen, sind nicht gesucht.
- **Adressbücher allein** (Basel 1862, Zürich 1859–1914, Bern, Lausanne) zählen mit, wo sie
  vorliegen. Die meisten Orte stehen aber nur im Telefonbuch.

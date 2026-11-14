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
  Initiale genügt nie. Haben beide Seiten zwei ausgeschriebene Vornamen, müssen sie
  übereinstimmen: «Karl Friedrich» ≠ «Karl Johann».
- Verschiedene Allianznamen widersprechen («Spörry-Streiff» ≠ «Spœrri-Duport»). Verglichen
  werden die ersten fünf Buchstaben, so ist «Tröndli» = «Tröndle».
- **Gegenbelege:**
  - Am alten Ort beginnt nach *t* eine verträgliche Einheit. Dann ist A nicht verschwunden,
    die Bündelung hat nur getrennt (18 515 Fälle).
  - Am neuen Ort gab es vor *t'* schon eine verträgliche Einheit (36 466 Fälle).
- **Eindeutigkeit:** A hat genau einen solchen Nachfolger, und B hat genau einen Vorgänger.
  23 249 Paare fallen hier weg.

### Punkte und Stufen

| Beleg | Punkte |
|---|---|
| Vorname ausgeschrieben gleich | 2 |
| Vorname als Abkürzung | 1 |
| Beruf mit gleichem Wortstamm, anders formuliert | 2 |
| Beruf mit gleichem Wortlaut (meist dieselbe Zeile, nicht derselbe Mensch anderswo) | 1 |
| sonst gleiche Berufsklasse ([occupations.py](../scripts/occupations.py)) | 1 |
| verschiedene Berufsklassen | −2 |
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
| um die erste Zeile von B stehen mindestens zwei weitere Einträge, die ebenfalls vom Ort A «gekommen» wären (der ganze Lauf gehört zu A; Nachbarn mit demselben Familiennamen zählen nicht) | 368 |
| die Ortsnamen beginnen gleich und liegen mindestens 5 km auseinander («Fleurier» → «Finhaut», «Altstätten» → «Alt St. Johann»: Nachbarn im Alphabet des Telefonbuchs) | 193 |
| vierstellige Stadtnummer an einem Ort mehr als 15 km vom nächsten Stadtnetz («36.86» unter Prez-vers-Siviriez); Vororte wie Versoix oder Renens liegen im Netz der Stadt | 78 |
| ortsfester Betrieb oder Posten auf beiden Seiten (Gasthaus, Mühle, Villa, Postablage, Sindaco, Richter …) mit gleichem Wortlaut oder gleichem Eigenwort («Löwenburg», «Ochsen») | 66 |
| B steht an einer Strasse, die es am Ort A gibt und an seinem eigenen Ort kaum | 64 |
| eine solche Strasse steht im Zusatz von B («boulanger, r. des Deux-Marchés», «past., Valentin») | 35 |
| Strassenangabe in der Sprache des alten Orts («Via alla Stazione» unter Luzern) | 22 |
| gleiche Adresse | 9 |

Übrig bleiben **339 Paare**: 33 `stark`, 172 `mittel`, 134 `schwach`.

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

Die Seite zeigt anfangs `stark` und `mittel`. Die Linien sind Hinweise, keine
Wanderungsstatistik.

## Grenzen

- **Berufe ohne Klasse** («Zinngiesserei» → «Schneider») zählen weder für noch gegen das
  Paar. Eine feinere Berufsliste würde `mittel` und `schwach` verbessern.
- **Namensvettern** in grossen Städten (Paul Piccard, Lausanne/Genève) lassen sich ohne
  Lebensdaten nicht trennen.
- **Mehrdeutige Paare** (23 249) fallen ganz weg. Häufige Namen kommen darum fast nie vor.
  Rufnummer und Adresse helfen hier nicht, weil sie sich beim Umzug ändern. Allianzname,
  Geburtsjahr oder Heimatort (Adressbücher) könnten helfen.
- **Firmen und Institutionen**, die den Sitz verlegen, sind nicht gesucht.
- **Adressbücher allein** (Basel 1862, Zürich 1859–1914, Bern, Lausanne) zählen mit, wo sie
  vorliegen. Die meisten Orte stehen aber nur im Telefonbuch.

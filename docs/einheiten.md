# Personen und Firmen über die Jahre (M3)

`scripts/cluster.py` bündelt die Einträge derselben Person oder Firma über
Telefonbuch-Ausgaben und Adressbuch-Bände zu **Einheiten**. `scripts/authority.py`
verbindet die Einheiten mit Normdaten. `scripts/measure_clusters.py` misst die Bündelung.
Alles läuft mit `make entities`.

## Was gebündelt wird

- **Telefonbuch:** alle Einträge ≤ 1914 mit Gemeinde (Ort `hoch` oder `mittel`, M1), Art
  `person` oder `firma`: 523 913 Einträge mit den Adressbüchern zusammen.
- **Adressbuch:** alle Einträge der Bände von Aarau (1884–1899) und Basel (1862).

Gebündelt wird je **Gemeinde 1914** und **Namensschlüssel** (Personen: Familienname,
Firmen: Leitname, wie in M2). Personen und Firmen bleiben getrennt. Zieht jemand in eine
andere Gemeinde, entstehen zwei Einheiten.

«Derselbe», «Dieselbe», «Dasselbe» (zweite Nummer, «Wohnung») übernehmen Namen und Art
des Eintrags, auf den sie verweisen, und hängen an ihm.

## Kanten

Zwei Einträge werden verbunden, wenn einer der folgenden Belege zutrifft und nichts
widerspricht. Direkt verbunden werden nur Einträge mit höchstens 5 Jahren Abstand; längere
Zeiträume entstehen über die Ausgaben dazwischen.

| Beleg | Bedingung |
|---|---|
| Telefonbuch ↔ Adressbuch | Paar aus M2 der Stufe `sicher` oder `wahrscheinlich` |
| gleiche Nummer | mit verträglichem Vornamen, Allianzname, Strasse oder gleichem Namen; **allein** nur bis 3 Jahre Abstand (die Zeile ist oft verlesen) |
| ausgeschriebener Vorname | mit Strasse, Beruf oder Allianzname |
| Initiale | mit Hausnummer, oder mit Strasse und Beruf bzw. Allianzname |
| gleiche Zeile | Name, Zusatz und Adresse wortgleich, bis 3 Jahre Abstand (Einträge ohne Nummer) |
| gleicher Name ohne Vornamen | «Orelli, Frau Prof.», Ämter: mit Nummer oder Strasse |
| Firmen | gleicher Firmenname (Rechtsform zählt: «Söhne» ≠ «& Co.») mit Nummer, Strasse oder Beruf; gleiche Nummer und Strasse |
| derselbe Band | zweite Nummer derselben Person; dieselbe Person im Einwohner-, Berufs- und Gebäudeverzeichnis |

Abgekürzte Strassen gelten als ausgeschrieben («Schanzeng.» = «Schanzengasse»).

## Widersprüche

Bündel werden nach der Stärke ihrer Kanten vereinigt. Eine Vereinigung unterbleibt, wenn
die beiden Bündel zusammen enthielten:
- zwei unverträgliche Vornamen. So verkettet «J.» nicht Johann und Jakob;
- zwei verschiedene Allianznamen;
- eine Witwe und eine Nicht-Witwe («Lorez, S.» und «Lorez, Wwe.»);
- einen Namensgeber und seine Nachfolger («Winter, G.» und «G. Winter’s Söhne»);
- zwei Einträge derselben Ausgabe, die nicht dieselbe Einheit sein können: weder Nummer
  noch Haus noch ein ausgeschriebener Vorname verbindet sie (Vater und Sohn mit eigener
  Nummer).

## Ergebnis

- `links/entities.csv.gz`: je Eintrag die Einheit (`record_id`, `entity_id`, `source`,
  `year`, `municipality`).
- `links/entity_edges.csv.gz`: die Kanten, die zur Bündelung führten, mit Belegen.
- `data/norm/entities.csv.gz`: je Einheit Name, Gemeinde, Jahre, Nummern, Adressen, Berufe.

`entity_id` ist aus dem kleinsten Eintrags-Bezeichner der Einheit gebildet. Sie bleibt
gleich, solange dieser Eintrag zur Einheit gehört; bei geänderten Regeln kann sie wechseln.

| | Anzahl |
|---|---|
| Einträge | 523 913 |
| Einheiten | 181 215 (Personen 130 497, Firmen und Ämter 50 718) |
| Einheiten mit mehr als einem Eintrag | 98 848 (mit 441 546 Einträgen) |
| über mindestens 10 Jahre belegt | 8 867 |
| im Telefon- und im Adressbuch | 466 (Aarau 1884–1899, Basel 1862) |

Dass nur 466 Einheiten in beiden Quellen stehen, liegt an den Adressbüchern: Aarau hat 3 035
Telefonbuch-Einträge, Basel nur den Band 1862, 19 Jahre vor dem ersten Telefonbuch.

## Messung

Beurteilt sind Paare in `data/review/m3_stichprobe.csv`. Die Sichtprüfung am gedruckten
Text beider Einträge hat Claude vorgenommen, nicht die Projektmitarbeitenden.
- **Stichproben 1–4** dienten zum Einstellen der Regeln. Jede hat Fehler gezeigt, die danach
  behoben wurden: abgekürzte Strassen, Einträge ohne erkannten Vornamen, verlesene Zeilen
  mit gleicher Nummer, gleiche Zeilen ohne Nummer, Nachfolger, «MmeVve».
- **Stichprobe 5** wurde nach dem letzten Regelwechsel gezogen und ist die Messung.

| Schicht | n | richtig | unklar | falsch | Präzision |
|---|---|---|---|---|---|
| Personen, nur Telefonbuch | 20 | 20 | 0 | 0 | 100 % |
| Personen mit Adressbuch | 10 | 10 | 0 | 0 | 100 % |
| Firmen | 10 | 10 | 0 | 0 | 100 % |
| erster und letzter Eintrag, ≥ 10 Jahre | 15 | 14 | 1 | 0 | 93–100 % |

**Vollständigkeit.** 30 zufällige Telefonbuch-Einträge, je gegen die nächste Ausgabe
derselben Gemeinde (höchstens 3 Jahre später): 6 stehen dort nicht mehr. Von den 24, die
wieder vorkommen, sind 18 gebündelt, 2 verpasst und 4 unklar: **75–92 %**.

In Stichprobe 4 (vor den letzten zwei Regeln) waren es 20 von 25 (80–88 %); auch die
Stichproben 1–3 zeigten bei der Präzision keine Lücke grösser als ein Fall, ausser bei
langen Einheiten (Stichprobe 1: ein Fehler, ein Geschäft und seine Nachfolger).

«Unklar» heisst meist: Vater oder Sohn, Mutter oder Tochter, Firma oder Inhaber. Die
Spanne zählt «unklar» einmal als falsch und einmal als richtig. Bei 10–30 Fällen je Schicht
ist die Unsicherheit gross.

**Was die Bündelung verfehlt** (Stichproben 3–5):
- dieselbe Einheit, einmal als Person und einmal als Firma zerlegt (M1);
- Zeilen, die mit der Nachbarzeile verschmolzen sind;
- Familienname mit Leerzeichen um den Bindestrich («Uhlmann - Eyraud»);
- Umzug in eine andere Gemeinde.

## Normdaten

`scripts/authority.py`, Ergebnis `links/authority.csv` (eine Zeile je Einheit).

**Übernahme der Städte.** Gehört ein Adressbuch-Eintrag mit Normdaten der Stadt
(`data/norm/ab_authority.csv`) zu einer Einheit, erhält die ganze Einheit diese Normdaten:
1 103 Einheiten (320 `wahrscheinlich`, 783 `möglich`). Nennen Einträge derselben Einheit
verschiedene Personen (25 Einheiten), wird die beste Verknüpfung übernommen, aber auf
`möglich` gesetzt.

**Zweiter Abgleich** für Personen ohne Normdaten der Stadt. Kandidaten sind 16 322 Menschen
in Wikidata (`data/ref/wikidata_persons.csv.gz`, geboren 1790–1895, gestorben 1880 oder
später, mit HLS-Artikel oder mit Wohn-, Wirkungs- oder Sterbeort in einer Schweizer
Gemeinde). Den Ort verbindet die **BFS-Gemeindenummer** (P771 des Ortes = `bfs_today` der
Einheit), nicht der Ortsname. HLS-Nummer und GND stammen aus demselben Wikidata-Eintrag.

Verlangt sind gleicher Familienname, verträglicher Vorname (kein zweiter Vorname der Einheit
widerspricht), ein Alter von 25–80 im ersten Jahr der Einheit, und Wohn-, Wirkungs- oder
Sterbeort in der Gemeinde. Dann:

| Stufe | Belege | Einheiten |
|---|---|---|
| `wahrscheinlich` | ausgeschriebener oder abgekürzter Vorname **und** passender Beruf | 315 |
| `möglich` | Initiale und passender Beruf; oder Vorname und Wohn- bzw. Wirkungsort ohne Beruf | 605 |

«Passender Beruf» heisst gleicher Wortstamm («Architekt» = «architecte») oder gleiche
Berufsgruppe (Arzt = médecin = Dr. med., Advokat = avocat = Jurist, Pfarrer = pasteur =
Theologe, Professor = Hochschullehrer …). Nur wenn genau ein Kandidat die Stufe erreicht,
wird verknüpft. Witwen und Einträge mit «Frau», «Mme» usw. bleiben ohne Abgleich, weil
Wikidata meist den Mann nennt. Firmen bleiben in diesem Schritt ohne Abgleich.

**Was nicht genügt.** In zwei Runden zum Einstellen (nicht als Messung gezählt) zeigte sich:
Name und Sterbeort ohne Beruf waren in 4 von 12 Fällen sicher richtig, 5 falsch
(«Stähelin, Karl, Chauffeur» ist nicht der Internist Rudolf Staehelin); Name und Wohn- bzw.
Wirkungsort ohne Beruf in 4 von 13, 3 falsch. Mit passendem Beruf waren alle 24 Fälle
richtig.
Diese Regeln sind danach festgelegt worden.

**Messung** (`data/review/m3_normdaten.csv`, nach dem Festlegen gezogen, beurteilt von
Claude an Telefonbuch-Eintrag und Wikidata):

| Stufe | n | richtig | unklar | falsch | Präzision |
|---|---|---|---|---|---|
| `wahrscheinlich` | 30 | 29 | 1 | 0 | 97–100 % |
| `möglich` | 20 | 14 | 5 | 1 | 70–95 % |

Zusammen tragen 1 405 Einheiten eine HLS-Nummer und 1 844 eine GND. Dieselbe Person kann
mehreren Einheiten zugeordnet sein (359 Personen): meist Einheiten, die getrennt blieben,
selten Wohnung und Geschäft in zwei Gemeinden (28).

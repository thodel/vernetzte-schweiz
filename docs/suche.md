# Erweiterte Suche (M7)

Die Namenssuche (`#/suche`) sucht vom Anfang des Familien- bzw. Firmennamens her. M7 fügt
hinzu:
- **Ähnliche Namen** (Schalter): Schreibvarianten und Lesefehler, siehe unten;
- **Vornamen in anderer Sprachform**: «Burckhardt Charles» findet «Burckhardt, Carl»
  (Liste der Sprachformen aus M2, `site/data/forenames.json`);
- **weitere Filter**: Jahre (Regler, ein Jahr oder ein Bereich), Art (Person, Firma), nur
  mit Normdaten, Quelle (Telefon-/Adressbuch); Sortierung nach Name, Gemeinde oder erstem
  Jahr.

## Ähnliche Namen

`scripts/fuzzy.py`, gleich gerechnet in `site/assets/pages.js` (`tests/test_fuzzy.py` hält
die im Browser nachgerechneten Werte fest).

1. **Namensschlüssel** `fkey()`: ohne Akzente (œ = oe), dann die Schreibvarianten aus M2
   eingeebnet (y/i, ß/ss, th/t, ck/k, dt/t, tz/z, ph/f, Doppelkonsonanten, ä/ae).
   Gleicher Schlüssel = gleicher Name: Meyer = Meier, Bürgi = Bürgy, Trösch = Trœsch. Diese
   Varianten sind immer dabei.
2. **Gewichtete Damerau-Levenshtein-Distanz** auf dem Schlüssel: Einfügen, Löschen,
   Ersetzen, Vertauschen kosten 1; typische Verwechslungen der Texterkennung 0,5 (b/h, n/u,
   l/i, l/t, c/e, m/n …); «ii» gilt als «u», «rn» als «m». Schwelle nach Länge des
   Schlüssels: bis 3 Buchstaben 0,5, bis 6 Buchstaben 1, länger 2.
3. **Ähnliche Namen werden nicht von selbst einbezogen.** Sie erscheinen als Schaltflächen
   mit der Zahl der Einheiten; ein Klick nimmt einen Namen dazu. Gestrichelt hervorgehoben
   sind seltene Namen, die nur durch einen typischen Lesefehler abweichen.

Die ganze Liste der Namensschlüssel (29 000, gepackt 230 KB) lädt der Browser einmal
(`site/data/keys.json.gz`) und rechnet die Distanz selbst; danach lädt er nur die Teile des
Suchindex der gewählten Namen.

## Messung

Beurteilt von Claude, nicht von den Projektmitarbeitenden: `data/review/m7_namen.csv`.

**Prüfsatz.** Aus den Telefonbüchern: gleiche Gemeinde, gleiche Nummer, gleicher
Anfangsbuchstabe des Vornamens, höchstens zwei Jahre Abstand, aber verschiedener
Namensschlüssel (Distanz bis 3): 1 560 Paare, davon 90 zufällig gezogen und beurteilt.
83 sind dieselbe Person mit verlesenem oder anders geschriebenem Namen (Imbach/Imhach,
Keiler/Keller, Pestaiozzi/Pestalozzi), 3 verschiedene Personen, 4 unklar.

**Was das am Plan geändert hat.** Viele Lesefehler betreffen den ersten Buchstaben
(Hager/Eager, Haase/Baase, Nägeli/Hägeli, Granger/Branger). Die geplante Regel «erster
Buchstabe gleich» hätte sie verloren; sie ist weggefallen.

| Schwelle | Paare gefunden (von 83) | Paare «verschieden» gefunden (von 3) | ähnliche Namen je Suche (Median, Höchstwert) |
|---|---|---|---|
| eng (≤4: 0,5 · ≤7: 1 · länger 1,5) | 69 | 0 | 3, 26 |
| **normal** (≤3: 0,5 · ≤6: 1 · länger 2) | **76** | 0 | 8, 109 |

Gewählt ist «normal». Von 83 Paaren erscheinen 78 als Schaltfläche (Suche nach dem
häufigeren Namen), 76 innerhalb der Schwelle des kürzeren Schlüssels.

**Warum nichts von selbst dazukommt.** Bei 40 zufälligen Suchnamen liefert «normal» im
Median 8 ähnliche Namen, die meisten eigene Namen (Keller: Heller, Koller, Zeller). Geprüft
wurde eine Vorauswahl «Distanz ≤ 0,5 und höchstens ein Zehntel so häufig wie der gesuchte
Name»: Von 17 vorausgewählten Namen waren 7 Lesefehler, 5 eigene Namen (Murer, Luchs,
Schorer), 5 unklar; sie hätte nur 28 der 83 Paare gefunden. Deshalb wählt die Seite nicht
selbst, sondern hebt diese Namen nur hervor.

## Grenzen

- Ähnliche Namen setzen den ganzen Familiennamen voraus, nicht nur seinen Anfang.
- Die Distanz kennt keine Lautregeln (Schmid/Schmied/Smid zählen als Zeichenabstand).
- Der Prüfsatz stammt aus Paaren gleicher Nummer: Er misst, ob Lesefehler gefunden werden,
  nicht, ob jemand nach «Mayer» auch «Maier» sucht (das macht der Schlüssel).

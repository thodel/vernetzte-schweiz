# Historisches Grundbuch Basel (EOS)

Das Historische Grundbuch Basel (HGB), aufbereitet im Projekt «Economies of Space» der
Universitäten Bern und Basel, verzeichnet die Basler Liegenschaften mit ihren Besitzern und
Bewohnern von etwa 1400 bis 1700: [eos_persons](https://thodel.github.io/eos_persons/), Repo
[thodel/eos_persons](https://github.com/thodel/eos_persons).

Die Personen dort lebten 150 bis 450 Jahre vor den Adress- und Telefonbüchern. Verbunden wird
darum nicht die Person, sondern der **Wohnort**: das Haus, in dem jemand 1862–1914 wohnte oder
arbeitete, und was das Grundbuch über dieses Haus weiss.

Skript: [scripts/eos_link.py](../scripts/eos_link.py) → `links/eos_haeuser.csv`,
`data/norm/eos_stats.json`. Die Dossiers sind auf einen Commit gepinnt (`EOS_COMMIT`) und liegen
als Abzug in `data/ref/eos/`.

## Grundlage

- **Grundbuch:** 3 700 Dossiers, davon 3 378 Liegenschaften, in 117 Strassen der Altstadt.
  - Jedes Dossier ist unter der heutigen Adresse geführt («Aeschenvorstadt 3», «Aeschengraben
    4-16», «Freie Strasse Theil von 35 neben 33»).
  - Es hat einen Punkt (LV95), die Jahre der Belege und die Personen mit Jahren und Berufen.
  - Dazu kommen die Hausnamen in ihren alten Schreibungen («Hus zem roten Juden», «Hus zer
    Megt»).
- **Vernetzte Schweiz:** alle Einträge in Basel mit Strasse:
  - das Adressbuch 1862: 15 478 Einträge;
  - die Telefonbücher 1880–1914: 95 464 Einträge.

  Neuere Strassen (Austrasse, Güterstrasse) liegen ausserhalb des Grundbuchs.

## Verknüpfung

1. **Strassennamen angleichen:**
   - Varianten «A / B» einzeln, Klammerzusätze weg, ohne «St.»;
   - ß, th und Umlaute eingeebnet, «Strasse» = «Str.»;
   - «Johanns-» = «Johann-», ebenso Peter, Leonhard, Alban, Martin, Clara, Elisabeth.
2. **Adresse:** Strasse und Hausnummer des Eintrags gleich einer Adresse im Grundbuch.
   Nummernbereiche bis 20 Nummern und Listen werden aufgelöst; «Theil von 35» zählt als 35.
3. **Hausname:** «zum Wolf», «zur Mägd» im Eintrag gegen die Hausnamen des Grundbuchs an
   derselben Strasse. Verglichen wird das Hauptwort ohne «Hus», «Herberg», «Gesellschaft» und
   ohne Eigenschaftswörter («wilden», «roten»), in angeglichener Schreibung («Megt» = «Mägd»,
   «Wolff» = «Wolf»).
4. Ein Eintrag mit mehr als drei möglichen Häusern bleibt ohne Haus.
5. **Gleicher Name im Haus:** Kommt der Familienname der Einheit unter den Personen des Hauses
   vor, steht das dabei. Gleicher Name heisst nicht gleiche Familie.

## Prüfung der Hausnummern

Das Grundbuch nennt heutige Nummern, die Bücher die Nummern ihrer Zeit. Ob sie übereinstimmen,
zeigen die Hausnamen. Kennt das Grundbuch einen Hausnamen aus einem Eintrag an derselben
Strasse, wird verglichen, unter welcher Nummer er dort steht.

| Quelle | gleiche Nummer | höchstens zwei daneben | anderswo | n |
|---|---|---|---|---|
| Telefonbücher 1880–1889 | 23 | 6 | 1 | 30 |
| Telefonbücher 1890–1899 | 49 | 6 | 0 | 55 |
| Telefonbücher 1900–1909 | 24 | 11 | 13 | 48 |
| Telefonbücher 1910–1914 | 12 | 0 | 2 | 14 |
| **Telefonbücher zusammen** | **108 (73 %)** | **23** | **16** | **147** |
| Adressbuch 1862 | 2 | 0 | 2 | 4 |

**Lesart:**
- Die Telefonbücher nummerieren wie heute: 73 % gleich, 89 % bis auf zwei Nummern.
- Abweichungen um eine oder zwei Nummern kommen von Häusern, die heute anders aufgeteilt sind
  («Theil von 35 neben 33»).
- Was weiter weg liegt, sind meist zwei Häuser gleichen Namens an einer Strasse («zum Greifen»
  an der Greifengasse 17 und 35).
- Für das Adressbuch 1862 reichen vier Fälle nicht. Basel hat die Häuser 1862 nach Strassen
  nummeriert; ob diese Nummern den heutigen entsprechen, ist hier nicht geprüft.

## Stufen und Ergebnis (19.11.2026)

| Stufe | Bedeutung | Paare Einheit–Haus |
|---|---|---|
| `sicher` | Adresse und Hausname stimmen überein | 28 |
| `wahrscheinlich` | Hausname an derselben Strasse, oder Adresse aus einem Telefonbuch | 6 375 |
| `möglich` | nur Adresse, nur aus dem Adressbuch 1862 | 9 594 |

- **Umfang:** zusammen 15 997 Paare, 10 207 Einheiten, 2 582 Häuser.
- **Gleicher Name im Haus:** 87 Einheiten tragen einen Familiennamen, der im Grundbuch im selben
  Haus vorkommt.

## Auf der Seite

**Die Seite einer Basler Einheit**
- Sie zeigt unter «Historisches Grundbuch Basel (EOS)» bis zu vier Häuser, die sichersten
  zuerst.
- Je Haus stehen da:
  - Adresse im Grundbuch, mit Link auf die Karte von EOS, die das Haus öffnet
    (`map.html?dossier=<ID>`, dafür in eos_persons ergänzt);
  - Jahre im Grundbuch und Zahl der Personen;
  - Stufe und Beleg mit der Adresse des Eintrags;
  - bei gleichem Familiennamen ein Link auf die Personensuche von EOS (`index.html?q=<Name>`).

## Grenzen

- Es ist dasselbe Haus, nicht dieselbe Person und meist nicht dieselbe Familie.
- Das Grundbuch reicht bis etwa 1700. Was dazwischen geschah (Abbruch, Teilung,
  Zusammenlegung), steht nur in den Gültigkeitsjahren der Dossiers. Diese sind nicht gegen die
  Jahre der Einträge geprüft.
- Hausnamen in den Telefonbüchern sind oft Geschäftsnamen («Restaurant zum Sternenberg»). Sie
  zählen nur, wenn das Grundbuch denselben Namen an der Strasse kennt.
- Die Altstadt ausserhalb der 117 Strassen des Grundbuchs und alle Vororte bleiben ohne Haus.

# Wege von Frauen über den Zivilstand (Versuch, M10b)

Die Wanderungen (M10, [wanderungen.md](wanderungen.md)) verbinden Einträge über den
Familiennamen. Frauen wechseln ihn mit der Heirat und fehlen dort darum fast ganz. Dieser
Versuch verbindet ihre Einträge über den Zivilstand: «Frl. Lina Blattner» → «Lina
Jungi-Blattner» → «Witwe», oder vom Ehemann zu seiner Witwe. Es ist mehr eine Wanderung des
Zivilstands als eine des Wohnorts. Die Verbindung über Gemeinden hinweg ist mitgerechnet, um
zu prüfen, ob sie trägt.

Skript: [scripts/frauen_wege.py](../scripts/frauen_wege.py) → `links/frauen_wege.csv`,
`data/norm/frauen_wege_stats.json`. Messung: [scripts/measure_frauen.py](../scripts/measure_frauen.py)
→ `data/review/frauen_wege.csv`, `data/norm/frauen_wege_quality.json`.

## Vorgehen

**Einträge**
- Grundlage sind alle Einträge der Adress- und Telefonbücher (312 187 mit erkennbarem Zivilstand
  oder Geschlecht), nicht die Einheiten aus M3: Diese bündeln nach dem Familiennamen.
- Einträge mit gleicher Gemeinde, gleichem Zivilstand und gleichem Namen (Familien-, Geburts-,
  Vorname) bilden eine **Spur** mit Jahren, Nummern, Adressen und Berufen.

**Zivilstand je Eintrag**

| Zivilstand | Woran erkannt | Spuren |
|---|---|---|
| `witwe` | Wwe., Witwe, Wittwe, Wb., Vve, veuve | 16 698 |
| `verheiratet` | Frau, Mme, geb., née; Frau mit Allianzname («Wächter-Lindenmann»: der zweite Name ist ihr Geburtsname) | 22 844 |
| `ledig` | Frl., Fräulein, Mlle, Jgfr. (ausdrücklich) | 1 718 |
| `ledig?` | Frau nach Vorname oder Berufsform (Näherin), ohne jedes Zeichen einer Ehe (vermutet) | 26 442 |
| `mann` | Mann nach Vorname (für Ehemann → Witwe) | 84 034 |

Steht bei einer Witwe ein Männername («Suter, Jakob, Becks Wittwe»), ist er der Vorname ihres
Mannes.

**Übergänge**

| Übergang | Bedingung | wichtigste Belege |
|---|---|---|
| Ehemann → Witwe | gleicher Ehename und gleiche Gemeinde; der Vorname des Mannes steht bei der Witwe, oder der Allianzname ist gleich; die Witwe erscheint bis 5 Jahre nach der letzten Nennung des Mannes, im selben Jahr nur mit derselben Telefonnummer | Nummer, Adresse, Beruf («Abwarts Wittwe») |
| Ehefrau → Witwe | gleicher Ehename, Vorname verträglich, Geburtsname gleich oder nicht genannt; die Witwe erst nach der letzten Nennung als Ehefrau | Geburtsname, Adresse |
| ledig → verheiratet (oder → Witwe) | Familienname der Ledigen = Geburtsname der Verheirateten; Vorname verträglich; später, höchstens 20 Jahre | Vorname, Gemeinde, Beruf |

**Punkte und Stufen**
- Vorname ausgeschrieben gleich 2, abgekürzt 1. Haben beide Seiten zwei Vornamen, beginnen sie
  Stelle für Stelle gleich.
- Gleiche Gemeinde 2, gleiche Telefonnummer 3, gleiche Adresse 2, gleicher Beruf 1, seltener
  Name 1, gleicher Geburtsname 3, Allianzname 3, Vorname des Mannes 2, «Frl.» ausdrücklich 1.
- Jedes Paar muss in beide Richtungen eindeutig sein, sonst fällt es weg (mehrdeutig).
- `wahrscheinlich` braucht dieselbe Gemeinde, ≥ 6 Punkte und einen starken Beleg (Nummer,
  Adresse, Geburts- oder Allianzname). `möglich` braucht ≥ 5 Punkte, oder ≥ 4 in derselben
  Gemeinde. Der Rest ist `schwach`. Über Gemeinden hinweg höchstens `möglich`.

## Ergebnis (18.11.2026)

| Übergang | Paare | gleiche Gemeinde | wahrscheinlich | möglich | schwach | mehrdeutig (weggefallen) |
|---|---|---|---|---|---|---|
| Ehemann → Witwe | 187 | 187 | 148 | 39 | 0 | 22 |
| Ehefrau → Witwe | 342 | 301 | 244 | 50 | 48 | 402 |
| ledig → verheiratet | 696 | 434 | 17 | 344 | 335 | 2 099 |
| ledig → Witwe | 286 | 156 | 3 | 107 | 176 | 969 |

Ganze Ketten ledig → verheiratet → Witwe gibt es 8. Die Bücher liegen in grossen Abständen vor
(Zürich 1867, 1875, 1885, 1900, 1914), und die Ehefrau steht selten mit eigenem Eintrag im Buch.

## Messung

Beurteilt von Claude, nicht von den Projektmitarbeitenden, nach den gedruckten Einträgen beider
Spuren. «richtig» heisst: etwas Gemeinsames ausser dem Namen bestätigt das Paar (Adresse, Beruf
wie «Fabrikinspektors Wittwe», Telefonnummer).

| Gruppe | n | richtig | unklar | falsch | Präzision |
|---|---|---|---|---|---|
| Ehemann → Witwe | 15 | 10 | 4 | 1 | 67–93 % |
| Ehefrau → Witwe | 15 | 12 | 3 | 0 | 80–100 % |
| ledig → verheiratet, gleiche Gemeinde | 15 | 2 | 13 | 0 | 13–100 % |
| ledig → verheiratet, andere Gemeinde | 10 | 0 | 10 | 0 | 0–100 % |
| ledig → Witwe | 10 | 0 | 10 | 0 | 0–100 % |

**Lesart:**
- **Ehemann → Witwe** gelingt am besten. Die Witwe führt oft das Geschäft weiter («Randegger,
  Conrad, Bierwirtschaft» → «Randegger-Wirth, Josephine, Wittwe, Wirthin zur bayrischen
  Bierhalle»). Sie nennt den Beruf des Mannes («Abwarts Wittwe») oder behält Adresse und
  Telefonnummer.
- Der eine Fehler (Ehemann und «seine Witwe» im selben Band) führte zur Regel «im selben Jahr
  nur mit derselben Nummer». Danach fallen er und vier unklare Paare weg. Alle beurteilten
  Paare, die bleiben, sind richtig (10 von 10). Das ist eine Prüfung, keine neue Messung.
- **Ehefrau → Witwe** ist ebenso verlässlich. Geburtsname, Adresse und Beruf gehen mit
  («Fuchs-Jaggi, Anna, maîtresse de pension» → «veuve, m. de pension»).
- **ledig → verheiratet** lässt sich aus den Büchern nicht prüfen. Eine ledige «Anna Wieland»
  und eine spätere «Anna geb. Wieland» haben ausser Vor- und Geburtsname meist nichts
  gemeinsam: anderer Name, andere Adresse, oft kein Beruf mehr. Bestätigen liessen sich nur zwei
  Paare mit gleichem Beruf und Ort (Damenschneiderin Lina Blattner, Hebamme Louise Fischer).
  Widerlegen liess sich keines. Die Zahl sagt darum nichts über die Präzision.
- **Über Gemeinden hinweg** trägt es nicht: In 10 Paaren ist keines bestätigt. Aus den Büchern
  allein lässt sich eine Frau nach Heirat und Umzug nicht wiederfinden; dazu bräuchte es
  Zivilstandsregister oder Bürgerbücher.

## Auf der Seite

- **Migration › Wege von Frauen** (`#/wanderungen?v=frauen`): alle Paare als Liste, mit Filtern
  nach Übergang, Stufe (Standard: wahrscheinlich und möglich) und Gemeinde, mit der Zahl je
  Übergang. Beide Seiten sind verlinkt, die gedruckten Einträge lassen sich aufklappen.
  Übergänge von ledig sind als «nicht prüfbar» gekennzeichnet.
- **Seite einer Einheit:** Unter «Zivilstand (Versuch)» stehen die Gegenstücke der Stufen
  `wahrscheinlich` und `möglich`: die Witwe zu einem Mann, der Mann zur Witwe, die Ehefrau
  zur Witwe und umgekehrt.

## Grenzen

- Ledige Frauen ohne «Frl.» sind nur vermutet (weiblicher Vorname, Berufsform). Ein Eintrag wie
  «— Anna, Spetterin» kann auch eine verheiratete Frau sein.
- Viele Witwen und Ehefrauen stehen ohne eigenen Vornamen («Frau Wwe.», «— geb. Fricker»); sie
  lassen sich nur über den Mann verbinden.
- Die Telefonbücher nennen fast nur Anschlussinhaber, die Adressbücher liegen nur für einzelne
  Jahre vor. Zwischen zwei Bänden können Heirat und Tod liegen.
- Mehrdeutig sind vor allem häufige Namen («Anna geb. Huber»); sie fallen weg.

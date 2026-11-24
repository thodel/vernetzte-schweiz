# Neulesung von Band 2a 1911–1914

Band 2a ist der Berner Band der gesamtschweizerischen Telefonbücher: zuerst die Stadt Bern als eigener Block,
danach alle Orte der Netzgruppe in einem Alphabet (Kanton Bern ohne Jura, Solothurn, dazu einzelne Orte in
Freiburg und Luzern), mit Überschriften wie «Trub (Langnau i. E.)».

In der Quelle (DHBern/PTT_phonebook_data_tsv, Charge B) fehlen viele dieser Überschriften, wie in Band 2b:

- Burgdorf steht unter «Büren zum Hof» und hat 1913 fünf Einträge (Regionalbuch 1910: 239).
- Bis zu 889 Einträge eines Bands stehen unter «Bibern (Hessigkofen)», bis zu 590 unter «Siselen (Aarberg)».
- Die Quelle kennt 596 bis 637 verschiedene Überschriften je Band, gedruckt sind rund 870 bis 900.

Darum sind die vier Bände ganz aus den Seitenbildern des PTT-Archivs neu gelesen, mit dem Verfahren von Band 2b
([neulesung_2b.md](neulesung_2b.md)): drei Läufe mit qwen3.8-27b (Massstab 1,3, 1,0 und 1,6), Abstimmung je Feld,
die Quelle als vierte Stimme für den Namen. Die Quelle selbst bleibt unverändert.

## Was der Band anders macht

`scripts/neulesung/convert_2b.py` liest beide Bände; für Band 2a kamen fünf Regeln dazu. Die vier veröffentlichten
Tabellen von Band 2b kommen mit dem erweiterten Skript unverändert heraus (geprüft Byte für Byte).

- **Zusätze am Ortsnamen.** «Ried (b. Frutigen) (Frutigen)» wird «Ried b. Frutigen» mit Zentrale Frutigen. In
  «Langnau i. E.» ist «E.» kein Kürzel für Dienststunden und bleibt stehen; Abkürzungen behalten ihren Punkt
  («Muri b. B.», «Biel, B.»). «(Bern)» ist die Zentrale, kein Kantonszusatz.
- **Dienststunden hinter der Zentrale** fallen weg («Bümpliz (Bern) 6/7 v bis 9 n»).
- **Kolumnentitel.** 1911 stehen sie in Versalien («B BERN», «J=K BERN») und nennen im Alphabet nur den Ort am
  Seitenkopf («Aarberg»); 1912–1914 nennen sie die Spanne («Belp=Biel»), die nicht als Ort zählt. Steht im Titel
  «Langnau» und in der Überschrift «Langnau i. E.», bleibt die Überschrift.
- **Landesausstellung 1914.** Vor dem Verzeichnis stehen sieben farbige Seiten mit den Anschlüssen der
  Schweizerischen Landesausstellung in Bern, geordnet nach «Neufeld», «Mittelfeld», «Viererfeld». Das sind keine
  Orte; die 408 Einträge gehören zu Bern (`FRONT`), wie in der Quelle.
- **Erfundene Seiten.** Auf leeren Seiten scheint die Rückseite durch. Das Modell erfindet dort eine Liste mit
  einem einzigen Namen und fortlaufenden Nummern, in jedem Lauf eine andere (1913, Bild 19: 198-mal «Aeppli-Roth»,
  185-mal «Aeschbach», 89-mal «Administration der»). `invented()` leert eine Seite in einem Lauf, wenn ein Name
  vier Fünftel von mindestens 20 Einträgen stellt und nicht alle drei Läufe denselben Namen so oft lesen. Das
  trifft drei Bilder (1913: 19 und 198; 1914: 118). Die 40 Feuer- und Unfallmeldestationen der Landesausstellung
  stehen wirklich untereinander und bleiben. In den Tabellen von Band 2b steht keine solche Seite.

Die Quelle zählt ihre Seiten anders als die Bilder (1914 liegen 23 Bilder vor der ersten Verzeichnisseite); der
Versatz wird je Bild aus den gemeinsamen Rufnummern bestimmt, im Bereich 4 bis 32.

## Ergebnis

Gelesen ab Bild 8. `Orte` sind verschiedene Überschriften, `Gemeinden` die Gemeinden von 1914 nach `places.py`.

| Band | Bilder | Einträge neu | Quelle | Orte neu | Quelle | Gemeinden neu | vorher | ohne Gemeinde neu | vorher |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 2a 1911 | 168 | 11 041 | 10 615 | 867 | 596 | 413 | 326 | 42 | 350 |
| 2a 1912 | 184 | 11 801 | 11 459 | 861 | 632 | 424 | 338 | 37 | 584 |
| 2a 1913 | 194 | 12 693 | 12 330 | 884 | 629 | 423 | 338 | 47 | 508 |
| 2a 1914 | 218 | 13 914 | 13 547 | 897 | 637 | 424 | 328 | 57 | 655 |

(Die Tabellen haben 11 043, 11 809, 12 708 und 13 922 Zeilen; `ingest_ptt.py` lässt Zeilen ohne Namen weg.)

Von den Einträgen ohne Gemeinde blieben nach der Neulesung zuerst 242 bis 321 je Band: Ortschaften, die 1914 keine
eigene Gemeinde waren und die `places.py` nicht eindeutig zuordnet (Wengen und Mürren in Lauterbrunnen,
Ostermundigen in Bolligen, Wabern in Köniz, Gümligen in Muri bei Bern, Schwarzenburg in Wahlern) oder deren
Gemeinde abgekürzt steht («Wangen a. A.»). 39 Zeilen in `data/ref/place_aliases.csv` ordnen sie zu; das wirkt auch
auf die Berner Regionalbücher 1898–1910. In allen Telefonbüchern zusammen sind 24 139 statt 27 338 Einträge ohne
Gemeinde, und 634 wechseln die Gemeinde (Schwarzenburg stand unter Guggisberg, Hohfluh unter Meiringen,
Dürrenast unter Thun, Papiermühle unter Bern).

Einträge je Gemeinde, vorher und nachher:

| Gemeinde | 1911 | 1912 | 1913 | 1914 |
|---|---|---|---|---|
| Burgdorf | 218 → 259 | 152 → 285 | 5 → 305 | 46 → 316 |
| Langnau im Emmental | 14 → 122 | 13 → 132 | 65 → 146 | 22 → 158 |
| Bern | 4 610 → 4 746 | 4 959 → 5 101 | 5 384 → 5 472 | 6 191 → 6 365 |

Dazu 1913/14: Grenchen 1 → 149 und 39 → 175, Spiez 18 → 117 und 19 → 125, Meiringen 8 → 95 und 6 → 97. Unter
«Büren zum Hof» stehen noch 2 bis 3 Einträge (vorher bis zu 259), unter «Stalden (VS)» einer (vorher 87 und 93;
gemeint war wohl Stalden im Emmental).

Ausserhalb der vier Bände wechseln 52 Einträge die Gemeinde, weil `places.py` Orte auch über die Familiennamen
benachbarter Jahrgänge zuordnet.

Abstimmung (Spalte `Check`):

| | 1911 | 1912 | 1913 | 1914 |
|---|---:|---:|---:|---:|
| Mehrheit überstimmt Lauf A: Name | 256 | 224 | 361 | 339 |
| … Rest | 476 | 561 | 715 | 637 |
| … Ort | 184 | 84 | 145 | 142 |
| Name nach der Quelle (`quelle`) | 167 | 227 | 215 | 281 |
| `uneins` | 33 | 36 | 27 | 49 |
| `ergänzt` | 3 | 3 | 3 | 19 |
| `nur-A`, `zwei-lesungen` | 4 | 2 | 12 | 7 |
| `nummer-quelle` | 0 | 0 | 0 | 30 |

## Prüfung am Seitenbild

24 zufällige Einträge aus den vier Tabellen (Seed 19111914), verglichen mit dem Ausschnitt des Seitenbilds.
23 lagen im Ausschnitt.

- Rufnummer, Name und Ort: 23 von 23 richtig.
- Zusatz: 19 von 23 richtig. Die Fehler: «Digglemann» für «Diggelmann», «Gips- u. Malermeister» für «Gipser- u.
  Malermeister», und zweimal ein Trennstrich vom Zeilenende («Hôtel-laube», «Dro-guérie», dort auch ein Akzent
  zu viel).

## Folgen für die abgeleiteten Zahlen

- Einheiten: 491 791 statt 495 788, bei 1 020 732 statt 1 017 210 Einträgen ([einheiten.md](einheiten.md); beide
  Stände mit Zürich 1901, das am selben Tag dazukam). Mit den Ortschaften aus `place_aliases.csv`: 492 457
  Einheiten und 1 023 615 Einträge.
- Eine öffentliche Sprechstelle bis 1914 haben 1 685 statt 1 727 Gemeinden (mit den Ortschaften aus der Liste 1 691): Die falschen Überschriften hatten
  Sprechstellen auf Gemeinden verteilt, die keine hatten ([infrastruktur.md](infrastruktur.md)).
- Der Namensabgleich über das Regionalbuch greift noch für 9 714 Zeilen (vorher 11 427).
- Die Reihen je Stadt zeigen neu auch Grenchen und Langnau im Emmental (23 statt 21 Städte).
- Wanderungen: 480 statt 482 Paare, mit den Ortschaften aus der Liste 484 ([wanderungen.md](wanderungen.md)).

## Was offen bleibt

- **Ohne Gemeinde** bleiben 37 bis 57 Einträge je Band: Wichtrach und Konolfingen (1914 je zwei Gemeinden),
  Goldiwil (seit 1913 bei Thun), verlesene oder zusammengezogene Überschriften («Habstetten (Papiermühle, Bern)»).
  «Büren» ohne Zusatz bleibt in den Regionalbüchern ohne Gemeinde.
- **Trennstriche vom Zeilenende** bleiben ausser vor dem Grundwort einer Strasse stehen, wie in Band 2b.
- **Zeilen ohne Rufnummer** (Abteilungen einer Behörde, Verweise) stehen in der Tabelle (54 bis 99 je Band).
- Die Bände 1 und 3 sind seit dem 24.11.2026 ebenfalls neu gelesen ([neulesung_13.md](neulesung_13.md)).

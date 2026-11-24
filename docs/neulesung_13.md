# Neulesung der Bände 1 und 3 1911–1914

Band 1 ist der Band der Westschweiz: zuerst Genève als eigener Block, danach alle Orte der Netzgruppe in einem
Alphabet (Waadt, Neuenburg, Freiburg, Wallis, Berner Jura), darin Lausanne und La Chaux-de-Fonds als Blöcke mit
Überschrift in Versalien. Band 3 ist der Band der Ostschweiz: zuerst Zürich, danach Zürich-Land, St. Gallen,
Appenzell, Thurgau, Schaffhausen, Glarus, Graubünden und Zug in einem Alphabet, darin St. Gallen als Block.

In der Quelle (DHBern/PTT_phonebook_data_tsv, Charge B) fehlen viele Überschriften, wie in den Bänden 2a und 2b:

- Lausanne steht in Band 1 1911 unter «LAUSANNE» (2 879), La Chaux-de-Fonds unter «Ea Chaux (Ste-Croix)» (1 503),
  Neuchâtel unter «Montmirial (St-Blaise. Neuchâtel)» (909), Montreux zum Teil unter «Naz (Echallens)» (1 101).
- In Band 3 1911 steht Winterthur unter «Winterberg (Kemptthal, Winterthur)» (949), St. Gallen unter «ST. GALLEN»,
  Davos unter «Elektrizitätswerke Davos», Chur, Frauenfeld, Herisau, Zug, Rorschach und Glarus haben keine eigene
  Überschrift.
- Die Quelle kennt 491 bis 1 098 verschiedene Überschriften je Band, die Neulesung 1 272 bis 1 710.

Darum sind die acht Bände ganz aus den Seitenbildern des PTT-Archivs neu gelesen, mit dem Verfahren von Band 2a und
2b ([neulesung_2a.md](neulesung_2a.md), [neulesung_2b.md](neulesung_2b.md)): drei Läufe mit qwen3.8-27b (Massstab
1,3, 1,0 und 1,6), Abstimmung je Feld, die Quelle als vierte Stimme für den Namen. Die Quelle selbst bleibt
unverändert.

## Was die Bände anders machen

`scripts/neulesung/convert_2b.py` liest alle vier Bände; für die Bände 1 und 3 kamen drei Regeln dazu. Die
Tabellen der Bände 2a und 2b kommen mit dem erweiterten Skript unverändert heraus (geprüft Byte für Byte).

- **Überschriften in Versalien.** «GENEVE» unter «Genève» lässt den Akzent weg; die bisherige Schreibung bleibt.
- **Buchstabe und Ort zusammengezogen.** Der Kolumnentitel «C LAUSANNE» nennt den Abschnitt und die Stadt. Das
  Modell liest ihn oft ohne Leerzeichen («CLAUSANNE», «FLAUSANNE», «PLAUSANNE», auch als Überschrift). Ein Wort in
  Versalien, das nach dem ersten Buchstaben der laufende Ort ist, wechselt den Ort nicht (`same_in_capitals()`);
  das betrifft 4 bis 378 Zeilen je Band, «EGENEVE» 1913 dazu.
- **Ort mit Bindestrich im Kolumnentitel.** Steht oben auf der Seite die Überschrift «La Chaux-de-Fonds» und im
  Kolumnentitel derselbe Name, galt die Überschrift bisher als mitgelesener Kolumnentitel und fiel weg: 1912 und
  1914 standen so 1 639 und 1 839 Einträge der Stadt unter «La Chaux-d'Abel». Weggelassen wird eine solche
  Überschrift nur noch, wenn der Titel eine Spanne zweier Orte ist (`is_span()`: «Gersau-Giubiasco»,
  «Romanshorn - Rorbas»), nicht bei «La Chaux-de-Fonds». Nebenbei kommen 11 Einträge von Au bei Wädenswil (Schloss
  Au, Gasthaus zur «Au») aus «Au bei Kradolf» und einzelne Einträge am Seitenkopf an ihren Ort.

**Erfundene Seiten** (`invented()`, siehe Band 2a): die leeren Schlussseiten 1913 Bild 444 und 1914 Bild 471 in
Band 1 (erfundene Hotels) und 1914 Bild 502 in Band 3. In Band 3 1911, Bild 116, stehen wirklich 46 von 67
Einträgen unter «Müller» (Zürich); dort fällt nur Lauf C weg, A und B bleiben.

## Ergebnis

`Orte` sind verschiedene Überschriften.

| Band | Bilder | Zeilen neu | Quelle | Orte neu | Quelle |
|---|---:|---:|---:|---:|---:|
| 1 1911 | 366 | 22 710 | 21 795 | 1 272 | 491 |
| 1 1912 | 392 | 24 156 | 23 390 | 1 293 | 693 |
| 1 1913 | 440 | 26 075 | 25 673 | 1 334 | 692 |
| 1 1914 | 467 | 27 755 | 27 252 | 1 345 | 682 |
| 3 1911 | 420 | 28 316 | 27 321 | 1 639 | 1 074 |
| 3 1912 | 436 | 30 271 | 29 234 | 1 623 | 1 034 |
| 3 1913 | 464 | 32 667 | 31 680 | 1 704 | 1 077 |
| 3 1914 | 498 | 34 510 | 33 309 | 1 710 | 1 098 |

`Gemeinden` sind die Gemeinden von 1914 nach `places.py`; `Einträge` ohne Zeilen ohne Namen.

| Band | Einträge neu | vorher | Gemeinden neu | vorher | ohne Gemeinde neu | vorher |
|---|---:|---:|---:|---:|---:|---:|
| 1 1911 | 22 699 | 21 793 | 806 | 331 | 206 | 1 299 |
| 1 1912 | 24 137 | 23 374 | 821 | 471 | 251 | 271 |
| 1 1913 | 26 060 | 25 671 | 836 | 489 | 289 | 2 108 |
| 1 1914 | 27 732 | 27 250 | 843 | 483 | 343 | 390 |
| 3 1911 | 28 289 | 27 305 | 681 | 504 | 431 | 968 |
| 3 1912 | 30 227 | 29 226 | 696 | 502 | 543 | 1 136 |
| 3 1913 | 32 611 | 31 671 | 725 | 526 | 513 | 1 431 |
| 3 1914 | 34 466 | 33 294 | 731 | 553 | 598 | 1 580 |

Montreux stand in der Quelle zum Teil unter Dörfern wie «Naz (Echallens)». Der Ort lag 1914 in zwei Gemeinden
(Le Châtelard-Montreux und Les Planches); auf Entscheid vom 24.11.2026 gehört «Montreux» ohne nähere Angabe zu
Le Châtelard-Montreux, der grösseren der beiden (964 bis 1 150 Einträge je Band, dazu 38 bis 110 je Regionalbuch
Montreux 1884 und Genève–Lausanne 1885/1890). Sechs Zeilen in `data/ref/place_aliases.csv`: Montreux, Davos-Platz
und Davos-Dorf (Davos), «Commune de Plainpalais», «Commune du Petit-Saconnex» und «Ville de Carouge»; das wirkt
auch auf die Regionalbücher Chur 1894–1909.

Einträge je Gemeinde, vorher und nachher (Auswahl):

- Band 1 1911: Lausanne 2 895 → 3 671, Vevey 0 → 518, Le Locle 15 → 361, Yverdon 2 → 240, Nyon 0 → 207, Morges
  1 → 172; Collonge-Bellerive 554 → 89, Leukerbad 316 → 5, Yens 241 → 1, Nuvilly 211 → 1.
- Band 1 1914: Lausanne 41 → 4 377 (in der Quelle unter «Genève»: Genève 13 621 → 9 493), Vevey 1 → 588,
  Le Locle 1 → 427; Montpreveyres 1 117 → 3, Lignerolle 400 → 1.
- Band 3 1911: Winterthur 718 → 1 010, Davos 0 → 467, Uster 16 → 168, Kreuzlingen 0 → 158, Romanshorn 6 → 161;
  Unteriberg 155 → 9, Weerswilen 140 → 1, Zell (ZH) 143 → 5.
- Band 3 1914: Winterthur 449 → 1 145, Davos 0 → 652, Chur 3 → 565, St. Moritz 98 → 361, Horgen 8 → 194;
  Cham 561 → 52, Lindau 328 → 12, Dättwil 214 → 1.

Abstimmung (Spalte `Check`):

| | 1 1911 | 1 1912 | 1 1913 | 1 1914 | 3 1911 | 3 1912 | 3 1913 | 3 1914 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Mehrheit überstimmt Lauf A: Name | 506 | 492 | 434 | 482 | 1 004 | 796 | 858 | 1 258 |
| … Rest | 1 053 | 931 | 1 011 | 1 124 | 1 554 | 1 623 | 1 716 | 1 764 |
| … Ort | 178 | 137 | 69 | 189 | 231 | 309 | 243 | 117 |
| Name nach der Quelle (`quelle`) | 248 | 408 | 368 | 469 | 935 | 584 | 689 | 755 |
| `uneins` | 52 | 51 | 55 | 42 | 116 | 309 | 406 | 203 |
| `ergänzt` | 2 | 2 | 6 | 2 | 47 | 23 | 38 | 32 |
| `nur-A`, `zwei-lesungen` | 3 | 3 | 2 | 21 | 33 | 14 | 34 | 20 |
| `nummer-quelle` | 0 | 2 | 0 | 25 | 32 | 18 | 72 | 45 |

## Prüfung am Seitenbild

24 zufällige Einträge aus den acht Tabellen (Seed 13111914), verglichen mit dem Ausschnitt des Seitenbilds.
23 lagen im Ausschnitt.

- Rufnummer, Name und Ort: 22 von 23 richtig. Der Fehler: «Diggielmann» für «Diggelmann». Ein weiterer stand
  zuerst unter «La Chaux-d'Abel» statt La Chaux-de-Fonds; das hat die dritte Regel oben behoben.
- Zusatz: 22 von 23 richtig; «Oberhänslí» für «Oberhänsli». Zweimal steht eine Adresse in der Spalte des Vornamens
  («Koechlin-d'Andiran | Pré-aux-Moines», «Privatwohnung | Bolleystr. 41»), der Text ist richtig.
- Unterzeilen («Appartement et ateliers», «Privatwohnung») stehen wie gedruckt als eigene Einträge ohne den Namen
  der Zeile darüber.

## Folgen für die abgeleiteten Zahlen

Gerechnet mit Montreux bei Le Châtelard-Montreux und zusammen mit den Normdaten von Basel nach der Prüfung gegen die EOS-Personen (adressbuecher-basel
53ccb22, vorher b94acb6).

- Einträge 1 488 236 → 1 515 778, Einheiten 568 645 → 550 624 (mit mehr als einem Eintrag 247 307 → 250 108); im
  Telefon- und im Adressbuch 14 274 → 15 949 ([einheiten.md](einheiten.md)). Weniger Einheiten bei mehr
  Einträgen: Einträge von Lausanne, Winterthur oder Davos stehen nicht mehr unter falschen Orten als eigene
  Einheiten.
- Telefon nach Gemeinden ([infrastruktur.md](infrastruktur.md)): 2 786 statt 2 709 Gemeinden haben bis 1914
  einen Eintrag. Ämter und Werke sinken, weil die falschen Überschriften sie auf Dörfer verteilt hatten: In Band 1
  1913 stand ganz Aigle unter «Aclens (Morges)», mit Greffe municipal, Gendarmerie und Préfecture. Bis 1914 eine
  Gemeindekanzlei 589 statt 706 Gemeinden, ein Elektrizitätswerk 223 statt 289, eine öffentliche Sprechstelle
  1 630 statt 1 691.
- Rangliste der Gemeinden ab 5 000 Einwohnern: Genève 18,7 % statt 25,6 % Personen je 100 Haushalte (der Lausanner
  Block zählte mit), neu vorn Davos 18,6 %, Lausanne 18,2 % und Montreux 17,9 %; die Reihen je Stadt zeigen neu Davos und Delémont
  (25 statt 23 Städte).
- Wanderungen 526 → 563 Paare (stark 62, mittel 370, schwach 131; [wanderungen.md](wanderungen.md)).

## Was offen bleibt

- **Montreux** steht ganz bei Le Châtelard-Montreux, auch Einträge, die zu Les Planches gehören (ein Teil des Orts
  lag in Les Planches). Die Telefondichte von Montreux rechnet darum mit der heutigen Gemeinde Montreux als
  Nenner.
- **Trennstriche vom Zeilenende** bleiben ausser vor dem Grundwort einer Strasse stehen, wie in Band 2a und 2b.

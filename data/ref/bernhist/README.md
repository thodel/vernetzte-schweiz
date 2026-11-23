# Werte aus BERNHIST

Dieser Ordner enthält Einzelwerte aus BERNHIST (Historisch-statistische Datenbank des Kantons Bern, Projekt
Christian Pfister, heute bei der Universitätsbibliothek Bern, <https://www.bernhist.ch>), die
`scripts/ref_bernhist.py` und `scripts/durchdringung_bern.py` als Nenner brauchen, und was daraus gerechnet ist.

- **Quelle:** Dump im Repo `ub-unibe-ch/bernhist` (Stand 22.03.2024), lokal in SQLite geladen. Der Dump selbst
  liegt nicht hier. `python scripts/ref_bernhist.py --bernhist <sqlite>` liest die Werte neu aus; ohne den
  Parameter rechnet das Skript Zuordnung, Einheiten und Abgleich aus `werte.csv` neu.
- **Rechte:** Die Nutzungsrechte an den BERNHIST-Daten sind nicht ausgewiesen (die MIT-Lizenz des Repos gilt
  für die Software). Dieser Ordner steht deshalb **nicht** unter der CC0-Freigabe von `data/`; er enthält nur,
  was zum Nachrechnen nötig ist: 5 011 von 1 958 047 Werten.

| Datei | Inhalt |
|---|---|
| `werte.csv` | je Zeile ein Wert: Reihe, Rang (bei doppelten Werten nach `data_entry.id`), Ort, Thema, Jahr, Wert, Nummer im Dump |
| `orte.csv` | BERNHIST-Ort (Einwohnergemeinde) → Gemeinde von 1914 (`hist_code`), Einheit, Methode, Bemerkung |
| `gemeinden_1914.csv` | Gemeinde von 1914 (Kanton BE) → BERNHIST-Ort, Einheit, Status |
| `einheiten.csv` | je Einheit Wohnbevölkerung 1880, 1888, 1900, 1910, Haushalte 1888, Erwerbstätige nach Sektor 1910 |
| `vergleich_bfs.csv` | Bevölkerung 1900 und 1910 gegen `data/ref/population_1850_2000.csv` (BFS) |
| `adressbuch_bern.csv` | Zähler und Quoten der Adressbücher 1883–84 und 1900 aus `thodel/adressbuecher-bern`, `data/abdeckung/abdeckung.csv`, Commit 8692f31 |

Reihen in `werte.csv`: für alle Einwohnergemeinden `bev_1880`, `bev_1888`, `bev_1900`, `bev_1910` (Thema 990),
`haushalte_1888` (543), `erw_1910`, `erw_s1_1910`, `erw_s2_1910`, `erw_s3_1910` (342, 305, 314, 327); nur für
die Stadt Bern (Ort 457) die Nenner der Gruppen (Zivilstand, Ärzte, Spezereigeschäfte, Erwerbszweige 1910 und
die Vergleichswerte von 1856 und 1930). Rang 0 ist bei den Erwerbstätigen 1910 die Reihe im Gebietsstand von
1910, Rang 1 die Reihe im späteren Gebietsstand; siehe `docs/durchdringung_bern.md`.

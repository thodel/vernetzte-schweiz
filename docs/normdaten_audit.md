# Normdaten der Adressbücher: Bestandsaufnahme

Stand 14.11.2026. Geprüft wurden die Checkouts in `~/Repos/adressbuecher-*` (Stand HEAD) und `vernetzte-schweiz` @ 3e32c82.
Zuerst wurde gezählt, dann 90 Verknüpfungen von Hand nachgeprüft: 15 je Stadt, Zufallsstichprobe mit Seed 20261114.
Geprüft wurde jede am HLS-Artikel (`hls`-MCP, `get_article`) und an Human Lineage (`humanlineage`-MCP, `get_by_identifier`, Snapshot 2026-10-10).
Für dieses Dokument wurde nichts verändert und nichts neu gerechnet. Ausnahme: ein Kontrolllauf von `82_normdaten.py` in einer Kopie außerhalb der Repos; er gibt `web/normdaten.csv` von Zürich byte-gleich wieder.

**Kurz:**
- Die Stufe «wahrscheinlich» hält: 27 von 34 Stichproben sind richtig, 2 falsch, 5 unklar.
- Die Stufe «möglich» ist zur Hälfte falsch: 27 von 56 richtig, 23 falsch, 6 unklar.
- Am schlechtesten sind Aarau und Basel bei «möglich» mit dem Beleg «nur Name+Daten». Alle 9 Stichproben dieser Art sind falsch.
- Genau diese 751 Verknüpfungen zeigt vernetzte-schweiz als «möglich» an.
- In Bern und Zürich liefert `82_normdaten.py` wegen eines Fehlers keinen einzigen reinen Wikidata-Kandidaten.
- Gar keine Normdaten haben Bern früh (1795–1848, alle Bände), Zürich 1859 und das kommende `adressbuecher-basel-frueh`.

## 1. Woher die Normdaten kommen

| Repo | Dateien | Skript | Prüfung |
|---|---|---|---|
| aarau | `data/csv/10_authority_links.csv` (630 Zeilen), `32_hls_check.csv` (81) | `scripts/11_authorities.py` (Wikidata-SPARQL, Cache `data/ext/wikidata/`, dazu Metagrid-Cache) | HLS-Treffer am Artikel geprüft (`hls_check`: 195 bestätigt, 35 zweifelhaft, 7 falsch, 255 ungeprüft); falsch → `verworfen` |
| basel | `10_authority_links.csv` (2239), `30_authority_candidates.csv` (1276 Amtsträger), `31_links_metagrid.csv` (1276), `32_hls_check.csv` (171) | `11_authorities.py` (Basler Fassung: Allianzname, Amtsträger, Mindestalter), `30_authority_candidates.py`, `31_metagrid_match.py` | wie Aarau, dazu Metagrid-Gegenprobe der Amtsträger. `hls_check`: 501 bestätigt, 140 falsch, 977 ungeprüft. Die Spalte `metagrid` hängt an jeder Zeile mit HLS-Nummer; sie ist eine Konkordanz, keine unabhängige Prüfung |
| baden, bern, lausanne, zuerich | `data/csv/10_authority_links.csv` **leer, mit Absicht** (README Zürich); `web/normdaten.csv` (Kandidaten nur für die eigene Seite) | `scripts/82_normdaten.py` (in allen vier Repos gleich): liest `hls_coverage.csv.gz`, `wikidata_persons.csv.gz` und `municipalities_1914.csv` aus vernetzte-schweiz (Baden, Bern, Lausanne @ 0bac003; Zürich @ 4e224e2) | **keine.** Die Seite zeigt sie als «ungeprüfte Kandidaten». Kein HLS-Artikel-Check, keine Metagrid-Abfrage |
| bern-frueh | – | – | keine Normdaten (Schema eigenes, nicht Aarau-Schema; nicht in `sources.toml`) |
| basel-frueh | – | – | wird gerade angelegt (andere Sitzung) |

**vernetzte-schweiz.**
- `scripts/ingest_ab.py` liest je Stadt `data/csv/10_authority_links.csv` am gepinnten Commit. Die Pins für Aarau und Basel sind für die Normdaten-Dateien gleich HEAD.
- Sichtbar wird alles bis «möglich», außer `hls_check` beginnt mit «falsch». Ergebnis: `data/norm/ab_authority.csv`, Aarau 623 und Basel 1227 Zeilen.
- `scripts/authority.py` hängt die Treffer an die Einheiten (`source = stadt`, 1102 Einheiten). Dazu kommt ein eigener zweiter Abgleich über Wikidata und BFS-Nummer (`source = telefonbuch`, 943 Einheiten: 324 wahrscheinlich, 619 möglich).
- Die `web/normdaten.csv` der vier qwen-Städte liest vernetzte-schweiz **nicht**.

## 2. Abdeckung je Repo, Band und Quelle

«Zeilen» = Einträge mit mindestens einem Kandidaten. QID/HLS/GND = Zeilen mit dieser Kennung. Für Aarau und Basel sind die Zeilen mit `hls_check` «falsch» oder Stufe «verworfen» mitgezählt; ausgeschlossen sind sie in der Spalte «sichtbar».

| Repo | Band | Einträge | Zeilen | wahrsch. | möglich | sichtbar in VS | QID | HLS | GND | weitere |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| aarau | 1884 | 2 991 | 68 | 36 | 31 | 67 | 68 | 54 | 66 | – |
| aarau | 1888 | 4 474 | 125 | 64 | 61 | 125 | 125 | 102 | 119 | – |
| aarau | 1892 | 4 546 | 127 | 66 | 60 | 125 | 127 | 94 | 115 | – |
| aarau | 1896 | 5 077 | 147 | 52 | 94 | 145 | 147 | 116 | 139 | – |
| aarau | 1899 | 4 870 | 163 | 54 | 108 | 161 | 163 | 126 | 153 | – |
| basel | 1841 | 4 270 | 480 | 104 | 371 | – (vor 1860) | 480 | 351 | 456 | Metagrid 351 |
| basel | 1850 | 3 894 | 433 | 130 | 298 | – (vor 1860) | 433 | 291 | 412 | Metagrid 291 |
| basel | 1862 | 15 488 | 1 326 | 329 | 978 | 1 227 | 1 326 | 997 | 1 261 | Metagrid 997; Amtsträger 186 |
| baden | 1900 | 1 879 | 20 | 6 | 14 | 0 | 20 | 20 | 20 | – |
| baden | 1910 | 8 288 | 17 | 6 | 11 | 0 | 17 | 16 | 17 | – |
| bern | 1883 | 12 467 | 126 | 58 | 68 | 0 | 126 | 126 | 124 | – |
| bern | 1900 | 22 276 | 166 | 92 | 74 | 0 | 166 | 166 | 161 | – |
| lausanne | 1896 | 23 952 | 106 | 33 | 73 | 0 | 106 | 96 | 104 | – |
| lausanne | 1907 | 58 861 | 223 | 62 | 161 | 0 | 222 | 198 | 211 | – |
| zuerich | 1859 | 8 158 | **0** | – | – | – | – | – | – | – |
| zuerich | 1875 | 19 744 | 96 | 63 | 33 | 0 | 96 | 96 | 93 | – |
| zuerich | 1885 | 34 758 | 158 | 89 | 69 | 0 | 158 | 158 | 157 | – |
| zuerich | 1900 | 60 671 | 203 | 76 | 127 | 0 | 203 | 203 | 200 | – |
| zuerich | 1914 | 81 737 | 274 | 147 | 127 | 0 | 274 | 274 | 270 | – |
| bern-frueh | 1795–1848 (6 Bände) | 17 247 | **0** | – | – | – | – | – | – | – |

Hinweise:
- Einträge = Zeilen aller `04_*`-Dateien und, für Aarau und Basel, `05_residents*`. Dieselbe Person zählt also mehrfach.
- Aarau: 630 Zeilen verweisen auf 168 verschiedene QIDs. Basel: 2239 Zeilen auf 552 QIDs.
- In den vier qwen-Städten kommt die HLS-Nummer fast immer mit, weil `hls_coverage` die Hauptquelle ist.
- Basel `31_links_metagrid.csv`: 1276 Amtsträger. Davon sind 199 «sicher», 53 «wahrscheinlich», 160 «unsicher», 98 «mehrdeutig» und 766 «kein».

**Belege der Stufe «möglich» in Aarau und Basel.** Das ist der wichtigste Befund der Zählung.

| Repo | «möglich» sichtbar | davon «nur Name+Daten» | davon mit Ortsbezug | am HLS-Artikel bestätigt |
|---|---:|---:|---:|---:|
| aarau | 351 | 221 | 130 | 12 |
| basel (alle Bände) | 1 536 | 859 | 677 | 171 |
| in vernetzte-schweiz (`ab_authority.csv`) | 1 249 | **751** (Aarau 221, Basel 1862 530) | 498 | – |

## 3. Stichprobe

90 Verknüpfungen, je 15 zufällig aus den sichtbaren Zeilen. Für Aarau und Basel ohne «verworfen» und ohne `hls_check` falsch, für die übrigen aus `web/normdaten.csv`.

Maßstab für «richtig»:
- Die Person lebte zur Zeit des Bandes erwachsen in dieser Stadt.
- Name und Beruf passen zum Eintrag.

«Unklar» heißt: Der Eintrag nennt keinen Beruf und der Ort passt, oder die Belege widersprechen sich.

**Ergebnis**

| Repo | wahrscheinlich r/f/u | möglich r/f/u | zusammen richtig |
|---|---|---|---|
| aarau | 7 / 0 / 0 | 1 / 6 / 1 | 8 von 15 |
| basel | 2 / 1 / 1 | 0 / 10 / 1 | 2 von 15 |
| baden | 3 / 1 / 1 | 9 / 1 / 0 | 12 von 15 |
| bern | 7 / 0 / 0 | 6 / 1 / 1 | 13 von 15 |
| lausanne | 4 / 1 / 2 | 7 / 0 / 1 | 11 von 15 |
| zuerich | 4 / 0 / 0 | 4 / 5 / 2 | 8 von 15 |
| **alle** | **27 / 2 / 5** (34) | **27 / 23 / 6** (56) | **54 von 90** |

Was die Fehler gemeinsam haben:
- **«nur Name+Daten» ist Rauschen.** In Aarau und Basel hatten 9 Stichproben diesen Beleg, alle 9 sind falsch.
  - Immer ist ein bekannter Namensvetter aus einer anderen Stadt mit anderem Beruf verknüpft.
  - Beispiel Basel 1862: «Wild, Johannes, Handelsmann» ist mit dem Zürcher Geodäsie-Professor (HLS 031183) verknüpft.
  - Beispiel Aarau 1896: «Jakob [Müller], Obergerichtsweibel» ist mit einem Zürcher Turnlehrer (HLS 016327) verknüpft.
- **Ein Basel-Bezug allein genügt in Basel nicht.** Von 4 Stichproben mit «möglich» und Basel-Bezug sind 3 falsch.
  - Der Allianzname im Eintrag widerspricht oft der Ehe im HLS: «Burckhardt-Haller» ist nicht der mit einer Preiswerk verheiratete Jurist, «Geigy-Forcart» nicht Geigy-Merian.
- **Häufige Namen in Zürich.** 5 von 11 «möglich» sind falsch: Huber, Nägeli, Müller, Wipfli, Bosshart.
  - `82_normdaten.py` lässt «möglich» zu, wenn der Familienname im Band selten ist *oder* der Beruf zum Feld passt. Der Beruf ist aber bloß ein Stichwort wie «Kaufmann» → Wirtschaft.
- **Der Allianzname ist der stärkste Beleg.** In Lausanne passen «Morel-Marcel», «Welti-Trachsel» und «Couchoud-Oboussier» zur Ehefrau im HLS, ebenso in Zürich «Bamberger-Sertorius» und «Bertschinger-Schwarz».
  - `82_normdaten.py` verwendet ihn bisher nicht. In Basel schließt er nur aus, wenn er widerspricht.
- **Vater und Sohn gleichen Namens:** Baden 1910 «Frey-Vogler, Emil, Musiklehrer» ist der Vater des verknüpften Pianisten.
- **Fragliche Repo-Urteile «bestätigt»:**
  - Basel «Bischoff-Bischoff» → Hieronymus Bischoff, der mit Respinger verheiratet war.
  - Basel «Geigy-Forcart» → Geigy-Merian.
  - Beide sollten noch einmal angesehen werden.
- **Kennungen:** Keine einzige QID trägt andere HLS- oder GND-Nummern als die Zeile.
  - 21 der 90 QIDs fehlen im Human-Lineage-Snapshot. Sie wurden nur am HLS-Artikel beurteilt.

Die Stichprobe ist klein: 15 je Stadt, 4–11 je Stufe. Die Anteile je Stadt sind darum grob, auf etwa ±25 Prozentpunkte. Der Unterschied zwischen «wahrscheinlich» und «möglich» und die 9 von 9 bei «nur Name+Daten» sind dagegen deutlich.

## 4. Vergleich mit vernetzte-schweiz

Je Repo-Zeile wurde geprüft, welche QIDs die zugehörige Einheit (`links/entities.csv.gz`) in `links/authority.csv` trägt.

| Repo | Repo-Zeilen | VS: gleiche QID | VS: andere QID | VS: keine | nicht in VS | VS-eigene Treffer (Telefonbuch-Abgleich) auf Einheiten ohne Repo-Kandidat |
|---|---:|---:|---:|---:|---:|---:|
| aarau | 630 | 605 | 18 | 7 (verworfen/falsch, mit Absicht) | 0 | 0 |
| basel | 2 239 | 1 209 | 18 | 99 (verworfen/falsch, mit Absicht) | 913 (1841/1850 vor dem Zeitfenster) | 1 |
| baden | 37 | 2 | 0 | 35 | 0 | 0 |
| bern | 292 | 22 | 0 | 270 | 0 | 43 |
| lausanne | 329 | 28 | 0 | 301 | 0 | 7 |
| zuerich | 731 | 100 | 1 | 630 | 0 | 124 |

- **Aarau und Basel:** VS übernimmt die Stadt-Treffer getreu.
  - Die 18 + 18 Abweichungen entstehen in `cluster.py`: Eine Einheit fasst Einträge mit verschiedenen QIDs zusammen (`authority_stats.json`: `stadt:mehrere_qids` 25).
  - Beispiele: Aarau 1896 «Frei, August» → Repo Q138758556, VS Q96364287 (August Frey); Basel 1862 «Jenny, Jean» → Repo Q113148178, VS Q138758886.
  - Gefährlich ist nicht die Übernahme, sondern die Stufe «möglich» mit «nur Name+Daten»: Sie geht ungefiltert hinein.
- **Baden, Bern, Lausanne, Zürich:** Die beiden Wege laufen nebeneinander.
  - Die Stadtseiten zeigen 1 389 ungeprüfte Kandidaten, VS sieht davon nichts.
  - Umgekehrt hat VS mit dem Telefonbuch-Abgleich eigene Treffer, die auf den Stadtseiten fehlen. Beispiele: Bern Bernhard Studer Q16214283, Zürich Robert Maillart Q123673, Lausanne Jean Landry Q971765.
  - Überschneidung: nur 152 Einträge mit derselben QID. Widerspruch: einer (Zürich 1914 «Keller, Adolf»: Repo Q362912, VS Q125243).
  - Die VS-eigenen Telefonbuch-Treffer sind hier nicht nachgeprüft. `authority.py` verlangt Beruf oder Wohn-/Wirkungsort per BFS-Nummer und ist strenger als `82_normdaten.py`.

## 5. Fehler in `82_normdaten.py`: Wikidata fällt in Bern und Zürich aus

- Das Skript verbindet Wikidata-Personen über die BFS-Nummer: `places & set(bfs)`, wobei `bfs` aus `municipalities_1914.csv` stammt.
- Für **Bern** und **Zürich** ist die Spalte `bfs` dort leer. Die Zeilen nennen nur `bfs_today`: Bern 351, Zürich 261. Bern ist `16401,,Bern,…,351`, Zürich ist `16453,,Zürich,…,261`.
- Deshalb ergibt der Wikidata-Teil für diese beiden Städte nichts. Sichtbar ist das in der Spalte `source`: Bern und Zürich 0 Zeilen «wikidata», Baden 9, Lausanne 79.
- Laut `wikidata_persons.csv.gz` gibt es aber Wikidata-Personen mit Ortsbezug Zürich: 2 395, davon 1 283 ohne HLS. Für Bern sind es 1 993, davon 498 ohne HLS.
- Behebung: `bfs_today` verwenden, wenn `bfs` leer ist. Danach Bern und Zürich neu rechnen.

## 6. Lücken und welches Skript sich portieren lässt

| Lücke | Grund | billigster Weg |
|---|---|---|
| **bern-frueh** 1795–1848 (17 247 Einträge) | Es gibt kein Normdaten-Skript. Das Schema ist eigenständig (`quarter`, `house_no`, `place`, `kind`). `82_normdaten.py` hilft nicht: seine Referenzlisten beginnen mit Geburt 1790 bzw. HLS-Orten ab 1875 | **`adressbuecher-basel/scripts/11_authorities.py`**: eigene SPARQL-Abfrage, das Geburtsfenster ist einstellbar (Basel: 1750–1844), Ortsbezug Q70 statt Q78, HLS-Check über den MCP schon eingebaut. Nötig ist ein Leseteil für das bern-frueh-Schema. Fenster etwa Geburt 1700–1830 |
| **Zürich 1859** (8 158) | VS-Referenzlisten: HLS-Orte erst ab 1880 (±5 Jahre), Wikidata nur Tod ≥ 1880; dazu der Fehler aus Abschnitt 5 | Nach der Behebung von Abschnitt 5 kommt der Wikidata-Teil für 1859 zum Teil. Sonst wie bern-frueh mit `11_authorities.py` (Ortsbezug Q72) |
| **basel-frueh** (im Aufbau) | – | `11_authorities.py` aus adressbuecher-basel, mit früherem Geburtsfenster; ein Repo derselben Stadt hat dieselben Regeln (Allianzname, Amtsträger) |
| Basel 1841/1850 | Normdaten vorhanden, aber vor dem VS-Zeitfenster 1860–1914 | nichts zu tun |

## 7. Empfohlene nächste Schritte (nach Nutzen je Aufwand)

1. **«möglich» mit «nur Name+Daten» aus der VS-Sicht nehmen.** Das sind 751 Verknüpfungen, in der Stichprobe 9 von 9 falsch. Am einfachsten über eine Regel in `ingest_ab.py` (`visible()`), besser in `11_authorities.py` von Aarau und Basel als eigene Stufe «schwach».
2. **`82_normdaten.py` reparieren** (`bfs_today`, Abschnitt 5) und Bern und Zürich neu rechnen; das Skript ist in vier Repos gleich.
3. **Den Allianznamen als Beleg in `82_normdaten.py` aufnehmen**: «X-Y» passt zur Ehefrau Y im HLS-Text bzw. in Wikidata (P26). In Lausanne und Zürich trug er die richtigen «möglich».
   - Zugleich sollte «möglich» nur über ein seltenes Familienname-Merkmal entstehen, nicht über ein Berufs-Stichwort allein. Zürich: 5 von 11 falsch.
4. **Einen Weg für die vier qwen-Städte festlegen.** Entweder kommen die Kandidaten aus `web/normdaten.csv` nach HLS-Prüfung in `10_authority_links.csv` und damit in VS, oder die Stadtseiten zeigen die VS-Treffer.
   - Heute gibt es zwei unverbundene Listen mit 152 Überschneidungen.
   - «wahrscheinlich» ist dort gut genug (18 von 23 richtig, 2 falsch, 3 unklar), um es mit dem HLS-Check aus Basel (`32_hls_check.csv`) zu prüfen und zu übernehmen.
5. **`11_authorities.py` (Basler Fassung) nach bern-frueh portieren**; dieselbe Fassung dient basel-frueh.
6. **Zwei Basler «bestätigt» nachprüfen**: Bischoff-Bischoff, Geigy-Forcart/Geigy-Merian.
7. **Die VS-eigenen Telefonbuch-Treffer** (943) mit derselben Methode stichprobenartig prüfen. Sie sind hier nicht erfasst.

## 8. Stichprobe im Einzelnen

Alle QIDs und HLS-Nummern zum Nachprüfen. «Beleg (Repo)» ist für Aarau und Basel die Spalte `evidence`, sonst die Quelle des Kandidaten (`hls` = `hls_coverage`, `wikidata` = `wikidata_persons`). Urteil und Begründung stammen aus der Prüfung am 14.11.2026; die Rohdaten lagen im Scratchpad dieser Sitzung.

#### Aarau

| Eintrag | Stufe | Beleg (Repo) | QID | HLS | Person | Urteil | Begründung |
|---|---|---|---|---|---|---|---|
| `1896-einwohner-150-L053` «— Jakob, Obergerichtsweibel, Milchgasse 143.» | möglich | nur Name+Daten | Q96487154 | 016327 | Johann Jakob Müller | **falsch** | HLS 016327: Johann Jakob Müller (1850–1931) war 1873–90 Sekundarlehrer und ab 1890 Turnlehrer in Zürich, nicht Obergerichtsweibel in Aarau. |
| `1884-einwohner-025-L045` «— -Beger, Adolf, Dr. Phil., Prof., v. Gontenschwyl, Casinostraße 576.» | möglich | HLS-Artikel bestätigt+HLS nennt Aarau+Heimatort | Q124151 | 011796 | Adolf Frey | **richtig** | HLS 011796: Adolf Frey, von Gontenschwil, ∞ 1883 Lina Beger, 1882–98 Lehrer am Gymnasium Aarau – deckt sich mit «Frey-Beger, Dr. phil., Prof., v. Gontenschwyl» 1884. |
| `1888-gebaeude-065-L035` «Conrad-Lüthi, Peter, Fürsprech, Regierungsrath, von Auw.» | wahrscheinlich | HLS-Artikel bestätigt+HLS-Heimatort+Aarau-Bezug+Heimatort | Q2074388 | 005486 | Peter Conrad | **richtig** | HLS 005486: Peter Conrad, Fürsprecher, von Auw, ∞ Lina Lüthy, 1885–1914 Aargauer Regierungsrat – passt vollständig; die QID ist aber nicht im Human-Lineage-Snapshot und konnte nicht gegengeprüft werden. |
| `1892-gebaeude-048-L015` «Meyer-Zschokke, F. E., Architekt, Direktor.» | möglich | nur Name+Daten | Q110552072 | 004398 | Philipp Meyer | **falsch** | HLS 004398: Philipp Meyer (1842–1909) war Landwirt und Zuger Regierungs- und Ständerat in Steinhausen; der Eintrag nennt einen Architekten F. E. Meyer-Zschokke. |
| `1899-gebaeude-030-L006` «Müller, Emma, Glätterin. Armenhausbewohner:» | möglich | nur Name+Daten | Q94732366 | 009361 | Emma Müller | **falsch** | HLS 009361: Emma Müller-Vogt war Frauenrechtlerin in Bern und Gattin von Bundesrat Eduard Müller, keine Glätterin im Aarauer Armenhaus. |
| `1899-gebaeude-081-L035` «Niggli-Bohnenblust, Arnold, Fürsprech u. Stadtschreiber.» | wahrscheinlich | HLS-Artikel bestätigt+Aarau-Bezug | Q19131379 | 020722 | Arnold Niggli | **richtig** | HLS 020722: Arnold Niggli, Fürsprecher, ∞ 1871 Johanna Bohnenblust, 1875–1909 Stadtschreiber von Aarau; die QID ist aber nicht im Human-Lineage-Snapshot. |
| `1899-einwohner-121-L035` «Hangartner, Ferdinand, Lithograph, Bachstraße 1048.» | wahrscheinlich | Aarau-Bezug+Beruf | Q125547191 | – | Ferdinand Hangartner | **richtig** | Kein HLS; Human Lineage: Ferdinand Hangartner (1852–1909), Lithograf – Beruf und Lebenszeit passen zu 1899. |
| `1899-gebaeude-054-L034` «Kutschera-Kiessner, E., Musik- und Gesangsdirektor, v. Brünn (Mähren).» | möglich | Aarau-Bezug+Heimatort | Q896895 | – | Eugen Kutschera | **unklar** | Kein HLS-Artikel, und weder QID noch GND sind im Human-Lineage-Snapshot; Musikdirektor E. Kutschera aus Brünn bleibt unbestätigt. |
| `1896-einwohner-121-L028` «— Franz, Dr. Professor, Gais 1267.» | wahrscheinlich | Aarau-Bezug | Q87392801 | – | Franz Fröhlich | **richtig** | Kein HLS; Human Lineage: Franz Fröhlich (1849–1912), Philologe und Mittelschullehrer – passt zu «Dr. Professor» 1896; der Ort Aarau ist nicht eigens belegt. |
| `1896-gebaeude-033-L009` «Hunziker-Müller, Friedr., Maschinenmeister. (Buchdr. Sauerländer).» | möglich | nur Name+Daten | Q55852723 | 044725 | Friedrich Hunziker | **falsch** | HLS 044725: Fritz Hunziker (1845–1908, ∞ Anna Maria Meyer) war Rektor der Industrieschule Zürich, nicht Maschinenmeister Hunziker-Müller bei Sauerländer. |
| `1884-einwohner-024-L027` «— Adolf, Reg.-Rath, von Reinach, Laurenzenvorstadt 422.» | wahrscheinlich | HLS-Artikel bestätigt+HLS-Heimatort+Aarau-Bezug+Heimatort | Q361553 | 003758 | Adolf Fischer | **richtig** | HLS 003758: Adolf Fischer, von Reinach, 1867–87 Aargauer Regierungsrat, gestorben 1893 in Aarau. |
| `1892-einwohner-150-L023` «[handschriftlich: ✕]Winteler-Eckart, Jost, Dr. Professor von Kerenzen » | wahrscheinlich | HLS-Artikel bestätigt+HLS nennt Aarau | Q18021448 | 012406 | Jost Winteler | **richtig** | HLS 012406: Jost Winteler, Dr. phil., 1884–1914 Gymnasiallehrer in Aarau, von Filzbach (Kerenzen), ∞ Pauline Eckhardt; die QID ist aber nicht im Human-Lineage-Snapshot. |
| `1899-einwohner-131-L039` «— Fritz, Bierbrauer, hinter dem Bahnhof 494.» | möglich | nur Name+Daten | Q94907204 | 012094 | Fritz Marti | **falsch** | HLS 012094: Fritz Marti (1866–1914) war Lehrer, Schriftsteller und ab 1899 Feuilletonchef der NZZ in Zürich, kein Bierbrauer. |
| `1896-einwohner-124-L068` «Hangartner, Ferdinand, Lithograph, Bachstraße 1048.» | wahrscheinlich | Aarau-Bezug+Beruf | Q125547191 | – | Ferdinand Hangartner | **richtig** | Kein HLS; Human Lineage: Ferdinand Hangartner (1852–1909), Lithograf – Beruf und Lebenszeit passen zu 1896. |
| `1892-einwohner-138-L032` «Schmid-Suter, Johann in Zofingen, „Pariser Bazar“, vord. Vorst. 889.» | möglich | nur Name+Daten | Q1577465 | 003589 | Johann Schmid | **falsch** | HLS 003589: Johann Schmid (1850–1931) war Anwalt und Politiker in Chur (von Vals), nicht Ladeninhaber «Pariser Bazar» aus Zofingen; die QID ist nicht im Snapshot. |

#### Basel

| Eintrag | Stufe | Beleg (Repo) | QID | HLS | Person | Urteil | Begründung |
|---|---|---|---|---|---|---|---|
| `1862-gebaeude-101-L009` «Wild, Johannes, Handelsmann» | möglich | nur Name+Daten | Q2735578 | 031183 | Johannes Wild | **falsch** | HLS 031183: Johannes Wild war 1855–89 Professor für Geodäsie am Polytechnikum Zürich, kein Handelsmann in Basel. |
| `1862-gebaeude-133-L027` «Christ-Stöcklin, Ludwig, Schuhmacher» | möglich | nur Name+Daten | Q64063780 | 011633 | Ludwig Christ | **falsch** | HLS 011633: Ludwig Christ (1791–1876) war Jurist und Redaktor in Chur und Glarus, kein Schuhmacher Christ-Stöcklin in Basel. |
| `1862-einwohner-388-L071` «Oechslin-Riedtmann, Joh. Conr., Schiffer u. Holzhändler. Rheingasse 86» | möglich | nur Name+Daten | Q1694917 | 022091 | Johann Jakob Oechslin | **falsch** | HLS 022091: Johann Jakob Oechslin war Bildhauer in Schaffhausen; der Eintrag nennt einen Schiffer und Holzhändler Joh. Conr. in Basel; die QID ist nicht im Snapshot. |
| `1862-einwohner-365-L105` «— -Rüttimeyer, Friedr., Gymnasiallehrer. Spalenberg 63.» | wahrscheinlich | Basel-Bezug | Q78064440 | 014196 | Friedrich Samuel Iselin | **richtig** | HLS 014196: Friedrich Samuel Iselin, ∞ 1853 Berta Rütimeyer, ab 1856 Lehrer am Humanistischen Gymnasium Basel. |
| `1862-einwohner-380-L098` «— -Forcart, I., Banquier. St. Elisabethen-Straße 27.» | möglich | Basel-Bezug (Namensvetter im Band) | Q1696019 | 004500 | Johann Rudolf Geigy-Merian | **falsch** | HLS 004500: Johann Rudolf Geigy war mit Maria Merian verheiratet und führte die Farbwarenfirma; der Eintrag «-Forcart, I., Banquier» hat einen anderen Allianznamen und eine andere Initiale. |
| `1862-gebaeude-243-L041` «Hartmann-Erzenberger, Joh., Zollbe-amter» | möglich | nur Name+Daten | Q138758864 | 005661 | Johann Jakob Hartmann | **falsch** | HLS 005661: Johann Jakob Hartmann war Notar und Regierungsstatthalter in Erlach (BE), 1864–78 Berner Regierungsrat, kein Zollbeamter in Basel. |
| `1850-einwohner-134-L074` «— Rud., Sohn, Kanzlist 1496» | wahrscheinlich | Basel-Bezug | Q19758104 | – | Rudolf Schmidt | **unklar** | Kein HLS, und die QID ist nicht im Human-Lineage-Snapshot; «Rud., Sohn, Kanzlist» lässt sich nicht bestätigen. |
| `1862-einwohner-360-L054` «Hof-Sarasin, Joh., Weinhändler. Steinenvorstadt 47.» | möglich | Basel-Bezug | Q61993419 | – | Johann Jakob Im Hof | **unklar** | Kein HLS; Human Lineage: Johann Jakob Im Hof (1815–1900), Basler Rats- und Appellationsrat – Ort und Zeit passen, Weinhändler und Allianzname Sarasin sind unbelegt. |
| `1862-gebaeude-082-L028` «Bischoff-Bischoff, Hieronimus, Kaufm» | wahrscheinlich | Basel-Bezug | Q61993490 | 029907 | Hieronymus Bischoff | **falsch** | HLS 029907: Hieronymus Bischoff war mit Dorothea Respinger verheiratet (Bischoff-Respinger); der Allianzname Bischoff-Bischoff verweist auf einen anderen Mann. |
| `1862-einwohner-339-L110` «— -Züricher, Joh., Maurerhandlanger. Rebgasse 37.» | möglich | nur Name+Daten | Q78061284 | 029498 | Johann Jakob Eichenberger | **falsch** | HLS 029498: Johann Jakob Eichenberger war Zigarrenfabrikant in Beinwil am See, kein Maurerhandlanger Eichenberger-Züricher in Basel. |
| `1862-gebaeude-126-L007` «Huber-Sommerhalder, Jak., Blatt- u. Zahnmacher» | möglich | nur Name+Daten | Q94765769 | 030471 | Jacques Huber | **falsch** | HLS 030471: Jacques Huber war Verleger der Thurgauer Zeitung in Frauenfeld, kein Blatt- und Zahnmacher in Basel. |
| `C00209-1850` «Amtsträger: Major; Rathsherr Eman. Burckhardt — J.U.D., Präsident — IV» | wahrscheinlich | Basel-Bezug+Basler Amt | Q133314962 | – |  | **richtig** | Kein HLS; Human Lineage: Emanuel Burckhardt (1819–1867), Jurist – passt zu «Rathsherr Eman. Burckhardt, J.U.D.» 1850. |
| `1862-einwohner-409-L049` «— -Kleis, Johs., Bahnarbeiter. Riehenteichweg 16.» | möglich | nur Name+Daten | Q96383797 | 029688 | Johann Rudolf Sommer | **falsch** | HLS 029688: Johann Rudolf Sommer war Käseexporteur in Häusernmoos und Langenthal, kein Bahnarbeiter in Basel. |
| `1850-einwohner-127-L084` «— J. J., Kondukteur 989» | möglich | Basel-Bezug | Q1448938 | 004604 | Johann Rudolf Merian | **falsch** | HLS 004604: Johann Rudolf Merian war Mathematikprofessor und Grossratspräsident; der Eintrag nennt einen Kondukteur J. J. Merian. |
| `1862-einwohner-332-L066` «Burckhardt-Haller, Joh. Rudolf, Dr. med. Kellergäßlein 7.» | möglich | Basel-Bezug | Q107000468 | 005947 | Johann Jakob Burckhardt | **falsch** | HLS 005947: Johann Jakob Burckhardt (∞ Esther Preiswerk) war Jurist und 1862 Untersuchungsrichter; der Eintrag nennt Dr. med. Joh. Rudolf Burckhardt-Haller. |

#### Baden

| Eintrag | Stufe | Beleg (Repo) | QID | HLS | Person | Urteil | Begründung |
|---|---|---|---|---|---|---|---|
| `1910-einwohner-107-076` «— Johann, Tapezierer, Langenstein 522» | möglich | Quelle hls | Q94914100 | 028153 | Johann Adolf Herzog | **falsch** | HLS: Johann Adolf Herzog war 1870–1915 Lehrer und ab 1902 Direktor des Lehrerseminars Wettingen, kein Tapezierer. |
| `1910-berufe-129-029` «Wanner, Otto, Bruggerstrasse 33, Baden H. ☎ 8» | möglich | Quelle hls | Q78074619 | 029541 | Otto Wanner | **richtig** | HLS: Otto Wanner (1867–1941) betrieb ab 1894 die Buchdruckerei in Baden (Badener Tagblatt); die Adresse Bruggerstrasse ist die der Druckerei laut den 1900er Einträgen. |
| `1900-einwohner-030-014` «Kellersberger, Armin, Fürsprech und Ständerat, Obere Halde 258.» | möglich | Quelle hls | Q1396848 | 003774 | Armin Kellersberger | **richtig** | HLS: Armin Kellersberger (1838–1905), Fürsprech in Baden, 1881–1905 Ständerat. (QID nicht im Human-Lineage-Snapshot, IDs dort nicht prüfbar.) |
| `1910-einwohner-051-007` «Hunziker-Brunner, Emil, Ingen., Dufourstrasse 12» | möglich | Quelle hls | Q78064116 | 031387 | Emil Hunziker | **richtig** | HLS: Emil Hunziker, 1900 verheiratet mit Maria Emilia Brunner, 1897–1934 Konstruktionschef bei BBC in Baden, ab 1902 Bürger von Ennetbaden. |
| `1910-einwohner-043-027` «— -Vogler, Emil, Musiklehrer, Kronengasse 22» | wahrscheinlich | Quelle wikidata | Q1336074 | 020573 | Emil Frey | **falsch** | HLS: Der Pianist Emil Frey (geb. 1889) ist der Sohn des Emil, Musiklehrers, und der Clara geb. Vogler – der Eintrag Frey-Vogler, Musiklehrer meint den Vater. (QID nicht im Snapshot.) |
| `1900-einwohner-022-005` «— Sidney William, Ingenieur, Badstraße ☎.» | möglich | Quelle hls | Q2281881 | 029569 | Sidney William Brown | **richtig** | HLS: Sidney William Brown, ab 1891 technischer Leiter, 1900–35 Delegierter von BBC in Baden. (QID nicht im Snapshot.) |
| `1900-einwohner-042-014` «Wanner, Otto, Buchdruckerei, Brugggerstraße ☎.» | möglich | Quelle hls | Q78074619 | 029541 | Otto Wanner | **richtig** | HLS: Otto Wanner kaufte 1894 die grossväterliche Buchdruckerei in Baden und war Verleger des Badener Tagblatts. |
| `1900-berufe-045-023` «Dorer, Otto, Badstrasse 671.» | wahrscheinlich | Quelle wikidata | Q96317583 | 019833 | Otto Dorer | **unklar** | HLS: Architekt Otto Dorer führte ab 1884 ein Büro in Baden; der Eintrag nennt keinen Beruf (Berufsrubrik nicht sichtbar), daher nur Anwesenheit bestätigt. |
| `1910-einwohner-043-033` «Fricker-Eichenberger, Bartholomäus, Bezirkslehrer, Schwerstr. 4 ☎» | wahrscheinlich | Quelle wikidata | Q77432088 | – | Bartholomäus Fricker | **richtig** | Kein HLS-Artikel; Wikidata/Human Lineage: Bartholomäus Fricker (1844–1913), Lehrer und Verfasser historischer Schriften und Führer – passt zu Bezirkslehrer, seltener Name. |
| `1900-einwohner-020-007` «Baldinger, Emil, Oberförster, Nationalrat, Postplatz.» | möglich | Quelle hls | Q1335785 | 003743 | Emil Albert Baldinger | **richtig** | HLS: Emil Albert Baldinger, 1887–1907 aargauischer Kantonsoberförster, 1876–1907 Nationalrat, starb 1907 in Baden. |
| `1900-berufe-047-026` «Wanner, Otto ☎ R. Verlag des Badener Tagblattes und der Schweizerische» | möglich | Quelle hls | Q78074619 | 029541 | Otto Wanner | **richtig** | HLS: Otto Wanner war ab 1894 Verleger und Redaktor des Badener Tagblatts. |
| `1900-berufe-047-005` «Müller, Hans, Dynamostr. 785. R.» | möglich | Quelle hls | Q15965122 | 029493 | Hans Müller | **richtig** | HLS: Hans Müller kaufte 1897 die Brauerei Weber in Baden (Müllerbräu); die Adresse Dynamostrasse ist die der Brauerei laut Eintrag 1910. (QID nicht im Snapshot.) |
| `1910-einwohner-062-045` «— -Küpper, Carl, Direktor, Badstr. 34 ☎» | wahrscheinlich | Quelle hls | Q110576612 | 029587 | Carl Pfister | **richtig** | HLS: Carl Pfister, 1874 verh. mit Marie Küpfer, 1891–1928 Direktor der Elektrizitätsgesellschaft Baden (Küpper = Lesung/Variante von Küpfer). |
| `1900-einwohner-040-035` «Täuber, Carl, Dr. phil., Große Bäder.» | wahrscheinlich | Quelle hls | Q110226679 | 046369 | Carl Täuber | **richtig** | HLS: Dr. phil. Carl Täuber (Dr. 1890) war 1901–1904 Korrespondent bei BBC in Baden und mit Ellen Brown verheiratet. |
| `1910-einwohner-060-042` «— -Hauser, Hans, Bierbrauer (Inhaber der Brauerei Müller), Dynamostras» | möglich | Quelle hls | Q15965122 | 029493 | Hans Müller | **richtig** | HLS: Hans Müller, verheiratet mit Johanna Hauser, Bierbrauer, Inhaber der Brauerei Müller in Baden ab 1897. (QID nicht im Snapshot.) |

#### Bern

| Eintrag | Stufe | Beleg (Repo) | QID | HLS | Person | Urteil | Begründung |
|---|---|---|---|---|---|---|---|
| `1900-einwohner-157-014` «Benteli, A., Rektor d. Real- u. Handelsschule a. städt. Gymnasium, Pri» | möglich | Quelle hls | Q55847398 | 043582 | Albert Benteli | **richtig** | HLS: Albert Benteli, 1889–1914 Rektor der Real- und Handelsschule am Städtischen Gymnasium Bern, ab 1874 PD. |
| `1883-einwohner-140-054` «— H., Oberrichter, Kramgasse 47» | möglich | Quelle hls | Q5319600 | 004593 | Hermann Lienhard | **richtig** | HLS: Hermann Lienhard war 1882–86 bernischer Oberrichter. (QID nicht im Snapshot, IDs nicht prüfbar.) |
| `1900-einwohner-283-015` «☎ Micheli, H., Journalist, Bundesg. 28 1262» | möglich | Quelle hls | Q26877865 | 003877 | Horace Micheli | **richtig** | HLS: Horace Micheli war 1893–1900 Berner Korrespondent und 1900–04 Bundeshausredaktor des Journal de Genève. |
| `1900-berufe-400-032` «Bürgi, Fr., Länggasse, Erlachstrasse Nr. 16a 711» | möglich | Quelle hls | Q96270233 | 004445 | Friedrich Bürgi | **unklar** | HLS: Friedrich Bürgi war Baumeister und Bauunternehmer in Bern (gest. 1909); der Eintrag nennt keinen Beruf, daher nur Anwesenheit bestätigt. |
| `1883-einwohner-162-047` «Rüetschi, Alb. Rudolf, Dr., Pfarrer am Münster, Herreng. 3» | wahrscheinlich | Quelle hls | Q78070383 | 010809 | Albrecht Rudolf Rüetschi | **richtig** | HLS: Albrecht Rudolf Rüetschi war 1867–97 Pfarrer am Berner Münster, Dr. theol. h.c. |
| `1883-einwohner-149-071` «— Ed., Dr., Prof. d. Theol., Pfarrer in der Waldau» | möglich | Quelle hls | Q5999350 | 043935 | Eduard Müller | **falsch** | HLS: Eduard Müller-Hess war Indologe/Anglist (keine Theologie), 1883–86 Lehrer in Cardiff – nicht Pfarrer in der Waldau. (QID nicht im Snapshot.) |
| `1900-einwohner-208-063` «Gobat, A., Dr., Reg.-Rat, Gr. Schanze, Falkenhöhenweg 13» | möglich | Quelle hls | Q179458 | 004505 | Albert Gobat | **richtig** | HLS: Albert Gobat, Dr. iur., 1882–1912 bernischer Regierungsrat. |
| `1900-berufe-391-002` «„ † Ritschard, Joh., Reg.-Rat 1497» | wahrscheinlich | Quelle hls | Q2570436 | 004664 | Johannes Ritschard | **richtig** | HLS: Johannes Ritschard war 1893–1908 bernischer Regierungsrat. |
| `1883-einwohner-147-052` «— Aug., Journalist, Zeughausg. 22» | wahrscheinlich | Quelle hls | Q85100312 | 028694 | Auguste Meylan | **richtig** | HLS: Auguste Meylan (1840–1897) war Journalist in Bern und starb dort. |
| `1883-einwohner-178-073` «— H. I. Sekretär der eidg. Oberzolldirektion, Neufeldstr. 36» | möglich | Quelle hls | Q108705943 | 011377 | Hermann Suter | **richtig** | HLS: Hermann Suter war ab 1883 1. Sekretär und Bürochef der Oberzolldirektion. |
| `1883-einwohner-163-060` «— Herm., Dr., Arzt, Kramg. 11» | wahrscheinlich | Quelle hls | Q122191 | 014612 | Hermann Sahli | **richtig** | HLS: Hermann Sahli, 1881 Dr. med., 1878–88 Assistenzarzt in Bern. |
| `1883-einwohner-095-044` «— Rud., Fürspr., Nationalrath (Bundesgasse 16), Marktgasse 45» | wahrscheinlich | Quelle hls | Q16060072 | 004437 | Rudolf Brunner | **richtig** | HLS: Rudolf Brunner, Fürsprecher in Bern, 1866–94 Gross- und Nationalrat. |
| `1900-einwohner-267-061` «— Paul, Dr., Vorstand d. † schweiz. landwirtschaftl. Versuchs- und Unt» | wahrscheinlich | Quelle hls | Q1622089 | 031508 | Paul Liechti | **richtig** | HLS: Paul Liechti, Dr. phil., 1897–1924 Leiter der schweizerischen agrikulturchemischen Anstalt Liebefeld bei Bern. |
| `1900-einwohner-316-016` «☎— Chr., Manufakturwarenhandlung, Spitalgasse 15/17 u. 21 321» | möglich | Quelle hls | Q78070400 | 048780 | Christian Rüfenacht | **richtig** | HLS: Christian Rüfenacht baute sein Textil- und Bekleidungsgeschäft bis in die 1890er Jahre zum Warenhaus an der Spitalgasse aus. |
| `1900-einwohner-344-011` «Stammler, Jak., römisch-kath. Pfarrer, Taubenstrasse 4 1595» | wahrscheinlich | Quelle hls | Q1520142 | 003016 | Jakob Stammler | **richtig** | HLS: Jakob Stammler war 1876–1906 (katholischer) Pfarrer in Bern. (QID nicht im Snapshot.) |

#### Lausanne

| Eintrag | Stufe | Beleg (Repo) | QID | HLS | Person | Urteil | Begründung |
|---|---|---|---|---|---|---|---|
| `1907-einwohner-206-049` «Morel-Marcel Marc, banquier, av. Rosemont. T 797. B. pl. St-François 1» | möglich | Quelle hls | Q18414741 | 004342 | Marc Morel | **richtig** | HLS: ab 1890 Bankier in Lausanne (Banque Morel, Chavannes, Günther), verheiratet mit Sophie Cécile Marcel – passt zu «Morel-Marcel, banquier» (QID nicht im Human-Lineage-Snapshot). |
| `1907-einwohner-076-018` «Chavannes-Dufour Ernest, banquier, Vuachère, Mousquines. T 1937.» | möglich | Quelle hls | Q78060232 | 030786 | Ernest Chavannes | **richtig** | HLS: leitete die Bank Chavannes, Morel, Gunther & Cie in Lausanne, 1894 verheiratet mit Marie Dufour – passt zu «Chavannes-Dufour, banquier». |
| `1907-einwohner-131-031` «Genillard Aug., étudiant, av. d'Ouchy 83» | wahrscheinlich | Quelle hls | Q78062069 | 030791 | Auguste Genillard | **richtig** | HLS: geb. 1883, Ingenieurschule der Univ. Lausanne, 1907 Mathematiklehrer – «étudiant» in Lausanne 1907 passt zur Ausbildungsphase. |
| `1907-gemeinden-879-003` «Syndic, Rubattel-Chuard Ernest, député et conseiller national.» | wahrscheinlich | Quelle wikidata | Q78070295 | 004360 | Ernest Rubattel | **richtig** | HLS: Rubattel, verh. mit Lucie Chuard, 1889–1906 Gemeindepräsident (Syndic) von Villarzel, Grossrat, 1900–06 Nationalrat – deckt den Eintrag genau, auch wenn er 1906 Staatsrat wurde (Angaben im Band leicht veraltet). |
| `1896-einwohner-157-017` «Palaz-Gourraud, Adrien, prof. électricien, Petites Toises, villas Merc» | wahrscheinlich | Quelle hls | Q2825230 | 031621 | Adrien Palaz | **richtig** | HLS: 1888 verheiratet mit Marguerite Gourraud, 1889–1904 Prof. für industrielle Elektrizität an der Univ. Lausanne – passt zu «Palaz-Gourraud, prof. électricien» (QID nicht im Human-Lineage-Snapshot). |
| `1907-einwohner-042-048` «Bezencenet - Karth Louis, architecte, sq. Georgette 2. T 582. Bureau a» | wahrscheinlich | Quelle hls | Q3261264 | 029103 | Louis Bezencenet | **richtig** | HLS: ab 1870 Architekt in Lausanne, 1874 verheiratet mit Marguerite Karth – passt zu «Bezencenet-Karth, architecte» (QID nicht im Human-Lineage-Snapshot). |
| `1907-gemeinden-903-023` «Boulenaz Auguste, r. Louis Meyer 2. R T.» | wahrscheinlich | Quelle hls | Q78058719 | 030782 | Auguste Boulenaz | **unklar** | HLS: Bauunternehmer in Vevey, 1897–1913 Gemeinderat von Vevey – der Eintrag (rue Louis Meyer, offenbar Vevey) nennt keinen Beruf, Ort passt, aber nichts bestätigt die Person. |
| `1907-einwohner-067-027` «Campiche-Gueissaz Ami, inspecteur fédéral des fabriques, Vert Site, ro» | möglich | Quelle hls | Q2843182 | 004284 | Ami Campiche | **richtig** | HLS: Eidg. Fabrikinspektor 1891–1910, in Lausanne wohnhaft, verheiratet mit Anna Elisa Gueissaz – passt genau (QID nicht im Human-Lineage-Snapshot). |
| `1907-gemeinden-879-009` «— Mayor Jules, président — Bersier Henri — Métraux Paul, pasteur — Ros» | möglich | Quelle wikidata | Q99305230 | 004905 | Jules Mayor | **unklar** | HLS: Jules Mayor (geb. 1884), Landwirt in Villarzel, 1905–09 Gemeinderat, Präsident der Gemeindeversammlung erst ab 1909 – gleiche Seite wie der Syndic von Villarzel, aber «président» 1907 passt nicht sicher und der gleichnamige Vater Jules kommt ebenso in Frage. |
| `1907-einwohner-086-060` «Couchoud - Oboussier J., imprimeur, Terreaux 4. At. Mauborget 7. R T 1» | möglich | Quelle hls | Q96287119 | 030616 | Jules Couchoud | **richtig** | HLS: Drucker in Lausanne (ab 1886 selbstständig), verheiratet mit Augusta Henriette Oboussier – passt zu «Couchoud-Oboussier, imprimeur». |
| `1907-gemeinden-739-060` «— Paris Charles» | wahrscheinlich | Quelle wikidata | Q136639021 | 013104 | Charles Paris | **unklar** | HLS: geb. 1886 in Onnens, Fotograf erst nach 1918 – der Eintrag nennt nur den Namen ohne Beruf; 1907 21-jährig, nichts bestätigt die Identität. |
| `1896-einwohner-213-026` «Wilson-Clarke, John, rentier, Montbenon, 3 bis. T.» | wahrscheinlich | Quelle wikidata | Q99536280 | – | John Wilson | **falsch** | Keine HLS-ID; Human Lineage: die QID ist ein Pfarrer der Free Church of Scotland (1843–1912) – kein Bezug zu Lausanne und nicht vereinbar mit «Wilson-Clarke, rentier». |
| `1907-einwohner-287-036` «Welti-Trachsel Oswald, photographe, Ferme aux Abeilles, Chailly.» | möglich | Quelle hls | Q53508255 | 027238 | Oswald Welti | **richtig** | HLS: Fotograf mit eigenem Atelier in Lausanne, verheiratet mit Emilie Bertha Trachsel – passt zu «Welti-Trachsel, photographe». |
| `1907-einwohner-291-017` «Würgler-Bory Eugène, photographe, av. Mont Blanc 10.» | möglich | Quelle hls | Q54396682 | 027239 | Eugène Würgler | **richtig** | HLS: Fotograf, ab 1903 Studio in Lausanne, 1900 verheiratet mit Julia Hélène Bory – passt zu «Würgler-Bory, photographe». |
| `1896-einwohner-169-059` «Rambert, Paul, avocat, av. Rosemont. 4.» | möglich | Quelle hls | Q93251503 | 016255 | Paul Rambert | **richtig** | HLS: Rechtsstudium in Lausanne, 1896 Promotion, Anwaltspatent erst 1898 – «avocat» 1896 ist leicht verfrüht, Name, Ort und Beruf passen sonst. |

#### Zürich

| Eintrag | Stufe | Beleg (Repo) | QID | HLS | Person | Urteil | Begründung |
|---|---|---|---|---|---|---|---|
| `1900-einwohner-229-012` «— Emil, Kaufmann, I Mühlegasse 23.» | möglich | Quelle hls | Q1336264 | 030985 | Emil Huber | **falsch** | HLS: Emil Huber(-Stockar) war 1891–1910 Direktionsmitglied der Maschinenfabrik Oerlikon (Ingenieur) – nicht vereinbar mit «Kaufmann, Mühlegasse». |
| `1914-berufe-753-088` «Junod, A. E., 1 Olgastrasse 2.» | möglich | Quelle hls | Q78064870 | 030769 | Albert Junod | **unklar** | HLS: 1905–14 Divisionssekretär im eidg. Volkswirtschaftsdepartement (Bern), 1914–18 Pro Sempione; ein Wohnsitz in Zürich 1914 ist nicht belegt und der Eintrag «A. E.» nennt keinen Beruf. |
| `1885-berufe-364-024` «Bosshart-Bettemann, J., Tonhallesstr. 20 Z.» | möglich | Quelle hls | Q117227 | 011589 | Jakob Bosshart | **falsch** | HLS: Jakob Bosshart war mit Elsa Forrer verheiratet und 1885 noch Student – nicht vereinbar mit «Bosshart-Bettemann, J.». |
| `1914-einwohner-590-024` «Vetsch, Jak., Dr. phil., 1 Spiegelgasse 18. (Redaktor am schweiz. Idio» | wahrscheinlich | Quelle hls | Q1679397 | 012365 | Jakob Vetsch | **richtig** | HLS: 1907 Dr. phil., ab 1903 Redaktor am Schweizerischen Idiotikon in Zürich – passt genau (QID nicht im Human-Lineage-Snapshot). |
| `1914-einwohner-054-089` «☎ — Sertorius, Eugen, Prof. Dr., 6 Germaniustr. 51.» | wahrscheinlich | Quelle hls | Q66391 | 031291 | Eugen Bamberger | **richtig** | HLS: Bamberger, 1888 verheiratet mit Marie Sertorius, 1893–1905 Prof. an der ETH Zürich, danach weiter forschend – passt zu «Bamberger-Sertorius, Prof. Dr.». |
| `1914-einwohner-407-098` «— -Bader, Joh., Handlanger, 6 Dammstrasse 7.» | möglich | Quelle hls | Q96487154 | 016327 | Johann Jakob Müller | **falsch** | HLS: Johann Jakob Müller war Turnlehrer an der Kantonsschule Zürich, verheiratet mit Dorothea Krauer – nicht vereinbar mit «Müller-Bader, Handlanger». |
| `1914-berufe-670-025` «☎ Veraguth, Dr. Otto, Nervenarzt u. Privatdozent an der Universität, 2» | wahrscheinlich | Quelle hls | Q117671 | 014678 | Otto Veraguth | **richtig** | HLS: Neurologe mit Praxis in Zürich, 1900 Habilitation für Neurologie an der Univ. Zürich – passt zu «Nervenarzt u. Privatdozent». |
| `1885-einwohner-309-086` «☎ — J., Agentur in roher Baumwolle u. Generalagentur des „Phönix“ in P» | möglich | Quelle hls | Q110572706 | 030993 | Jakob Wirz | **unklar** | HLS: Jakob Wirz war bis 1890 Kaufmann in Zürich (Grosser Stadtrat ab 1880) – eine Baumwollagentur ist vereinbar, der Eintrag nennt aber nur «J.». |
| `1900-einwohner-516-035` «Wipfli, Jos., Schuppenarb., III Konradstrasse 17.» | möglich | Quelle hls | Q78075423 | 041338 | Josef Wipfli | **falsch** | HLS: Josef Wipfli war Priester, 1900–1908 Pfarrhelfer in Lungern – nicht vereinbar mit «Schuppenarbeiter» in Zürich. |
| `1914-einwohner-074-095` «☎ Schwarz, Walo, Ingenieur, 7 Wotanstrasse 8.» | wahrscheinlich | Quelle hls | Q78057538 | 029584 | Walo Bertschinger | **richtig** | HLS: Bauingenieur, 1902 verheiratet mit Martha Schwarz – passt zu «Bertschinger-Schwarz, Walo, Ingenieur»; Zürcher Wohnsitz 1914 nicht ausdrücklich belegt (Firma in Zürich erst 1917). |
| `1900-einwohner-336-014` «— Otto, Kaufmann, IV Tannenstrasse 1.» | möglich | Quelle hls | Q6054730 | 014568 | Otto Nägeli | **falsch** | HLS: Otto Naegeli war Arzt (1897 Promotion, ab 1900 PD an der Univ. Zürich) – nicht vereinbar mit «Kaufmann» (QID nicht im Human-Lineage-Snapshot). |
| `1900-einwohner-049-111` «— -v. Barbere, Joh., Dr. phil., I Obmannamtsg. 15.» | möglich | Quelle hls | Q78057239 | 031292 | Johann Barbieri | **richtig** | HLS: Barbieri, 1873 verheiratet mit Hermina Aloisia von B., Dr. chem., Titularprof. am Polytechnikum Zürich, Bürger von Hottingen – passt zu «Barbieri-v. Barbere, Dr. phil.». |
| `1885-einwohner-196-044` «☎Moser, Rob., Ingenieur, Bauunternehmer, Feldeggstr. 69 R.» | möglich | Quelle hls | Q1455355 | 031538 | Robert Moser | **richtig** | HLS: Bauingenieur, 1879–83 Mitunternehmer beim Bau der Gotthard-Nordrampe, in Zürich tätig – passt zu «Ingenieur, Bauunternehmer» (QID nicht im Human-Lineage-Snapshot). |
| `1914-einwohner-337-081` «☎ Kutter, H., Pfarrer, Lic. theol., 8 Zollikerstrasse 76.» | möglich | Quelle hls | Q124749 | 010483 | Hermann Kutter | **richtig** | HLS: 1896 Lic. theol., 1898–1926 Pfarrer am Zürcher Neumünster – passt zu «Pfarrer, Lic. theol., Zollikerstrasse». |
| `1914-einwohner-217-073` «☎— Herm., Dr., Rechtsanwalt, Bureau: 1 Bahnhofplatz 1. Wohnung ☎2 Gart» | möglich | Quelle hls | Q94878772 | 009979 | Hermann Guggenheim | **richtig** | HLS: Dr. iur., erster jüdischer Anwalt in Zürich – passt zu «Dr., Rechtsanwalt». |

## Umgesetzt (14.11.2026)

- **Schritt 1:** `scripts/ingest_ab.py` (`visible()`) übernimmt «möglich» mit dem Beleg «nur Name+Daten» nicht mehr:
  751 Zeilen ausgeblendet (Aarau 221, Basel 530). Die Stadt-Verknüpfungen der Einheiten sinken von 1 102 auf 609.
- **Schritt 2:** `82_normdaten.py` (Baden, Bern, Lausanne, Zürich, gleiche Datei) nimmt für Bern und Zürich die heutige
  BFS-Nummer, aber nur für die Gemeinde, die heute so heisst (sonst nähme Höngg die 261). Dabei zwei weitere Fehler:
  Eine Person aus HLS und Wikidata zählte für denselben Eintrag doppelt, «eindeutig im Verzeichnis» schlug darum fehl
  (Baden 23, Lausanne 132 Einträge rutschten zu Unrecht auf «möglich»); Wikidata nennt oft nur den ersten Vornamen
  («Johann» passte zu «Joh. Bernhard» Spyri), jetzt gelten alle aus dem Label. Neue Kandidaten: Bern 91, Zürich 307.
- Offen: «Joh.» passt in `forename_score` (81_baende.py) auch zu «Johanna» (Johanna Spyri ← Bernhard Spyri).

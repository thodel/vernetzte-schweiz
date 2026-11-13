# Vernetzte Schweiz 1860–1914 — Plan

Stand 10.11.2026 (M2 abgeschlossen).

Ein eigenständiger Demonstrator, der die Adressbücher einzelner Schweizer Städte mit den
historischen Telefonbüchern der PTT verknüpft und die Personen und Firmen mit Wikidata,
dem HLS und der GND verbindet. Die Städte werden in eigenen Repos ausgewertet
(adressbuecher-aarau, adressbuecher-basel, weitere folgen); hier werden sie
zusammengeführt, verknüpft und gezeigt.

## Entscheide (10.11.2026)

| Frage | Entscheid |
|---|---|
| Zeitfenster | 1860–1914. Von Basel zählt damit nur der Band 1862. |
| Nächste Städte | weitere |
| Wo wird verknüpft? | Hier, zentral. Telefonbuch ↔ Adressbuch und die Bündelung über die Jahre laufen in diesem Repo. Die Normdaten-Abgleiche der Städte (mit ihren lokalen Regeln) werden übernommen. |
| Umfang Telefonbücher | Alle Einträge bis 1914 sind suchbar, auch Orte ohne Adressbuch. |
| Charge A | Wird im PTT-Repo eintragsweise neu aufbereitet (`tsv/a/<RefCode>.tsv`); hier nur übernommen, nicht neu gelesen. Charge B (1911–1914) wird hier verortet und zerlegt. |
| Sichtbarkeit von Normdaten | Alles bis «möglich»; was in der HLS-Prüfung als falsch erkannt oder als «verworfen» eingestuft ist, erscheint nicht. |
| Lizenzen | Seite und Code: MIT. Inhalte der Bücher bis 1914: gemeinfrei (URG Art. 2 Abs. 1, Art. 29 Abs. 2). Daten und Verknüpfungen: CC0 1.0 (Entscheid 11.11.2026, README). |
| Verknüpfungen als Datensatz | Ja, vorerst als CSV in diesem Repo (`links/`). |
| Sprache | Deutsch; alle Texte der Seite liegen in `site/i18n/de.json`, damit fr/it/en folgen können. |
| Sichtbarkeit Repo | öffentlich |

## Meilensteine

**M0 — Gerüst und Datenvertrag.** Repo, Pages, `config/sources.toml` mit gepinnten
Commits, Adapter für Aarau, Basel und PTT-Charge A nach `data/norm/`
([Datenvertrag](docs/datenvertrag.md)), Startseite mit Bestandszahlen.

**M1 — Telefonbücher bis 1914 vollständig.** ✔ 10.11.2026. 638 701 Einträge (Charge A
1880–1910: 308 481, Charge B 1911–1914: 330 220), eintragsweise zerlegt und verortet:

- Orte gegen die Gemeinden zum 1.1.1914 (BFS) und das Ortschaftenverzeichnis (swisstopo)
  aufgelöst: 2 606 Gemeinden 1914; Konfidenz hoch 450 391, mittel 103 931, unsicher 68 538,
  keine 15 841.
- Befund Charge B: die Ortsspalte ist eine übertragene Überschrift. Fehlt eine, erben ganze
  Seiten den falschen Ort (Zürich 1912 und 1914 als «Zwillikon (Affoltern a. A.)», Zürich
  1913 auf vier Fehlüberschriften, Genf 1913 als «Orsières», St. Gallen im Zürcher Block).
  Läufe, die mehr Zeilen tragen, als ihr Ort haben kann, werden über die anderen Jahrgänge
  geprüft (gleicher Abonnent = Name + Rufnummer oder Name + Strasse): 43 476 Einträge neu
  verortet, je Zeile oder seitenweise in Stadtblöcken. Gegenprobe über die Strassennamen
  (kommt die Strasse unter den sicher verorteten Einträgen der neuen Stadt vor?): je Zeile
  12 174 ja, 2 434 nur anderswo, 1 406 unbekannt; seitenweise 4 610 / 1 318 / 787. «Nur
  anderswo» ist eine obere Grenze für Fehler, Lesefehler im Strassennamen landen auch dort. Eine Zuweisung ganzer Läufe wurde verworfen:
  sie legte zusammengelegte Dörfer auf einen Ort.
- Unsicher bleiben vor allem Dorfläufe, deren Überschriften fehlen («La Chaux (Cossonay)»
  trägt 1 600–1 800 Zeilen je Jahr): ohne neues Lesen der Seiten nicht zu klären.
- Zerlegung: Person/Firma/Amt/Zusatzzeile, Familien- und Allianzname, Vornamen und
  Initialen (Vornamenliste aus den Daten), Titel, Beruf, Strasse + Nummer, Rufnummer;
  verrutschte Spalten werden umgestellt und markiert.

**M2 — Zentraler Verknüpfer Telefonbuch ↔ Adressbuch.** ✔ 10.11.2026.
Regeln, Stufen und Messung: [docs/verknuepfung.md](docs/verknuepfung.md); Ergebnis
`links/ptt_ab.csv`.

- Geblockt wird nach Stadt, Band und Familienname (Firmen: Leitname, nie Allianzname).
  Belege: Vorname bzw. Abkürzung bzw. Initiale, Allianzname, Strasse, Hausnummer (Aarau:
  alte Gebäudenummer), Beruf, Telefonzeichen. Widersprechen sich Vornamen oder
  Allianznamen, wird nicht verknüpft.
- Verknüpft wird nur, wenn genau eine Person am besten passt; über 15 und 30 Jahre
  Abstand braucht es mehr Belege.
- **Aarau:** 2 172 von 3 035 Telefonbuch-Einträgen mit Adressbuch-Einträgen verbunden.
- **Basel:** 4 113 von 103 903, weil es nur den Band 1862 gibt (19–52 Jahre Abstand).
- **Präzision** (Stichprobe 2, 20 Paare je Stufe):
  - Aarau: sicher 95–100 %, wahrscheinlich 90–100 %, möglich 90–100 %;
  - Basel: wahrscheinlich 85–95 %, möglich 80–95 %.
- **Vollständigkeit:** Von den Aarauer Einträgen mit Telefonzeichen sind 87 % (1896) bzw.
  85 % (1899) der erreichbaren verknüpft.
- **Nebenbefund M1:** Die Vornamenliste enthielt Berufe aus der Vornamenspalte («Wirt»,
  «Comestibles», «Architekt»). Sie werden jetzt ausgeschlossen: 809 statt 920 Namen.
- **Vorbehalte:**
  - Die Stichprobe ist von Claude beurteilt, nicht von Projektmitarbeitenden.
  - 20 Paare je Stufe sind wenig.
  - Aarau hat im Telefonbuch 1912–1914 keine Einträge. Die Stadt steckt vermutlich in
    einem Lauf mit fehlender Überschrift, zu prüfen in M3.

**M3 — Personen und Firmen über die Jahre.** ✔ 10.11.2026. `scripts/cluster.py` bündelt
523 913 Einträge (Telefon- und Adressbuch) zu 181 215 Einheiten je Gemeinde, 98 848 davon mit
mehr als einem Eintrag; Belege Nummer, Vorname, Adresse, Beruf, gleiche Zeile und die
M2-Paare, mit Widerspruchsprüfung (Vornamen, Allianzname, Witwe, Nachfolger, gleichzeitige
Einträge). Gemessen an Stichprobe 5 (nach dem letzten Regelwechsel): Paare 40/40 richtig,
lange Einheiten 14/15 (1 unklar), Vollständigkeit gegen die nächste Ausgabe 75–92 %.
`scripts/authority.py`: Normdaten der Städte für 1 103 Einheiten übernommen; zweiter
Abgleich über Wikidata (16 322 Kandidaten) und die BFS-Gemeindenummer: 315 `wahrscheinlich`
(97–100 %, n = 30), 605 `möglich` (70–95 %, n = 20). Beruf ist Pflicht für
`wahrscheinlich`; Name und Sterbeort allein sind zu schwach (4 von 12). Firmen noch ohne
Normdaten-Abgleich. Ergebnis: `links/entities.csv.gz`, `links/authority.csv`;
[Regeln und Messung](docs/einheiten.md).

**M4 — Seite.** ✔ 10.11.2026. Suche über geteiltes JSON (Name, Vorname/Beruf, Gemeinde);
Seite je Einheit (Normdaten, Zeitleiste, Einträge mit Fundstelle, mögliche weitere
Adressbuch-Einträge, Karte der Gemeinde), je Adresse, je Gemeinde (Einträge je Jahr,
häufigste Namen) und eine Liste der Orte; Seite «Vorbehalte». Kartenpunkt = Gemeinde, nicht
Adresse; Seitenbilder nur für Basel verlinkbar. [Aufbau](docs/seite.md).

**M5 — Weitere Städte.** Zürich, Baden: Eintrag in `sources.toml`, Adapter prüfen,
Verknüpfung und Bau laufen durch.
- ✔ 13.11.2026 **Baden** 1900 und 1910 aus [adressbuecher-baden](https://github.com/thodel/adressbuecher-baden)
  (qwen3.8, ohne Nachkorrektur): 10 145 Einträge in 29 Gemeinden des Bezirks. Neu: ein Band kann mehrere
  Gemeinden umfassen; jeder Eintrag trägt `municipality`, verknüpft wird je Gemeinde. 1 226 von 2 359
  Telefonbuch-Einträgen des Bezirks verknüpft; Stichprobe `data/review/m5_baden.csv`: 24 von 30 richtig,
  6 unklar, keiner falsch. HLS-Abdeckung (M9) fast unverändert (+3 wahrscheinlich, +1 Normdaten): die
  Badener HLS-Personen waren schon über die Telefonbücher erreichbar.
- ✔ 13.11.2026 **Bern** 1883–84 und 1900 ([adressbuecher-bern](https://github.com/thodel/adressbuecher-bern), 34 743
  Einträge) und **Lausanne** 1896 und 1907, nur die Stadt ([adressbuecher-lausanne](https://github.com/thodel/adressbuecher-lausanne),
  53 703 Einträge; «m. a.» = Adresse des vorigen Eintrags). Telefonbuch verknüpft: Bern 27 450 von 55 380, Lausanne
  1 748 von 4 514. Stichprobe `data/review/m5_bern_lausanne.csv`: Lausanne 14 von 18 richtig, 3 unklar, 1 falsch; **Bern
  10 von 18 richtig, 4 unklar, 4 falsch** (Namensvettern; Initiale + Telefonzeichen reicht in der Grossstadt nicht, selbst
  ein «sicher» war falsch). HLS (M9): +15 wahrscheinlich, +6 Normdaten, +12 möglich.
- ✔ 13.11.2026 **Bern-Verknüpfung geschärft** (`scripts/link_ptt_ab.py`): abgekürzte Gasse/Platz («Kramg.», «Bärenpl.»)
  zählen als Strasse; Initiale + Telefonzeichen trägt bei mehr als 5 Personen gleichen Namens im Band nichts mehr;
  allgemeine Firmenwörter (`GENERIC_FIRM`) brauchen die gleiche Strasse; weitere Einträge derselben Person im Band
  (Beleg `zusatz`) nur bei gleicher Strasse, Hausnummer oder gleichem ausgeschriebenem Vornamen. Bern Stichprobe 2
  (40, geschichtet): sicher 10/10, wahrscheinlich 7/10 (2 unklar), möglich 7/10, zusatz 8/10; davor rund 27/40.
  Aarau fast unverändert (Paare 16 731 → 16 440, gemessene Präzision gilt weiter).
- ✔ 13.11.2026 **Waadtländer Gemeinden** aus dem Indicateur 1907 (S. 670–962, adressbuecher-lausanne f8c0678,
  Datei `04_gemeinden.csv`, Art `gemeinden`): 29 122 Einträge in 386 Gemeinden; Gemeinde 1914 je Bezirk aus dem Namen
  im Buch, Montreux nach Ortsteil, Namen aus Gedankenstrich-Listen ergänzt. Verknüpft: Lausanne mit Gemeinden 2 440
  von 13 417 Telefonbuch-Einträgen (+848). Stichprobe 3 (24): sicher 8/8, wahrscheinlich 8/8, möglich 5/8 (1 falsch).
- ✔ 13.11.2026 **Zürich** 1875, 1885, 1900 und 1914 aus [adressbuecher-zuerich](https://github.com/thodel/adressbuecher-zuerich)
  (qwen3.8, ohne Nachkorrektur; 1859 liegt im Repo, aber vor dem Zeitfenster): 196 910 Einträge, die Ausgemeinden von
  1875/1885 gehören zur Gemeinde Zürich von 1914. Telefonbuch verknüpft: 36 087 von 62 474. Neue Regel für weitere
  Einträge derselben Person (`zusatz`): gleiche Hausnummer an einer anderen Strasse zählt nicht mehr (vorher 3 von 14
  `sicher` falsch). Stichprobe `data/review/m5_zuerich.csv` (1914, 30): sicher 10/10, wahrscheinlich 10/10, möglich 7/10.
  Die Regel nimmt Bern 2 369 Zusatz-Paare weg, Aarau 147; gelesen waren die weggefallenen überwiegend falsch.
  HLS (M9): +18 wahrscheinlich, +13 Normdaten, +22 möglich.
- offen: Bern 1860 (Fraktur, nicht ganz gelesen).

**M6 — Visualisierungen.** ✔ 10.11.2026: Karten «Wer bekam wann ein Telefon», «Berufe», «Namen» (`#/karten`), Berufssuche mit Karte und Quellenfilter in der Suche; [Aufbau und Messung](docs/karten.md). Umgesetzt sind die ersten drei Punkte; die weiteren Ideen bleiben offen. Nachgetragen: Regler für Jahre (ein Jahr oder Bereich) statt Zeiträumen, Quelle Telefon-/Adressbuch in «Berufe» und «Namen». Grundlage sind die Einheiten aus M3 (eine Person oder Firma
zählt einmal, nicht einmal je Jahrgang) und die Orte aus M1 (Gemeinde 1914, Koordinaten).
Jede Ansicht nennt ihre Grundgesamtheit: wer im Telefonbuch steht, nicht wer in der
Gemeinde lebte.
- **Wer bekam wann ein Telefon:** Heatmap der Schweiz nach Jahr des ersten Eintrags
  (Zeitregler 1880–1914), Filter nach Beruf bzw. Berufsklasse, Person/Firma, Kanton.
- **Wo lebten welche Berufe:** Heatmap je Beruf/Berufsklasse; dazu Anteil an allen
  Abonnenten des Ortes, damit Zürich und Basel nicht jede Karte füllen.
- **Häufigste Namen je Ort:** Top 5 der Familiennamen je Gemeinde (Karte mit Liste beim
  Klick); **Wanderung der Namen:** wo ein Name zuerst und wo er später steht, als
  Schwerpunkt je Jahr bzw. als Pfeile zwischen Gemeinden, getrennt für Einheiten, die den
  Ort wechseln (gleiche Nummer/Person in M3), und für blosse Namensverbreitung.
- **Weitere Ideen:**
  1. Ausbreitung des Netzes: Zahl der Abonnenten je Gemeinde und Jahr als Diffusionskurve,
     erster Anschluss je Ort; Vergleich mit Bevölkerung 1910 (BFS-Volkszählung).
  2. Frauen am Telefon: Witwen, «Frau», «Fräulein», weibliche Vornamen; Anteil je Ort und
     Jahr, Berufe der Frauen.
  3. Berufe im Wandel: welche Berufe kamen zuerst (Ärzte, Banken, Hotels), welche später
     (Handwerk, Privatanschlüsse).
  4. Stadtkarten Aarau und Basel: Abonnenten auf Strassen bzw. Gebäuden (Adressbuch-
     Geokodierung der Städte), Telefon vs. Nicht-Telefon im selben Quartier.
  5. Firmennetze: Firmen mit Filialen in mehreren Gemeinden (gleicher Firmenname), Hotel-
     und Tourismusorte als eigene Schicht.
  6. Nummernlandschaft: Länge der Rufnummern als Zeiger für die Grösse der Zentrale;
     Umnummerierungen (Charge B 1911: «37.69»).
  7. Lebenswege: Einheiten mit Normdaten (M3) auf einer Zeitleiste: Adressen, Nummern,
     Berufe; Sprachgrenze: französische/deutsche Vornamen und Berufe je Ort.

**M7 — Erweiterte Suche mit unscharfem Namensvergleich.** ✔ 10.11.2026: Schalter «Ähnliche
Namen» (Schlüssel + gewichtete Distanz, ähnliche Namen zum Anklicken statt automatisch),
Vornamen in anderer Sprachform, Filter Jahre/Art/Normdaten/Quelle, Sortierung. Gemessen:
76 von 83 Lesefehler-Paaren innerhalb der Schwelle; die Regel «erster Buchstabe gleich»
ist nach der Messung weggefallen. [Regeln und Messung](docs/suche.md). Ursprünglicher Plan: Die Suche aus M4 findet nur den
Namensanfang. Gesucht werden soll auch über Schreibvarianten (Meyer/Maier/Meier,
Schmid/Schmidt, Bürgi/Bürgy) und Lesefehler der Texterkennung (rn/m, u/n, ii/ü, c/e).
- **Zwei Stufen statt blosser Levenshtein-Distanz.** Zuerst der Namensschlüssel aus M2
  (`nkey`: Akzente, ss/ß, y/i, th/t, ck/k, Doppelkonsonanten, ae/ä), der die häufigen
  Varianten ohne Fehlertreffer zusammenführt; danach die Distanz auf dem Schlüssel.
- **Distanz mit Mass:** Damerau-Levenshtein (Vertauschung zählt 1) mit der Schwelle nach
  Länge: bis 4 Buchstaben 0, 5–7 Buchstaben 1, ab 8 Buchstaben 2. Typische
  OCR-Verwechslungen kosten 0,5 (rn↔m, u↔n, c↔e, ii↔ü, l↔I↔1, 0↔O). Der erste Buchstabe
  muss gleich sein, ausser bei bekannten Paaren (C/K, Ph/F, J/I, Y/I), sonst wird aus
  «Huber» «Muber».
- **Index:** eine Liste aller unterschiedlichen Namensschlüssel (rund 40 000, gepackt
  etwa 150 KB) wird ganz geladen; die Distanz rechnet der Browser. Dann werden nur die
  Teile der passenden Namen geladen.
- **Rangfolge und Anzeige:** exakt > gleicher Schlüssel > Distanz 1 > Distanz 2; jeder
  Treffer nennt, warum er passt («Variante», «1 Zeichen anders»). Unscharf ist zu- und
  abschaltbar.
- **Weitere Filter:** Jahre von–bis, Gemeinde, Kanton, Quelle (Telefon-/Adressbuch), Art,
  Berufsklasse, mit oder ohne Normdaten; Sortierung nach Name, Ort oder Jahr; Vorname
  ebenfalls unscharf (über die Sprachformen aus M2: Charles = Carl).
- **Messung:** ein Prüfsatz aus bekannten Varianten und aus den Lesefehlern der
  M3-Stichproben («Fimmelsherg»/«Fimmelsberg», «Kreienbtthl»/«Kreienbühl»). Gemessen wird,
  wie oft der gesuchte Name unter den Treffern ist und wie viele Fehltreffer die ersten
  20 enthalten, je Schwelle; die Schwellen werden erst danach festgelegt.

**M8 — Volltext und Telefonbücher.** ✔ 10.11.2026. Alle 638 701 Einträge durchsuchbar wie
auf historic.localsearch (ein Feld oder Felder, genau oder ungefähr, Jahre, Treffer nach
Jahr); jede Zelle der Übersicht Kanton × Jahr öffnet die Einträge mit Filtern; Seitenbilder
vom IIIF-Server des PTT-Archivs für die Bände bis 1910. Offen: Versatz Seite → Bild für
1911–1914. [Aufbau](docs/volltext.md).

**M9 — Vom HLS zum Eintrag.** ✔ 11.11.2026, Seite `#/hls`. Ursprünglicher Plan vom selben Tag: Die umgekehrte Prüfung
([Messung](docs/hls_abdeckung.md)) erwartet 5 981 HLS-Personen an Orten und in Jahren mit
Telefon- oder Adressbuch; gefunden sind etwa 1 200 (rund 20 %). Die Ansicht macht diese
Prüfung für jede Person sichtbar, ohne Kandidaten als Identifikation auszugeben.

- **Personenseite `#/hls/<HLS-Nummer>`:**
  - Name, Lebensdaten, Link zum HLS-Artikel. Kein Artikeltext: die Rechte daran liegen
    beim HLS.
  - Ein Raster der erwachsenen Jahre 1880–1914 mal Orte der Person. Jede Zelle zeigt, ob
    dort in jenem Jahr ein Buch vorliegt und ob ein Eintrag gefunden ist.
  - Die Treffer nach Stufe, klar getrennt: «Normdaten» als Verknüpfung, «Kandidat: Name,
    Ort, Vorname» und «Kandidat: Initiale» als Vorschläge. Jeder mit Link zur Einheit, zum
    Eintrag und zum Seitenbild.
  - Bei «nicht gefunden» der Grund: kein Buch an diesem Ort in diesen Jahren; Name fehlt
    ganz; Name steht anderswo, mit Liste.
- **Übersicht `#/hls`:**
  - die Quote insgesamt, nach Kanton, nach Geburtsjahrzehnt, nach Geschlecht und nach dem
    Fachgebiet des HLS-Artikels (wer hatte Telefon?);
  - eine sortierbare Liste mit Filtern nach Stufe, Ort und Jahren;
  - eine Suche nach Name oder HLS-Nummer.
- **Rückweg:** Auf der Seite einer Einheit erscheint ein HLS-Kandidat als «möglicher
  HLS-Eintrag», getrennt von den Normdaten.
- **Daten:**
  - `hls/<xx>.json.gz` in 64 Teilen nach FNV der HLS-Nummer;
  - `hls.json.gz` als Index (Nummer, Name, Jahre, Stufe), für Liste und Suche;
  - Bau in `build_hls.py` aus `data/norm/hls_coverage.csv.gz`.
  - Die HLS-CSV liegt nicht im Repo. `hls_coverage.py` läuft lokal, sein Ergebnis wird
    eingecheckt.
- **Vorher:** Orte mit Jahr aus dem Artikeltext und Beruf als Bedingung (siehe Messung).
  Beides wird an je 40 Personen je Stufe gemessen, bevor die Ansicht Kandidaten zeigt.
- **Ziel:** Eine HLS-Person mit Telefon ist in zwei Klicks bei ihrem Eintrag und dem
  Seitenbild. Wer fehlt, sieht warum.

## Offene Fragen

1. ~~Lizenz der Daten~~ und 2. ~~Verknüpfungen ohne Lizenz~~: entschieden 11.11.2026. Die
   Inhalte der Bücher bis 1914 sind gemeinfrei; `data/` und `links/` stehen unter CC0 1.0
   (README, `data/LICENSE.md`, `links/LICENSE.md`).
3. **Zürich und Baden:** Gibt es schon Repos oder Scans, und welche Bände?

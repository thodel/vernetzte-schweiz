# Datenvertrag

Was «Vernetzte Schweiz» von einer Quelle übernimmt und in welcher Form. Die Adapter in
`scripts/` lesen jede Quelle an dem Commit, den `config/sources.toml` nennt, und schreiben
die vereinheitlichten Tabellen nach `data/norm/`. Die Quell-Repos müssen dafür nichts
ändern; eine neue Stadt braucht nur einen Eintrag in `sources.toml`, solange sie das
CSV-Schema von [adressbuecher-aarau](https://github.com/thodel/adressbuecher-aarau/blob/main/docs/schema.md) einhält.

Alle Dateien: UTF-8, Komma, Kopfzeile. Zeitfenster 1860–1914 (`[window]`); was ausserhalb
liegt, wird nicht übernommen (Basel 1841 und 1850 fallen dadurch weg).

## Bezeichner

| Objekt | Form | Beispiel |
|---|---|---|
| Adressbuch-Eintrag | `<stadt>:<entry_id der Quelle>` | `aarau:1896-einwohner-111-L010` |
| Telefonbuch-Eintrag | `ptt:<RefCode>:<Zeile>` (Zeile = 1-basiert ohne Kopfzeile) | `ptt:P-260-1_Aarau_1889:4` |

Die Bezeichner der Quellen bleiben unverändert erhalten; das Präfix macht sie über Städte
hinweg eindeutig. Ändert eine Quelle ihre `entry_id` (neue Zeilentrennung), zeigt der
Diff in `data/norm/` die verlorenen Bezeichner.

## data/norm/ab_entries.csv — Adressbuch-Einträge

| Spalte | Inhalt |
|---|---|
| `id` | siehe oben |
| `city`, `volume` | Stadt-Id aus `sources.toml`, Band (Jahr) |
| `kind` | `einwohner`, `berufe`, `bewohner` (Bewohner unter einem Gebäude), `behoerden` (Amtsträger; Basel, aus `30_authority_candidates.csv`, Id `<cand_id>-<Band>`) |
| `page` | PDF-Seite im Band |
| `entry_type` | `person` / `firma` |
| `surname`, `alliance_name`, `maiden_name`, `forename`, `title`, `civil_status` | wie in der Quelle; `surname` mit geerbtem Familiennamen gefüllt, wo die Quelle ihn nur über den Gedankenstrich hat |
| `occupation` | `occupation_raw`; im Berufsregister die Rubrik (`heading`), wenn `occupation_raw` leer ist |
| `origin` | Heimatort wie gedruckt |
| `street`, `building_no`, `building_no_system` | Adresse wie gedruckt; `building_no_system` nur wo die Quelle es kennt (Basel: alte/neue Nummern) |
| `phone_flag` | `1`, wenn der Eintrag das Telefonzeichen trägt |
| `parse_confidence` | wie in der Quelle |
| `text` | der gedruckte Eintrag |
| `municipality` | Gemeinde zum Stand 1914 |
| `district` | Gebiet in der Stadt, wie gedruckt; nur wo die Quelle es angibt (bisher Zürich), sonst leer |

### Abweichungen einzelner Quellen vom Schema von Aarau

| Stadt | Abweichung |
|---|---|
| Zürich | **Zusätzliche Spalte `district`** (ab [adressbuecher-zuerich@3c1a6a7](https://github.com/thodel/adressbuecher-zuerich/commit/3c1a6a7)): 1859 `Grosse Stadt` / `Kleine Stadt` (g/k an der Hausnummer), 1875 und 1885 die alte Gemeinde hinter der Hausnummer (`Riesbach`, `Aussersihl` …; seit 1893 Teil der Stadt), 1900 `Kreis I`–`Kreis V`, 1914 `Kreis 1`–`Kreis 8`; leer ausserhalb der Stadt (dann steht die Gemeinde in `municipality`). **`building_no` 1914:** das Lesemodell hatte in 12 015 Einträgen den Kreis als Hausnummer gelesen («6 Habsburgstrasse 26» → `6`); seit 3c1a6a7 steht die gedruckte Nummer. Die Hausnummern 1859 und die der Ausgemeinden 1875/1885 sind alte Nummern und nicht mit den heutigen vergleichbar. |

## data/norm/ab_authority.csv — Normdaten der Adressbuch-Einträge

Übernommen aus `10_authority_links.csv` der Städte. **Sichtbar ist alles bis «möglich»**:
Zeilen mit `tier = verworfen` und Zeilen, deren HLS-Prüfung mit `falsch` beginnt, werden
nicht übernommen.

| Spalte | Inhalt |
|---|---|
| `id` | Adressbuch-Eintrag |
| `qid`, `label`, `birth`, `death` | Wikidata |
| `hls_id`, `gnd` | HLS-Artikelnummer, GND |
| `tier` | `wahrscheinlich`, `möglich` |
| `hls_check` | Ergebnis der Prüfung am HLS-Artikel (`bestätigt: …`, `zweifelhaft: …`, `ungeprüft`, leer) |
| `evidence`, `score` | Begründung und Punktzahl der Stadt |

## data/norm/ptt_entries.csv.gz — Telefonbuch-Einträge (gzip)

Charge A (`tsv/a/<RefCode>.tsv`, eintragsweise, 1880–1910) und Charge B (`tsv/b*.tsv`,
gesamtschweizerische Bände 1, 2a, 2b, 2c, 3; im Zeitfenster 1911–1914). Erzeugt von
`ingest_ptt.py` (Rohstufe in `.cache/`) und `enrich_ptt.py` (Orte: `places.py`,
Zerlegung: `parse_ptt.py`).

| Spalte | Inhalt |
|---|---|
| `id` | `ptt:<Datei oder Band>:<seq>` |
| `batch`, `seq` | Charge `A`/`B`; Zeilennummer je Datei (A) bzw. je Band (B) in Lesereihenfolge |
| `year`, `network` | Jahrgang; Telefonnetz (nur Charge A) |
| `refcode`, `page`, `image` | Archivsignatur bzw. Band, Seite, Bilddatei (nur A) |
| `name1`, `name2`, `supplement`, `street`, `locality`, `phone` | die Spalten der Quelle, Leerraum bereinigt |
| **Ort** | |
| `place_name`, `place_kind` | aufgelöster Ort; `gemeinde_1914` (Gemeinde zum 1.1.1914) oder `ortschaft` (Ortschaft des amtlichen Verzeichnisses, nie Gemeinde gewesen) |
| `hist_code_1914`, `municipality_1914` | Historisierungsnummer und Name der Gemeinde 1914 (BFS); leer bei Ortschaften |
| `bfs_today`, `canton`, `lat`, `lon` | heutige BFS-Nummer(n), Kanton, Koordinaten (WGS84) |
| `exchange_raw` | Zentrale in Klammern, wie gelesen |
| `place_method` | Weg der Auflösung, z. B. `überschrift:name:eindeutig`, `überschrift:abkürzung:zentrale`, `jahresabgleich:zeile`, `…:lauf-unplausibel` |
| `place_confidence` | `hoch` (Name genau, eindeutig oder durch Kanton/Zentrale bestimmt, oder zwei Jahrgänge stimmen überein), `mittel`, `unsicher` (Überschrift trägt mehr Zeilen, als der Ort haben kann, und kein anderer Jahrgang klärt sie), `keine` |
| **Zerlegung** | |
| `entity_type` | `person`, `firma` (auch Hotels, Vereine, Einrichtungen), `amt` (Gemeinde-Sprechstationen, Post, Polizei …), `zusatz` (zweite Zeile eines Abonnenten: Wohnung, Filiale …) |
| `parent_id` | bei `zusatz`: der Haupteintrag davor |
| `surname`, `alliance_name` | Familienname und Allianzname (`Maggi-Strehler`), nur bei Personen |
| `forename`, `initials` | ausgeschriebene Vornamen (aus der Vornamenliste) und Initialen aller Vornamen, auch abgekürzter (`Joh.` → `J`) |
| `title` | `Dr.`, `Frau`, `Wwe.`, `Mme` … |
| `occupation` | Beruf und übrige Zusätze, `; `-getrennt |
| `street_name`, `house_no`, `street_key` | Strasse und Nummer wie gelesen; `street_key` vereinheitlicht (`Limmatstr.` → `limmatstrasse`, `r. du Flon` → `rue flon`) |
| `phone_norm` | Rufnummer nur Ziffern |
| `parse_flags` | `vorname-im-namen`, `strasse-umgestellt` (Adresse stand nicht in der Strassenspalte) |

## data/ref/ — Register

| Datei | Inhalt |
|---|---|
| `municipalities_1914.csv` | Gemeinden zum 1.1.1914 (BFS, Historisiertes Gemeindeverzeichnis) mit Bezirk, Kanton und heutiger BFS-Nummer über die Mutationen bis heute (`bfs_today`; der Schnappschuss selbst gibt Zürich, Bern u. a. die Platzhalter-Nummer 7700) |
| `localities.csv` | amtliches Ortschaftenverzeichnis (swisstopo): Ortschaft, PLZ, heutige Gemeinde, Koordinaten |
| `forenames.csv` | Vornamenliste aus den Daten (Adressbücher, Telefonbücher), mit Häufigkeiten |

Handkorrekturen der Orte: `data/review/places_manual.csv` (`place_raw` → `hist_code` oder
Ortschaft `name` + `canton`).

## links/ptt_ab.csv — Telefonbuch ↔ Adressbuch (M2)

Ein Paar je Zeile: dieser Telefonbuch-Eintrag ist in diesem Adressbuch-Band diese Person
oder Firma. Steht die Person im Band mehrfach (Einwohner-, Berufs-, Gebäudeverzeichnis),
gibt es je Eintrag eine Zeile mit derselben Stufe. Regeln und Messung:
[verknuepfung.md](verknuepfung.md).

| Spalte | Inhalt |
|---|---|
| `ptt_id`, `ab_id` | Telefonbuch- und Adressbuch-Eintrag (Bezeichner wie oben) |
| `city` | Stadt-Id aus `sources.toml` |
| `ptt_year`, `ab_volume`, `year_gap` | Jahrgang, Band, Abstand in Jahren |
| `tier` | `sicher`, `wahrscheinlich`, `möglich` |
| `score`, `evidence` | Punkte und Belege (`vorname:gleich`, `vorname:abkürzung`, `vorname:initiale`, `allianzname`, `strasse`, `hausnummer`, `gebäudenummer`, `beruf`, `telefonzeichen`, `firma`, `firma-person`) |
| `ptt_name`, `ab_name`, `ptt_address`, `ab_address` | zum Lesen: Name und Adresse beider Seiten |

`links/authority.csv` (Personen und Firmen ↔ Wikidata/HLS/GND) folgt in M3.

## data/review/m2_stichprobe.csv — beurteilte Paare

`nr`, `stichprobe`, `ptt_id`, `ab_id`, `city`, `tier_bei_ziehung`, `ptt_year`, `ab_volume`,
`ptt_text`, `ab_text`, `urteil` (`richtig` / `falsch` / `unklar`), `begruendung`.

## links/entities.csv.gz — Einträge je Einheit (M3)

Jeder gebündelte Eintrag (Telefonbuch und Adressbuch) mit seiner Einheit. Regeln:
[Einheiten](einheiten.md).

| Spalte | Inhalt |
|---|---|
| `record_id` | Eintrag (`ptt:…` oder Adressbuch-Bezeichner) |
| `entity_id` | Einheit, `e` + 10 Hex-Zeichen; gebildet aus dem kleinsten `record_id` der Einheit |
| `source` | `ptt` oder `ab` |
| `year` | Jahrgang bzw. Band |
| `municipality` | Gemeinde 1914 |

## links/entity_edges.csv.gz — Kanten der Bündelung

Die Kanten, die zwei Bündel vereinigt haben (ein Baum je Einheit). `a`, `b` = Einträge,
`kind` = `ptt-ptt`, `ab-ab` oder `ptt-ab`, `strength` = Reihenfolge der Verarbeitung,
`evidence` = Belege mit `+` (`telefon`, `vorname:gleich`, `strasse`, `hausnummer`, `beruf`,
`allianzname`, `zeile`, `ganze-zeile`, `firmenname`, `derselbe`, `m2:sicher` …).

## data/norm/entities.csv.gz — Einheiten

Je Einheit: `kind` (`person`, `firma`), `municipality`, `bfs_today`, `canton`, `name`
(Firmen), `surname`, `forename` (häufigster ausgeschriebener Vorname), `first_year`,
`last_year`, `years`, `n_ptt`, `n_ab`, `phones`, `addresses` (neueste zuerst),
`occupations`.

## links/authority.csv — Normdaten je Einheit (M3)

| Spalte | Inhalt |
|---|---|
| `entity_id` | Einheit |
| `qid`, `label`, `birth`, `death` | Wikidata |
| `hls_id`, `gnd` | aus demselben Wikidata-Eintrag |
| `tier` | `wahrscheinlich`, `möglich` |
| `source` | `stadt` (aus `ab_authority.csv` übernommen) oder `telefonbuch` (zweiter Abgleich) |
| `evidence` | Belege (Stadt: deren Begründung; sonst `vorname:…`, `wohnort`, `wirkungsort`, `sterbeort`, `geburtsort`, `beruf`) |
| `hls_check` | Ergebnis der HLS-Prüfung der Stadt (nur `source = stadt`) |
| `via` | Adressbuch-Eintrag, der die Normdaten trug (nur `source = stadt`) |

## data/ref/wikidata_persons.csv.gz — Kandidaten des zweiten Abgleichs

Menschen in Wikidata, geboren 1790–1895, gestorben 1880 oder später, mit HLS-Artikel oder
Wohn-, Wirkungs- bzw. Sterbeort in einer Schweizer Gemeinde. `places` = `beziehung:BFS-Nr.`
mit `|`. Neu holen mit `make wikidata`; Stand im Commit-Datum.

## data/review/m3_stichprobe.csv, m3_normdaten.csv — beurteilte Bündel und Normdaten

`m3_stichprobe.csv`: `stichprobe` (1–5), `schicht`, beide Einträge mit Text, `urteil`
(`richtig`/`falsch`/`unklar`; Schicht `getrennt`: `gleich`/`verschieden`/`unklar`;
Schicht `naechste_ausgabe`: `verknüpft`/`verpasst`/`fehlt`/`unklar`), `begruendung`.
`m3_normdaten.csv`: neue Normdaten-Verknüpfungen mit `urteil` und `begruendung`.

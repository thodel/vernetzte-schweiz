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

## Verknüpfungen (ab M2)

`links/ptt_ab.csv` (Telefonbuch ↔ Adressbuch) und `links/authority.csv` (Cluster ↔
Wikidata/HLS/GND) sind der veröffentlichte Datensatz. Ihr Format wird in M2 festgelegt.

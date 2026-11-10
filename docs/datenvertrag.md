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

Aus Charge A (`tsv/a/*.tsv`), Jahre im Zeitfenster.

| Spalte | Inhalt |
|---|---|
| `id` | siehe oben |
| `year`, `network` | Jahrgang und Telefonnetz (wie im Dateinamen/`Network`) |
| `refcode`, `page`, `image` | Archivsignatur, Seite, Bilddatei der Quelle |
| `name1`, `name2`, `supplement` | `EntityName1` (Familien- oder Firmenname), `EntityName2` (Vorname/Zusatz), `Supplement` (Beruf, Abteilung) |
| `street`, `locality`, `phone` | wie gelesen |

## Verknüpfungen (ab M2)

`links/ptt_ab.csv` (Telefonbuch ↔ Adressbuch) und `links/authority.csv` (Cluster ↔
Wikidata/HLS/GND) sind der veröffentlichte Datensatz. Ihr Format wird in M2 festgelegt.

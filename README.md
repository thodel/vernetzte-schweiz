# Vernetzte Schweiz 1860–1914

Adressbücher Schweizer Städte und die historischen Telefonbücher der PTT, miteinander
verknüpft und mit Wikidata, dem Historischen Lexikon der Schweiz (HLS) und der GND
verbunden.

Seite: https://thodel.github.io/vernetzte-schweiz/

Plan, Entscheide und offene Fragen: [PLAN.md](PLAN.md) · Datenvertrag:
[docs/datenvertrag.md](docs/datenvertrag.md)

## Quellen

- Adressbücher Aarau 1884–1899 — [adressbuecher-aarau](https://github.com/thodel/adressbuecher-aarau)
- Adressbuch Basel 1862 — [adressbuecher-basel](https://github.com/thodel/adressbuecher-basel)
- Telefonbücher bis 1914 — PTT-Archiv P-260, aufbereitet von DH Bern und localsearch
  ([DHBern/PTT_phonebook_data_tsv](https://github.com/DHBern/PTT_phonebook_data_tsv),
  [historic.localsearch.ch](https://historic.localsearch.ch))

Jede Quelle ist in [config/sources.toml](config/sources.toml) an einen Commit gebunden.

## Betrieb

```bash
make ingest   # Quellen am gepinnten Commit lesen → data/norm/
make site     # Kennzahlen und Seitendaten → site/data/
make serve    # Seite lokal auf http://localhost:8000
```

Das PTT-Repo wird lokal gelesen (Pfad in `sources.toml`, `ptt.local`); der Adapter prüft,
dass der Checkout auf dem gepinnten Commit steht. GitHub Pages baut `site/` bei jedem Push.

## Lizenz

Code und Seite: MIT ([LICENSE](LICENSE)). Die Lizenz der Daten in `data/` und der
Verknüpfungen in `links/` ist noch nicht festgelegt (siehe [PLAN.md](PLAN.md)).

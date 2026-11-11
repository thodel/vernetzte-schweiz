# Vernetzte Schweiz 1860–1914

Adressbücher Schweizer Städte und die historischen Telefonbücher der PTT, miteinander
verknüpft und mit Wikidata, dem Historischen Lexikon der Schweiz (HLS) und der GND
verbunden.

Seite: https://thodel.github.io/vernetzte-schweiz/

Plan, Entscheide und offene Fragen: [PLAN.md](PLAN.md) · Datenvertrag:
[docs/datenvertrag.md](docs/datenvertrag.md) · Verknüpfung:
[docs/verknuepfung.md](docs/verknuepfung.md), [docs/einheiten.md](docs/einheiten.md) · Seite: [docs/seite.md](docs/seite.md), [docs/karten.md](docs/karten.md), [docs/suche.md](docs/suche.md), [docs/volltext.md](docs/volltext.md)

## Quellen

- Adressbücher Aarau 1884–1899 — [adressbuecher-aarau](https://github.com/thodel/adressbuecher-aarau)
- Adressbuch Basel 1862 — [adressbuecher-basel](https://github.com/thodel/adressbuecher-basel)
- Telefonbücher 1880–1914 — PTT-Archiv P-260, aufbereitet von DH Bern und localsearch
  ([DHBern/PTT_phonebook_data_tsv](https://github.com/DHBern/PTT_phonebook_data_tsv),
  [historic.localsearch.ch](https://historic.localsearch.ch))
- Ortsregister — Historisiertes Gemeindeverzeichnis (BFS), amtliches Ortschaftenverzeichnis (swisstopo)

Jede Quelle ist in [config/sources.toml](config/sources.toml) an einen Commit gebunden.

## Betrieb

```bash
make ref      # Ortsregister (BFS-Gemeinden 1914, Ortschaften) → data/ref/
make ingest   # Quellen am gepinnten Commit lesen, Orte auflösen, zerlegen → data/norm/
make link     # Telefonbuch ↔ Adressbuch verknüpfen und messen → links/, data/norm/
make entities # Einheiten über die Jahre bündeln, Normdaten, Messung → links/, data/norm/
make wikidata # Kandidaten für den Normdaten-Abgleich neu holen → data/ref/
make site     # Kennzahlen, Suchindex, Einheiten-, Adress- und Ortsseiten → site/data/
make serve    # Seite lokal auf http://localhost:8000
```

Das PTT-Repo wird lokal gelesen (Pfad in `sources.toml`, `ptt.local`); der Adapter prüft,
dass der Checkout auf dem gepinnten Commit steht. GitHub Pages baut `site/` bei jedem Push.

## Lizenz

- **Code und Seite:** MIT ([LICENSE](LICENSE)).
- **Inhalte der Telefon- und Adressbücher (bis 1914):** gemeinfrei. Nach dem
  Urheberrechtsgesetz (URG Art. 2 Abs. 1) sind nur geistige Schöpfungen mit individuellem
  Charakter geschützt. Adress- und Telefonverzeichnisse nach alphabetischen oder
  geografischen Kriterien erreichen diese Schöpfungshöhe in der Regel nicht. Selbst wo ein
  Werk vorläge (Vorwort, Stadtplan), erlischt der Schutz 70 Jahre nach dem Tod des Urhebers
  (Art. 29 Abs. 2 URG).
- **Daten in `data/` und Verknüpfungen in `links/`:** entsprechend frei weiterzunutzen, als
  [CC0 1.0](https://creativecommons.org/publicdomain/zero/1.0/deed.de) (Entscheid
  11.11.2026).
- **Ausnahmen:** Wikidata-Angaben stehen ebenfalls unter CC0. Aus dem HLS übernehmen wir
  nur Fakten (Name, Lebensdaten, Nummer, Fachgebiet), keinen Artikeltext.

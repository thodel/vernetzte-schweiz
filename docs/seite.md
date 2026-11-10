# Die Seite (M4)

Die Seite ist statisch (GitHub Pages). `scripts/build_site.py` schreibt die Kennzahlen der
Startseite, `scripts/build_pages.py` die Daten der Unterseiten nach `site/data/`. Beides
läuft bei jedem Push im Pages-Workflow und lokal mit `make site`; `site/data/` ist nicht im
Repo.

## Unterseiten

| Adresse | Inhalt |
|---|---|
| `#/suche?q=…&m=…&s=t\|a` | Personen und Firmen nach Familien- bzw. Firmenname (vom Anfang her, ohne Akzente), weitere Wörter grenzen nach Vorname oder Beruf ein, `m` nach Gemeinde |
| `#/e/<entity_id>` | eine Einheit: Normdaten, Zeitleiste 1860–1914, alle Einträge mit Adresse, Nummer und Fundstelle, mögliche weitere Adressbuch-Einträge (M2, nicht gebündelt), Gemeinde auf der Karte |
| `#/a/<Gemeinde>\|<Strasse>\|<Nr.>` | eine Adresse: alle Einträge aller Jahre mit Strasse und Hausnummer |
| `#/g/<Gemeinde>` | eine Gemeinde 1914: Telefonbuch-Einträge je Jahr, Zahl der Personen und Firmen, die zehn häufigsten Familiennamen, Karte |
| `#/orte` | alle Gemeinden, nach Zahl der Einträge |
| `#/vorbehalte` | was die Daten können und was nicht |
| `#/karten?v=telefon\|berufe\|namen` | Karten (M6, [docs/karten.md](karten.md)) |
| `#/suche?b=…` | Suche nach Berufen mit Karte (M6) |

Die alten Anker der Startseite (`#quellen`, `#einheiten` …) bleiben gültig.

Gleiche Zeilen aus mehreren Ausgaben desselben Jahres (Basel 1884: zwei Ausgaben, dazu
Nachträge) stehen auf der Seite einer Einheit einmal, mit allen Fundstellen.

## Daten in Teilen

| Datei | Schlüssel | Inhalt |
|---|---|---|
| `names/<xx>.json.gz` | erste zwei Buchstaben des Familien- bzw. Firmennamens, ohne Akzente und ohne «von», «de» usw. | je Einheit: Bezeichner, Name, Gemeinde, Jahre, Art, Zahl der Einträge, Normdaten-Stufe, Berufe (gekürzt) |
| `e/<xx>.json.gz` | Zeichen 2–3 der `entity_id` | Einheiten mit Einträgen, Normdaten, möglichen weiteren Adressbuch-Einträgen |
| `a/<xx>.json.gz` | FNV-1a des Adressschlüssels, letztes Byte | Adressen mit ihren Einträgen |
| `g/<xx>.json.gz`, `places.json` | FNV-1a des Gemeindenamens | Gemeinden 1914 |

Alle Teile sind gzip-gepackt; `pages.js` entpackt sie mit `DecompressionStream`. So bleibt
das Pages-Paket bei rund 40 MB statt 180 MB, und der Deploy läuft in der Zeit.

`fold()` und `fnv()` sind in `scripts/build_pages.py` und `site/assets/pages.js` gleich
gerechnet; `tests/test_pages.py` hält die im Browser geprüften Werte fest.

Adressschlüssel: Gemeinde, Strassenschlüssel (wie in M3: ohne «St.», Abkürzungen
ausgeschrieben) und Hausnummer ohne Zusatzbuchstaben. Einträge ohne Hausnummer haben keine
Adressseite.

## Grenzen

- Die Suche führt Schreibvarianten (Meyer/Maier/Meier) nicht zusammen; sie sucht vom
  Anfang des Namens her.
- Der Kartenpunkt ist der Mittelpunkt der Gemeinde (aus M1), nicht die Adresse. Die
  Karte lädt Leaflet von cdnjs und Kacheln von OpenStreetMap.
- Fundstellen nennen Band und Seite. Bilder der Seiten verlinkt die Seite nur für Basel
  (Digitaler Lesesaal des Staatsarchivs, Band 1862); für Aarau und die Telefonbücher gibt
  es keinen frei verlinkbaren Seitenaufruf.

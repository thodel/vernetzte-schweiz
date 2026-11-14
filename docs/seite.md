# Die Seite (M4)

Die Seite ist statisch (GitHub Pages). `scripts/build_site.py` schreibt die Kennzahlen der
Startseite, `scripts/build_pages.py` die Daten der Unterseiten nach `site/data/`. Beides
läuft bei jedem Push im Pages-Workflow und lokal mit `make site`; `site/data/` ist nicht im
Repo.

## Unterseiten

| Adresse | Inhalt |
|---|---|
| `#/suche?q=…&m=…&j=…&s=t\|a&f=1&x=…&k=…&n=1&a=…&z=…&o=…` | Personen und Firmen nach Familien- bzw. Firmenname (vom Anfang her, ohne Akzente), weitere Wörter grenzen nach Vorname oder Beruf ein, `m` nach Gemeinde, `j` nach Beruf (Weitere Filter; jedes Wort muss im Beruf oder Zusatz stehen), `u=1` sucht den Beruf auch übersetzt |
| `#/e/<entity_id>` | eine Einheit: Normdaten, Zeitleiste 1860–1914, alle Einträge mit Adresse, Nummer und Fundstelle, mögliche weitere Adressbuch-Einträge (M2, nicht gebündelt), Gemeinde auf der Karte |
| `#/a/<Gemeinde>\|<Strasse>\|<Nr.>` | eine Adresse: alle Einträge aller Jahre mit Strasse und Hausnummer |
| `#/g/<Gemeinde>` | eine Gemeinde 1914: Telefonbuch-Einträge je Jahr, Zahl der Personen und Firmen, die zehn häufigsten Familiennamen, Karte |
| `#/orte` | alle Gemeinden, nach Zahl der Einträge |
| `#/vorbehalte` | was die Daten können und was nicht |
| `#/quellen/<quellen\|telefon\|ortsqualitaet\|verknuepfung\|einheiten\|vorgehen>` | Quellen & Qualität: die Abschnitte, die früher auf der Startseite standen, mit Unternavigation |
| `#/wanderungen?…&vo=…&na=…&ort=…` | Wanderungen (M10, Versuch, [docs/wanderungen.md](wanderungen.md)); `vo`/`na`/`ort` grenzen auf einen Ort ein (Klick auf Linie oder Punkt öffnet so einen neuen Tab); früher `#/karten?v=wanderungen`, das weiterleitet |
| `#/karten?v=telefon\|berufe\|namen` | Karten (M6, [docs/karten.md](karten.md)) |
| `#/suche?b=…&q=…` | Suche nach Berufen mit Karte (M6); `q` grenzt nach Name ein (Weitere Filter), `u=1` sucht den Beruf auch übersetzt |
| `#/suche?v=ft&q=…` | Volltext über alle Einträge (M8, [docs/volltext.md](volltext.md)) |
| `#/buch?kt=…&y=…` | alle Einträge eines Kantons und Jahrgangs (M8) |

Die alten Anker der Startseite (`#quellen`, `#einheiten` …) führen zur passenden Unterseite von Quellen & Qualität.

Gleiche Zeilen aus mehreren Ausgaben desselben Jahres (Basel 1884: zwei Ausgaben, dazu
Nachträge) stehen auf der Seite einer Einheit einmal, mit allen Fundstellen.

## Daten in Teilen

| Datei | Schlüssel | Inhalt |
|---|---|---|
| `names/<xx>.json.gz` | erste zwei Buchstaben des Familien- bzw. Firmennamens, ohne Akzente und ohne «von», «de» usw. | je Einheit: Bezeichner, Name, Gemeinde, Jahre, Art, Zahl der Einträge, Normdaten-Stufe, Berufe (gekürzt) |
| `e/<xx>.json.gz` | Zeichen 2–3 der `entity_id` | Einheiten mit Einträgen, Normdaten, möglichen weiteren Adressbuch-Einträgen |
| `a/<xx>.json.gz` | FNV-1a des Adressschlüssels, letztes Byte | Adressen mit ihren Einträgen |
| `g/<xx>.json.gz`, `places.json` | FNV-1a des Gemeindenamens, 64 Teile | Gemeinden 1914 |

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
- Fundstellen nennen Band und Seite. Seitenbilder: Telefonbücher bis 1910 (IIIF des
  PTT-Archivs, M8), Adressbuch Basel 1862 (Digitaler Lesesaal des Staatsarchivs); für
  Aarau und die Telefonbücher 1911–1914 noch nicht.

## Berufe übersetzt

Mit «Übersetzungen mitsuchen» (`u=1`) findet die Suche denselben Beruf auch in den anderen
Sprachen. Beschrieben in [berufssuche.md](berufssuche.md).

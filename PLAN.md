# Vernetzte Schweiz 1860–1914 — Plan

Stand 10.11.2026 (M1 abgeschlossen).

Ein eigenständiger Demonstrator, der die Adressbücher einzelner Schweizer Städte mit den
historischen Telefonbüchern der PTT verknüpft und die Personen und Firmen mit Wikidata,
dem HLS und der GND verbindet. Die Städte werden in eigenen Repos ausgewertet
(adressbuecher-aarau, adressbuecher-basel, weitere folgen); hier werden sie
zusammengeführt, verknüpft und gezeigt.

## Entscheide (10.11.2026)

| Frage | Entscheid |
|---|---|
| Zeitfenster | 1860–1914. Von Basel zählt damit nur der Band 1862. |
| Nächste Städte | Zürich, Baden, weitere |
| Wo wird verknüpft? | Hier, zentral. Telefonbuch ↔ Adressbuch und die Bündelung über die Jahre laufen in diesem Repo. Die Normdaten-Abgleiche der Städte (mit ihren lokalen Regeln) werden übernommen. |
| Umfang Telefonbücher | Alle Einträge bis 1914 sind suchbar, auch Orte ohne Adressbuch. |
| Charge A | Wird im PTT-Repo eintragsweise neu aufbereitet (`tsv/a/<RefCode>.tsv`); hier nur übernommen, nicht neu gelesen. Charge B (1911–1914) wird hier verortet und zerlegt. |
| Sichtbarkeit von Normdaten | Alles bis «möglich»; was in der HLS-Prüfung als falsch erkannt oder als «verworfen» eingestuft ist, erscheint nicht. |
| Lizenzen | Seite und Code: MIT. Daten: noch festzulegen. Verknüpfungen: ohne Lizenz (siehe offene Fragen). |
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

**M2 — Zentraler Verknüpfer Telefonbuch ↔ Adressbuch.** Blocken nach Stadt und
Familienname; Merkmale Vorname/Initiale, Beruf, Strasse + Nummer (mit Konkordanz alter und
neuer Nummern), Jahresabstand. Stufen `sicher` / `wahrscheinlich` / `möglich`. Messen an
den bestehenden Verknüpfungen der Städte (Aarau `09_links_ptt.csv`, Basel
`20_phonebook_links.csv`) und an rund 200 von Hand geprüften Paaren; Präzision je Stufe
ausweisen. Ergebnis: `links/ptt_ab.csv`.

**M3 — Personen und Firmen über die Jahre.** Einträge derselben Person oder Firma über
Bände und Telefonbuch-Jahrgänge bündeln; Normdaten der Städte übernehmen; zweiter
Abgleich für Personen und Firmen, die nur im Telefonbuch stehen (Wikidata, HLS, GND; Join
nur über Bezeichner, nie über blosse Namen). Ergebnis: `links/authority.csv`.

**M4 — Seite.** Suche im Browser über geteiltes JSON; Seite je Person/Firma (Einträge,
Telefon, Normdaten, Zeitleiste, Karte), Seite je Adresse, Abdeckung je Stadt und Jahr,
eine gut sichtbare Seite zu den Vorbehalten (OCR, Verknüpfungsstufen).

**M5 — Weitere Städte.** Zürich, Baden: Eintrag in `sources.toml`, Adapter prüfen,
Verknüpfung und Bau laufen durch.

## Offene Fragen

1. **Lizenz der Daten.** Die PTT-Daten sind laut Projektleitung (06.11.2026) frei
   nutzbar, das PTT-Repo hat aber keine Lizenzdatei. Welche Lizenz, und wer gibt sie frei?
2. **«Verknüpfungen ohne Lizenz».** Ohne Lizenz gilt rechtlich «alle Rechte vorbehalten»;
   andere dürfen den Datensatz dann nicht weiterverwenden. Gemeint ist vermutlich CC0
   (gemeinfrei). Bis zur Klärung trägt `links/` keine Lizenzdatei.
3. **Zürich und Baden:** Gibt es schon Repos oder Scans, und welche Bände?

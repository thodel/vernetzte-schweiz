# Karten und Berufssuche (M6)

`scripts/build_maps.py` schreibt die Daten der Karten (`site/data/maps.json.gz`), der
Namenskarte (`nm/`) und der Berufssuche (`ow/`); `scripts/occupations.py` ordnet Berufe
Klassen zu. Beides läuft im Pages-Workflow und mit `make site`.

## Was gezählt wird

**Einheiten, nicht Einträge** (M3): Eine Person oder Firma zählt einmal, auch wenn sie
20 Jahre im Telefonbuch steht. Die Karten zählen nur Einheiten mit Telefonbuch-Eintrag
(163 971); der Punkt ist die Gemeinde 1914, nicht die Adresse. Die Grundgesamtheit sind
**Abonnenten**, nicht die Bevölkerung.

## Die drei Karten (`#/karten`)

- **Wer bekam wann ein Telefon.** Heatmap nach dem ersten Jahr, in dem eine Einheit im
  Telefonbuch steht; «neu in diesem Jahr» oder «bis zu diesem Jahr»; Filter nach Art,
  Berufsklasse und Kanton. Darunter die Zahl je Jahr (Filter wie Karte) und die Zahl der
  Gemeinden mit Einträgen im gewählten Jahr.
  **Vorbehalt:** «Erstes Jahr» ist die erste *vorliegende* Ausgabe. Bis 1910 liegen nur
  einzelne Ausgaben vor (Charge A), 1911–1914 jährlich die ganze Schweiz (Charge B). Der
  Sprung 1911 kommt aus der Überlieferung, nicht aus einem Boom.
- **Berufe.** Je Berufsklasse und Zeitraum: Anzahl als Heatmap, oder Anteil an allen
  Abonnenten der Gemeinde (Gemeinden ab 20 Abonnenten; Farbe in fünf Stufen: 0 % und die
  Quartile der übrigen). Beispiel: Uhren zeigen den Jurabogen.
- **Namen.** Ohne Namen: Klick auf eine Gemeinde zeigt die fünf häufigsten Familiennamen
  (Personen) je Zeitraum. Mit Namen: wo Personen dieses Namens in einem Jahr stehen (Kreise),
  der Schwerpunkt je Jahr (rote Linie) und das erste Jahr je Gemeinde. Der Schwerpunkt
  springt auch, wenn Ausgaben fehlen oder hinzukommen. Gleicher Name heisst nicht gleiche
  Familie.

Karten: Leaflet 1.9.4 und leaflet.heat 0.2.0 von cdnjs, Kacheln von OpenStreetMap.

## Berufssuche (`#/suche?b=…`)

Sucht im Berufsfeld aller Einheiten (auch nur im Adressbuch), vom Wortanfang her, ohne
Akzente; ein zweites Wort grenzt ein. Ergebnis: Liste und Karte der Gemeinden (Kreisfläche =
Treffer). Keine Übersetzung: «Metzger» findet nicht «boucher». Filter: Gemeinde, Zeitraum,
Quelle.

**Quelle** (auch in der Namenssuche): Telefon- und Adressbuch, nur Einheiten mit
Telefonbuch-Eintrag, nur Einheiten mit Adressbuch-Eintrag. Wer in beiden steht, erscheint
bei beiden.

## Berufsklassen

16 Klassen aus Schlüsselwörtern über Beruf, Zusatz und Firmenname, deutsch, französisch
und italienisch (`scripts/occupations.py`); die erste passende Klasse gewinnt. Die Klassen
sind grob und für Karten gedacht.

**Messung** (`data/review/m6_berufe.csv`, beurteilt von Claude, nicht von den
Projektmitarbeitenden):
- **Stichprobe 1** (zum Einstellen): 53 von 60 klassierten Einheiten richtig, 4 falsch,
  3 unklar. Die Fehler waren Musterfehler («A.-G.» traf «Agenturen», «vin» traf «Boivin»,
  «Kanton» zog ein Elektrizitätswerk zur Verwaltung) und wurden behoben.
- **Stichprobe 2** (danach gezogen): 53 von 60 richtig, 5 falsch, 2 unklar: **88–92 %**.
  Fehler: Adresse als Beruf gelesen («Güterbahnhof»), «Hôtel de Ville» als Gastgewerbe,
  «Anstalt» als Bildung.
- **Abdeckung:** 112 612 von 181 215 Einheiten (62 %) haben eine Klasse. Unter 30
  Einheiten ohne Klasse, aber mit Text im Berufsfeld, nannten 18 einen Beruf, den die
  Schlüsselwörter nicht kennen («Modistinnen», «Taglöhner», «Warenhaus»), 10 keinen.
  Karten nach Klassen zeigen deshalb weniger, als im Telefonbuch steht.

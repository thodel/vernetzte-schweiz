# Infrastruktur (Versuch)

Was zeigen Telefon- und Adressbücher vom Ausbau der Infrastruktur? `scripts/infrastruktur.py` misst
drei Dinge; die Seite zeigt sie unter `#/infrastruktur`.

```bash
make infrastruktur                      # data/norm/infrastruktur.json
python scripts/infrastruktur.py site    # site/data/infrastruktur.json.gz (läuft im Pages-Workflow)
```

## Die Quellen und ihre Lücken

Die Telefonbücher decken die ganze Schweiz erst ab **1911** (Landesbuch, Bände 1, 2a–2c, 3). Vorher
liegen Regionalbücher vor, je nach Jahr für Basel, Bern, St. Gallen, Aarau, Chur, Bellinzona, Genève,
Zürich (1909–1910) und ihre Netze. Ein Ort, der erst 1911 erscheint, kann früher ein Telefon gehabt
haben, wenn sein Regionalbuch fehlt (vor allem Waadt und Wallis). Auch im Landesbuch ist nicht jeder
Band ganz gelesen (Band 2c fehlt 1913 und 1914, Lausanne 1912–1914 und Chur 1911–1914 sind dünn).

## 1. Telefonnetz

**Reihen je Stadt.** Einträge je Stadt und Jahr. Liegen für ein Jahr mehrere Bände vor (Basel 1899),
zählt der mit den meisten Einträgen. Ein Jahr mit weniger als 60 % des vorigen behaltenen Jahrs gilt
als unvollständig gelesen und fällt weg. Gezeigt sind 19 Städte mit mindestens acht Jahrgängen
vor 1911 und mindestens 150 Einträgen im letzten Jahr. Basel wächst von 145 Einträgen
(1881) auf 8'813 (1914), Bern von 74 auf 6'159.
Ein Eintrag ist nicht ein Anschluss: Firmen stehen unter mehreren Namen, Geschäftsleute mit
Wohnungsanschluss zweimal.

**Telefon in der Wohnung.** Anteil der Einträge mit einem Wohnungsanschluss («Wohnung», «Privat»,
«domicile», «appartement», «abitazione»). Basel steigt von 0 % (1881–1886) auf 4,1 % (1914), Bern
von 0,1–0,2 % (1890er Jahre) auf 9,7 % (1909), St. Gallen auf 6,8 % (1910). Der Anteil der Einträge
unter Personennamen taugt dafür nicht: «Weitnauer, Cigarrenhandlung» ist eine Person mit Geschäft.
Der frühe Gipfel in Bern (1881–1884, 2–5 %) beruht auf vier bis sechs Wohnungen unter 74 bis 192
Einträgen.

**Gemeinden.** Erstes Jahr, in dem eine Gemeinde in einem Telefonbuch steht, Einträge 1914 und
öffentliche Sprechstellen («Gemeindesprechstation», «station téléphonique publique», «posto
telefonico»). Von den 3'151 Gemeinden am 1.1.1914 (BFS) haben 2'626 bis 1914 mindestens einen
Eintrag (83%), 2'330 schon bis 1911. Eine öffentliche Sprechstelle haben 1911–1914 zusammen
733 Gemeinden, im Jahr 1914 allein 457.

## 2. Berufe der Infrastruktur

Sieben Gruppen nach Stichwörtern im Beruf, bei Firmen und Ämtern auch im Namen (`GROUPS` im Skript):
Bahn; Post, Telegraf, Telefon; Elektrizität; Gas und Wasser; Auto und Velo; Tram, Schiff, Omnibus;
Ingenieure und Bau.

- Gaststätten, die nach Bahnhof oder Post heissen («Hôtel de la Gare», «Wirtschaft z. Post»,
  «Bahnhofbuffet»), zählen nicht zu Bahn oder Post.
- Die Bahnen vor der Verstaatlichung 1902 stehen abgekürzt im Buch: N.O.B. (Nordostbahn), J.-S.
  (Jura-Simplon), S.C.B. (Centralbahn), V.S.B., J.-B.-L.; ohne sie fehlte Lausanne 1896 fast jede
  Bahnstelle (0,5 statt 14,8 je 1000 Einträge). Danach S.B.B. / C.F.F.
- «Postkondukteur» (Postkutsche) zählt zur Post, «Tramkondukteur» zum Tram.

**Adressbücher, je 1000 Einträge** (Einwohner- und Gebäudelisten), Zürich:

| Gruppe | 1867 | 1875 | 1885 | 1900 | 1914 |
|---|---|---|---|---|---|
| Bahn | 5.4 | 32.7 | 18.1 | 20.5 | 33.7 |
| Post, Telegraf, Telefon | 9.9 | 11.3 | 9.3 | 12.3 | 16.3 |
| Elektrizität | 0.3 | 0.0 | 0.1 | 1.5 | 3.9 |
| Gas und Wasser | 1.0 | 0.5 | 0.3 | 0.6 | 1.3 |
| Auto und Velo | 0.0 | 0.0 | 0.0 | 0.5 | 3.3 |
| Tram, Schiff, Omnibus | 2.0 | 1.9 | 1.7 | 3.0 | 6.1 |
| Ingenieure und Bau | 6.5 | 8.3 | 7.2 | 8.6 | 13.5 |

Zürich 1867 umfasst fast nur die Altstadt, 1875–1885 auch die Ausgemeinden (Bahnhof und Werkstätten
in Aussersihl). Weitere Reihen: Aarau 1867–1899, Bern 1883/1900, Lausanne 1896/1907, Baden 1900/1910.

**Landesbücher 1911–1914**, Einträge (Gemeinden):

| Gruppe | 1911 | 1912 | 1913 | 1914 |
|---|---|---|---|---|
| Bahn | 398 (141) | 444 (154) | 481 (165) | 501 (164) |
| Post, Telegraf, Telefon | 753 (275) | 838 (298) | 904 (349) | 963 (365) |
| Elektrizität | 583 (180) | 600 (207) | 636 (219) | 664 (216) |
| Gas und Wasser | 269 (75) | 289 (82) | 310 (84) | 331 (88) |
| Auto und Velo | 363 (53) | 459 (66) | 542 (73) | 590 (78) |
| Tram, Schiff, Omnibus | 139 (36) | 156 (42) | 163 (44) | 163 (43) |
| Ingenieure und Bau | 1'350 (211) | 1'345 (230) | 1'327 (241) | 1'369 (247) |
| Einträge insgesamt | 73'403 | 79'216 | 86'262 | 91'339 |

Die Telefonbücher nennen nur Abonnenten: ein Elektrizitätswerk oder eine Garage mit Telefon, nicht
jeden Elektriker oder Chauffeur.

## 3. Weitere Spuren und Ideen

- **Bahnhofstrasse** (umgesetzt): Gemeinden mit Einträgen an einer Bahnhofstrasse, Rue de la Gare,
  Via Stazione: 52 (1911), 65 (1914).
- **Rufnummern als Mass der Zentrale:** die höchste vergebene Nummer wächst mit den Linien (Basel
  um 1895 über 2 000); Sprünge zeigen Umnummerierungen beim Ausbau einer Zentrale.
- **Gemeindewerke:** Elektrizitätswerke, Gas- und Wasserversorgungen als Abonnenten ergeben mit
  ihrem ersten Jahr eine Karte der kommunalen Werke.
- **Ämter am Netz:** Gemeindekanzleien, Bahnhöfe, Posthalter mit Telefon.
- **Fremdenverkehr:** In den Bergorten sind Hotels die ersten Abonnenten (St. Moritz 1894: 21 von 38
  Einträgen, Grindelwald 1893: alle 8, Beatenberg 1895: 11 von 13).
- **Mit weiteren Daten:** Einwohnerzahlen der Volkszählungen 1888/1900/1910 (Anschlüsse je 1000
  Einwohner), Eröffnungsjahre der Bahnlinien (folgte das Telefon der Bahn?).

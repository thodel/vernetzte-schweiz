# Berufssuche

Wie man auf der Seite nach Berufen sucht, was dabei im Hintergrund geschieht und wo die
Suche an Grenzen stösst. Die Karten nach Berufsklassen beschreibt
[karten.md](karten.md), die Namenssuche [suche.md](suche.md).

## Drei Wege

| Wo | Adresse | Wofür |
|---|---|---|
| **Suche › Beruf** | `#/suche?b=…` | alle Personen und Firmen mit einem Beruf, mit Karte der Gemeinden |
| **Suche › Name**, Feld «Beruf» unter «Weitere Filter» | `#/suche?q=…&j=…` | Namensträger mit einem bestimmten Beruf («Meier» und «Bäcker») |
| **Karten › Berufe** | `#/karten?v=berufe` | Verteilung einer der 16 Berufsklassen über die Schweiz (Heatmap oder Anteil) |

In der Berufssuche steht unter «Weitere Filter» umgekehrt ein Feld «Name»
(`#/suche?b=…&q=…`). Beide Suchen kennen den Schalter **«Übersetzungen mitsuchen»**
(`u=1`).

## Bedienung

**Suche › Beruf**
- **Suchwort:** vom Wortanfang her, ohne Akzente und ohne Gross- und Kleinschreibung.
  «Uhrmach» findet «Uhrmacher» und «Uhrmacherei», «epic» findet «épicier» und
  «épicerie».
- **Zweites Wort:** grenzt ein und muss irgendwo im Berufsfeld stehen. «fabr horlog»
  findet die Uhrenfabrikanten.
- **Gemeinde, Jahre, Quelle:** wie in der Namenssuche. Der Regler wählt die Jahre, in denen
  ein Treffer belegt ist. Die Quelle ist Telefonbuch, Adressbuch oder beide.
- **Name (Weitere Filter):** Jedes Wort muss im Namen stehen, also Familienname oder
  Vorname.
- **Ergebnis:** die Zahl der Personen und Firmen, eine Karte (Kreisfläche = Treffer je
  Gemeinde), die Gemeinden mit den meisten Treffern und eine Liste der ersten 300.

**Suche › Name, Feld «Beruf»**
- Jedes Wort im Feld muss im Beruf oder Zusatz der Einheit stehen, und zwar irgendwo,
  nicht nur am Wortanfang.
- Alle anderen Filter der Namenssuche gelten weiter.

Gezählt werden **Einheiten**, nicht Einträge ([einheiten.md](einheiten.md)): Wer zwanzig
Jahre im Telefonbuch steht, zählt einmal. Gesucht wird in den Berufen aller Jahre einer
Einheit.

## Übersetzungen mitsuchen

Die Telefonbücher sind deutsch, französisch und italienisch geschrieben, oft abgekürzt.
Ohne Übersetzung findet «Metzger» nur, was «Metzger…» heisst. Mit dem Schalter findet er
auch «boucher», «charcutier» und «macellaio».

| Suchwort (Suche › Beruf) | ohne Übersetzung | mit Übersetzung | mitgesucht |
|---|---|---|---|
| Metzger | 4 574 in 697 Gemeinden | 7 514 in 1 130 Gemeinden | Metzger (boucher, macellaio, butcher) |
| Uhrmacher | 456 in 20 Gemeinden | 1 521 in 155 Gemeinden | Uhrmacher (horloger, orologiaio, watchmaker) |
| boulanger | 1 003 in 223 Gemeinden | 4 721 in 634 Gemeinden | Bäcker (boulanger, panettiere, baker) |

Stand: Seite vom 14.11.2026. In der Namenssuche ergibt «Meier» mit Beruf «boulanger» ohne
Übersetzung 0 Treffer, mit Übersetzung 40 (Bäcker und Bäckereien).

Über den Treffern steht, was mitgesucht wurde. An jedem Treffer steht der erkannte Beruf in
der Sprache der Seite: «≈ Bäcker» auf Deutsch, «≈ boulanger» auf Französisch, «≈ baker» auf
Englisch. Kennt die Liste das Suchwort nicht, sagt die Seite das, und gesucht wird nur der
Wortlaut.

### Woher die Übersetzung kommt

Grundlage ist die **feine Berufsliste** [scripts/occupations_fine.py](../scripts/occupations_fine.py).
Sie entstand für die Wanderungen ([wanderungen.md](wanderungen.md)), um zu entscheiden, ob
zwei Einträge derselbe Beruf sind.
- **124 Berufe**, je mit einem Muster, das die deutschen, französischen und italienischen
  Formen samt üblichen Abkürzungen erfasst. Ein Beispiel ist Metzger:
  `metzg|boucher|boucherie|charcut|macellaio|salumier|…`.
- **Gruppen verwandter Berufe** (Bäcker ↔ Konditor). Die Suche nutzt sie nicht; sie
  zählen nur für die Wanderungen.
- **`LABELS`:** je Beruf eine Bezeichnung auf Deutsch, Französisch, Italienisch und
  Englisch, für die Anzeige.

Daraus baut [scripts/build_maps.py](../scripts/build_maps.py) zwei Dinge:
1. **Wörterbuch** (`site/data/berufe.json`). Jedes Wort aus den Berufsfeldern (ab 4
   Buchstaben) wird mit den Mustern geprüft. Trifft eines, wird das Wort ohne Akzente dem
   Beruf zugeordnet. Das ergibt 8 603 Wörter, 868 davon gehören zu mehr als einem Beruf
   («arbeiter» zu Fabrikarbeiter und Handlanger).
2. **Index je Beruf** (`site/data/fk/<i>.json.gz`). Er enthält alle Einheiten, deren
   Berufsfeld ein Muster des Berufs trifft. Das sind 287 880 Einheiten mit mindestens einem
   Beruf der Liste. 392 460 der 446 721 Einheiten haben überhaupt Text im Berufsfeld.

**Im Browser:**
- Das Suchwort wird im Wörterbuch nachgeschlagen.
- Steht es dort nicht («horlog»), zählt die Seite die Berufe aller Wörter, die so
  beginnen. Sie nimmt jeden Beruf, der mindestens ein Viertel so oft vorkommt wie der
  häufigste.
- Dann lädt sie die Indizes dieser Berufe und vereinigt sie mit den Treffern nach Wortlaut.
- In der Namenssuche trägt jeder Treffer seine Berufe schon mit sich. Der Filter prüft:
  Wortlaut oder gleicher Beruf.

Am häufigsten erkannt werden: Privat/Rentier (20 149 Einheiten), Wirt (17 425),
Commis (14 675), Schneider (12 634), Kaufmann (11 219), Handlanger (11 098), Schreiner
(9 003), Knecht/Magd (8 258), Metzger (7 449).

## Die Berufslisten im Projekt

| Liste | Datei | Umfang | wofür |
|---|---|---|---|
| Berufsklassen | [scripts/occupations.py](../scripts/occupations.py) | 16 Klassen | Karten nach Berufen; grob, gemessen 88–92 % richtig ([karten.md](karten.md)) |
| feine Berufsliste | [scripts/occupations_fine.py](../scripts/occupations_fine.py) | 124 Berufe | Wanderungen (gleicher, verwandter oder anderer Beruf), Übersetzung in der Suche |

Die Klassen fassen zusammen: Metzger und Bäcker sind beide «Lebensmittel». Die feine
Liste trennt sie. Für die Übersetzung taugt nur die feine Liste.

## Daten

| Datei | Inhalt |
|---|---|
| `site/data/ow/<x>.json.gz` | Berufswörter (ab 4 Buchstaben, ohne Akzente) nach erstem Buchstaben: `w` Wort → Einheiten, `e` Einheit → [Name, Gemeinde, erstes Jahr, letztes Jahr, Beruf (80 Zeichen), Quelle, Berufe der feinen Liste] |
| `site/data/berufe.json` | `k`: [Schlüssel, Gruppe, de, fr, it, en] je Beruf (Index = Stelle); `v`: Wort → Berufe |
| `site/data/fk/<i>.json.gz` | je Beruf alle Einheiten damit, Zeilen wie in `ow/` |
| `site/data/names/<xx>.json.gz` | Namenssuche; an elfter Stelle die Berufe der feinen Liste |

Alle Dateien entstehen im Pages-Workflow (`build_pages.py`, `build_maps.py`) und liegen
nicht im Repo.

## Grenzen

- **Nicht gemessen.** Die Übersetzung ist maschinell: Muster, nicht Durchsicht. Die
  Berufsklassen sind gemessen, die feine Liste nur indirekt über die Wanderungen. Eine
  Stichprobe «Treffer mit Übersetzung, die den gesuchten Beruf nicht haben» fehlt noch.
- **Die Muster greifen breit.** «Café» und «Restaurant» gelten als Wirt, «Monteur» als
  Maschinist. Einzelne Treffer sind falsch, weil ein Muster mitten in einem Wort greift:
  «Alkoholdirektor» trifft «rektor» und gilt auch als Professor, «apprentissages» trifft
  «tissage» und gilt als Weber.
- **Nur Berufe der Liste.** «Seiler», «Treillageur» und viele seltene Berufe werden nur
  nach dem Wortlaut gefunden.
- **Kurze Wörter.** Die Suche nach Wortlaut kennt nur Wörter ab 4 Buchstaben; «Kfm.»
  allein findet nichts. Mit Übersetzung findet «Kaufmann» auch «Kfm.», weil das Muster es
  kennt.
- **Namenssuche:** Das Feld «Beruf» sieht nur die ersten 60 Zeichen des Berufsfelds. Die
  Übersetzung wertet dagegen das ganze Feld aus.
- **Berufsfeld ist nicht Beruf.** Es enthält auch Zusätze: Firmennamen, Hausnamen («zum
  Löwen»), Hinweise wie «Wohnung» und gelegentlich Teile von Nachbarzeilen.

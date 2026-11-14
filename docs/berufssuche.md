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
- **127 Berufe**, je mit einem Muster, das die deutschen, französischen und italienischen
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
| feine Berufsliste | [scripts/occupations_fine.py](../scripts/occupations_fine.py) | 127 Berufe | Wanderungen (gleicher, verwandter oder anderer Beruf), Übersetzung in der Suche |

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

## Messung

Beurteilt von Claude, nicht von den Projektmitarbeitenden, nach dem ganzen Berufsfeld der
Einheit ([scripts/measure_berufe.py](../scripts/measure_berufe.py)). Die Spanne zählt
«unklar» einmal als falsch und einmal als richtig.

**1. Zuordnung** (`data/review/berufe_zuordnung.csv`, Seed 20): 80 zufällige Paare aus
Einheit und Beruf, gezogen aus allen 335 041 Zuordnungen. Frage: Nennt das Berufsfeld
diesen Beruf?

| n | richtig | unklar | falsch | Präzision |
|---|---|---|---|---|
| 80 | 61 | 7 | 12 | **76–85 %** |

**2. Gewinn durch die Übersetzung** (`data/review/berufe_gewinn.csv`, Seed 21): für fünf
Suchwörter je 12 Treffer, die nur die Übersetzung findet, nicht der Wortlaut. Das sieht,
wer «Übersetzungen mitsuchen» einschaltet. Frage: Hat der Treffer den gesuchten Beruf?

| Suchwort | Treffer nach Wortlaut | nur durch Übersetzung | n | richtig | unklar | falsch | Präzision |
|---|---|---|---|---|---|---|---|
| Metzger | 4 574 | 2 940 | 12 | 8 | 1 | 3 | 67–75 % |
| Uhrmacher | 456 | 1 065 | 12 | 11 | 1 | 0 | 92–100 % |
| boulanger | 1 003 | 3 718 | 12 | 12 | 0 | 0 | 100 % |
| instituteur | 867 | 5 005 | 12 | 12 | 0 | 0 | 100 % |
| Schreiner | 6 208 | 2 879 | 12 | 4 | 1 | 7 | 33–42 % |
| **alle** | | | **60** | **47** | **3** | **10** | **78–83 %** |

Die Zahl der Treffer nach Wortlaut und nur durch Übersetzung steht in
`data/norm/berufe_gewinn_umfang.json`. Die Treffer nach Wortlaut sind nicht geprüft.

**Lesart:**

- **Wo die Übersetzung gut ist:** Gleiche Berufe in anderer Sprache werden zuverlässig
  gefunden. «boulanger» bringt 3 718 deutsche Bäcker dazu, «instituteur» 5 005 Lehrer und
  Lehrerinnen, «Uhrmacher» 1 065 «horlogers» und Uhrenfabriken. In diesen Stichproben ist
  kein Treffer falsch.
- **Wo sie schlecht ist:** dort, wo das Muster mehr als den Beruf fasst.
  - **Schreiner:** Das Muster schloss Glaser und vitriers ein. 6 der 7 Fehler waren
    Glaser, einer war «parquet du procureur» (die Staatsanwaltschaft).
  - **Metzger:** Das Muster schloss Viehhändler und «bétail» ein; die Viehinspektoren
    zählten so als Metzger.

  Beides ist seither behoben (Runde 2, unten).
- **Lehrer:** Die Liste trennt Schul- von Privatlehrern nicht. Wer «instituteur» sucht,
  findet auch Klavier-, Tanz- und Sprachlehrerinnen; beurteilt wurden sie als richtig
  (Beruf «Lehrer»).
- **Fehler der Zuordnung** (Stichprobe 1):
  - Muster mitten im Wort: «Direktor» trifft «rektor» und gilt als Professor,
    «Eilgutexpediteur» trifft «editeur» und gilt als Buchhändler, «Commissionsgeschäft» als
    Commis, «Privatabonnemente» als Rentier.
  - «arbeiter» zählt Fabrik-, Bahn- und Telephonarbeiter als Handlanger oder
    Fabrikarbeiter.
  - Ein Familienname wird als Beruf gelesen («Müller-Zürcher»).
  - Rubriken aus Nachbarzeilen («BOUCHERIES» im Feld einer Elektrofirma).

**3. Runde 2: Glaser, Viehhändler, Viehinspektor als eigene Berufe**
(`data/review/berufe_gewinn_2.csv`, Seed 22).
- **Änderung an der Liste:** Glaser (Glaser, vitrier, vetraio, Bleiglaser, Glashandlung)
  sind aus «Schreiner» herausgelöst. Vieh- und Pferdehändler und die Viehinspektoren sind
  aus «Metzger» herausgelöst. Das Muster «parquet» greift nur noch für Parqueteur,
  Parquetier und Parqueterie.
- **Folge für die Wanderungen:** Die feine Liste hat jetzt 127 Berufe. Ein Paar wechselt
  dadurch von `schwach` nach `mittel`.
- **Stichprobe:** Danach gezogen wurden je 12 neue Treffer, die nur die Übersetzung findet,
  ohne die Einheiten aus Runde 1.

| Suchwort | Treffer nach Wortlaut | nur durch Übersetzung | n | richtig | unklar | falsch | Präzision |
|---|---|---|---|---|---|---|---|
| Metzger | 4 574 | 2 067 | 12 | 12 | 0 | 0 | 100 % |
| Schreiner | 6 208 | 2 093 | 12 | 11 | 1 | 0 | 92–100 % |
| Glaser (neu) | 754 | 299 | 12 | 8 | 4 | 0 | 67–100 % |
| Viehhändler (neu) | 445 | 229 | 12 | 12 | 0 | 0 | 100 % |
| **alle** | | | **48** | **43** | **5** | **0** | **90–100 %** |

**Lesart:**
- **Metzger und Schreiner:** Die neuen Stichproben enthalten keinen falschen Treffer mehr.
  «Metzger» findet jetzt 2 067 statt 2 940 Einheiten nur durch die Übersetzung,
  «Schreiner» 2 093 statt 2 879; weggefallen sind Glaser, Viehhändler und Viehinspektoren.
- **Prüfung an Runde 1** (keine Messung): Nach den neuen Regeln fielen alle 10 Fehler bei
  «Metzger» und «Schreiner» aus der Trefferliste. Übrig bleiben bei «Metzger» 8 richtige
  und 1 unklarer Treffer, bei «Schreiner» 4 richtige und 1 unklarer.
- **Glaser:** Die 4 unklaren Treffer sind Glashandlungen («Porzellan- und Glashandlung»).
  Das Muster «glashandl» zählt Glashändler zu den Glasern, wie «Schuhhandlung» zu den
  Schuhmachern zählt.
- **Viehhändler:** Die Übersetzung bringt vor allem Pferdehändler dazu. Die Liste fasst Vieh-
  und Pferdehändler zusammen; beurteilt wurde nach diesem Beruf.
- **Stichprobe 1 (Zuordnung)** ändert sich nicht: Ihre 12 Fehler betrafen andere Muster
  («rektor», «editeur», «arbeiter», Familiennamen, Rubriken). Diese sind noch offen.

## Grenzen

- **Maschinell.** Die Übersetzung folgt Mustern, nicht einer Durchsicht. Gemessen sind
  76–85 % richtige Zuordnungen. In Runde 1 waren 78–83 % der zusätzlichen Treffer richtig,
  in Runde 2, nach der Trennung von Glaser und Viehhändler, 90–100 %.
- **Die Muster greifen breit.** «Café» und «Restaurant» gelten als Wirt, «Monteur» als
  Maschinist, Glashändler als Glaser, Pferde- als Viehhändler. Andere Treffer sind falsch,
  weil ein Muster mitten in einem Wort greift: «Direktor» trifft «rektor» und gilt auch als
  Professor, «apprentissages» trifft «tissage» und gilt als Weber.
- **Nur Berufe der Liste.** «Seiler», «Treillageur» und viele seltene Berufe werden nur
  nach dem Wortlaut gefunden.
- **Kurze Wörter.** Die Suche nach Wortlaut kennt nur Wörter ab 4 Buchstaben; «Kfm.»
  allein findet nichts. Mit Übersetzung findet «Kaufmann» auch «Kfm.», weil das Muster es
  kennt.
- **Namenssuche:** Das Feld «Beruf» sieht nur die ersten 60 Zeichen des Berufsfelds. Die
  Übersetzung wertet dagegen das ganze Feld aus.
- **Berufsfeld ist nicht Beruf.** Es enthält auch Zusätze: Firmennamen, Hausnamen («zum
  Löwen»), Hinweise wie «Wohnung» und gelegentlich Teile von Nachbarzeilen.

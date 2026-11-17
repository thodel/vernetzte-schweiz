# Verknüpfung Telefonbuch ↔ Adressbuch (M2)

`scripts/link_ptt_ab.py` verbindet die Telefonbuch-Einträge einer Stadt mit den
Einträgen derselben Person oder Firma in jedem Adressbuch-Band dieser Stadt.
`scripts/measure_links.py` misst das Ergebnis. Beides läuft mit `make link`.

## Was verglichen wird

- **Telefonbuch:** Einträge der Gemeinde 1914, deren Ort `hoch` oder `mittel` aufgelöst ist
  (M1), Art `person` oder `firma`. Ämter und Zusatzzeilen bleiben aussen vor.
- **Adressbuch:** alle Einträge aller Bände der Stadt: Einwohner-, Berufs- und
  Gebäudeverzeichnis, in Basel auch die Amtsträger.

Jeder Telefonbuch-Eintrag wird mit jedem Band verglichen. Eine Verknüpfung heisst also:
*dieser Abonnent ist in diesem Band diese Person*. Bündeln über die Jahre folgt in M3.

## Blocken

Kandidaten sind die Einträge des Bandes mit demselben **Familiennamen**. Der Schlüssel
ist ohne Akzente und mit eingeebneten Schreibvarianten gebildet: ss/ß, ck/k, th/t, y/i,
Doppelkonsonanten, ä/ae. Firmen werden unter ihrem Leitnamen gesucht («von Speyr & Co.»
→ speyr, «Jenny & Weigel» → jenny).

Der Allianzname («Maggi-*Strehler*») ist der Name des Ehepartners und gehört zu einer
anderen Familie. Er dient deshalb nie zum Blocken, nur als Beleg.

## Belege und Widersprüche

| Merkmal | Punkte | Widerspruch (keine Verknüpfung) |
|---|---|---|
| Vorname ausgeschrieben gleich (auch Sprachformen: Charles = Carl, Jules = Julius) | 4 | zwei ausgeschriebene Vornamen verschieden |
| Abkürzung passt (Friedr. → Friedrich; Zusammenziehung Hch., Gg., Chs. in Folge) | 3 | Abkürzung passt zu keinem Vornamen (Ad. ≠ Andr., Alf. ≠ Adolf) |
| nur Initiale passt | 2 | Initialen verschieden |
| Allianzname gleich | 3 | beide haben einen, verschieden («andere Ehe») |
| Strasse gleich | 3 | – |
| Hausnummer gleich (im selben Nummernsystem) | +3 | andere Nummer: −1 |
| Aarau: stadtweite Gebäudenummer gleich (im selben System) | 6 | – |
| Aarau: gleiches Gebäude über die Umnummerierung 1900 (alte Nr. → neue Nr.), gleiche Strasse | 6 | – |
| Aarau: dasselbe über die Umnummerierung, andere Strasse | 2 | – |
| Aarau: gleiche Strasse, über die Umnummerierung ein anderes Haus | – | −1 |
| Beruf (gemeinsamer Wortstamm) | 1 | – |
| Telefonzeichen im Adressbuch | 1 | – |
| Firma gegen Firma | 2 | – |
| Telefonbuch als Person gelesen, aber «& Co.», «& Cie.», «Gebr.», «Söhne», «Frères» (nicht hinter «vorm.», «Vertr.», «i. Fa.»): gegen eine Firma | 1 | – |
| Witwe im Telefonbuch | – | Eintrag im Adressbuch ist keine Witwe (also ihr Mann) |

**Umnummerierung Aarau 1900.** Aarau hat 1900 die Gebäude neu durchnummeriert, wieder stadtweit (neue Nummern
bis gegen 1500). Die Telefonbücher tragen ab 1900 die neue Nummer, die Adressbücher bis 1899 die alte. Über die
Grenze zählt eine Nummer nur über die Konkordanz aus dem «Verzeichnis der neuen Hausnumerierung der Stadt Aarau»
(adressbuecher-aarau, `05_hausnumerierung_1900.csv`, 1 459 alte Nummern; `renumbering` in `config/sources.toml`);
gleiche Ziffern in beiden Systemen meinen verschiedene Häuser. Gemessen an sicheren Paaren Telefonbuch 1900–1910 ↔
Adressbuch 1899: gleiche Ziffern 2–8 je Jahrgang, gleiches Haus über die Konkordanz 177–266 (16.11.2026). Wirkung
auf die Telefonbücher ab 1900: `sicher` 2 824 → 3 449, `wahrscheinlich` 1 505 → 2 418, `möglich` 2 660 → 1 638,
verknüpfte Einträge 928 → 960; vor 1900 unverändert. Über die Konkordanz bei anderer Strasse nur 2 Punkte: ein
Lesefehler in der Konkordanz trug sonst «Frey, R. & M.» zur Baumwollspinnerei «Frey & Cie.» in der Telli.
Wie innerhalb eines Systems kostet eine andere Hausnummer an derselben Strasse einen Punkt, wenn die Konkordanz
zeigt, dass es ein anderes Haus ist (sonst lag «Frey, Fr., Weinhandlung» 1910 mit einem vornamenlosen Frey derselben
Strasse gleichauf). «Oehler, A., & Co.» ist im Telefonbuch als Person gelesen; der Firmenpunkt bringt ihn zur Firma
«Oehler A. & Cie.», Gais 1405 = Industriestrasse 932, statt gleichauf mit dem Inhaber Alfred Oehler (17.11.2026).
Liegen ein solcher Eintrag und mehrere Personen gleichauf und bilden die Firmen darunter eine einzige, gilt die
Firma: Inhaber und eigene Firma («Lippmann, Rob. & Co.» ↔ Robert Lippmann und Lippmann & Cie.) lagen sonst
gleichauf und der Eintrag blieb mehrdeutig. Stichprobe aller 57 Einträge, die der Firmenpunkt allein verlor: 41 kommen
so zurück, meist an die Firma; von den übrigen 16 waren 9 falsch (Holliger, Tapezierer ≠ Schriftsetzer), 5 unklar,
2 richtig (Märki). Hinter «vorm.», «Vertr.» oder «i. Fa.» steht eine andere Firma oder der Inhaber selbst
(«Peschel, Ludw., i. Fa. Ludw. Peschel & Co., Wohnung»); dort zählt «& Co.» nicht.

Ein späterer Vorname kann der Rufname sein: Es genügt ein passendes Paar
(«E.» ↔ «Hermann Emil»).

Als Vornamen gelten nur Wörter der Vornamenliste (`data/ref/forenames.csv`) und
Abkürzungen. Ein Beruf im Vornamenfeld («Julius. Weinhandlung») wird so kein «W.».

## Eine Person, nicht ein Eintrag

Dieselbe Person steht in einem Band oft mehrfach: im Einwohner-, im Berufs- und im
Gebäudeverzeichnis, mal mit, mal ohne Allianzname. Einträge gelten als dieselbe Person,
wenn
- die Vornamen sich nicht widersprechen,
- der Allianzname gleich ist oder fehlt,
- die Hausnummer gleich ist oder fehlt,
- und mindestens Vorname oder Hausnummer auf beiden Seiten steht.

Verknüpft wird nur, wenn **genau eine Person** die höchste Punktzahl hat. Dann werden
alle ihre Einträge im Band verknüpft (Beleg `zusatz`), seit dem 13.11.2026 aber nur jene mit
gleicher Strasse, gleicher Hausnummer oder gleichem ausgeschriebenem Vornamen wie der beste
Eintrag: in Bern teilen viele «J. Gerber» Initiale und Namen. Die gleiche Hausnummer zählt nur,
wenn die Strasse nicht eine andere ist (Zürich: «Meier & Hendess, Sihlstrasse 6» ist nicht «Meier,
Ulrich, Röslistrasse 6»); als dieselbe Strasse gelten auch ein Lesefehler mit gleichem Anfang
(«Neuong» für «Neuengasse») und eine Strasse mit vorangestelltem Quartier («Längg.,
Gesellschaftsstrasse»). Passen zwei Personen gleich gut
(Vater und Sohn am selben Haus), entsteht keine Verknüpfung (`mehrdeutig`).

## Stufen

| Stufe | Belege |
|---|---|
| `sicher` | Vorname (auch nur Initiale) **und** Adresse; Firma und Adresse; ausgeschriebener Vorname und Allianzname |
| `wahrscheinlich` | ausgeschriebener Vorname; Initiale und Beruf oder Allianzname; Initiale und Telefonzeichen, wenn höchstens 5 Personen des Namens im Band stehen; Hausnummer; Firma, deren Name im Band nur einmal vorkommt |
| `möglich` | Strasse; Allianzname; Name im Band nur einmal vorhanden (mit Initiale, oder ohne bei höchstens 10 Jahren Abstand); Firma gegen ihren Inhaber am selben Haus |

**Jahresabstand.** Söhne und Nachfolger tragen Namen, Haus und Geschäft weiter. Deshalb
gelten zwei Grenzen:
- **Über 15 Jahre:** keine Stufe `sicher`. Für `wahrscheinlich` braucht es einen
  ausgeschriebenen Vornamen mit Adresse, Allianzname oder Beruf, oder eine Initiale mit
  gleicher Hausnummer. Eine Adresse ohne Vornamen genügt nicht mehr.
- **Über 30 Jahre:** nur noch gleiche Adresse mit passendem Vornamen, als `möglich`.

**Grossstadt (Bern, M5).** Abgekürzte Gassen und Plätze («Kramg.», «Bärenpl.») zählen als
Strasse. Allgemeine Firmenwörter als Leitname («Schweizerische», «Café», «Bureau»,
«Gesellschaft», Liste `GENERIC_FIRM`) verknüpfen nur bei gleicher Strasse. Gemessen in
`data/review/m5_bern_lausanne.csv`, Stichprobe 2: `sicher` 10/10, `wahrscheinlich` 7/10
(2 unklar), `möglich` 7/10, `zusatz` 8/10.

**Zürich (M5).** `data/review/m5_zuerich.csv`, Band 1914: `sicher` 10/10, `wahrscheinlich`
10/10, `möglich` 7/10. Vor der Regel zur Hausnummer an anderer Strasse waren 3 von 14
`sicher` falsch, alle mit Beleg `zusatz`; danach 14/16.

Basel hat bisher nur den Band 1862, die Telefonbücher beginnen 1881. Basel hat deshalb
keine Stufe `sicher`.

## Messung

**Präzision.** Die Paare in `data/review/m2_stichprobe.csv` sind von Hand beurteilt
(Sichtprüfung durch Claude am gedruckten Text beider Einträge, Urteil `richtig` /
`falsch` / `unklar`, mit Begründung).
- **Stichprobe 1** (200 Paare, 40 je Stadt und Stufe) diente zum Einstellen der Regeln.
  Ihre Zahlen sind deshalb geschönt und werden nicht als Messung ausgewiesen.
- **Stichprobe 2** (100 Paare, 20 je Stadt und Stufe) wurde nach dem Festlegen der Regeln
  aus Telefonbuch-Einträgen gezogen, die in Stichprobe 1 nicht vorkamen. Ihre Fehler
  Nr. 273 (Doppelname als Firma gelesen) und Nr. 295 (Alf. ≠ Adolf) wurden danach noch
  behoben. Gezählt wird die Stufe zum Zeitpunkt der Ziehung.

| Stadt | Stufe | n | richtig | falsch | unklar | Präzision |
|---|---|---|---|---|---|---|
| Aarau | sicher | 20 | 19 | 0 | 1 | 95–100 % |
| Aarau | wahrscheinlich | 20 | 18 | 0 | 2 | 90–100 % |
| Aarau | möglich | 20 | 18 | 0 | 2 | 90–100 % |
| Basel | wahrscheinlich | 20 | 17 | 1 | 2 | 85–95 % |
| Basel | möglich | 20 | 16 | 1 | 3 | 80–95 % |

Nach der Ziehung kam eine Regel hinzu: Über 30 Jahre ist eine Verknüpfung höchstens
`möglich`. Damit fiel ein Teil der Basler Paare der Stufe `wahrscheinlich` nach `möglich`
(Entscheide 1 774 → 1 194).

Die Spanne zählt `unklar` einmal als falsch und einmal als richtig. Bei 20 Paaren je
Stufe ist die Unsicherheit gross: Ein Fehler mehr oder weniger verschiebt die Zahl um
5 Punkte. «Unklar» heisst meist: Vater oder Sohn, Firma oder Inhaber, Witwe oder Mann.

**Vollständigkeit (Aarau).** Die Bände 1896 und 1899 setzen ein Telefonzeichen vor die
Adresse der Abonnenten. Gemessen wird, wie viele dieser Einträge mit einem Telefonbuch
von höchstens zwei Jahren Abstand verknüpft sind:

| Band | mit Telefonzeichen | Familienname im Telefonbuch ± 2 Jahre | verknüpft |
|---|---|---|---|
| 1896 | 142 | 107 | 93 (87 % der erreichbaren) |
| 1899 | 209 | 183 | 156 (85 % der erreichbaren) |

Was fehlt, sind vor allem:
- Einträge ohne lesbaren Familiennamen («Wirt, [tel] Schachen 727»);
- Firmen, die im Telefonbuch unter einem anderen Namen stehen;
- Vater und Sohn am selben Haus.

**Vergleich mit den Städten.**
- **Basel:** `20_phonebook_links.csv` verknüpft vor allem über die Adresse (gleiches Haus)
  und über Familienname mit Strasse, ohne Vornamen und über bis zu 52 Jahre. Solche Paare
  verbindet der Verknüpfer hier bewusst nicht («Burckhardt, Dr. August» 1914 ↔
  «Burckhardt, Albert, Kaufm.» 1862). Die Übereinstimmung ist deshalb gering und kein Mass
  für die Güte.
- **Aarau:** `09_links_ptt.csv` gilt zu 95 % den Telefonbüchern ab 1921 und zu einer
  älteren Lesung der Charge A. Ein Vergleich ist nicht möglich.

## Ergebnis

`links/ptt_ab.csv`: ein Paar je Zeile. Felder siehe [Datenvertrag](datenvertrag.md).
Kennzahlen je Stadt in `data/norm/link_stats.json`, Messung in
`data/norm/link_quality.json`.

"""BERNHIST als Referenz (scripts/ref_bernhist.py) und Durchdringung des Telefons im Kanton Bern (scripts/durchdringung_bern.py).

Die Tests brauchen den BERNHIST-Dump nicht: Sie prüfen die Regeln an kleinen Beispielen und die abgelegten
Referenzdateien unter data/ref/bernhist/ auf Schlüssigkeit.
"""
import sys
import unittest
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import durchdringung_bern as d  # noqa: E402
import ref_bernhist as r  # noqa: E402
from common import ROOT, open_csv  # noqa: E402

REF = ROOT / "data" / "ref" / "bernhist"


def eintrag(name1="", name2="", supplement="", occupation=None, title="", entity_type="person", surname=None,
            forename="", initials="", **mehr) -> dict:
    x = {"name1": name1, "name2": name2, "supplement": supplement, "title": title, "entity_type": entity_type,
         "occupation": supplement if occupation is None else occupation,
         "surname": name1 if surname is None else surname, "forename": forename, "initials": initials}
    x.update(mehr)
    return x


class Ortsnamen(unittest.TestCase):
    def test_zusaetze_und_artikel(self):
        self.assertEqual(r.ort_schluessel("Bümpliz (bis 1919)"), "bumpliz")
        self.assertEqual(r.ort_schluessel("Bargen (BE)"), r.ort_schluessel("Bargen"))
        self.assertEqual(r.ort_schluessel("Ferrière, La"), r.ort_schluessel("La Ferrière"))
        self.assertEqual(r.ort_schluessel("Lütschenthal"), r.ort_schluessel("Lütschental"))
        self.assertEqual(r.ort_schluessel("Biel / Bienne (BE) (ab 1920 mit Bözingen, Mett, Madretsch)"), "biel bienne")

    def test_doppelnamen(self):
        self.assertIn("interlaken", r.ort_varianten("Interlaken / Aarmühle"))
        self.assertIn("dicki", r.ort_varianten("Kriechenwil / Dicki"))
        self.assertEqual(r.ort_varianten("Thun"), ["tun"])          # th = t, auf beiden Seiten


class Zuordnung(unittest.TestCase):
    GEM = [{"hist_code": "1", "name": "Thun", "district": "Amtsbezirk Thun"},
           {"hist_code": "2", "name": "Strättligen", "district": "Amtsbezirk Thun"},
           {"hist_code": "3", "name": "Rüdtligen", "district": "Amtsbezirk Burgdorf"},
           {"hist_code": "4", "name": "Porrentruy", "district": "District de Porrentruy"},
           {"hist_code": "5", "name": "Kandersteg", "district": "Amtsbezirk Frutigen"}]
    ORTE = [{"bernhist_id": 10, "bernhist_name": "Thun"}, {"bernhist_id": 11, "bernhist_name": "Strättligen (bis 1920)"},
            {"bernhist_id": 12, "bernhist_name": "Rüdtligen-Alchenflüh"}, {"bernhist_id": 13, "bernhist_name": "Riedtwil (bis 1851)"},
            {"bernhist_id": 14, "bernhist_name": "Kandersteg (ab 1909)"}]
    HAND = [{"bernhist_name": "Rüdtligen-Alchenflüh", "art": "name", "ziel": "Rüdtligen", "grund": "Name von 1914"},
            {"bernhist_name": "Strättligen (bis 1920)", "art": "einheit", "ziel": "Thun", "grund": "bei Thun"}]

    def test_methoden_und_einheiten(self):
        orte, gem = r.zuordnen(self.ORTE, self.GEM, self.HAND, hat_bev={10, 12})
        o = {x["bernhist_name"]: x for x in orte}
        self.assertEqual((o["Thun"]["methode"], o["Thun"]["einheit_id"]), ("exakt", 10))
        self.assertEqual((o["Strättligen (bis 1920)"]["methode"], o["Strättligen (bis 1920)"]["einheit_id"]), ("normalisiert", 10))
        self.assertEqual((o["Rüdtligen-Alchenflüh"]["methode"], o["Rüdtligen-Alchenflüh"]["hist_code"]), ("hand", "3"))
        self.assertEqual((o["Riedtwil (bis 1851)"]["hist_code"], o["Riedtwil (bis 1851)"]["einheit_id"]), ("", ""))
        g = {x["name"]: x["status"] for x in gem}
        self.assertEqual(g["Thun"], "zugeordnet")
        self.assertEqual(g["Strättligen"], "Teil einer Einheit")
        self.assertEqual(g["Kandersteg"], "ohne Bevölkerung in BERNHIST")
        self.assertTrue(g["Porrentruy"].startswith("nicht in BERNHIST"))

    def test_unbekannter_name_in_der_handtabelle_bricht_ab(self):
        with self.assertRaises(SystemExit):
            r.zuordnen(self.ORTE, self.GEM, [{"bernhist_name": "Gibtesnicht", "art": "name", "ziel": "Thun", "grund": ""}], {10})


class Sektoren(unittest.TestCase):
    def test_reihe_a_mit_rest(self):
        w = {("erw_1910", 1): [100.0, 100.0], ("erw_s1_1910", 1): [50.0, 50.0], ("erw_s2_1910", 1): [30.0, 30.0], ("erw_s3_1910", 1): [20.0]}
        s = r.sektoren(1, [], w)
        self.assertEqual((s["erw"], s["s1"], s["s2"], s["s3"], s["pruefung"]), (100, 50, 30, 20, ""))

    def test_reihe_b_im_spaeteren_gebiet_zaehlt_nicht(self):
        # Bern: Reihe B rechnet Bümpliz dazu; verwendet wird die Reihe im Gebiet der Bevölkerung
        w = {("erw_1910", 1): [35250.0, 37247.0], ("erw_s1_1910", 1): [676.0, 1055.0], ("erw_s2_1910", 1): [17277.0, 18384.0],
             ("erw_s3_1910", 1): [17808.0]}
        s = r.sektoren(1, [], w)
        self.assertEqual((s["erw"], s["s3"]), (35250, 17297))
        self.assertIn("anderes Gebiet", s["pruefung"])

    def test_teile_ohne_eigene_bevoelkerung_kommen_dazu(self):
        # Thun: Reihe A ohne Strättligen, Bevölkerung mit; Reihe B bestätigt die Summe
        w = {("erw_1910", 1): [300.0, 400.0], ("erw_s1_1910", 1): [10.0, 40.0], ("erw_s2_1910", 1): [150.0, 200.0], ("erw_s3_1910", 1): [160.0],
             ("erw_1910", 2): [100.0], ("erw_s1_1910", 2): [30.0], ("erw_s2_1910", 2): [50.0]}
        s = r.sektoren(1, [2], w)
        self.assertEqual((s["erw"], s["s1"], s["s2"], s["s3"]), (400, 40, 200, 160))
        self.assertEqual(s["pruefung"], "")

    def test_lueckenhafte_reihe_a_weicht_auf_b_aus(self):
        # Kirchlindach: Reihe A ohne 1. Sektor
        w = {("erw_1910", 1): [375.0, 470.0], ("erw_s1_1910", 1): [0.0, 291.0], ("erw_s2_1910", 1): [125.0, 125.0], ("erw_s3_1910", 1): [54.0]}
        s = r.sektoren(1, [], w)
        self.assertEqual((s["erw"], s["s1"], s["quelle"]), (470, 291, "Reihe B (Reihe A lückenhaft)"))

    def test_spaetere_gemeinde_mit_einer_reihe(self):
        # Tramelan: ein Wert, Summe der beiden Gemeinden von 1910
        w = {("erw_1910", 1): [2432.0], ("erw_s1_1910", 1): [221.0], ("erw_s2_1910", 1): [1929.0], ("erw_s3_1910", 1): [259.0],
             ("erw_1910", 2): [734.0], ("erw_1910", 3): [1698.0]}
        s = r.sektoren(1, [2, 3], w)
        self.assertEqual((s["erw"], s["s3"]), (2432, 282))
        self.assertIn("259", s["pruefung"])


class Referenzdateien(unittest.TestCase):
    """Was im Repo liegt, muss ohne Dump schlüssig sein."""

    @classmethod
    def setUpClass(cls):
        cls.orte = open_csv(REF / "orte.csv")
        cls.gem = open_csv(REF / "gemeinden_1914.csv")
        cls.einh = open_csv(REF / "einheiten.csv")
        cls.werte = open_csv(REF / "werte.csv")
        cls.vergleich = open_csv(REF / "vergleich_bfs.csv")

    def test_jede_gemeinde_hoechstens_einmal_gebunden(self):
        codes = [o["hist_code"] for o in self.orte if o["hist_code"]]
        self.assertEqual(len(codes), len(set(codes)))
        be = {g["hist_code"] for g in open_csv(ROOT / "data" / "ref" / "municipalities_1914.csv") if g["canton"] == "BE"}
        self.assertTrue(set(codes) <= be)
        self.assertEqual(len(self.gem), len(be))

    def test_nicht_zugeordnetes_ist_ausgewiesen(self):
        for o in self.orte:
            if not o["hist_code"]:
                self.assertTrue(o["bemerkung"] or o["einheit_id"], o["bernhist_name"])
        status = Counter(g["status"].split(" (")[0] for g in self.gem)
        self.assertGreater(status["zugeordnet"], 400)
        self.assertEqual(status["nicht in BERNHIST"], sum(1 for g in self.gem if not g["bernhist_id"]))

    def test_stadt_bern(self):
        bern = next(e for e in self.einh if e["einheit_id"] == "457")
        self.assertEqual(bern["gemeinden_1914"], "Bern")
        self.assertEqual([bern[f"bev_{y}"] for y in (1880, 1888, 1900, 1910)], ["43197", "46009", "64227", "85651"])
        self.assertEqual((bern["haushalte_1888"], bern["erw_1910"]), ("9931", "35250"))

    def test_sektoren_ergeben_die_summe(self):
        for e in self.einh:
            if e["s1_1910"] != "":
                self.assertEqual(int(e["s1_1910"]) + int(e["s2_1910"]) + int(e["s3_1910"]), int(e["erw_1910"]), e["name"])
                self.assertGreaterEqual(int(e["s3_1910"]), 0, e["name"])

    def test_abgleich_mit_bfs(self):
        vergleichbar = [v for v in self.vergleich if v["bfs_1910"]]
        self.assertGreater(len(vergleichbar), 400)
        ueber = sorted(v["name_bfs"] for v in vergleichbar if v["ueber_schwelle"])
        self.assertEqual(ueber, ["Frutigen", "Kirchdorf (BE)"])
        self.assertGreater(sum(1 for v in vergleichbar if v["identisch"]), 0.98 * len(vergleichbar))

    def test_nur_verwendete_reihen_liegen_im_repo(self):
        erlaubt = set(r.GEMEINDE_REIHEN) | set(r.STADT_REIHEN)
        self.assertTrue({w["reihe"] for w in self.werte} <= erlaubt)
        self.assertLess(len(self.werte), 6000)          # der Dump hat 1 958 047 Werte
        nur_stadt = [w for w in self.werte if w["reihe"] in set(r.STADT_REIHEN) - set(r.GEMEINDE_REIHEN)]
        self.assertEqual({w["bernhist_id"] for w in nur_stadt}, {"457"})


class Berufsangaben(unittest.TestCase):
    def test_wie_im_adressbuch(self):
        for beruf, s in (("Schneidermeister", "2"), ("Milch-, Anken- u. Käsehändler", "3"), ("Privatier", "ohne"),
                         ("Landwirt", "1"), ("Fürsprecher", "3"), ("Bäckermeister", "2"), ("Taglöhner", "unbestimmt"),
                         ("Lehrer, Feuerwehr-Hauptmann", "3"), ("", "")):
            self.assertEqual(d.sektor(beruf), s, beruf)
        self.assertEqual(d.sektor("des Schusters Wwe.", witwe=True), "ohne")
        self.assertEqual(d.sektor("", "Dr. med."), "3")

    def test_ergaenzungen_fuer_das_telefonbuch(self):
        for beruf, s in (("Wohnung", ""), ("(Wohnung)", ""), ("Frau Wwe", ""), ("Velo- und Nähmaschinenhandlung", "3"),
                         ("Direktor der Möbelfabrik A. Pfluger & Co", "2"), ("Direktor der Schweiz. Volksbank", "3"),
                         ("Graphische Anstalt", "2"), ("Charcuterie", "2"), ("Buchdruckerei", "2"), ("Comestibles", "3"),
                         ("Hôtels", "3"), ("Doctoren", "3")):
            self.assertEqual(d.sektor(beruf, telefon=True), s, beruf)
        self.assertEqual(d.sektor("Wohnung"), "unbestimmt")       # ohne die Ergänzung bleibt die Regel des Adressbuchs

    def test_frauen(self):
        self.assertEqual(d.frau("Wwe.", ""), "witwe")
        self.assertEqual(d.frau("Frl.", "Helene"), "fraeulein")
        self.assertEqual(d.frau("Frau", ""), "frau")
        self.assertEqual(d.frau("", "Rosa", "Hebamme"), "weiblich")
        self.assertEqual(d.frau("Fr.", "", "Bäckermeister"), "")   # «Fr.» ist Fritz

    def test_gruppen(self):
        self.assertTrue(d.gruppe("aerzte", "Arzt"))
        self.assertFalse(d.gruppe("aerzte", "Zahnarzt"))
        self.assertTrue(d.gruppe("aerzte_med", "", "Prof. Dr. med."))
        self.assertFalse(d.gruppe("aerzte_med", "", "Dr. med. vet."))
        self.assertTrue(d.gruppe("spezerei", "Spezerei-Handlungen"))
        self.assertTrue(d.gruppe("gastgewerbe", "Café Ratskeller"))
        self.assertTrue(d.gruppe("nahrung", "Schweinemetzgerei"))
        self.assertTrue(d.gruppe("druck", "Lithographie und Buchdruckerei"))


class Eintraege(unittest.TestCase):
    def test_art(self):
        self.assertEqual(d.art(eintrag("Gygax", supplement="Fürsprecher")), "person")
        self.assertEqual(d.art(eintrag("Oberfeldarzt", supplement="eidg.")), "amt")
        self.assertEqual(d.art(eintrag("Waldau", supplement="Irrenanstalt")), "amt")
        self.assertEqual(d.art(eintrag("Civilstandsamt Bern", entity_type="firma")), "amt")
        self.assertEqual(d.art(eintrag("Waffenchef der Kavallerie", entity_type="firma")), "amt")
        self.assertEqual(d.art(eintrag("Weibel", "Gebr.", "Spezereihandlung", initials="G")), "firma")
        self.assertEqual(d.art(eintrag("Demme", supplement="Gebrüder")), "firma")
        self.assertEqual(d.art(eintrag("Schweizerhof", supplement="Hôtel")), "firma")
        self.assertEqual(d.art(eintrag("Derselbe", supplement="Wohnung", entity_type="zusatz")), "zusatz")
        self.assertEqual(d.art(eintrag("Richter", "A.", "Notar", initials="A")), "person")   # Familienname, kein Amt

    def test_angabe_bei_firmen(self):
        f = lambda *a, **k: d.lies_eintrag(eintrag(*a, entity_type="firma", **k))  # noqa: E731
        self.assertEqual(f("Benteli, A., & Co.", occupation="A, & Co, Buchdruckerei")["sektor"], "2")
        self.assertEqual(f("Café Ratskeller", occupation="Aug, Bohnenblust")["sektor"], "3")
        self.assertEqual(f("Hirter & Werthmüller", occupation="")["sektor"], "")             # kein Müller
        self.assertEqual(f("Kasino, Café", occupation="Reitinger, Th, Maschinist")["sektor"], "3")
        self.assertEqual(f("Schweizer Bauer", occupation="Administration")["sektor"], "3")

    def test_angabe_bei_personen(self):
        e = d.lies_eintrag(eintrag("Scheidegger-Moser", "M.", "Frau Wwe., Droguerie", occupation="Frau Wwe, Droguerie", initials="M"))
        self.assertEqual((e["frau"], e["sektor"]), ("witwe", "3"))
        e = d.lies_eintrag(eintrag("Böhme-Sterchi", occupation="vorm. Hausmann & Co, Fabrik"))
        self.assertEqual(e["sektor"], "2")
        e = d.lies_eintrag(eintrag("Ledermann", "E.", "Dr., Zahnarzt", occupation="Zahnarzt", title="Dr.", initials="E"))
        self.assertEqual((e["sektor"], e["gruppen"]), ("3", []))
        e = d.lies_eintrag(eintrag("Sahli", "H.", "Prof. Dr. med.", occupation="Prof. Dr. med", initials="H"))
        self.assertEqual(e["sektor"], "3")

    def test_eine_person_zaehlt_einmal(self):
        a = eintrag("Wetli", "J.", "Tapezierer", initials="J")
        b = eintrag("Wetli", "J.", "Möbelfabrikant u. Tapezierer", initials="J")
        c = eintrag("Wetli", "Emil", "Wohnung", forename="Emil")
        self.assertEqual(d.inhaber(a), d.inhaber(b))
        self.assertNotEqual(d.inhaber(a), d.inhaber(c))

    def test_stadt_zaehlen(self):
        basis = {"municipality_1914": "Bern", "year": "1885", "refcode": d.BAND[1885], "place_confidence": "hoch", "phone_norm": ""}
        P = [eintrag("Wetli", "J.", "Tapezierer", initials="J", **basis),
             eintrag("Wetli", "J.", "Wohnung", initials="J", **basis),
             eintrag("Sommer", "Joh.", "Spezerei-Handlungen", initials="J", **basis),
             eintrag("Spar- und Leihkasse", supplement="Bank-Geschäfte", entity_type="firma", **basis),
             eintrag("Generalstabs-Bureau", entity_type="amt", **basis),
             eintrag("Wetli", "J.", "Tapezierer", initials="J", **{**basis, "refcode": "anderer Band"}),
             eintrag("Wetli", "J.", "Tapezierer", initials="J", **{**basis, "municipality_1914": "Biel (BE)"})]
        z = d.stadt_zaehlen(P, 1885)
        self.assertEqual((z["eintraege"], z["person"], z["firma"], z["amt"]), (5, 2, 1, 1))
        self.assertEqual((z["sektor_2"], z["sektor_3"], z["spezerei"], z["person_wohnung"]), (1, 2, 1, 1))


class Nenner(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.w = d.stadt_werte()

    def test_bevoelkerung_und_haushalte(self):
        n = d.nenner(self.w, 1885)
        self.assertAlmostEqual(n["bevoelkerung"][0], 43197 + (46009 - 43197) * 5 / 8)
        self.assertEqual(n["bevoelkerung"][1], "interpoliert")
        n = d.nenner(self.w, 1910)
        self.assertEqual(n["bevoelkerung"][:2], (85651.0, "direkt"))
        self.assertAlmostEqual(n["haushalte"][0], 85651 * 9931 / 46009)

    def test_1910_ist_direkt_und_ohne_buempliz(self):
        n = d.nenner(self.w, 1910)
        self.assertEqual((n["erwerbstaetige"][0], n["erwerbstaetige"][1]), (35250.0, "direkt"))
        self.assertEqual([round(n[f"sektor{s}"][0]) for s in "123"], [676, 17277, 17297])
        self.assertEqual(n["aerzte"][0], 116.0)
        self.assertEqual(n["gastgewerbe"][0], 2441.0)

    def test_1900_ist_geschaetzt(self):
        n = d.nenner(self.w, 1900)
        self.assertEqual(n["sektor3"][1], "geschätzt")
        self.assertAlmostEqual(sum(n[f"sektor{s}"][0] for s in "123"), n["erwerbstaetige"][0])
        self.assertNotIn("gastgewerbe", n)

    def test_ausserhalb_wird_nicht_extrapoliert(self):
        with self.assertRaises(ValueError):
            d.interpoliere(1880, 1.0, 1888, 2.0, 1890)


class Gemeinden(unittest.TestCase):
    def test_gruppen_und_klassen(self):
        self.assertEqual(d.sektorgruppe(70, 20, 10), d.SEKTORGRUPPEN[0])
        self.assertEqual(d.sektorgruppe(45, 40, 15), "gemischt")
        self.assertEqual(d.sektorgruppe(20, 65, 15), d.SEKTORGRUPPEN[2])
        self.assertEqual(d.sektorgruppe(10, 50, 40), d.SEKTORGRUPPEN[3])
        self.assertEqual((d.groessenklasse(499), d.groessenklasse(500), d.groessenklasse(85651)), ("0–499", "500–999", "ab 5000"))

    def test_rangkorrelation(self):
        self.assertEqual(d.rang_korrelation([1, 2, 3, 4], [10, 20, 30, 40]), 1.0)
        self.assertEqual(d.rang_korrelation([1, 2, 3, 4], [4, 3, 2, 1]), -1.0)

    def test_kreuztabelle(self):
        def zeile(name, bev, n, s, aus=""):
            return {"name": name, "bev_1910": bev, "eintraege": n, "je_100_einwohner": round(100 * n / bev, 2),
                    "s1_prozent": s[0], "s2_prozent": s[1], "s3_prozent": s[2], "groessenklasse": d.groessenklasse(bev),
                    "sektorgruppe": d.sektorgruppe(*s), "ausgeschlossen": aus}
        rows = [zeile("A", 400, 2, (70, 20, 10)), zeile("B", 300, 0, (65, 25, 10)), zeile("C", 450, 9, (20, 40, 40)),
                zeile("D", 6000, 300, (5, 50, 45)), zeile("X", 200, 90, (50, 40, 10), aus="Ortszuordnung unplausibel")]
        k = d.kreuztabelle(rows)
        self.assertEqual((k["n"], len(k["ausgeschlossen"])), (4, 1))
        self.assertEqual(k["klassen"]["0–499"]["n"], 3)
        self.assertEqual(k["klassen"]["0–499"]["mit_telefon"], 2)
        self.assertEqual(k["klassen"]["0–499"]["je_100"], round(100 * 11 / 1150, 2))
        self.assertEqual(k["kreuz"]["0–499"][d.SEKTORGRUPPEN[0]]["n"], 2)
        self.assertEqual(k["sektorgruppen"][d.SEKTORGRUPPEN[3]]["n"], 2)

    def test_ergebnistabelle(self):
        rows = open_csv(d.OUT_GEMEINDEN)
        self.assertGreater(len(rows), 400)
        bern = next(x for x in rows if x["name"].startswith("Bern ("))
        self.assertEqual((bern["bev_1910"], bern["groessenklasse"], bern["ausgeschlossen"]), ("85651", "ab 5000", ""))
        self.assertIn("Frutigen", {x["name"] for x in rows if x["ausgeschlossen"]})
        stadt = open_csv(d.OUT_STADT)
        self.assertEqual({x["jahr"] for x in stadt}, {"1885", "1900", "1910"})
        for x in stadt:
            if x["nenner"]:
                self.assertIn(x["nenner_art"], ("direkt", "interpoliert", "geschätzt"))


class Seite(unittest.TestCase):
    def test_auszug_und_zeichenketten(self):
        import json
        daten = json.loads(d.OUT_JSON.read_text(encoding="utf-8"))
        s = d.site_daten(daten["gemeinden"], open_csv(d.OUT_STADT), daten["stichprobe"]["3_damals"])
        self.assertEqual(s["jahre"], [1885, 1900, 1910])
        self.assertEqual([len(z[1]) for z in s["kreuz"]], [4] * len(d.SIZE_CLASSES))
        self.assertTrue(all(len(v) == 3 and all(n > 0 for _, n, _ in v) for _, v in s["stadt"]))
        keys = ["inf_be_h", "inf_be_p", "inf_be_city_p", "inf_be_col_group", "inf_be_note", "inf_be_doc"]
        keys += [f"inf_be_g_{g}" for g in s["gruppen"]] + [f"inf_be_r_{k}" for k, _ in s["stadt"]]
        for lang in ("de", "fr", "en"):
            t = json.loads((ROOT / "site" / "i18n" / f"{lang}.json").read_text(encoding="utf-8"))
            self.assertEqual([k for k in keys if not t.get(k)], [], lang)


class Stichproben(unittest.TestCase):
    def test_umfang_und_trefferquote(self):
        for pfad in (d.STICHPROBE, d.STICHPROBE_2, d.STICHPROBE_3):
            rows = open_csv(pfad)
            self.assertGreaterEqual(len(rows), 40)
            self.assertTrue(all(x["soll_art"] and x["richtig"] in ("ja", "nein") for x in rows))
        t = d.trefferquote(d.STICHPROBE_3, damals=True)
        self.assertEqual((t["n"], t["alle"]), (60, 56))
        self.assertEqual(d.trefferquote(d.STICHPROBE_3)["alle"], 56)   # seit der Ziehung keine Regel mehr geändert

    def test_ids_sind_verschieden(self):
        ids = [x["id"] for p in (d.STICHPROBE, d.STICHPROBE_2, d.STICHPROBE_3) for x in open_csv(p)]
        self.assertEqual(len(ids), len(set(ids)))


if __name__ == "__main__":
    unittest.main()

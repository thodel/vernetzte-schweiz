"""Zuzüge mit Heimatort: Auflösung des Heimatorts und Verknüpfung über die Bände (scripts/origins.py, zuzuege.py)."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import origins as o  # noqa: E402
import zuzuege as z  # noqa: E402


class Origins(unittest.TestCase):
    def test_bracket_hint_wins(self):
        self.assertEqual(o.classify("Sulzbach (Wtbg.)")[1:3], ("Ausland", "DE"))
        self.assertEqual(o.classify("Freiburg (Baden)")[1:3], ("Ausland", "DE"))
        self.assertEqual(o.classify("Küttigen (Bern)")[1], "CH")

    def test_unbracketed_grand_duchy_is_a_country_not_a_place(self):
        r = o.classify("Grh. Baden")
        self.assertEqual((r.cls, r.region, r.lat), ("Ausland", "DE", None))

    def test_swiss_old_spellings_and_prefixes(self):
        self.assertEqual(o.classify("Langnau")[1:3], ("CH", "BE"))       # Langnau im Emmental
        self.assertIn(o.classify("Zezwyl")[1], ("CH", "CH?"))          # Zetzwil
        self.assertEqual(o.classify("Ryken")[1], "CH")                   # vor der Fusion
        self.assertEqual(o.classify("soloth")[1:3], ("CH", "SO"))        # nur der Kanton

    def test_swiss_place_is_not_foreign_although_geonames_has_it(self):
        self.assertEqual(o.classify("Baden")[1:3], ("CH", "AG"))

    def test_foreign_place(self):
        r = o.classify("von Erfurt")
        self.assertEqual((r.name, r.cls, r.region), ("Erfurt", "Ausland", "DE"))
        self.assertIsNotNone(r.lat)

    def test_empty_and_ditto(self):
        self.assertEqual(o.classify("daselbst")[1], "leer")
        self.assertEqual(o.classify("")[1], "leer")


def entry(vol, surname, forename, origin="", occ="", street="", no="", **kw):
    x = {"id": f"{vol}-{surname}-{forename}", "volume": str(vol), "surname": surname, "forename": forename,
         "origin": origin, "occupation": occ, "street": street, "building_no": no, "civil_status": "",
         "text": f"{surname}, {forename}", "maiden_name": "", "alliance_name": "", "district": ""}
    global_no = kw.pop("global_no", True)
    x.update(kw)
    return z.prepare(x, 1877 if global_no else 0, global_no)


class Linking(unittest.TestCase):
    def test_same_person_links(self):
        a = entry(1867, "Frey", "Johann", "Küttigen", "Schreiner")
        b = entry(1869, "Frey", "Johann", "Küttigen", "Schreiner")
        self.assertIn(b["id"], z.link([a], [b]))

    def test_different_home_town_contradicts(self):
        a = entry(1867, "Frey", "Johann", "Küttigen")
        b = entry(1869, "Frey", "Johann", "Erfurt")
        self.assertIsNone(z.score(a, b))
        self.assertEqual(z.link([a], [b]), {})

    def test_misread_surname_links_in_the_same_house(self):
        a = entry(1888, "Udel", "Jakob", "Suhr", street="Laurenzenvorstadt", no="12")
        b = entry(1892, "Adel", "Jakob", "Suhr", street="Laurenzenvorstadt", no="12")
        self.assertIn(b["id"], z.link([a], [b]))

    def test_house_numbers_do_not_count_across_the_renumbering(self):
        a = entry(1869, "Frey", "Johann", street="Rathausgasse", no="5")
        b = entry(1877, "Frey", "Johann", street="Rathausgasse", no="5")
        self.assertNotIn("haus", z.score(a, b)[1])

    def test_bern_renumbered_in_1882(self):
        # Bern nummeriert je Strasse und hat 1882 umnummeriert: 1879→1883 zählt die Nummer nicht, 1877→1879 schon
        renumbered, global_no = z.CITIES["Bern"]
        self.assertEqual((renumbered, global_no), (1882, False))

        def be(vol, forename):
            return z.prepare({"id": f"{vol}-{forename}", "volume": str(vol), "surname": "Frey", "forename": forename,
                              "origin": "", "occupation": "", "street": "Kramg.", "building_no": "189",
                              "civil_status": "", "text": "", "maiden_name": "", "alliance_name": "", "district": ""},
                             renumbered, global_no)
        self.assertIn("haus", z.score(be(1877, "Johann"), be(1879, "Johann"))[1])
        self.assertNotIn("haus", z.score(be(1879, "Johann"), be(1883, "Johann"))[1])
        prev = {z.nkey("Frey"): [be(1879, "Johann")]}
        self.assertEqual(z.status(be(1883, "Anna"), prev, False), "haushalt")

    def test_status(self):
        prev = {z.nkey("Frey"): [entry(1888, "Frey", "Johann", street="Rathausgasse", no="5")]}
        self.assertEqual(z.status(entry(1892, "Frey", "Anna", street="Rathausgasse", no="5"), prev, False), "haushalt")
        self.assertEqual(z.status(entry(1892, "Frey", "Anna", street="Kirchgasse", no="9"), prev, False), "neu_familie")
        self.assertEqual(z.status(entry(1892, "Meier", "Anna"), prev, False), "neu")

    def test_similar_names_need_length_and_likeness(self):
        sim = z.similar_names({"rauchenstein", "frey", "meier"}, {"rauschenstein", "frei", "meyer"})
        self.assertEqual(sim, {"rauschenstein": ["rauchenstein"]})

    def test_street_numbering_needs_the_same_street(self):
        # Zürich nummeriert je Strasse: Nr. 5 an zwei Strassen ist nicht dasselbe Haus
        a = entry(1900, "Udel", "Jakob", street="Seefeldstrasse", no="5", global_no=False)
        b = entry(1914, "Adel", "Jakob", street="Bahnhofstrasse", no="5", global_no=False)
        self.assertEqual(z.link([a], [b]), {})
        c = entry(1914, "Adel", "Jakob", street="Seefeldstrasse", no="5", global_no=False)
        self.assertIn(c["id"], z.link([a], [c]))

    def test_initial_links_with_street_or_occupation(self):
        # Bern 1883/1900: viele Einträge nennen nur die Initiale
        a = entry(1883, "Hügi", "R", occ="Heizer", street="Könizstrasse", no="58", global_no=False)
        b = entry(1900, "Hügi", "Rud", occ="Lokomotivführer", street="Könizstrasse", no="12", global_no=False)
        self.assertIn(b["id"], z.link([a], [b]))                      # Initiale und Strasse
        c = entry(1900, "Hügi", "Rud", occ="Heizer", street="Holligenstrasse", global_no=False)
        self.assertIn(c["id"], z.link([a], [c]))                      # Initiale und Beruf
        d = entry(1900, "Hügi", "Rud", occ="Gärtner", street="Holligenstrasse", global_no=False)
        self.assertEqual(z.link([a], [d]), {})                        # Initiale allein
        e = entry(1900, "Hügi", "", occ="Gärtner", street="Könizstrasse", global_no=False)
        self.assertEqual(z.link([a], [e]), {})                        # ohne Vornamen reicht die Strasse nicht
        f = entry(1900, "Hügli", "Rud", occ="Gärtner", street="Könizstrasse", global_no=False)
        self.assertEqual(z.link([a], [f]), {})                        # ähnlicher Name braucht weiter 5 Punkte
        # Vater und Sohn in derselben Strasse: der zweite Vorname widerspricht
        g = entry(1900, "Graf", "Joh. Heinr", occ="Wirt", street="Zweierstrasse", global_no=False)
        h = entry(1901, "Graf", "Joh. Bapt", occ="Ausläufer", street="Zweierstrasse", global_no=False)
        self.assertEqual(z.link([g], [h]), {})
        i = entry(1901, "Graf", "Joh", occ="Ausläufer", street="Zweierstrasse", global_no=False)
        self.assertIn(i["id"], z.link([g], [i]))                      # zweiter Vorname fehlt nur auf einer Seite
        k = entry(1903, "Huber", "H", occ="Kaufmann", street="Morgartenstrasse", global_no=False)
        m = entry(1907, "Huber", "Joh. H", occ="Architekt", street="Morgartenstrasse", global_no=False)
        self.assertEqual(z.link([k], [m]), {})                        # «H.» steht nicht an erster Stelle

    def test_firms_and_buildings_are_not_persons(self):
        base = {"forename": "", "occupation": ""}
        self.assertFalse(z.is_person({**base, "text": "Erismann & Blattner, Eisenhandlung"}))
        self.assertFalse(z.is_person({**base, "forename": "Jakob", "text": "Frey, Jakob, Scheune"}))
        self.assertTrue(z.is_person({**base, "forename": "Jakob", "text": "Frey, Jakob"}))
        self.assertFalse(z.is_person({**base, "surname": "Petranit A. G.", "text": "Petranit A. G., Verwertung von Patenten"}))
        self.assertFalse(z.is_person({**base, "surname": "Erne & Cie.", "forename": "Eduard", "text": "— Eduard, Kaufmann"}))
        self.assertFalse(z.is_person({**base, "surname": "Hämig", "forename": "Söhne, Heinr", "text": "— Söhne, Heinr., Cigarrenhdlg."}))
        # Initialen sind keine Aktiengesellschaft
        self.assertTrue(z.is_person({**base, "surname": "Wolters", "forename": "Joh. A. G. Otto", "text": "Wolters, Joh. A. G. Otto, Schlosser"}))


if __name__ == "__main__":
    unittest.main()

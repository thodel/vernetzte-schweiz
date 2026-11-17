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
         "text": f"{surname}, {forename}", "maiden_name": "", "alliance_name": ""}
    x.update(kw)
    return z.prepare(x, 1877)


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

    def test_status(self):
        prev = [entry(1888, "Frey", "Johann", street="Rathausgasse", no="5")]
        self.assertEqual(z.status(entry(1892, "Frey", "Anna", street="Rathausgasse", no="5"), prev, False), "haushalt")
        self.assertEqual(z.status(entry(1892, "Frey", "Anna", street="Kirchgasse", no="9"), prev, False), "neu_familie")
        self.assertEqual(z.status(entry(1892, "Meier", "Anna"), prev, False), "neu")

    def test_firms_and_buildings_are_not_persons(self):
        base = {"forename": "", "occupation": ""}
        self.assertFalse(z.is_person({**base, "text": "Erismann & Blattner, Eisenhandlung"}))
        self.assertFalse(z.is_person({**base, "forename": "Jakob", "text": "Frey, Jakob, Scheune"}))
        self.assertTrue(z.is_person({**base, "forename": "Jakob", "text": "Frey, Jakob"}))


if __name__ == "__main__":
    unittest.main()

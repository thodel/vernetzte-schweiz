"""Infrastruktur: Berufsgruppen und Wohnungsanschluss (scripts/infrastruktur.py)."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import infrastruktur as i  # noqa: E402


class Groups(unittest.TestCase):
    def test_railways_before_1902_are_abbreviated(self):
        for t in ("commis d. n. o. b.", "empl. j.-s.", "zugführer der s. c.-b.", "beamter d. j.-b.-l.-bahn", "empl. c. f. f.", "Bahnarb."):
            self.assertIn("bahn", i.groups(t), t)

    def test_inns_named_after_station_or_post_are_not_jobs(self):
        for t in ("Hôtel de la Gare", "Wirtschaft z. Post", "Bahnhofbuffet", "Bahnhofrestaurateur"):
            self.assertNotIn("bahn", i.groups(t), t)
            self.assertNotIn("post_tel", i.groups(t), t)

    def test_conductors(self):
        self.assertEqual(i.groups("Kondukteur"), ["bahn"])
        self.assertEqual(i.groups("Tramkondukteur"), ["tram_schiff"])
        self.assertEqual(i.groups("Postkondukteur"), ["post_tel"])

    def test_utilities_and_cars(self):
        self.assertIn("strom", i.groups("Elektrizitätswerk"))
        self.assertIn("gas_wasser", i.groups("Gas- und Wasserversorgung"))
        self.assertIn("auto_velo", i.groups("Garage moderne"))

    def test_home_line_and_call_office(self):
        self.assertTrue(i.HOME.search("Kaufmann, Wohnung"))
        self.assertFalse(i.HOME.search("Wohnungsvermittlung"))
        self.assertTrue(i.CALL_OFFICE.search("Gemeindesprechstation"))
        self.assertTrue(i.STATION_STREET.search("Rue de la Gare 12"))


def entry(name1, entity_type="amt", name2=""):
    return {"name1": name1, "name2": name2, "entity_type": entity_type}


class Spuren(unittest.TestCase):
    def test_top_of_range_skips_detached_blocks(self):
        self.assertEqual(i.top_of_range([1, 2, 3, 250, 520, 8000, 8001]), 520)
        # Basel 1896: wenige tiefe Nummern, dann der neue Bereich bis 4302
        self.assertEqual(i.top_of_range([5, 80, 119] + list(range(1000, 4303, 2))), 4302)

    def test_offices_by_name_not_inns(self):
        self.assertEqual(i.office(entry("Gemeindekanzlei")), "gemeinde")
        self.assertEqual(i.office(entry("Greffe municipal", "firma")), "gemeinde")
        self.assertEqual(i.office(entry("Bahnhof S. B. B.")), "bahnhof")
        self.assertEqual(i.office(entry("Postbureau")), "post")
        self.assertIsNone(i.office(entry("Hôtel de la Gare", "firma")))
        self.assertIsNone(i.office(entry("Bahnhofbuffet", "firma")))
        self.assertIsNone(i.office(entry("Postkutscher", "person")))

    def test_works_need_a_business_name(self):
        self.assertEqual(i.works(entry("Elektrizitätswerk", "firma")), "strom")
        self.assertEqual(i.works(entry("Usine à gaz", "firma")), "gas")
        self.assertEqual(i.works(entry("Wasserversorgung der Stadt Bern", "firma")), "wasser")
        self.assertIsNone(i.works(entry("Kägi", "person", "Chefmonteur des Gaswerkes")))

    def test_hotels(self):
        for x in ("Hôtel Eiger", "Kurhaus Tarasp", "Pension Alpenblick", "Albergo Svizzero"):
            self.assertTrue(i.HOTEL.search(x), x)
        self.assertFalse(i.HOTEL.search("Gasthof zum Bären"))

    def test_unit_2000(self):
        units = {"261", "351"}
        self.assertEqual(i.unit_2000({"bfs": "261", "valid_to": "", "bfs_today": "261"}, units), "261")
        # Oerlikon, 1934 eingemeindet: zählt zu Zürich
        self.assertEqual(i.unit_2000({"bfs": "245", "valid_to": "31.12.1933", "bfs_today": "261"}, units), "261")
        self.assertEqual(i.unit_2000({"bfs": "9999", "valid_to": "", "bfs_today": "9998"}, units), "")


if __name__ == "__main__":
    unittest.main()

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


if __name__ == "__main__":
    unittest.main()

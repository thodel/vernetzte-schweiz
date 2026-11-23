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
        self.assertEqual(i.works(entry("Elektrizitätswerk", "firma")), ["strom"])
        self.assertEqual(i.works(entry("Usine à gaz", "firma")), ["gas"])
        self.assertEqual(i.works(entry("Wasserversorgung der Stadt Bern", "firma")), ["wasser"])
        self.assertEqual(i.works(entry("Kägi", "person", "Chefmonteur des Gaswerkes")), [])

    def test_combined_works_count_for_each_kind(self):
        self.assertEqual(i.works(entry("Gas-, Wasser- u. Elektrizitätswerk", "firma")), ["strom", "gas", "wasser"])
        self.assertEqual(i.works(entry("Gas- und Wasserwerk", "firma")), ["gas", "wasser"])
        self.assertEqual(i.works(entry("Mineralwasser- und Colonialwarenhandlung", "firma")), [])

    def test_call_offices_are_not_stations_or_post(self):
        # «Station communale» ist die Gemeindesprechstelle, «Poste de gendarmerie» ein Polizeiposten
        for name in ("Station communale", "Station publique", "Stazione pubblica", "Stazione consortile", "Gemeindestation",
                     "Gemeindesprechstation"):
            self.assertTrue(i.CALL_OFFICE.search(name), name)
            self.assertIsNone(i.office(entry(name)), name)
        self.assertIsNone(i.office(entry("Poste de gendarmerie")))
        self.assertIsNone(i.office(entry("Poste de police")))
        self.assertEqual(i.office(entry("Station S. B. B.")), "bahnhof")
        self.assertEqual(i.office(entry("Gare C. F. F.")), "bahnhof")
        self.assertEqual(i.office(entry("Bureau des postes")), "post")

    def test_cumulative_counts_first_years(self):
        c = i.cumulative({"a": 1880, "b": 1890, "c": [1890, "Gaswerk"], "d": 1914})
        self.assertEqual(len(c), 35)
        self.assertEqual((c[0], c[9], c[10], c[33], c[34]), (1, 1, 3, 3, 4))

    def test_term_is_the_searchable_start_of_the_name(self):
        self.assertEqual(i.term({"name1": "Elektrizitätswerk (Bureau)"}), "Elektrizitätswerk")

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
        # Büren zum Hof: «valid_to 31.12.1978» ist die Neunummerierung der Berner Bezirke, keine Fusion
        units = {"534", "538"}
        self.assertEqual(i.unit_2000({"bfs": "534", "valid_to": "31.12.1978", "bfs_today": "538"}, units), "534")
        # Ilanz: 2000 eigene Gemeinde, die heutige Nummer (Ilanz/Glion) steht nicht in der Tabelle von 2000
        self.assertEqual(i.unit_2000({"bfs": "3574", "valid_to": "31.12.1977", "bfs_today": "3619"}, {"3574"}), "3574")


if __name__ == "__main__":
    unittest.main()

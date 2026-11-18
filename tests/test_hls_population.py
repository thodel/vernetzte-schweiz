"""Einwohnerzahlen aus HLS-Artikeln (scripts/hls_population.py) und Durchdringung (infrastruktur.py)."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import hls_population as h  # noqa: E402
import infrastruktur as i  # noqa: E402


class Prose(unittest.TestCase):
    def test_series_in_running_text(self):
        t = "1254/55 Hasela. 1764 1411 Einwohner; 1850 2253; 1900 2390; 1950 2831; 2000 2948.Spuren"
        self.assertEqual(h.prose(t), {1764: 1411, 1850: 2253, 1900: 2390, 1950: 2831, 2000: 2948})

    def test_thousands_and_notes(self):
        self.assertEqual(h.prose("1764 251 Einw. (62 Feuerstätten); 1850 390; 1900 1'354"), {1764: 251, 1850: 390, 1900: 1354})

    def test_second_series_and_estimates(self):
        t = "Polit. Gem.: 2000 3'422 Einw. Ehem. Munizipalgem.: 1850 1'185 Einw.; 1870 1'155; 1900 1'866"
        self.assertEqual(h.prose(t)[1900], 1866)
        # «um» und «ca.» sind Schätzungen, das Glied ohne Jahr zählt nicht
        self.assertEqual(h.prose("15. Jahrhundert 100 Einwohner; um 1750 ca. 500; 1850 741; 1900 805"), {1850: 741, 1900: 805})


class Table(unittest.TestCase):
    def test_row_einwohner_under_year_header(self):
        page = ("<table><tr><th>Jahr</th><th>1850</th><th>1870b</th><th>1900</th></tr>"
                "<tr><td><strong>Einwohner</strong></td><td>17 858</td><td>26 398</td><td>ca. 53 000</td></tr>"
                "<tr><td>Deutsch</td><td></td><td></td><td>51 059</td></tr></table>")
        self.assertEqual(h.table(page), {1850: 17858, 1870: 26398})


class Names(unittest.TestCase):
    def test_title_to_name_and_canton(self):
        self.assertEqual(h.name_and_canton("Biel BE, Gemeinde", ""), ("Biel", "BE"))
        self.assertEqual(h.name_and_canton("St. Gallen Gemeinde", "['Schweiz -> SG']"), ("St. Gallen", "SG"))
        self.assertEqual(h.name_and_canton("Hasle bei Burgdorf", "['Schweiz -> BE']"), ("Hasle bei Burgdorf", "BE"))


class Penetration(unittest.TestCase):
    def test_interpolation_is_geometric_between_censuses(self):
        v = {1900: 1000, 1910: 4000}
        self.assertEqual(i.interpolate(v, 1900), 1000)
        self.assertAlmostEqual(i.interpolate(v, 1905), 2000)
        self.assertEqual(i.interpolate(v, 1914), 4000)      # ausserhalb: der nächste Wert
        self.assertEqual(i.interpolate(v, 1890), 1000)

    def test_person_counts_once(self):
        a = {"surname": "Weitnauer", "forename": "Emil", "initials": ""}
        b = {"surname": "WEITNAUER", "forename": "Emil", "initials": "E."}
        self.assertEqual(i.person_key(a), i.person_key(b))
        self.assertNotEqual(i.person_key(a), i.person_key({"surname": "Weitnauer", "forename": "", "initials": "K."}))


if __name__ == "__main__":
    unittest.main()

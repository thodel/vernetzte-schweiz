"""M9: Orte mit Jahren aus dem HLS-Text, Namensschlüssel und Stufen (scripts/hls_coverage.py)."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from hls_coverage import (YEARS, cand_tier, fields_of, gazetteer, surname_keys, text_places,  # noqa: E402
                          year_span)

GAZ = gazetteer({"Baar", "Zürich", "Basel", "Genève", "Wald (ZH)", "Wald (AR)", "Buchs (SG)", "Buchs (AG)", "Hedingen",
                 "Hinwil", "Porrentruy"})


class YearSpan(unittest.TestCase):
    def span(self, s, death=None):
        return year_span(next(YEARS.finditer(s)), death)

    def test_forms(self):
        self.assertEqual(self.span("1889-1894 Kantonsrat"), (1889, 1894))
        self.assertEqual(self.span("1909-45 o. Prof."), (1909, 1945))
        self.assertEqual(self.span("ab 1897 Praxis", death=1930), (1897, 1930))
        self.assertEqual(self.span("bis 1880 Lehrer"), (1875, 1880))
        self.assertEqual(self.span("1901 PD"), (1901, 1910))


class TextPlaces(unittest.TestCase):
    def test_year_before_place_in_same_clause(self):
        tp = text_places("Autor: X 2.1.1837 Küsnacht, 18.11.1907 Baar, ref. 1889-1894 freisinniger Kantonsrat, "
                         "1892-1894 Gemeinderat in Baar.", GAZ, 1907)
        self.assertEqual([(a, b) for a, b, _ in tp["Baar"]], [(1892, 1894)])

    def test_place_without_year_in_clause_is_dropped(self):
        tp = text_places("Autor: X Gymnasium in Zürich, ab 1852 Stud. der Theologie in Basel, 1855 Ordination.", GAZ, 1909)
        self.assertNotIn("Zürich", tp)
        self.assertEqual([(a, b) for a, b, _ in tp["Basel"]], [(1852, 1909)])

    def test_life_dates_do_not_count(self):
        tp = text_places("Autor: X 14.8.1873 Bösingen, 20.10.1937 Freiburg. Sekundarschule in Zürich.", GAZ, 1937)
        self.assertEqual(tp, {})

    def test_exonyms_and_ambiguous_names(self):
        tp = text_places("Autor: X 1878-80 Anwaltspraktikum in Genf; 1890 Lehrer in Wald; 1895 Pfarrer in Buchs (SG).",
                         GAZ, 1920)
        self.assertIn("Genève", tp)
        self.assertNotIn("Wald (ZH)", tp)  # zweideutig und als Wort zu häufig
        self.assertIn("Buchs (SG)", tp)  # mit Kantonszusatz eindeutig

    def test_pruntrut(self):
        self.assertIn("Porrentruy", text_places("Autor: X Ab 1906 Notar in Pruntrut.", GAZ, 1930))


class Names(unittest.TestCase):
    def test_surname_keys(self):
        self.assertIn("puri", surname_keys("de Pury"))  # Namensschlüssel: y = i
        self.assertIn("schmid", surname_keys("Schmid von Grüneck"))
        self.assertIn("grunek", surname_keys("Schmid von Grüneck"))

    def test_fields(self):
        self.assertEqual(fields_of("['Personen -> Politik (1848-) -> Kantone', 'Personen -> Wirtschaft und Beruf']"),
                         ["Politik", "Wirtschaft und Beruf"])
        self.assertEqual(fields_of("kaputt ["), [])


class Tiers(unittest.TestCase):
    def test_job_carries_text_alone_does_not(self):
        self.assertEqual(cand_tier((None, "gleich", False, True)), "wahrscheinlich")
        self.assertEqual(cand_tier((None, "gleich", True, False)), "möglich")
        self.assertEqual(cand_tier((None, "initiale", True, True)), "wahrscheinlich")
        self.assertEqual(cand_tier((None, "initiale", False, True)), "schwach")
        self.assertEqual(cand_tier((None, "", True, True)), "schwach")


if __name__ == "__main__":
    unittest.main()

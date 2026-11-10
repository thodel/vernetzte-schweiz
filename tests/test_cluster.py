import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from cluster import Clusters, distinct, edge, firm_name_key, line_key, street  # noqa: E402
from link_ptt_ab import forename_tokens  # noqa: E402


def rec(id_, year, fn="", phone="", st="", no="", ak="", widow=False, succ=False, firm=False, fnk="",
        slot=None, line="", full="", occ=(), same_as=""):
    return {"id": id_, "source": "ptt", "year": year, "fn": tuple(forename_tokens(fn)), "phone": phone,
            "st": street(st), "no": no, "ak": ak, "widow": widow, "succ": succ, "firm": firm, "fnk": fnk,
            "slot": slot or ("ptt", str(year)), "line": line, "full": full, "occ": frozenset(occ), "same_as": same_as}


class KeyTest(unittest.TestCase):
    def test_firm_forms_kept(self):
        self.assertEqual(firm_name_key("Gebr. Sulzer"), firm_name_key("Sulzer Gebrüder"))
        self.assertNotEqual(firm_name_key("Preiswerk Söhne"), firm_name_key("Preiswerk & Co."))
        self.assertEqual(firm_name_key("Frey & Co."), firm_name_key("Frey & Cie."))

    def test_street_abbreviations(self):
        self.assertEqual(street("Schanzeng."), street("Schanzengasse"))
        self.assertEqual(street("Wildeggstr."), street("Wildeggstrasse"))
        self.assertEqual(street("Münsterpl."), street("Münsterplatz"))
        self.assertNotEqual(street("Kirchberg"), street("Kirchbergasse"))

    def test_line_key(self):
        self.assertEqual(line_key("Orelli,", "Frau Prof."), line_key("Orelli", "Frau Prof"))


class EdgeTest(unittest.TestCase):
    def test_phone_and_forename(self):
        self.assertIsNotNone(edge(rec("a", 1905, "Hans", "1767"), rec("b", 1907, "Hans", "1767")))

    def test_phone_alone_only_close(self):
        self.assertIsNotNone(edge(rec("a", 1911, phone="14"), rec("b", 1913, phone="14")))
        self.assertIsNone(edge(rec("a", 1905, phone="14"), rec("b", 1909, phone="14")))

    def test_contradictions(self):
        self.assertIsNone(edge(rec("a", 1905, "Alfred", "12"), rec("b", 1906, "Adolf", "12")))
        self.assertIsNone(edge(rec("a", 1905, "S.", "46"), rec("b", 1906, "", "46", widow=True)))
        self.assertIsNone(edge(rec("a", 1898, "G.", "1609"), rec("b", 1900, "G.", "1609", succ=True)))
        self.assertIsNone(edge(rec("a", 1905, "Otto", "1", ak="frei"), rec("b", 1906, "Otto", "1", ak="muler")))

    def test_identical_line_without_number(self):
        a = rec("a", 1902, "J.", full="stegmann j wirt weierboden", line="stegmann j")
        b = rec("b", 1904, "J.", full="stegmann j wirt weierboden", line="stegmann j")
        self.assertIsNotNone(edge(a, b))
        self.assertIsNone(edge(a, {**b, "year": 1909}))


class ConflictTest(unittest.TestCase):
    def test_initial_does_not_chain_two_forenames(self):
        recs = [rec("a", 1900, "Johann", "5"), rec("b", 1901, "J.", "5"), rec("c", 1902, "Jakob", "5")]
        cl = Clusters(recs)
        self.assertEqual(cl.union(0, 1), "")
        self.assertEqual(cl.union(1, 2), "vorname")

    def test_two_concurrent_subscribers(self):
        # Vater und Sohn «J.» mit eigener Nummer und Adresse in derselben Ausgabe
        a = rec("a", 1905, "J.", "12", "Kohlenberg", "11")
        b = rec("b", 1905, "J.", "40", "Spalenberg", "3")
        self.assertTrue(distinct(a, b))
        self.assertFalse(distinct(a, {**b, "same_as": "a"}))  # «Derselbe (Wohnung)»
        self.assertFalse(distinct(a, rec("c", 1905, "J.", "12", "Kohlenberg", "11")))


if __name__ == "__main__":
    unittest.main()

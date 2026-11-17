"""Umnummerierung Aarau 1900: alte und neue Nummern nur über die Konkordanz vergleichen."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import link_ptt_ab as l  # noqa: E402


class Renumbering(unittest.TestCase):
    def setUp(self):
        l.RENUMBERED.clear()
        l.RENUMBERED["Aarau"] = (1900, {"511": {"572"}, "697": {"640"}})

    def rec(self, year, no):
        sys_, bld = l.numbering("Aarau", year, no)
        return {"_no": no, "_sys": sys_, "_bld": bld}

    def test_system_by_year(self):
        self.assertEqual(l.numbering("Aarau", 1899, "511"), ("alt", frozenset({"572"})))
        self.assertEqual(l.numbering("Aarau", 1900, "572"), ("neu", frozenset({"572"})))
        self.assertEqual(l.numbering("Bern", 1900, "5"), ("", frozenset()))

    def test_concordance_across_the_switch(self):
        self.assertEqual(l.building("aarau", self.rec(1910, "572"), self.rec(1899, "511")), "konkordanz")

    def test_same_number_in_different_systems_is_not_the_same_house(self):
        self.assertEqual(l.building("aarau", self.rec(1910, "511"), self.rec(1899, "511")), "")
        self.assertFalse(l.same_numbering("aarau", self.rec(1910, "511"), self.rec(1899, "511")))

    def test_same_system_unchanged(self):
        self.assertEqual(l.building("aarau", self.rec(1898, "511"), self.rec(1899, "511")), "gleich")
        self.assertEqual(l.building("aarau", self.rec(1898, "12"), self.rec(1899, "12")), "")

    def test_other_house_on_same_street_costs_a_point(self):
        base = {"_firm": False, "_sk": "frey", "_ak": "", "_fn": [], "_widow": False, "_occ": set(),
                "phone_flag": "", "_st": "laurenzenvorstadt"}
        p = {**base, **self.rec(1910, "640")}
        same = {**base, **self.rec(1896, "697")}
        other = {**base, **self.rec(1896, "511")}
        self.assertGreater(l.score(p, same, "aarau")[0], l.score(p, other, "aarau")[0])
        self.assertEqual(l.score(p, other, "aarau")[0], 2)  # Strasse 3, anderes Haus −1

    def test_firm_read_as_person_prefers_the_firm(self):
        self.assertTrue(l.FIRMLIKE.search("Oehler A. & Co."))
        base = {"_sk": "oehler", "_ak": "", "_fn": [("a", True)], "_widow": False, "_occ": set(),
                "phone_flag": "", "_st": "", "_no": "", "_sys": "", "_bld": frozenset()}
        p = {**base, "_firm": False, "_firmlike": True}
        firm, owner = {**base, "_firm": True}, {**base, "_firm": False}
        # ohne Adresse gleichauf (vorher lag die Firma einen Punkt hinter dem Inhaber) ...
        self.assertEqual(l.score(p, firm, "aarau")[0], l.score(p, owner, "aarau")[0])
        # ... mit dem Gebäude über die Konkordanz vorn (Oehler: Gais 1405 = Industriestrasse 932)
        p2 = {**p, **self.rec(1910, "640"), "_st": "industriestrase"}
        firm2 = {**firm, **self.rec(1899, "697"), "_st": "gais"}
        self.assertGreater(l.score(p2, firm2, "aarau")[0], l.score(p2, owner, "aarau")[0])

    def tearDown(self):
        l.RENUMBERED.clear()


if __name__ == "__main__":
    unittest.main()

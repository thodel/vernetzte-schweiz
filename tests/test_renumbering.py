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

    def tearDown(self):
        l.RENUMBERED.clear()


if __name__ == "__main__":
    unittest.main()

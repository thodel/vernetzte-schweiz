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

    def test_firm_word_after_other_firm_marker_does_not_count(self):
        own = lambda t: bool(l.FIRMLIKE.search(l.OTHER_FIRM.split(t)[0]))
        self.assertTrue(own("Lippmann Rob. & Co."))
        self.assertTrue(own("Pfister E. & Cie. Nachf. v. J. L. Reinhard"))
        self.assertFalse(own("Kirchhofer H., vorm. Bourry-Séquin & Co., Patentbureau"))
        self.assertFalse(own("Peschel Ludw. i. Fa. Ludw. Peschel & Co., Wohnung"))
        self.assertFalse(own("Braun Emil, Generalvertreter der Gebr. Körting"))

    def test_multi_number_houses_are_one_house(self):
        # Märki, Bern 1900: «Wasserwerkgasse 4 und 6» (Möbelhandlung) und «(6) 4 u. 6» (Möbelfabrik)
        mk = lambda no: {"_group": ("marki", "", "k"), "_fn": [("k", True)], "_ak": "",
                         "_no": l.house(no), "_nos": l.multi_numbers(no)}
        self.assertTrue(l.same_person(mk("4 und 6"), mk("(6) 4 u. 6")))
        self.assertTrue(l.same_person(mk("4 und 6"), mk("4, 6")))
        self.assertFalse(l.same_person(mk("4 und 6"), mk("8")))
        self.assertFalse(l.same_person(mk("46"), mk("64")))
        # Bern 1900: «Kramgasse (48) 16» ist Nr. 16; die Klammer trifft keine andere Nr. 48 (Rüfenacht)
        self.assertTrue(l.same_person(mk("(48) 16"), mk("16")))
        self.assertFalse(l.same_person(mk("(39) 11"), mk("39")))
        # eine einzelne Nummer mit «Nr.» bleibt beim bisherigen Vergleich (Rüfenacht & Co., Marktgasse Nr. 39)
        self.assertFalse(l.same_person(mk("Nr. 39"), mk("39")))
        self.assertEqual(l.persons([mk("4 und 6"), mk("(6) 4 u. 6")]), 1)

    def test_fran_is_a_misread_frau(self):
        self.assertEqual(l.forename_tokens("Fran J."), [("j", True)])
        self.assertEqual(l.forename_tokens("Fran."), [("fran", True)])

    def test_woman_is_not_a_firm_on_another_street(self):
        base = {"_sk": "marki", "_ak": "", "_widow": False, "_occ": set(), "phone_flag": "1",
                "_no": "", "_sys": "", "_bld": frozenset(), "_firmlike": False}
        clara = {**base, "_firm": False, "_fn": [("clara", False)], "_ak": "dic", "_woman": True,
                 "_st": "amthausgase"}
        firm = {**base, "_firm": True, "_fn": [("c", True)], "_st": "matewaserwerkgase"}
        self.assertIsNone(l.score(clara, firm, "bern"))
        self.assertIsNotNone(l.score({**clara, "_st": "matewaserwerkgase"}, firm, "bern"))
        self.assertIsNotNone(l.score({**clara, "_woman": False}, firm, "bern"))

    def test_woman_of_another_line_does_not_count(self):
        row = lambda sup, title="": {"entity_type": "person", "name1": "Gusthiot", "name2": "J.", "surname": "Gusthiot",
                                     "forename": "", "initials": "J", "supplement": sup, "title": title,
                                     "alliance_name": "", "street_name": "", "house_no": "", "occupation": "",
                                     "municipality_1914": "Lausanne", "year": "1913"}
        self.assertFalse(l.prepare_ptt(row("moulin, Michoud-Martignier, Mme", "Mme"))["_woman"])
        self.assertTrue(l.prepare_ptt(row("Mme, Château de Chéserex", "Mme"))["_woman"])
        self.assertTrue(l.prepare_ptt(row("Frau", "Frau"))["_woman"])

    def tearDown(self):
        l.RENUMBERED.clear()


if __name__ == "__main__":
    unittest.main()

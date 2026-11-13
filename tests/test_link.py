import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from link_ptt_ab import (GENERIC_FIRM, compare_forenames, forename_tokens, nkey, same_house_or_name,  # noqa: E402
                         same_person, skey, tier_for)


def cmp(ptt: str, ab: str) -> str:
    return compare_forenames(forename_tokens(ptt), forename_tokens(ab))


class ForenameTest(unittest.TestCase):
    def test_agree(self):
        for ptt, ab, want in [
            ("Charles", "Carl", "gleich"), ("Gustave", "Gustav", "gleich"), ("Louis", "Ludwig", "gleich"),
            ("Konradin", "Conradin", "gleich"), ("Hch.", "Heinrich", "abkürzung"),
            ("Jos.", "Joseph", "abkürzung"), ("Chs.", "Carl", "abkürzung"), ("Fr.", "Friedr.", "initiale"),
            ("E.", "Hermann Emil", "initiale"), ("J. J.", "Joh. Jak.", "initiale"),
        ]:
            self.assertEqual(cmp(ptt, ab), want, (ptt, ab))

    def test_contradict(self):
        # Fälle aus der Stichprobe, die zuerst falsch verknüpft wurden
        for ptt, ab in [("Ad.", "Andr"), ("Alf.", "Adolf"), ("Ernst", "Erhard u. Jacob"), ("Jules", "Isaac"),
                        ("Aug.", "Anton"), ("August", "Albert"), ("Emil", "Emilie"), ("Alfred", "geb. Wolf, Anna"),
                        ("W.", "Julius. Weinhandlung")]:
            self.assertEqual(cmp(ptt, ab), "widerspruch", (ptt, ab))

    def test_missing(self):
        self.assertEqual(cmp("", "Carl"), "")


class TierTest(unittest.TestCase):
    def test_close_years(self):
        self.assertEqual(tier_for(["vorname:initiale", "strasse"], 1, 3, 4), "sicher")
        self.assertEqual(tier_for(["vorname:gleich"], 1, 3, 4), "wahrscheinlich")
        self.assertEqual(tier_for(["strasse"], 1, 3, 4), "möglich")
        self.assertEqual(tier_for([], 1, 3, 4), "")
        self.assertEqual(tier_for(["vorname:gleich", "strasse"], 2, 3, 4), "")  # zwei Personen

    def test_generation_gap(self):
        self.assertEqual(tier_for(["vorname:initiale", "strasse"], 1, 3, 20), "möglich")
        self.assertEqual(tier_for(["vorname:gleich", "strasse"], 1, 3, 20), "wahrscheinlich")
        self.assertEqual(tier_for(["strasse", "hausnummer"], 1, 3, 20), "")
        self.assertEqual(tier_for(["vorname:gleich", "allianzname"], 1, 3, 35), "")
        self.assertEqual(tier_for(["vorname:gleich", "strasse", "hausnummer"], 1, 3, 35), "möglich")

    def test_firm_against_person(self):
        self.assertEqual(tier_for(["firma-person", "strasse", "beruf"], 1, 3, 5), "möglich")
        self.assertEqual(tier_for(["firma-person", "strasse"], 1, 3, 5), "")
        self.assertEqual(tier_for(["firma-person", "vorname:initiale", "strasse", "hausnummer"], 1, 3, 5),
                         "wahrscheinlich")


class PersonTest(unittest.TestCase):
    def entry(self, fn: str, ak: str = "", no: str = "") -> dict:
        tokens = forename_tokens(fn)
        return {"_fn": tokens, "_ak": nkey(ak), "_no": no, "_group": ("x", nkey(ak), tokens[0][0][:1] if tokens else "")}

    def test_same_person(self):
        self.assertTrue(same_person(self.entry("Otto", no="895"), self.entry("Otto", "Siebenmann", "895")))
        self.assertTrue(same_person(self.entry("Friedr."), self.entry("Friedrich")))
        self.assertFalse(same_person(self.entry("Alfred"), self.entry("Adolf")))
        self.assertFalse(same_person(self.entry("Otto", "Frey"), self.entry("Otto", "Müller")))
        self.assertFalse(same_person(self.entry("Otto", no="12"), self.entry("Otto", no="14")))

    def test_name_key(self):
        self.assertEqual(nkey("Schießer"), nkey("Schiesser"))
        self.assertEqual(nkey("Dreyfuß"), nkey("Dreifus"))
        self.assertEqual(nkey("Jäcker"), nkey("Jaecker"))


if __name__ == "__main__":
    unittest.main()


class BigCityTest(unittest.TestCase):
    """Bern (M5): Namensvettern in der Grossstadt, gemessen in data/review/m5_bern_lausanne.csv."""

    def test_abbreviated_streets(self):
        self.assertEqual(skey("Marktg."), skey("Marktgasse"))
        self.assertEqual(skey("Kramg"), skey("Kramgasse"))
        self.assertEqual(skey("Bärenpl."), skey("Bärenplatz"))
        for name in ("Seidenweg", "Schlossberg", "Hasenburg", "Aarberg"):
            self.assertNotIn("gas", skey(name), name)

    def test_initial_and_phone_sign_not_enough_for_common_names(self):
        ev = ["vorname:initiale", "telefonzeichen"]
        self.assertEqual(tier_for(ev, 1, 2, 0), "wahrscheinlich")
        self.assertEqual(tier_for(ev, 1, 40, 0), "")  # «Müller, R.» in Bern 1900: keine Verknüpfung

    def test_generic_firm_words(self):
        for w in ("Schweizerische", "Café", "Bureau", "Gesellschaft"):
            self.assertIn(nkey(w), GENERIC_FIRM, w)
        self.assertNotIn(nkey("Volksbank"), GENERIC_FIRM)

    def test_attached_entry_needs_house_or_full_name(self):
        def rec(fn, st="", no=""):
            return {"_fn": forename_tokens(fn), "_st": skey(st), "_no": no}
        moser_f = rec("F.", "Wabernstrasse", "22")
        self.assertFalse(same_house_or_name(rec("Frieda", "Predigergasse", "10"), moser_f))
        self.assertTrue(same_house_or_name(rec("Fr.", "Wabernstr.", "22"), moser_f))
        self.assertTrue(same_house_or_name(rec("Theophil", "Kirchg.", "6"), rec("Theophil", "Kramgasse", "7")))
        # Zürich 1900: gleiche Nummer an anderer Strasse; ein Lesefehler in der Strasse zählt nicht
        self.assertFalse(same_house_or_name(rec("", "Sihlstrasse", "6"), rec("", "Röslistrasse", "6")))
        self.assertTrue(same_house_or_name(rec("", "", "6"), rec("", "Röslistrasse", "6")))
        self.assertTrue(same_house_or_name(rec("", "Neuong", "32"), rec("", "Neuengasse", "32")))
        self.assertTrue(same_house_or_name(rec("", "Längg., Gesellschaftsstrasse", "18a"),
                                           rec("", "Gesellschaftsstrasse", "18a")))


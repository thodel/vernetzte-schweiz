import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from link_ptt_ab import compare_forenames, forename_tokens, nkey, same_person, tier_for  # noqa: E402


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

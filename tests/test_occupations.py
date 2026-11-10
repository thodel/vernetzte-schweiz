import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from occupations import classify  # noqa: E402


class OccupationTest(unittest.TestCase):
    def test_classes(self):
        for text, want in [
            ("Dr. med.", "medizin"), ("méd.-dentiste", "medizin"), ("Dr-niéd; oculiste", "medizin"),
            ("Gasthof zum Ochsen", "gast"), ("zum Rössli", "gast"), ("Rest. Freihof", "gast"), ("albergo", "gast"),
            ("Kantonalbank", "bank"), ("avocat", "recht"), ("Patentanwalt Dr. Ing", "recht"),
            ("Fuhrhalter", "verkehr"), ("fabr. d'horlogerie", "uhren"), ("Broderies", "textil"),
            ("Metzger", "lebensmittel"), ("Weinhandlung", "lebensmittel"), ("Molkerei", "lebensmittel"),
            ("Baumeister", "bau"), ("architecte", "bau"), ("Elektrizitätswerke des Kantons Zürich", "industrie"),
            ("A.-G. für Thon", "industrie"), ("Buchdruckerei", "druck"), ("phot", "druck"),
            ("Pfarrer", "bildung"), ("Kantonsschule", "bildung"), ("Damenschneiderin", "handwerk"),
            ("Kaufmann", "handel"), ("Agenturen", "handel"), ("Rentier", "privat"), ("Landwirt", "land"),
        ]:
            self.assertEqual(classify(text), want, text)

    def test_false_friends(self):
        # Fehler aus der ersten Stichprobe (data/review/m6_berufe.csv)
        self.assertNotEqual(classify("lithographie Marsens et Boivin"), "lebensmittel")  # «vin» in «Boivin»
        self.assertNotEqual(classify("Agenturen"), "industrie")  # «A.-G.» in «Agenturen»
        self.assertEqual(classify("Wohnung"), "")


if __name__ == "__main__":
    unittest.main()

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from fuzzy import dist, fkey, key_of_label, threshold  # noqa: E402


class FuzzyTest(unittest.TestCase):
    """site/assets/pages.js rechnet fkey() und dist() gleich; diese Werte sind im Browser mit
    dem Code aus pages.js nachgerechnet (10.11.2026)."""

    def test_shared_with_browser(self):
        for a, b, ka, kb, d in [
            ("Keller", "Keiler", "keler", "keiler", 1), ("Müller", "Miiller", "muler", "miiler", 0),
            ("Pestalozzi", "Pestaiozzi", "pestalozzi", "pestaiozzi", 0.5), ("Imbach", "Imhach", "imbach", "imhach", 0.5),
            ("Schmid", "Schmidt", "schmid", "schmit", 1), ("Bœtsch", "Boetsch", "botsch", "botsch", 0),
            ("Hager", "Eager", "hager", "eager", 1), ("Gmelin", "Grnelin", "gmelin", "grnelin", 0),
            ("Meyer", "Maier", "meier", "maier", 1),
        ]:
            self.assertEqual((fkey(a), fkey(b), dist(fkey(a), fkey(b))), (ka, kb, d), (a, b))

    def test_variants_share_the_key(self):
        self.assertEqual(fkey("Meyer"), fkey("Meier"))
        self.assertEqual(fkey("Bürgi"), fkey("Bürgy"))
        self.assertEqual(fkey("Trösch"), fkey("Trœsch"))

    def test_threshold_by_length(self):
        self.assertEqual(threshold("hug"), 0.5)
        self.assertEqual(threshold("keler"), 1)
        self.assertEqual(threshold("pestalozzi"), 2)

    def test_key_of_label(self):
        self.assertEqual(key_of_label("Müller-Frey, Hans", "p"), "muler")
        self.assertEqual(key_of_label("von Speyr & Co.", "f"), "speir")


if __name__ == "__main__":
    unittest.main()

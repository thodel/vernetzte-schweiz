import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from build_pages import fnv, fold, name_shard  # noqa: E402


class SharedWithBrowserTest(unittest.TestCase):
    """site/assets/pages.js rechnet fold() und fnv() gleich; die Werte sind im Browser geprüft
    (10.11.2026). Ändert sich eine Seite, findet der Browser die Teile nicht mehr."""

    def test_fnv(self):
        for key, want in [("Basel|gartenstrase|24", "fb"), ("Zürich|bahnhofstrase|1", "19"),
                          ("Genève|ruedurhone|58", "ef"), ("Biel (BE)|centralstrase|38", "ef")]:
            self.assertEqual(fnv(key), want, key)

    def test_fold(self):
        for raw, want in [("Müller", "muller"), ("Großmann", "grossmann"), ("Œuvre", "oeuvre"),
                          ("Ægerter", "aegerter"), ("Pénard", "penard")]:
            self.assertEqual(fold(raw), want, raw)

    def test_name_shard(self):
        self.assertEqual(name_shard("von Speyr & Co."), "sp")
        self.assertEqual(name_shard("Müller"), "mu")
        self.assertEqual(name_shard("Ö"), "o_")
        self.assertEqual(name_shard("—"), "__")


if __name__ == "__main__":
    unittest.main()

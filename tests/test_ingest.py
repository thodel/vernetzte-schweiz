import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from common import in_window  # noqa: E402
from ingest_ab import visible  # noqa: E402
from ingest_ptt import PARTIAL_START, replaced_rows  # noqa: E402

CFG = {"window": {"year_from": 1860, "year_to": 1914}}


class Visibility(unittest.TestCase):
    def test_down_to_moeglich(self):
        self.assertTrue(visible({"tier": "wahrscheinlich", "hls_check": "bestätigt: …"}))
        self.assertTrue(visible({"tier": "möglich", "hls_check": "ungeprüft"}))
        self.assertTrue(visible({"tier": "möglich", "hls_check": "zweifelhaft: …"}))

    def test_rejected_hidden(self):
        self.assertFalse(visible({"tier": "verworfen", "hls_check": ""}))
        self.assertFalse(visible({"tier": "möglich", "hls_check": "falsch: anderer Namensvetter"}))
        self.assertFalse(visible({"tier": "wahrscheinlich", "hls_check": "Falsch: …"}))


class Window(unittest.TestCase):
    def test_bounds(self):
        self.assertTrue(in_window("1860", CFG))
        self.assertTrue(in_window(1914, CFG))
        self.assertFalse(in_window("1850", CFG))
        self.assertFalse(in_window("1915", CFG))
        self.assertFalse(in_window("", CFG))


class PartialOverride(unittest.TestCase):
    """Teil-Neulesung (Band 2b 1913/14): die Liste nennt die ersetzten Zeilen der Quelle, der Rest behält seine Nummern."""

    def rows(self, text):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "x.ersetzt.txt"
            p.write_text(text, encoding="utf-8")
            return replaced_rows(p)

    def test_ranges_and_numbers(self):
        self.assertEqual(self.rows("3-5\n9\n"), {3, 4, 5, 9})
        self.assertEqual(self.rows("7"), {7})
        self.assertEqual(self.rows(""), set())

    def test_range_bounds_inclusive(self):
        got = self.rows("5867-16604")
        self.assertIn(5867, got)
        self.assertIn(16604, got)
        self.assertNotIn(5866, got)
        self.assertNotIn(16605, got)

    def test_new_rows_cannot_collide_with_source(self):
        # die neu gelesenen Zeilen zählen ab PARTIAL_START; keine Zeile der Quelle darf so hoch liegen
        root = Path(__file__).resolve().parent.parent / "data" / "override" / "ptt"
        for lst in root.glob("*.ersetzt.txt"):
            self.assertLess(max(replaced_rows(lst)), PARTIAL_START, lst.name)
            self.assertTrue(lst.with_suffix("").with_suffix(".tsv").exists(), lst.name)


if __name__ == "__main__":
    unittest.main()

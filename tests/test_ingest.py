import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from common import in_window  # noqa: E402
from ingest_ab import visible  # noqa: E402

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


if __name__ == "__main__":
    unittest.main()

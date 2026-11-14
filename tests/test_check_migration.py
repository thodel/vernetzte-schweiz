import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
from check_migration import compare  # noqa: E402


class CompareTest(unittest.TestCase):
    old = {"inputs": {"a.csv": "1", "b.py": "2"}, "volumes": {"Chur": {"1900": 100}, "Bern": {"1900": 500}}}

    def test_unchanged(self):
        self.assertEqual(compare(self.old, self.old), [])

    def test_new_place_year_and_input(self):
        new = {"inputs": {"a.csv": "1", "b.py": "3"},
               "volumes": {"Chur": {"1894": 300, "1900": 100}, "Bern": {"1900": 500}, "Fribourg": {"1897": 700}}}
        out = "\n".join(compare(self.old, new))
        self.assertIn("geändert: b.py", out)
        self.assertIn("neue Gemeinden (1): Fribourg", out)
        self.assertIn("neue Jahrgänge (1): Chur 1894", out)

    def test_count_change_needs_margin(self):
        small = {**self.old, "volumes": {"Chur": {"1900": 103}, "Bern": {"1900": 500}}}
        self.assertEqual(compare(self.old, small), [])
        big = {**self.old, "volumes": {"Chur": {"1900": 140}, "Bern": {"1900": 500}}}
        self.assertIn("Chur 1900 (100 → 140)", "\n".join(compare(self.old, big)))


if __name__ == "__main__":
    unittest.main()

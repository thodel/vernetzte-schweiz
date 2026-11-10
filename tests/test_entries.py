import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from build_entries import words  # noqa: E402


class EntryWordsTest(unittest.TestCase):
    def test_words(self):
        self.assertEqual(words("Böhme-Asal", "n"), {"bohme", "asal"})
        self.assertEqual(words("Dr., Arzt", "b"), {"dr", "arzt"})
        self.assertEqual(words("37.69", "t"), {"3769"})  # Charge B schreibt 37.69, der Browser sucht 3769
        self.assertEqual(words("", "s"), set())


if __name__ == "__main__":
    unittest.main()

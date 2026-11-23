"""GitHub nimmt keine Datei über 100 MB an; ein Push mit so einer Datei scheitert erst beim Server.

Am 23.11.2026 hielt data/norm/ab_entries.csv (98,5 MB) die Zürcher Bände 1903–1907 auf: mit 1903 wäre sie über
100 MB gewachsen. Seither liegt sie gepackt als ab_entries.csv.gz. Die Grenze hier liegt bei 90 MB, damit eine
wachsende Datei auffällt, bevor der Push scheitert; dann gehört sie gepackt (common.write_csv packt bei .gz).
"""

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GRENZE = 90_000_000


class Dateigroesse(unittest.TestCase):
    def test_keine_datendatei_ueber_90_mb(self):
        zu_gross = [
            (str(p.relative_to(ROOT)), p.stat().st_size)
            for d in ("data", "links", "site")
            for p in (ROOT / d).rglob("*")
            if p.is_file() and p.stat().st_size > GRENZE
        ]
        self.assertEqual(zu_gross, [], "über 90 MB, als .gz ablegen")

    def test_grosse_tabellen_gepackt(self):
        for p in (ROOT / "data" / "norm" / "ab_entries.csv", ROOT / "links" / "ptt_ab.csv"):
            self.assertTrue(p.with_suffix(".csv.gz").exists(), p)
            self.assertFalse(p.exists(), p)


if __name__ == "__main__":
    unittest.main()

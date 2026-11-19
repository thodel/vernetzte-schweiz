import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts" / "neulesung"))

import convert_2b as c  # noqa: E402


def row(phone, name, alts=(), check="", image=20):
    return {"image": image, "phone": phone, "name": name, "rest": "", "check": check,
            "alts": [(name, "")] + [(a, "") for a in alts]}


class Witness(unittest.TestCase):
    """Die Quelle als vierte Stimme (Band 2b 1913/14): unabhängige Lesung, zugeordnet über Seite und Rufnummer."""

    def run_with(self, source, rows):
        old = c.source_pages
        c.source_pages = lambda vol: source
        try:
            return c.witness(rows, "2b_1913")
        finally:
            c.source_pages = old

    def test_minority_reading_wins_with_the_source(self):
        # zwei Läufe lesen «Nyferer», einer «Nyfeler» wie die Quelle
        rows = [row("8.21", "Bruder-Nyferer", ["Bruder-Nyferer", "Bruder-Nyfeler"]), row("1.10", "Abt"), row("1.11", "Aebi")]
        n = self.run_with({6: [("8.21", c.key("Bruder-Nyfeler")), ("1.10", "abt"), ("1.11", "aebi")]}, rows)
        self.assertEqual(rows[0]["name"], "Bruder-Nyfeler")
        self.assertEqual(n["quelle"], 1)

    def test_source_alone_changes_nothing(self):
        # kein Lauf liest wie die Quelle: ihre Lesung wird nicht übernommen (sie zerlegt Einträge oft falsch)
        rows = [row("8.21", "Dischler", ["Dischler", "Dischler"]), row("1.10", "Abt"), row("1.11", "Aebi")]
        self.run_with({6: [("8.21", "dischier"), ("1.10", "abt"), ("1.11", "aebi")]}, rows)
        self.assertEqual(rows[0]["name"], "Dischler")

    def test_agreement_clears_the_flag(self):
        rows = [row("8.21", "Krayer", ["Kraye", "Kreyer"], check="uneins"), row("1.10", "Abt"), row("1.11", "Aebi")]
        n = self.run_with({6: [("8.21", "krayer"), ("1.10", "abt"), ("1.11", "aebi")]}, rows)
        self.assertEqual(rows[0]["check"], "")
        self.assertEqual(n["quelle-bestätigt"], 1)

    def test_shifted_numbers_follow_the_source(self):
        # Neulesung: Nummern um eine Zeile verrutscht (Gonin trägt die Nummer von Gonner, Gonner die von Gonten)
        rows = [row("1.01", "Abt"), row("1.04", "Gonin"), row("1.08", "Gonner"), row("2.00", "Gonten"),
                row("1.05", "Haas"), row("1.06", "Iten"), row("1.07", "Jost")]
        src = {6: [("1.01", "abt"), ("1.03", "gonin"), ("1.04", "gonner"), ("1.08", "gonten"),
                   ("1.05", "haas"), ("1.06", "iten"), ("1.07", "jost")]}
        self.run_with(src, rows)
        self.assertEqual([r["phone"] for r in rows[1:3]], ["1.03", "1.04"])
        self.assertEqual([r["check"] for r in rows[1:3]], ["nummer-quelle"] * 2)
        self.assertEqual(rows[0]["phone"], "1.01")

    def test_single_divergent_number_is_left_alone(self):
        # nur eine Zeile weicht ab: kein Verrutschen, die Nummer der Neulesung bleibt
        rows = [row("1.01", "Abt"), row("1.04", "Gonin"), row("1.09", "Gonner"), row("1.05", "Haas"), row("1.06", "Iten")]
        src = {6: [("1.01", "abt"), ("1.03", "gonin"), ("1.04", "gonner"), ("1.05", "haas"), ("1.06", "iten")]}
        self.run_with(src, rows)
        self.assertEqual(rows[1]["phone"], "1.04")

    def test_page_missing_in_source(self):
        rows = [row("8.21", "Bruder-Nyferer", ["Bruder-Nyfeler"]), row("1.10", "Abt"), row("1.11", "Aebi")]
        self.run_with({6: [("8.21", c.key("Bruder-Nyfeler"))]}, rows)       # nur eine von drei Nummern gemeinsam
        self.assertEqual(rows[0]["name"], "Bruder-Nyferer")


if __name__ == "__main__":
    unittest.main()

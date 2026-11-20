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


class ProMemoria(unittest.TestCase):
    """Das Merkblatt am Ende des Bands (Polizei, Feuerwache) ist kein Verzeichnis."""

    def entry(self, place, phone, name):
        return {"place": place, "net": "", "phone": phone, "name": name, "rest": ""}

    def test_page_with_header_pro_memoria_is_skipped(self):
        pages = {186: ([self.entry("Zofingen", "42", "Häfliger & Co.")], {"header": "Zofingen"}),
                 190: ([self.entry("BASEL", "4.03", "Polizeidepartement:")], {"header": "Pro memoria"})}
        rows = c.resolve(pages)
        self.assertEqual([(r["image"], r["place"]) for r in rows], [(186, "Zofingen")])

    def test_other_pages_stay(self):
        pages = {20: ([self.entry("Basel", "8.21", "Bruder-Nyfeler")], {"header": "Basel B"})}
        self.assertEqual(len(c.resolve(pages)), 1)


def entry(phone, name, place="", net="", rest=""):
    return {"place": place, "net": net, "phone": phone, "name": name, "rest": rest}


class Band2a(unittest.TestCase):
    """Eigenheiten des Berner Bands 2a 1911–1914."""

    def load(self, line):
        import tempfile
        with tempfile.NamedTemporaryFile("w", suffix=".jsonl", delete=False, encoding="utf-8") as f:
            f.write(line + "\n")
        return c.load(f.name)[0][0]

    def test_im_emmental_keeps_its_e(self):
        # «E.» ist sonst ein Kürzel für Dienststunden und fällt aus der Zentrale
        e = self.load('{"place": "Trub", "net": "Langnau i. E.", "phone": "1", "name": "Post", "rest": ""}')
        self.assertEqual(e["net"], "Langnau i. E.")
        e = self.load('{"place": "Olten", "net": "Aarau) E", "phone": "1", "name": "Post", "rest": ""}')
        self.assertEqual(e["net"], "Aarau")

    def test_bei_belongs_to_the_place(self):
        e = self.load('{"place": "Ried", "net": "b. Frutigen (Frutigen)", "phone": "1", "name": "Post", "rest": ""}')
        self.assertEqual((e["place"], e["net"]), ("Ried b. Frutigen", "Frutigen"))
        e = self.load('{"place": "Schwarzenegg", "net": "b. Thun", "phone": "1", "name": "Post", "rest": ""}')
        self.assertEqual((e["place"], e["net"]), ("Schwarzenegg b. Thun", ""))

    def test_service_hours_after_the_exchange(self):
        e = self.load('{"place": "Bümpliz", "net": "Bern) 6/7 v bis 9 n", "phone": "1", "name": "Post", "rest": ""}')
        self.assertEqual(e["net"], "Bern")

    def test_header_in_capitals_and_with_equals(self):
        self.assertEqual(c.header_town("J=K BERN"), "Bern")
        self.assertEqual(c.header_town("B BERN"), "Bern")
        self.assertEqual(c.header_town("Belp=Biel"), "")           # Spanne zweier Orte
        self.assertEqual(c.heading("BERN"), "Bern")

    def test_header_town_does_not_shorten_the_place(self):
        # Titel «Langnau», Ort «Langnau i. E.»: der Ort bleibt, wie er in der Überschrift steht
        pages = {1: ([entry("1", "Abt", place="Langnau i. E.")], {"header": "Langenthal-Langnau"}),
                 2: ([entry("2", "Aebi")], {"header": "Langnau"})}
        self.assertEqual([r["place"] for r in c.resolve(pages, dots=True)], ["Langnau i. E.", "Langnau i. E."])
        pages = {1: ([entry("1", "Abt", place="Neufeld")], {"header": "B BERN"}),
                 2: ([entry("2", "Aebi")], {"header": "BERN B"})}
        self.assertEqual([r["place"] for r in c.resolve(pages)], ["Neufeld", "Bern"])

    def test_front_pages_belong_to_one_town(self):
        # Landesausstellung 1914: «Neufeld», «Mittelfeld» sind Zwischentitel, keine Orte
        pages = {8: ([entry("51.00", "Feuerwehrposten", place="Neufeld")], {"header": ""}),
                 9: ([entry("51.30", "Postbureau")], {"header": ""}),
                 31: ([entry("1.01", "Abt", place="Bern")], {"header": "Bern A"})}
        rows = c.resolve(pages, c.FRONT["2a_1914"])
        self.assertEqual([r["place"] for r in rows], ["Bern", "Bern", "Bern"])

    def test_abbreviation_keeps_its_period_outside_2b(self):
        pages = {1: ([entry("1", "Abt", place="Trub", net="Langnau i. E.")], {"header": ""})}
        self.assertEqual(c.resolve(pages, dots=True)[0]["net"], "Langnau i. E.")
        pages = {1: ([entry("1", "Abt", place="Soazza", net="Mesocco S.")], {"header": ""})}
        self.assertEqual(c.resolve(pages)[0]["net"], "Mesocco S")


class Invented(unittest.TestCase):
    """Leere Seiten mit durchscheinender Rückseite: jeder Lauf erfindet eine andere Liste."""

    def page(self, name, n=30):
        return ([entry(f"1.{i:02d}", name) for i in range(n)], {"header": "Bern A"})

    def test_three_different_inventions_are_dropped(self):
        runs = {"A": {19: self.page("Aeppli-Roth")}, "B": {19: self.page("Aeschbach")}, "C": {19: self.page("Administration der")}}
        self.assertEqual(c.invented(runs), [19])
        self.assertEqual([len(runs[r][19][0]) for r in "ABC"], [0, 0, 0])

    def test_one_run_alone_is_dropped(self):
        runs = {"A": {118: ([], {})}, "B": {118: self.page("Bär")}, "C": {118: ([], {})}}
        self.assertEqual(c.invented(runs), [118])
        self.assertEqual(len(runs["B"][118][0]), 0)

    def test_real_repetition_stays(self):
        # die Feuer- und Unfallmeldestationen der Landesausstellung stehen wirklich 40-mal untereinander
        runs = {r: {8: self.page("Feuer- und Unfallmeldestation", 40)} for r in "ABC"}
        self.assertEqual(c.invented(runs), [])
        self.assertEqual(len(runs["A"][8][0]), 40)

    def test_ordinary_page_stays(self):
        mixed = ([entry(f"1.{i:02d}", "Müller" if i < 23 else f"Name{i}") for i in range(66)], {"header": "Bern M"})
        runs = {r: {69: mixed} for r in "ABC"}
        self.assertEqual(c.invented(runs), [])

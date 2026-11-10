import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import parse_ptt  # noqa: E402
from parse_ptt import parse  # noqa: E402

parse_ptt.FORENAMES.update({"Wilhelm", "Stefano", "Johannes", "Emil", "Louis", "Robert"})
from places import split_locality  # noqa: E402


def row(name1, name2="", supplement="", street="", phone=""):
    return {"name1": name1, "name2": name2, "supplement": supplement, "street": street, "phone": phone}


class Locality(unittest.TestCase):
    def test_parts(self):
        self.assertEqual(split_locality("Bibern, Sol. (Hessigkofen)"), ("Bibern", "SO", "Hessigkofen"))
        self.assertEqual(split_locality("Winterberg (Kemptthal, Winterthur)"), ("Winterberg", "", "Kemptthal, Winterthur"))
        self.assertEqual(split_locality("Biel, B."), ("Biel", "BE", ""))
        self.assertEqual(split_locality("Gossau St. Gallen"), ("Gossau", "SG", ""))

    def test_ocr(self):
        self.assertEqual(split_locality("Ea Chaux (Cossonay)")[0], "La Chaux")
        self.assertEqual(split_locality("Winkeln (8t. Galien)")[2], "St. Galien")


class Parse(unittest.TestCase):
    def test_person_with_address(self):
        p = parse(row("Bucher", "Wilhelm", "Schreinermeister", "Limmatstr. 192", "7.30"))
        self.assertEqual((p["entity_type"], p["surname"], p["forename"], p["initials"]), ("person", "Bucher", "Wilhelm", "W"))
        self.assertEqual((p["occupation"], p["street_name"], p["house_no"]), ("Schreinermeister", "Limmatstr.", "192"))
        self.assertEqual((p["street_key"], p["phone_norm"]), ("limmatstrasse", "730"))

    def test_forename_in_name(self):
        p = parse(row("Comte. Jos.", "négociant"))
        self.assertEqual((p["surname"], p["initials"], p["occupation"]), ("Comte", "J", "négociant"))

    def test_shifted_columns(self):
        p = parse(row("Girardet", "E.", "nég., pl. St-Laurent", "13", "1.87"))
        self.assertEqual((p["initials"], p["occupation"], p["street_key"], p["house_no"]), ("E", "nég", "place st laurent", "13"))

    def test_alliance_and_initials(self):
        p = parse(row("Maggi-Strehler", "E.", "", "Bergstr. 89"))
        self.assertEqual((p["surname"], p["alliance_name"], p["initials"]), ("Maggi", "Strehler", "E"))

    def test_given_from_lexicon_only(self):
        p = parse(row("Fenkart-Facklam", "Villa Freya", "Wiesenstrasse"))
        self.assertEqual((p["initials"], p["occupation"], p["street_name"]), ("", "Villa Freya", "Wiesenstrasse"))
        self.assertEqual(parse(row("Beretta Stefano", "fabbrica letti"))["surname"], "Beretta")

    def test_abbreviations(self):
        self.assertEqual(parse(row("Dietrich", "Ls.", "", "Greifengasse 31"))["initials"], "L")
        p = parse(row("Casino", "", "Rest. (Frau Böhlen)", "Casinoplatz 15"))
        self.assertEqual(p["initials"], "")

    def test_title_anywhere(self):
        p = parse(row("Decrusch", "J.", "Dr., Bezirksanw.", "Seestr. 82"))
        self.assertEqual((p["title"], p["occupation"], p["initials"]), ("Dr.", "Bezirksanw", "J"))

    def test_continuation_line(self):
        self.assertEqual(parse(row("Wohnung", "St. Karlistr. 30"))["entity_type"], "zusatz")

    def test_firm_gets_no_forename(self):
        p = parse(row("Roth & Reinhardt", "", "Weinhandlung", "Bollwerk 23"))
        self.assertEqual((p["entity_type"], p["initials"], p["occupation"]), ("firma", "", "Weinhandlung"))

    def test_firm_and_office(self):
        self.assertEqual(parse(row("Bahnstation Tobel-Affeltrangen"))["entity_type"], "amt")
        self.assertEqual(parse(row("Zoologischer Garten", "", "Direktion"))["entity_type"], "firma")
        self.assertEqual(parse(row("Bidermann & Co.", "Jb. u. And.", "Spinnerei"))["entity_type"], "firma")
        self.assertEqual(parse(row("Gemeindesprechstation", "Postbureau"))["entity_type"], "amt")
        self.assertEqual(parse(row("Hôtel Pfistern", "", "A. Mennet-Studer", "Zeitglocken 4"))["entity_type"], "firma")


if __name__ == "__main__":
    unittest.main()

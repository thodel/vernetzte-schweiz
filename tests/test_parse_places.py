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

    def test_three_part_name_is_a_person(self):
        """«Name. Vorname. Rest» in den gesamtschweizerischen Bänden: Person mit Zusatz, keine Einrichtung."""
        p = parse(row("Münzer. J.. Bijoutier"))
        self.assertEqual((p["entity_type"], p["surname"], p["initials"], p["occupation"]), ("person", "Münzer", "J", "Bijoutier"))
        p = parse(row("Bordoni. Emil. Piazza Commercio 105"))
        self.assertEqual((p["entity_type"], p["forename"], p["street_name"], p["house_no"]), ("person", "Emil", "Piazza Commercio", "105"))
        p = parse(row("Rutishauser. W. Conditorei u. Caféhalle"))     # der Betrieb im Zusatz macht keine Firma
        self.assertEqual((p["entity_type"], p["occupation"]), ("person", "Conditorei u. Caféhalle"))
        p = parse(row("Siegrist-Moll. Frau F.. Centralstr. 18"))
        self.assertEqual((p["surname"], p["alliance_name"], p["title"], p["street_name"]), ("Siegrist", "Moll", "Frau", "Centralstr"))
        self.assertEqual(parse(row("Baumgartner. A.-J.", "professeur"))["initials"], "AJ")
        self.assertEqual(parse(row("Cattori dott. Emil"))["title"], "dott.")
        # kein Vorname nach dem Punkt: bleibt Einrichtung
        for name in ("Schweiz. Musikhaus", "Rest. Helvetia", "Chem. Laboratorium", "Hanfseilerei. Ebnatstr. 71"):
            self.assertEqual(parse(row(name))["entity_type"], "firma", name)

    def test_repair(self):
        r = row("Spirgi Emil . . . . . .", "laboratorio . .")
        self.assertEqual(parse_ptt.repair(r), ["fuehrungspunkte"])
        self.assertEqual((r["name1"], r["name2"]), ("Spirgi Emil", "laboratorio"))
        self.assertEqual(parse(r)["entity_type"], "person")
        # zweite Hälfte der Rufnummer vor dem Namen
        r = row("16 Biscuiterie nationale", "r. d'Arve") | {"phone": "64"}
        self.assertEqual(parse_ptt.repair(r), ["nummer-zusammengesetzt"])
        self.assertEqual((r["name1"], r["phone"], parse(r)["phone_norm"]), ("Biscuiterie nationale", "64.16", "6416"))
        # vollständige Nummer: die Zahl ist Taxspalte und fällt nur weg
        r = row("16 Biscuiterie nationale") | {"phone": "64.20"}
        self.assertEqual(parse_ptt.repair(r), ["zahl-im-namen"])
        self.assertEqual((r["name1"], r["phone"]), ("Biscuiterie nationale", "64.20"))
        r = row("1er sous-chef") | {"phone": "7"}
        self.assertEqual((parse_ptt.repair(r), r["name1"]), ([], "1er sous-chef"))
        self.assertEqual(parse(row("6.89 1.57 22 2.78"))["entity_type"], "zusatz")

    def test_continuation_in_name(self):
        p = parse(row("Wohnung. Nägelistr. 9"))
        self.assertEqual((p["entity_type"], p["street_name"], p["house_no"]), ("zusatz", "Nägelistr", "9"))
        self.assertEqual(parse(row("Derselbe (Wohnung)"))["entity_type"], "zusatz")
        self.assertEqual(parse(row("Privat. Emil"))["entity_type"], "person")

    def test_name_and_forename_in_one_field(self):
        """Tessiner Bände: «Tami Fulgenzio». Ein unbekanntes Wort nach bekanntem Familiennamen ist dort Vorname."""
        parse_ptt.SURNAMES.update({"Tami", "Basler"})
        parse_ptt.ONE_FIELD.add("P-260-1_2c_1911")
        try:
            p = parse(row("Tami Fulgenzio", "impresario") | {"refcode": "P-260-1_2c_1911"})
            self.assertEqual((p["entity_type"], p["surname"], p["initials"], p["occupation"]), ("person", "Tami", "F", "impresario"))
            for name in ("Tami Fratelli", "Tami Sorelle", "Banca Cantonale Ticinese", "Albergo Bellinzona", "Ufficio postale"):
                self.assertNotEqual(parse(row(name) | {"refcode": "P-260-1_2c_1911"})["entity_type"], "person", name)
            # in allen anderen Bänden bleibt es bei der Liste: «Basler Strassenbahnen» ist kein Herr Basler
            self.assertEqual(parse(row("Basler Vorwärts") | {"refcode": "P-260-1_1_1911"})["entity_type"], "firma")
            self.assertEqual(parse(row("Tami Fulgenzio"))["entity_type"], "firma")
        finally:
            parse_ptt.SURNAMES.clear()
            parse_ptt.ONE_FIELD.clear()

    def test_italian_words(self):
        self.assertEqual(parse(row("Stazione pubblica", "caffè Federale"))["entity_type"], "amt")
        self.assertEqual(parse(row("Villa Maria"))["entity_type"], "firma")
        self.assertEqual(parse(row("Villa", "Joh."))["entity_type"], "person")        # Herr Villa
        self.assertEqual(parse(row("Sottocasa", "Emil"))["entity_type"], "person")

    def test_particle_names(self):
        p = parse(row("Wyss-von Wattenwyl", "E.", "Fürspr."))
        self.assertEqual((p["entity_type"], p["surname"], p["alliance_name"]), ("person", "Wyss", "von Wattenwyl"))
        self.assertEqual(parse(row("de Saussure"))["entity_type"], "person")
        self.assertEqual(parse(row("Koch's Wwe.", "", "Gasthof zum Kreuz"))["surname"], "Koch")

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

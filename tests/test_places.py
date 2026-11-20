import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import places  # noqa: E402


def entry(batch, year, locality, name1, phone, refcode="", page="1", network=""):
    return {"batch": batch, "year": year, "locality": locality, "network": network, "refcode": refcode,
            "page": page, "name1": name1, "name2": "", "street": "", "phone": phone}


class Resolve(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.res = places.Resolver(places.Gazetteer())

    def place(self, raw):
        out = self.res.resolve(raw, "B1", "")
        return out["place_name"], out["canton"]

    def test_similar_name_near_exchange(self):
        # Betten VS liegt 114 km von Echallens; gemeint ist Bettens VD
        self.assertEqual(self.place("Betten* (Echallens)"), ("Bettens", "VD"))
        self.assertEqual(self.place("Bellerive (Vésenaz, Genève)"), ("Collonge-Bellerive", "GE"))

    def test_unknown_hamlet_falls_back_to_exchange(self):
        self.assertEqual(self.place("Kienberg (Balterswil)"), ("Balterswil", "TG"))
        self.assertEqual(self.place("Watt (Arbon)"), ("Arbon", "TG"))

    def test_exchange_disambiguated_by_rest_of_parenthesis(self):
        self.assertEqual(self.place("Autiçpiy (Cottens, Fribourg)"), ("Cottens (FR)", "FR"))

    def test_locality_gets_its_1914_municipality(self):
        """Eine Ortschaft trägt die Gemeinde von 1914, wenn ihre heutige Gemeinde aus genau einer hervorgeht,
        oder wenn data/ref/place_aliases.csv sie nennt."""
        def mun(raw):
            r = dict(self.res.resolve(raw, "B2c", ""))             # Kopie: der Resolver merkt sich das Ergebnis
            places.municipality_of_locality(r, self.res.gaz)       # die eindeutige Regel greift erst am Ende
            return r["municipality_1914"]
        self.assertEqual(mun("Tenero"), "Tenero-Contra")           # eindeutig
        self.assertEqual(mun("Paradiso"), "Calprino")              # Liste: 1914 hiess die Gemeinde Calprino
        self.assertEqual(mun("Cassarate"), "Castagnola")           # Liste: kein Eintrag im Ortschaftenverzeichnis
        self.assertEqual(mun("Ambrì"), "Quinto")                   # Liste: Quinto hat heute zwei Vorgänger
        self.assertEqual(mun("Acquarossa"), "")                    # liegt in mehreren Gemeinden von 1914
        self.assertEqual(mun("Wengen"), "Lauterbrunnen")           # Liste: Lauterbrunnen hat heute zwei Vorgänger
        self.assertEqual(mun("Ostermundigen (Bern)"), "Bolligen")  # Liste: 1914 noch keine eigene Gemeinde
        self.assertEqual(mun("Wangen a. A."), "Wangen an der Aare")  # Liste: abgekürzter Gemeindename

    def test_name_matching_reads_the_source_line(self):
        """Der Namensabgleich zählt die Namenszeile der Quelle, nicht die von repair() gereinigte:
        «64 Müller» blieb ohne Schlüssel, und daran sind die Schwellen geeicht."""
        self.assertEqual(places.source_surname({"name1": "Müller", "_name1_raw": "64 Müller"}), "")
        self.assertEqual(places.source_surname({"name1": "Müller"}), "muller")

    def test_locality_rule_comes_last(self):
        """Die Regel «eindeutige Ortschaft» darf die Auflösung selbst nicht ändern (Eidberg bliebe sonst Seen
        und die Seiten von Einsiedeln fielen nicht mehr an Einsiedeln)."""
        r = dict(self.res.resolve("Tenero", "B2c", ""))
        self.assertEqual(r["hist_code_1914"], "")
        places.municipality_of_locality(r, self.res.gaz)
        self.assertEqual(r["municipality_1914"], "Tenero-Contra")

    def test_reread_volume_is_reliable(self):
        self.assertTrue(places.reliable({"batch": "A", "image": ""}))
        self.assertTrue(places.reliable({"batch": "B", "image": "0057"}))      # neu gelesen, Ort je Eintrag
        self.assertFalse(places.reliable({"batch": "B", "image": ""}))

    def test_near_heading_kept(self):
        self.assertEqual(self.place("Fiez (Grandson)"), ("Fiez", "VD"))


class Series(unittest.TestCase):
    """Die Kantons-Vorliebe gilt je Band: «2b» und «3» desselben Jahres decken verschiedene Landesteile ab."""

    def test_volume_not_year(self):
        a = places.series({"batch": "B", "refcode": "P-260-1_2b_1914", "network": ""})
        b = places.series({"batch": "B", "refcode": "P-260-1_3_1914", "network": ""})
        c = places.series({"batch": "B", "refcode": "P-260-1_2b_1913", "network": ""})
        self.assertNotEqual(a, b)
        self.assertNotEqual(a, c)
        self.assertIn("2b", a)

    def test_batch_a_by_network(self):
        self.assertEqual(places.series({"batch": "A", "refcode": "x", "network": "Bern"}), "ABern")


class Runs(unittest.TestCase):
    """Ein Dorf-Lauf, in dem die Überschrift einer Stadt ausgefallen ist."""

    @classmethod
    def setUpClass(cls):
        rows = [entry("A", "1910", "Neuchâtel", f"Muster{i}", f"{i}.{i % 7}", refcode="a", network="Neuchâtel")
                for i in range(200)]
        rows.append(entry("A", "1910", "Törbel", "Einzig", "9.9", refcode="a2", network="Visp"))
        b = dict(refcode="P-260-1_1_1911", page="283")
        rows += [entry("B", "1911", "Naz (Echallens)", "Station communale", "35", **b)]
        rows += [entry("B", "1911", "Naz (Echallens)", f"Muster{i}", f"{i}.{i % 7}", **b) for i in range(100)]
        rows += [entry("B", "1911", "Naz (Echallens)", "Einzig", "9.9", **b)]
        rows += [entry("B", "1911", "Naz (Echallens)", f"Muster{i}", f"{i}.{i % 7}", **b) for i in range(100, 200)]
        places.resolve_all(rows)
        cls.block = rows[-202:]

    def test_city_block_reassigned(self):
        city = [r for r in self.block if r["place_name"] == "Neuchâtel"]
        self.assertGreaterEqual(len(city), 199)
        self.assertTrue(all(r["place_method"].startswith("jahresabgleich") for r in city))

    def test_far_village_vote_ignored(self):
        # «Einzig, 9.9» steht 1910 nur in Törbel VS: zu weit von Naz und keine Stadt;
        # die Zeile gehört zum Stadtblock, in dem sie steht
        r = next(r for r in self.block if r["name1"] == "Einzig")
        self.assertEqual(r["place_name"], "Neuchâtel")


class Names(unittest.TestCase):
    """Eine Stadt ohne Überschrift, deren Regionalbuch keine Rufnummern nennt (Burgdorf unter «Büren zum Hof»)."""

    SURNAMES = [f"{a}{b}mann" for a in "BDFGHKLMNPRSTW" for b in ("ach", "eck", "ing", "ohl", "urr")]   # 70 Namen

    @classmethod
    def setUpClass(cls):
        rows = [entry("A", "1910", "Burgdorf", n, "", refcode="a", network="Burgdorf") for n in cls.SURNAMES]
        rows += [entry("A", "1910", "Thun", f"Thuner{i}", "", refcode="t", network="Thun") for i in range(60)]
        b = dict(refcode="P-260-1_2a_1911")
        rows += [entry("B", "1911", "Büren zum Hof (Fraubrunnen)", "Zaugg", "3", page="92", **b)]
        rows += [entry("B", "1911", "Büren zum Hof (Fraubrunnen)", f"{n}. Fritz", str(i), page="92", **b) for i, n in enumerate(cls.SURNAMES)]
        rows += [entry("B", "1911", "Büren zum Hof (Fraubrunnen)", n, str(i), page="93", **b) for i, n in enumerate(cls.SURNAMES[:10])]
        rows += [entry("B", "1911", "Busswil (Lyss)", "Meier", "1", page="93", **b)]
        cls.rows = rows
        places.resolve_all(rows)

    def of(self, page, locality="Büren zum Hof (Fraubrunnen)"):
        return [r for r in self.rows if r["batch"] == "B" and r["page"] == page and r["locality"] == locality]

    def test_page_goes_to_the_town_whose_names_it_carries(self):
        town = [r for r in self.of("92") if r["place_name"] == "Burgdorf"]
        self.assertEqual(len(town), len(self.SURNAMES))
        self.assertTrue(all(r["place_method"] == "namensabgleich:seite" for r in town))

    def test_rows_before_the_alphabet_restarts_keep_the_heading(self):
        self.assertEqual(self.of("92")[0]["place_name"], "Büren zum Hof")

    def test_short_rest_on_next_page_follows(self):
        self.assertTrue(all(r["place_name"] == "Burgdorf" for r in self.of("93")))

    def test_next_heading_untouched(self):
        self.assertTrue(self.of("93", "Busswil (Lyss)")[0]["place_name"].startswith("Busswil"))

    def test_alphabet(self):
        self.assertTrue(places.between("Büren zum Hof", "Burgdorf", "Busswil"))
        self.assertFalse(places.between("Genève", "La Chaux-de-Fonds", "Genolier"))
        self.assertFalse(places.between("Cousset", "Neuchâtel", ""))        # nächste Überschrift unlesbar
        self.assertTrue(places.between("Acquarossa", "Lugano", None))       # letzter Lauf des Bandes
        self.assertFalse(places.between("12.83 Gemeindeammann", "Herisau", "Hof"))

    def test_network_of_a_regional_book_is_its_exchange(self):
        res = places.Resolver(places.Gazetteer())
        self.assertEqual(res.resolve("Muri", "ABern", "Bern")["municipality_1914"], "Muri bei Bern")
        self.assertEqual(res.resolve("Interlaken", "ABern", "Bern")["place_name"], "Interlaken")   # weit weg, aber kein Doppelgänger


if __name__ == "__main__":
    unittest.main()

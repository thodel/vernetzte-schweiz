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

    def test_near_heading_kept(self):
        self.assertEqual(self.place("Fiez (Grandson)"), ("Fiez", "VD"))


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


if __name__ == "__main__":
    unittest.main()

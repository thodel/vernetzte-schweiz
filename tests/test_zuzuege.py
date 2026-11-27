"""Zuzüge mit Heimatort: Auflösung des Heimatorts und Verknüpfung über die Bände (scripts/origins.py, zuzuege.py)."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import origins as o  # noqa: E402
import zuzuege as z  # noqa: E402


class Origins(unittest.TestCase):
    def test_bracket_hint_wins(self):
        self.assertEqual(o.classify("Sulzbach (Wtbg.)")[1:3], ("Ausland", "DE"))
        self.assertEqual(o.classify("Freiburg (Baden)")[1:3], ("Ausland", "DE"))
        self.assertEqual(o.classify("Küttigen (Bern)")[1], "CH")

    def test_unbracketed_grand_duchy_is_a_country_not_a_place(self):
        r = o.classify("Grh. Baden")
        self.assertEqual((r.cls, r.region, r.lat), ("Ausland", "DE", None))

    def test_swiss_old_spellings_and_prefixes(self):
        self.assertEqual(o.classify("Langnau")[1:3], ("CH", "BE"))       # Langnau im Emmental
        self.assertIn(o.classify("Zezwyl")[1], ("CH", "CH?"))          # Zetzwil
        self.assertEqual(o.classify("Ryken")[1], "CH")                   # vor der Fusion
        self.assertEqual(o.classify("soloth")[1:3], ("CH", "SO"))        # nur der Kanton

    def test_swiss_place_is_not_foreign_although_geonames_has_it(self):
        self.assertEqual(o.classify("Baden")[1:3], ("CH", "AG"))

    def test_foreign_place(self):
        r = o.classify("von Erfurt")
        self.assertEqual((r.name, r.cls, r.region), ("Erfurt", "Ausland", "DE"))
        self.assertIsNotNone(r.lat)

    def test_foreign_place_without_country_1913(self):
        # 1913 nennt den Heimatort ohne Land; die Liste kommt aus GeoNames, ohne die geprüften Fehltreffer
        self.assertEqual(o.classify("Eisenach")[1:3], ("Ausland", "DE"))
        self.assertEqual(o.classify("Bergamo")[1:3], ("Ausland", "IT"))
        for name in ("Altorf", "Murri", "Koch", "Amerika"):
            self.assertNotEqual(o.classify(name)[1], "Ausland", name)
        self.assertTrue(o.NOT_FOREIGN.isdisjoint(o.foreign()), "NOT_FOREIGN steht in places_foreign.csv")

    def test_empty_and_ditto(self):
        self.assertEqual(o.classify("daselbst")[1], "leer")
        self.assertEqual(o.classify("")[1], "leer")


def entry(vol, surname, forename, origin="", occ="", street="", no="", **kw):
    x = {"id": f"{vol}-{surname}-{forename}", "volume": str(vol), "surname": surname, "forename": forename,
         "origin": origin, "occupation": occ, "street": street, "building_no": no, "civil_status": "",
         "text": f"{surname}, {forename}", "maiden_name": "", "alliance_name": "", "district": ""}
    global_no = kw.pop("global_no", True)
    x.update(kw)
    return z.prepare(x, 1877 if global_no else 0, global_no)


class Linking(unittest.TestCase):
    def test_same_person_links(self):
        a = entry(1867, "Frey", "Johann", "Küttigen", "Schreiner")
        b = entry(1869, "Frey", "Johann", "Küttigen", "Schreiner")
        self.assertIn(b["id"], z.link([a], [b]))

    def test_different_home_town_contradicts(self):
        a = entry(1867, "Frey", "Johann", "Küttigen")
        b = entry(1869, "Frey", "Johann", "Erfurt")
        self.assertIsNone(z.score(a, b))
        self.assertEqual(z.link([a], [b]), {})

    def test_misread_surname_links_in_the_same_house(self):
        a = entry(1888, "Udel", "Jakob", "Suhr", street="Laurenzenvorstadt", no="12")
        b = entry(1892, "Adel", "Jakob", "Suhr", street="Laurenzenvorstadt", no="12")
        self.assertIn(b["id"], z.link([a], [b]))

    def test_house_numbers_do_not_count_across_the_renumbering(self):
        a = entry(1869, "Frey", "Johann", street="Rathausgasse", no="5")
        b = entry(1877, "Frey", "Johann", street="Rathausgasse", no="5")
        self.assertNotIn("haus", z.score(a, b)[1])

    def test_bern_renumbered_in_1882(self):
        # Bern nummeriert je Strasse und hat 1882 umnummeriert: 1879→1883 zählt die Nummer nicht, 1877→1879 schon
        renumbered, global_no = z.CITIES["Bern"]
        self.assertEqual((renumbered, global_no), (1882, False))

        def be(vol, forename):
            return z.prepare({"id": f"{vol}-{forename}", "volume": str(vol), "surname": "Frey", "forename": forename,
                              "origin": "", "occupation": "", "street": "Kramg.", "building_no": "189",
                              "civil_status": "", "text": "", "maiden_name": "", "alliance_name": "", "district": ""},
                             renumbered, global_no)
        self.assertIn("haus", z.score(be(1877, "Johann"), be(1879, "Johann"))[1])
        self.assertNotIn("haus", z.score(be(1879, "Johann"), be(1883, "Johann"))[1])
        prev = {z.nkey("Frey"): [be(1879, "Johann")]}
        self.assertEqual(z.status(be(1883, "Anna"), prev, False), "haushalt")

    def test_aarau_renumbered_1900_through_the_concordance(self):
        # Aarau 1900: neue Nr. 87 = alte 96/1256, neue Nr. 5 = alte 4, neue Nr. 900 ohne alte (Neubau)
        renumbered, global_no = z.CITIES["Aarau"]
        saved = dict(z.HOUSES)
        z.HOUSES["Aarau"] = (1900, {"87": "96", "5": "4"}, {"96": "96", "1256": "96", "4": "4"})
        self.addCleanup(lambda: (z.HOUSES.clear(), z.HOUSES.update(saved)))

        def aa(vol, no):
            return z.prepare({"id": f"{vol}-{no}", "municipality": "Aarau", "volume": str(vol), "surname": "Frey",
                              "forename": "Johann", "origin": "", "occupation": "", "street": "Rathausgasse", "building_no": no,
                              "civil_status": "", "text": "", "maiden_name": "", "alliance_name": "", "district": ""},
                             renumbered, global_no)
        self.assertIn("haus", z.score(aa(1899, "1256"), aa(1901, "87"))[1])
        self.assertIn("haus", z.score(aa(1899, "96"), aa(1913, "87"))[1])
        self.assertIn("haus", z.score(aa(1901, "87"), aa(1913, "87"))[1])
        self.assertIn("haus", z.score(aa(1901, "900"), aa(1913, "900"))[1])
        self.assertNotIn("haus", z.score(aa(1899, "87"), aa(1901, "87"))[1])  # gleiche Zahl, anderes Haus
        self.assertNotIn("haus", z.score(aa(1899, "900"), aa(1901, "900"))[1])  # Neubau: eigenes System
        self.assertNotIn("haus", z.score(aa(1869, "4"), aa(1901, "5"))[1])  # vor 1877 ein anderes System

    def test_bern_street_abbreviations(self):
        # «Krmg.» und «Kramg.» sind dieselbe Strasse; «Lorraine» bleibt die Lorraine, nicht ein Hof darin;
        # «Hrng.» passt zu Herrengasse und Hornergasse: nicht eindeutig, bleibt
        streets = ["Kramg."] * 40 + ["Krmg."] * 10 + ["Lorraine"] * 50 + ["Lorraine, Quartierhof"] * 40
        canon = z.street_canon(streets)
        self.assertEqual(canon.get(z.skey("Krmg.")), z.skey("Kramg."))
        self.assertNotIn(z.skey("Lorraine"), canon)
        self.assertNotIn(z.skey("Kramg."), canon)
        amb = z.street_canon(["Herreng."] * 40 + ["Hornerg."] * 40 + ["Hrng."] * 10)
        self.assertNotIn(z.skey("Hrng."), amb)
        self.assertEqual(z.street_canon(["Herreng."] * 40 + ["Hrng."] * 10).get(z.skey("Hrng.")), z.skey("Herreng."))

        def be(vol, street):
            return z.prepare({"id": f"{vol}-{street}", "volume": str(vol), "surname": "Frey", "forename": "J.",
                              "origin": "", "occupation": "", "street": street, "building_no": "192",
                              "civil_status": "", "text": "", "maiden_name": "", "alliance_name": "", "district": ""},
                             1882, False, canon)
        a, b = be(1877, "Krmg."), be(1879, "Kramg.")
        self.assertEqual(z.score(a, b)[1], ["vorname:initiale", "strasse", "haus"])
        self.assertIn(b["id"], z.link([a], [b]))

    def test_zurich_only_cut_street_names(self):
        # Zürich vor 1893: «Hirschengr.» ist der Hirschengraben; «Seestr.» bleibt die Seestrasse, nicht die Seefeldstrasse
        self.assertEqual(z.ABBR_STREETS["Zürich"], (1893, True))
        streets = ["Hirschengraben"] * 40 + ["Hirschengr."] * 10 + ["Seefeldstr."] * 60 + ["Seestr."] * 30
        canon = z.street_canon(streets, cut_only=True)
        self.assertEqual(canon.get(z.skey("Hirschengr.")), z.skey("Hirschengraben"))
        self.assertNotIn(z.skey("Seestr."), canon)
        self.assertIn(z.skey("Seestr."), z.street_canon(streets))  # der freie Vergleich würde sie zusammenlegen
        # «Mühle» endet auf einen Selbstlaut: ein eigener Name, nicht der abgeschnittene Mühlebach
        self.assertNotIn(z.skey("Mühle"), z.street_canon(["Mühlebach"] * 40 + ["Mühle"] * 10, cut_only=True))

    def test_imported_city_keeps_only_volumes_in_the_window(self):
        # Basel: im Quell-Repo gerechnet; 1862 übernommen, 1850 (vor dem Zeitfenster) nur als Vorband mit Personenzahl
        stats = ("volume,prev_volume,personen,mit_alter_nummer,zuzuege,neu,neu_familie,bleibt,witwe,haushalt\n"
                 "1841,,3,3,,0,0,0,0,0\n1850,1841,2,2,1,1,0,1,0,0\n1862,1850,2,2,1,0,1,1,0,0\n")
        head = "entry_id,volume,prev_volume,status,linked_from,points,evidence,surname,forename,occupation_raw\n"
        rows = head + ("1850-e-1,1850,1841,bleibt,1841-e-1,5,vorname+3 haus,Day,Joh.,Schreiner\n"
                       "1862-e-1,1862,1850,bleibt,1850-e-1,5,vorname+3 haus,Day,Joh.,Schreiner\n"
                       "1862-e-2,1862,1850,neu_familie,,,,Day,Anna,Näherin\n")
        cfg = {"window": {"year_from": 1860, "year_to": 1914},
               "city": [{"id": "basel", "label": "Basel", "repo": "r", "commit": "c" * 40,
                         "zuzuege": "z.csv", "zuzuege_stats": "s.csv"}, {"id": "aarau", "label": "Aarau"}]}
        old = z.config, z.fetch
        z.config, z.fetch = (lambda: cfg), (lambda repo, commit, path: stats if path == "s.csv" else rows)
        try:
            out, st = z.imported({"basel:1862-e-1": "e1"}, {"basel:1862-e-1"})
        finally:
            z.config, z.fetch = old
        self.assertEqual([r["record_id"] for r in out], ["basel:1862-e-1", "basel:1862-e-2"])
        self.assertEqual((out[0]["entity_id"], out[0]["linked_from"], out[1]["entity_id"]), ("e1", "basel:1850-e-1", ""))
        self.assertEqual(sorted(st["Basel"]), ["1850", "1862"])
        self.assertTrue(st["Basel"]["1850"]["ausserhalb"])
        self.assertEqual(st["Basel"]["1850"]["personen"], 2)
        self.assertEqual((st["Basel"]["1862"]["neu_familie"], st["Basel"]["1862"]["zuzug_mit_heimatort"]), (1, 0))

    def test_status(self):
        prev = {z.nkey("Frey"): [entry(1888, "Frey", "Johann", street="Rathausgasse", no="5")]}
        self.assertEqual(z.status(entry(1892, "Frey", "Anna", street="Rathausgasse", no="5"), prev, False), "haushalt")
        self.assertEqual(z.status(entry(1892, "Frey", "Anna", street="Kirchgasse", no="9"), prev, False), "neu_familie")
        self.assertEqual(z.status(entry(1892, "Meier", "Anna"), prev, False), "neu")

    def test_similar_names_need_length_and_likeness(self):
        sim = z.similar_names({"rauchenstein", "frey", "meier"}, {"rauschenstein", "frei", "meyer"})
        self.assertEqual(sim, {"rauschenstein": ["rauchenstein"]})

    def test_street_numbering_needs_the_same_street(self):
        # Zürich nummeriert je Strasse: Nr. 5 an zwei Strassen ist nicht dasselbe Haus
        a = entry(1900, "Udel", "Jakob", street="Seefeldstrasse", no="5", global_no=False)
        b = entry(1914, "Adel", "Jakob", street="Bahnhofstrasse", no="5", global_no=False)
        self.assertEqual(z.link([a], [b]), {})
        c = entry(1914, "Adel", "Jakob", street="Seefeldstrasse", no="5", global_no=False)
        self.assertIn(c["id"], z.link([a], [c]))

    def test_initial_links_with_street_or_occupation(self):
        # Bern 1883/1900: viele Einträge nennen nur die Initiale
        a = entry(1883, "Hügi", "R", occ="Heizer", street="Könizstrasse", no="58", global_no=False)
        b = entry(1900, "Hügi", "Rud", occ="Lokomotivführer", street="Könizstrasse", no="12", global_no=False)
        self.assertIn(b["id"], z.link([a], [b]))                      # Initiale und Strasse
        c = entry(1900, "Hügi", "Rud", occ="Heizer", street="Holligenstrasse", global_no=False)
        self.assertIn(c["id"], z.link([a], [c]))                      # Initiale und Beruf
        d = entry(1900, "Hügi", "Rud", occ="Gärtner", street="Holligenstrasse", global_no=False)
        self.assertEqual(z.link([a], [d]), {})                        # Initiale allein
        e = entry(1900, "Hügi", "", occ="Gärtner", street="Könizstrasse", global_no=False)
        self.assertEqual(z.link([a], [e]), {})                        # ohne Vornamen reicht die Strasse nicht
        f = entry(1900, "Hügli", "Rud", occ="Gärtner", street="Könizstrasse", global_no=False)
        self.assertEqual(z.link([a], [f]), {})                        # ähnlicher Name braucht weiter 5 Punkte
        # Vater und Sohn in derselben Strasse: der zweite Vorname widerspricht
        g = entry(1900, "Graf", "Joh. Heinr", occ="Wirt", street="Zweierstrasse", global_no=False)
        h = entry(1901, "Graf", "Joh. Bapt", occ="Ausläufer", street="Zweierstrasse", global_no=False)
        self.assertEqual(z.link([g], [h]), {})
        i = entry(1901, "Graf", "Joh", occ="Ausläufer", street="Zweierstrasse", global_no=False)
        self.assertIn(i["id"], z.link([g], [i]))                      # zweiter Vorname fehlt nur auf einer Seite
        k = entry(1903, "Huber", "H", occ="Kaufmann", street="Morgartenstrasse", global_no=False)
        m = entry(1907, "Huber", "Joh. H", occ="Architekt", street="Morgartenstrasse", global_no=False)
        self.assertEqual(z.link([k], [m]), {})                        # «H.» steht nicht an erster Stelle

    def test_firms_and_buildings_are_not_persons(self):
        base = {"forename": "", "occupation": ""}
        self.assertFalse(z.is_person({**base, "text": "Erismann & Blattner, Eisenhandlung"}))
        self.assertFalse(z.is_person({**base, "forename": "Jakob", "text": "Frey, Jakob, Scheune"}))
        self.assertTrue(z.is_person({**base, "forename": "Jakob", "text": "Frey, Jakob"}))
        self.assertFalse(z.is_person({**base, "surname": "Petranit A. G.", "text": "Petranit A. G., Verwertung von Patenten"}))
        self.assertFalse(z.is_person({**base, "surname": "Erne & Cie.", "forename": "Eduard", "text": "— Eduard, Kaufmann"}))
        self.assertFalse(z.is_person({**base, "surname": "Hämig", "forename": "Söhne, Heinr", "text": "— Söhne, Heinr., Cigarrenhdlg."}))
        # Initialen sind keine Aktiengesellschaft
        self.assertTrue(z.is_person({**base, "surname": "Wolters", "forename": "Joh. A. G. Otto", "text": "Wolters, Joh. A. G. Otto, Schlosser"}))


if __name__ == "__main__":
    unittest.main()

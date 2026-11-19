"""Lesungen von Band 2b 1913/14 → Tabelle im Format der Charge B. convert_2b.py VOL YEAR OUT.tsv [--report]

Der Band beginnt mit Basel und Luzern als eigenen Blöcken und ordnet danach alle Orte der Netzgruppe (Aargau,
Baselland, Innerschweiz, Solothurn, Tessin) in einem Alphabet. Neu gelesen ist alles ab dem Block Luzern; der
Block Basel bleibt aus der Quelle. Lauf A (Massstab 1,3) gibt Reihenfolge und Bestand vor; je Feld (Name, Rest,
Ort) gilt, was zwei von drei Läufen (B 1,0, C 1,6) gleich lesen, sonst A. Zugeordnet wird über die Rufnummer auf
derselben Seite. Spalte Check wie in convert_2c.py. Wiederholungszeichen » werden aus dem Eintrag darüber
aufgelöst. Der Ort gilt über den Seitenwechsel weiter; nennt der Kolumnentitel eine einzelne Stadt («M-N
Luzern»), gilt sie für die Einträge am Seitenkopf.
"""
import csv, glob, json, os, re, sys, unicodedata



COLS = ["EntityName1", "EntityName2", "Supplement", "Street", "Locality", "PhoneNumber", "Year", "Page", "File",
        "Network", "Image", "Check"]


MONTHS = r"(?i)\b(jan|feb|märz|april|mai|juni|juli|aug|sept|okt|nov|dez|luglio|ottobre|giugno|settembre|agosto|maggio)"
CANTON = r"(?i)(aarg|luz|nidw|obw|sol|soloth|b\.-l|bas\.-l|ticino|tic|schw)\.?"


def load(path):
    out, meta = [], {}
    for line in open(path, encoding="utf-8"):
        line = line.strip().rstrip(",").replace("\u00ad", "")      # auch als JSON-Liste ausgegeben; weiche Trennstriche weg
        if not line.startswith("{"):
            continue
        try:
            d = json.loads(line)
        except json.JSONDecodeError:
            meta["broken"] = meta.get("broken", 0) + 1
            continue
        if d.get("meta"):
            meta.update(d)
        elif "header" in d and "name" not in d:
            meta["header"] = d.get("header") or ""
        elif d.get("end"):
            meta["declared"] = d.get("entries")
        elif "name" in d:
            e = {k: " ".join(str(d.get(k) or "").split()) for k in ("place", "net", "phone", "name", "rest")}
            m = re.match(r"^([^()]*?)\)?\s*\((.*)$", e["net"])       # «Aarg. (Aarau»: Kantonszusatz und Zentrale in einem
            if m and e["place"]:
                e["place"], e["net"] = f"{e['place']}, {m.group(1).strip()}", m.group(2).strip(" )")
            e["net"] = re.sub(r"\)\s*[A-Z0-9][A-Za-z0-9-]{0,4}$", "", e["net"]).strip(" ()")    # «Luzern) N»
            if not re.search(r"[a-zäöüàèéìòù]{3}", e["net"]):       # «(N)», «ER»: Kürzel der Zentrale, kein Netzort
                e["net"] = ""
            if re.search(MONTHS, e["net"]):                      # «(April—Okt)»: Betriebszeit, kein Netzort
                e["net"] = ""
            e["net"] = re.sub(r"(?<![\w-])(C-[a-z]|E[RN]?|N|C)(?![\w-])\.?", "", e["net"]).strip(" ,;()")   # Dienststunden-Kürzel
            if e["place"] and re.fullmatch(CANTON, e["net"]):    # «Bremgarten (Aarg.)»: Kantonszusatz, keine Zentrale
                e["place"], e["net"] = f"{e['place']}, {e['net']}", ""
            if ", " in e["name"]:                                # Fettdruck bis zum Vornamen: wie die Quelle am Komma teilen
                e["name"], _, tail = e["name"].partition(", ")
                e["rest"] = ", ".join(x for x in (tail, e["rest"]) if x)
            out.append(e)
    return out, meta


def ditto(cur: str, prev: str) -> str:
    """» steht für das Wort an derselben Stelle darüber, auch in der Mitte und am Ende («» credito »»)."""
    toks, ptoks = cur.split(), prev.split()
    if "»" not in toks or "«" in cur:                       # « Corriere del Ticino » ist ein Titel
        return cur
    if all(t == "»" for t in toks):                         # nur Zeichen: die ganze Angabe darüber
        return prev
    out = []
    for i, t in enumerate(toks):
        if t != "»":
            out.append(t)
        elif i and i == len(toks) - 1 and len(ptoks) > len(toks):  # letztes Zeichen: der ganze Rest darüber
            out.extend(ptoks[i:])
        elif i < len(ptoks):
            out.append(ptoks[i])
    return " ".join(out)


# Gattungswort, unter dem das Verzeichnis mehrere Häuser mit » aufreiht
HEADWORD = re.compile(r"(?i)^(albergo|pension[e]?|caff[èe]|café|societ[àa]|soc\.|banca|h[oô]tel|offic(\.|ina)|ufficio|farmacia|"
                      r"ferrov[iì]a|ristorante|trattoria|fabbrica|grand|restaurant|gasthaus|gasthof|wirtschaft|kurhaus|villa)$")


def key(s: str) -> str:
    s = unicodedata.normalize("NFKD", s.lower())
    return re.sub(r"[^a-z0-9]+", "", s)


def volume(vol, run):
    """Seiten eines Laufs: {Bildnummer: (Einträge, Meta)}."""
    pages = {}
    for p in sorted(glob.glob(f"raw/{vol}/{run}/*.jsonl")):
        pages[int(os.path.basename(p)[:4])] = load(p)
    return pages


def header_town(header: str) -> str:
    """«M-N Luzern», «Luzern S-T-U» → Luzern; «Meggen-Mellingen» (Spanne zweier Orte) → nichts."""
    words = [w for w in re.split(r"[\s,]+", header)
             if w and (w == "St." or not re.fullmatch(r"(?:[A-ZÄÖÜ][a-z]?\.?)(?:[-–—][A-ZÄÖÜ][a-z]?\.?)*", w))]
    town = " ".join(words)
    return "" if re.search(r"[-–—]", town) else town      # Spanne zweier Orte: kein einzelner Ort


def heading(place: str) -> str:
    """«Münster (Luz.)» → «Münster, Luz.»: der Kantonszusatz steht in der Quelle nach einem Komma."""
    p = place.strip(" —-,")
    m = re.fullmatch(r"(.+?)\s*\(([^()]*)\)?\.?", p)
    if m:
        p = f"{m.group(1).strip(' ,')}, {m.group(2).strip()}"
    return p if re.search(r"\b[A-Za-z]{1,5}\.$", p) and "," in p else p.rstrip(".")


def resolve(pages):
    rows, place, net, name = [], "", "", ""
    for n in sorted(pages):
        entries, meta = pages[n]
        town = header_town(meta.get("header", ""))
        if town and key(town) != key(place) and entries and not entries[0]["place"]:
            place, net, name = town, "", ""             # Stadtblock: der Kolumnentitel nennt den Ort
        for e in entries:
            if e["place"] and key(e["place"]) == key(meta.get("header", "")) and not town:
                e["place"] = ""                             # Kolumnentitel «Gersau-Giubiasco» als Ort gelesen: weitertragen
            if e["place"]:
                p = heading(e["place"])
                if key(p) != key(place):
                    name = ""                               # neuer Ort: kein Zeichen greift über die Überschrift
                place, net = p, e["net"].strip(" ().,")
            while e["rest"].startswith("» ") and "«" not in e["rest"]:   # Zeichen des Namens, in den Rest gerutscht
                e["name"], e["rest"] = e["name"] + " »", e["rest"][2:]
            toks, ptoks = e["name"].split(), name.split()
            if len(toks) >= 2 and set(toks) == {"»"} and len(ptoks) > len(toks) and e["rest"][:1].isalpha():
                head = re.split(r",| \(", e["rest"], maxsplit=1)[0]      # «» » Kreuz (Widmer)» unter «Gasthaus z. Adler»
                kept = ptoks[:len(toks)]
                if re.match(r"(?i)(zum|zur|z\.|du|de la|des|al|alla) ", head) and len(kept) > 1:
                    kept = kept[:-1]                                     # «» » zum Kreuz»: das zweite Zeichen steht für nichts
                e["name"], e["rest"] = " ".join(kept + [head.strip()]), e["rest"][len(head):].lstrip(", ")
            elif e["name"] == "»" and e["rest"][:1].isalpha() and name.split()[:1] and HEADWORD.match(name.split()[0]):
                first, _, tail = e["rest"].partition(",")
                e["name"], e["rest"] = name.split()[0] + " " + first.strip(), tail.strip()
            elif "»" in e["name"]:
                e["name"] = ditto(e["name"], name) if name else e["name"]
            name = e["name"]
            rows.append({**e, "place": place, "net": net, "image": n})
    return rows


def match(e, others):
    """Eintrag mit derselben Nummer auf derselben Seite; bei mehreren der mit dem ähnlichsten Namen."""
    c = [o for o in others if key(o["phone"]) == key(e["phone"])]
    if not c:
        return None
    k = key(e["name"])
    return max(c, key=lambda o: (key(o["name"]) == k, len(os.path.commonprefix([key(o["name"]), k]))))


def placed(rows):
    """Ort im Format der Quelle («Melide (Bissone)»); der Block Basel am Anfang bleibt aus der Quelle."""
    keep, started = [], False
    for r in rows:
        started = started or key(r["place"]) != "basel"
        if started and r["place"]:
            r["locality"] = f"{r['place']} ({r['net']})" if r["net"] else r["place"]
            keep.append(r)
    return keep


def main():
    vol, year, out = sys.argv[1], sys.argv[2], sys.argv[3]
    A = resolve(volume(vol, "A"))
    others = []
    for run in ("B", "C"):
        by = {}
        for r in resolve(volume(vol, run)):
            by.setdefault(r["image"], []).append(r)
        others.append(by)
    stats = {"entries": 0, "voted": {f: 0 for f in ("name", "rest", "place")}, "uneins": 0, "nur-A": 0, "ergänzt": 0}
    rows, seen = [], {}
    for r in A:
        m = [match(r, by.get(r["image"], [])) if r["phone"] else None for by in others]
        have = [x for x in m if x]
        check = ""
        if r["phone"] and all(r["image"] in by for by in others) and not have:
            check = "nur-A"
        if len(have) == 2:
            for f in ("name", "rest", "place"):
                if have[0][f] == have[1][f] != r[f]:
                    r[f] = have[0][f]
                    if f == "place":
                        r["net"] = have[0]["net"]
                    stats["voted"][f] += 1
            if len({key(r["name"]), key(have[0]["name"]), key(have[1]["name"])}) == 3:
                check = "uneins"
        if len(have) == 1 and key(have[0]["name"]) != key(r["name"]):
            check = "zwei-lesungen"
        r["check"] = check
        rows.append(r)
        seen.setdefault(r["image"], set()).add(key(r["phone"]))
    for img, bl in others[0].items():
        cl = others[1].get(img, [])
        for b in bl:
            if b["phone"] and key(b["phone"]) not in seen.get(img, set()):
                c = match(b, cl)
                if c and key(c["name"]) == key(b["name"]) and key(c["place"]) == key(b["place"]):
                    pos = max((i for i, r in enumerate(rows) if r["image"] <= img), default=len(rows) - 1)
                    rows.insert(pos + 1, {**b, "check": "ergänzt"})
                    seen.setdefault(img, set()).add(key(b["phone"]))
    total = len(rows)
    rows = placed(rows)
    for r in rows:
        if r["check"]:
            stats[r["check"]] = stats.get(r["check"], 0) + 1
    stats["entries"] = len(rows)
    with open(out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=COLS, delimiter="\t", quoting=csv.QUOTE_NONE, escapechar="\\", lineterminator="\n")
        w.writeheader()
        for r in rows:
            first, _, tail = r["rest"].partition(",")
            w.writerow({"EntityName1": r["name"], "EntityName2": first.strip(), "Supplement": tail.strip(), "Street": "",
                        "Locality": r["locality"], "PhoneNumber": r["phone"], "Year": year, "Page": r["image"],
                        "File": f"P-260-1_{vol}", "Network": "", "Image": f"{r['image']:04d}", "Check": r["check"]})
    if "--report" in sys.argv:
        print(json.dumps({"gelesen": total, **stats, "orte": len({r["locality"] for r in rows})}, ensure_ascii=False))


if __name__ == "__main__":
    main()

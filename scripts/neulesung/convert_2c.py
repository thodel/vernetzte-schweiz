"""Lesungen von Band 2c → Tabelle im Format der Charge B. convert_2c.py VOL YEAR OUT.tsv [--report]

Drei Lesungen derselben Seite (Lauf A Massstab 1,6, B 1,25, C 2,0). A gibt Reihenfolge und Bestand vor; je Feld
(Name, Zusatz, Strasse, Ort) gilt, was zwei von drei Läufen gleich lesen, sonst A. Zugeordnet wird über die
Rufnummer auf derselben Seite. Spalte Check: «uneins» = alle drei Namen verschieden, «nur-A» = Nummer in keinem
anderen Lauf, «ergänzt» = Eintrag fehlt in A, steht aber in B und C, «zwei-lesungen» = für die Seite gibt es
erst zwei Läufe und sie lesen den Namen verschieden. Wiederholungszeichen » werden aus dem
vorangehenden Eintrag aufgelöst, der Ort gilt über den Seitenwechsel weiter.
"""
import csv, glob, json, os, re, sys, unicodedata

COLS = ["EntityName1", "EntityName2", "Supplement", "Street", "Locality", "PhoneNumber", "Year", "Page", "File",
        "Network", "Image", "Check"]


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
        elif d.get("end"):
            meta["declared"] = d.get("entries")
        elif "name" in d:
            out.append({k: " ".join(str(d.get(k) or "").split()) for k in ("place", "section", "phone", "name", "desc", "street")})
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
                      r"ferrov[iì]a|ristorante|trattoria|fabbrica|grand)$")


def key(s: str) -> str:
    s = unicodedata.normalize("NFKD", s.lower())
    return re.sub(r"[^a-z0-9]+", "", s)


def volume(vol, run):
    """Seiten eines Laufs: {Bildnummer: (Einträge, Meta)}."""
    pages = {}
    for p in sorted(glob.glob(f"raw/{vol}/{run}/*.jsonl")):
        pages[int(os.path.basename(p)[:4])] = load(p)
    return pages


def resolve(pages):
    rows, place, name, street = [], "", "", ""
    for n in sorted(pages):
        entries, _ = pages[n]
        for e in entries:
            if not e["phone"] and re.search(r"\bvedi\b", e["name"] + " " + e["desc"]):
                continue                                   # Verweis («Hôtel vedi Alberghi»), kein Anschluss
            if e["place"]:
                place = e["place"].strip(" —-.")
            while e["desc"].startswith("» ") and "«" not in e["desc"]:   # Zeichen des Namens, in den Zusatz gerutscht
                e["name"], e["desc"] = e["name"] + " »", e["desc"][2:]
            if e["name"] == "»" and e["desc"][:1].isalpha() and name.split()[:1] and HEADWORD.match(name.split()[0]):
                e["name"], e["desc"] = name.split()[0] + " " + e["desc"], ""   # «Albergo» / «» Flora» = Albergo Flora
            elif "»" in e["name"]:
                e["name"] = ditto(e["name"], name)
            if "»" in e["street"]:
                e["street"] = ditto(e["street"], street)
            name, street = e["name"], e["street"] or street
            rows.append({**e, "place": place, "image": n})
    return rows


def match(e, others):
    """Eintrag mit derselben Nummer auf derselben Seite; bei mehreren der mit dem ähnlichsten Namen."""
    c = [o for o in others if key(o["phone"]) == key(e["phone"])]
    if not c:
        return None
    k = key(e["name"])
    return max(c, key=lambda o: (key(o["name"]) == k, len(os.path.commonprefix([key(o["name"]), k]))))


def main():
    vol, year, out = sys.argv[1], sys.argv[2], sys.argv[3]
    A = resolve(volume(vol, "A"))
    others = []
    for run in ("B", "C"):
        by = {}
        for r in resolve(volume(vol, run)):
            by.setdefault(r["image"], []).append(r)
        others.append(by)
    stats = {"entries": 0, "voted": {f: 0 for f in ("name", "desc", "street", "place")}, "uneins": 0, "nur-A": 0, "ergänzt": 0}
    rows, seen = [], {}
    for r in A:
        m = [match(r, by.get(r["image"], [])) if r["phone"] else None for by in others]
        have = [x for x in m if x]
        check = ""
        if r["phone"] and all(r["image"] in by for by in others) and not have:
            check = "nur-A"
        if len(have) == 2:
            for f in ("name", "desc", "street", "place"):
                if have[0][f] == have[1][f] != r[f]:
                    r[f] = have[0][f]
                    stats["voted"][f] += 1
            if len({key(r["name"]), key(have[0]["name"]), key(have[1]["name"])}) == 3:
                check = "uneins"
        if len(have) == 1 and key(have[0]["name"]) != key(r["name"]):
            check = "zwei-lesungen"                        # erst zwei Läufe vorhanden, Namen verschieden
        if check:
            stats[check] = stats.get(check, 0) + 1
        r["check"] = check
        rows.append(r)
        seen.setdefault(r["image"], set()).add(key(r["phone"]))
    # in A übersprungene Einträge: Nummer steht in B und C, mit gleichem Namen
    for img, bl in others[0].items():
        cl = others[1].get(img, [])
        for b in bl:
            if b["phone"] and key(b["phone"]) not in seen.get(img, set()):
                c = match(b, cl)
                if c and key(c["name"]) == key(b["name"]):
                    pos = max((i for i, r in enumerate(rows) if r["image"] <= img), default=len(rows) - 1)
                    rows.insert(pos + 1, {**b, "check": "ergänzt"})
                    seen.setdefault(img, set()).add(key(b["phone"]))
                    stats["ergänzt"] += 1
    stats["entries"] = len(rows)
    with open(out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=COLS, delimiter="\t", quoting=csv.QUOTE_NONE, escapechar="\\", lineterminator="\n")
        w.writeheader()
        for r in rows:
            sec = r["section"].strip(" .")
            w.writerow({"EntityName1": r["name"], "EntityName2": r["desc"].replace("\t", " "),
                        "Supplement": "" if sec.lower() in ("", "abbonati") else sec, "Street": r["street"],
                        "Locality": r["place"], "PhoneNumber": r["phone"], "Year": year, "Page": r["image"],
                        "File": f"P-260-1_{vol}", "Network": "", "Image": f"{r['image']:04d}", "Check": r["check"]})
    print(json.dumps(stats, ensure_ascii=False))


if __name__ == "__main__":
    main()

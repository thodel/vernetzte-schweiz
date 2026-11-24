"""Lesungen der Bände 1, 2a, 2b und 3 1911–1914 → Tabelle im Format der Charge B.
convert_2b.py VOL YEAR OUT.tsv [--ganz] [--quelle ORDNER] [--report]      (VOL: 2b_1913, 2a_1911, 1_1912, 3_1914 …)

Band 2b beginnt mit Basel und (ausser 1911) Luzern als eigenen Blöcken und ordnet danach alle Orte der Netzgruppe
(Aargau, Baselland, Innerschweiz, Solothurn, 1913/14 auch Tessin) in einem Alphabet. Band 2a beginnt mit Bern und
ordnet danach die Orte der Netzgruppe Bern (Kanton Bern ohne Jura, Solothurn, Teile von Freiburg und Luzern); 1914
stehen davor sieben Seiten der Landesausstellung, die zu Bern gehören (FRONT). Das Merkblatt «Pro memoria» am Ende
des Bands bleibt weg, ebenso leere Seiten, auf denen das Modell Einträge erfindet (invented()). Band 1 (Westschweiz)
beginnt mit Genève, Band 3 (Ostschweiz) mit Zürich, danach je ein Alphabet; die grossen Städte (Lausanne, St. Gallen)
stehen als Block mit Überschrift in Versalien darin.

Lauf A (Massstab 1,3) gibt Reihenfolge und Bestand vor; je Feld (Name, Rest, Ort) gilt, was zwei von drei Läufen
(B 1,0, C 1,6) gleich lesen, sonst A. Zugeordnet wird über die Rufnummer auf derselben Seite. Spalte Check wie in
convert_2c.py. Wiederholungszeichen » werden aus dem Eintrag darüber aufgelöst. Der Ort gilt über den Seitenwechsel
weiter; nennt der Kolumnentitel eine einzelne Stadt («M-N Luzern», «B BERN», 1911 auch «Aarberg»), gilt sie für die
Einträge am Seitenkopf.

--ganz nimmt den ganzen Band samt erstem Block (so veröffentlicht); ohne den Schalter beginnt die Tabelle nach dem
Block Basel. --quelle nennt den Ordner tsv/ der Quelle (DHBern/PTT_phonebook_data_tsv): ihre Lesung dient als
vierte Stimme für den Namen und deckt verrutschte Rufnummern auf, siehe witness().
"""
import collections, csv, glob, json, os, re, sys, unicodedata



WHOLE = "--ganz" in sys.argv        # ganzer Band samt Block Basel
SOURCE = sys.argv[sys.argv.index("--quelle") + 1] if "--quelle" in sys.argv else ""    # Ordner tsv/ der Quelle
COLS = ["EntityName1", "EntityName2", "Supplement", "Street", "Locality", "PhoneNumber", "Year", "Page", "File",
        "Network", "Image", "Check"]


MONTHS = r"(?i)\b(jan|feb|märz|april|mai|juni|juli|aug|sept|okt|nov|dez|luglio|ottobre|giugno|settembre|agosto|maggio)"
CANTON = r"(?i)(aarg|luz|nidw|obw|sol|soloth|b\.-l|bas\.-l|ticino|tic|schw|b|frib|freib|neuch)\.?"
# Seiten vor dem Verzeichnis, die zu einem Ort gehören: {Band: (erstes Bild, letztes Bild, Ort)}
FRONT = {"2a_1914": (8, 14, "Bern")}       # Schweizerische Landesausstellung Bern 1914 (farbige Seiten, nach Feldern geordnet)
# Versatz zwischen Bild und gedruckter Seite der Quelle: Band 2b 8–22, Band 2a 6–31 (1914 liegen 23 Seiten vor dem Verzeichnis)
def offset(vol):
    return (8, 23) if vol.startswith("2b") else (4, 33)


# Trennstrich vor dem Grundwort einer Strasse: am Zeilenende gesetzt, die Lesung gibt ihn mit oder ohne Leerzeichen wieder
BREAK = re.compile(r"(?<=[a-zäöü])-\s?(?=[a-zäöü]*(?:(?:strasse|gasse|gässlein|vorstadt|graben|weg|platz|ring|allee|anlage|rain)\b|str\.))")


def load(path, bei=True):
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
            for k in ("name", "rest"):                           # Trennstrich am Zeilenende: «Sevogel-strasse 60»
                e[k] = BREAK.sub("", e[k])
            m = re.match(r"((?:b\.|bei) [^()]+?)\)?\s*(?:\((.*))?$", e["net"])    # «Ried (b. Frutigen) (Frutigen)»: Zusatz zum Ortsnamen
            if m and e["place"] and bei:                       # nicht in Band 2b: dort bleibt «Wil, bei Olten», wie veröffentlicht
                e["place"], e["net"] = f"{e['place']} {m.group(1).strip()}", (m.group(2) or "").strip(" )")
            m = re.match(r"^([^()]*?)\)?\s*\((.*)$", e["net"])       # «Aarg. (Aarau»: Kantonszusatz und Zentrale in einem
            if m and e["place"]:
                e["place"], e["net"] = f"{e['place']}, {m.group(1).strip()}", m.group(2).strip(" )")
            e["net"] = re.sub(r"\)\s*\d.*$", "", e["net"])                    # «Bern) 6/7 v bis 9 n»: Dienststunden
            e["net"] = re.sub(r"\)\s*[A-Z0-9][A-Za-z0-9-]{0,4}$", "", e["net"]).strip(" ()")    # «Luzern) N»
            if not re.search(r"[a-zäöüàèéìòù]{3}", e["net"]):       # «(N)», «ER»: Kürzel der Zentrale, kein Netzort
                e["net"] = ""
            if re.search(MONTHS, e["net"]):                      # «(April—Okt)»: Betriebszeit, kein Netzort
                e["net"] = ""
            e["net"] = re.sub(r"(?<![\w-])(?<!i\. )(?<!i\.)(C-[a-z]|E[RN]?|N|C)(?![\w-])\.?", "", e["net"]).strip(" ,;()")   # Dienststunden-Kürzel
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
        pages[int(os.path.basename(p)[:4])] = load(p, not vol.startswith("2b"))
    return pages


def invented(runs):
    """Leere Seiten, auf denen die Rückseite durchscheint: das Modell erfindet eine Liste mit einem einzigen Namen
    und fortlaufenden Nummern, in jedem Lauf eine andere (2a 1913, Bild 19: 198× «Aeppli-Roth», 185× «Aeschbach»,
    89× «Administration der»). Eine Seite gilt in einem Lauf als erfunden, wenn ein Name vier Fünftel von
    mindestens 20 Einträgen stellt und nicht alle drei Läufe denselben Namen so oft lesen (die Meldestationen der
    Landesausstellung 1914 stehen wirklich 40-mal untereinander). Die Seite wird in diesem Lauf geleert."""
    top = {}
    for run, pages in runs.items():
        for n, (entries, _) in pages.items():
            names = [e["name"] for e in entries if e["name"].strip(" »")]
            if len(entries) >= 20 and names:
                name, k = collections.Counter(names).most_common(1)[0]
                if k >= 0.8 * len(entries):
                    top.setdefault(n, {})[run] = key(name)
    dropped = set()
    for n, by in top.items():
        if len(by) == len(runs) and len(set(by.values())) == 1:
            continue
        for run in by:
            runs[run][n] = ([], runs[run][n][1])
        dropped.add(n)
    return sorted(dropped)


def header_town(header: str) -> str:
    """«M-N Luzern», «Luzern S-T-U» → Luzern; «Meggen-Mellingen» (Spanne zweier Orte) → nichts."""
    words = [w for w in re.split(r"[\s,]+", header)
             if w and (w == "St." or not re.fullmatch(r"(?:[A-ZÄÖÜ][a-z]?\.?)(?:[-–—=][A-ZÄÖÜ][a-z]?\.?)*", w))]
    town = " ".join(w.title() if w.isupper() and len(w) > 3 else w for w in words)
    return "" if re.search(r"[-–—=]", town) else town      # Spanne zweier Orte: kein einzelner Ort


def is_span(header: str) -> bool:
    """«Gersau-Giubiasco», «Romanshorn - Rorbas»: zwei Orte. «La Chaux-de-Fonds» ist einer (vor «de» steht ein
    Bindestrich, aber kein zweiter Ort)."""
    return bool(re.search(r"[A-ZÄÖÜÀ-Þ][\w'.]*\s*[-–—=]\s*[A-ZÄÖÜÀ-Þ]", header))


def heading(place: str, dots: bool = False) -> str:
    """«Münster (Luz.)» → «Münster, Luz.»: der Kantonszusatz steht in der Quelle nach einem Komma."""
    p = place.strip(" —-,")
    if p.isupper() and len(p) > 3:                          # «BERN» im Kolumnentitel und als Überschrift des Blocks
        p = p.title()
    m = re.fullmatch(r"(.+?)\s*\(([^()]*)\)?\.?", p)
    if m:
        p = f"{m.group(1).strip(' ,')}, {m.group(2).strip()}"
    if dots and re.search(r"(?:^|[ .])[A-Za-z]\.$", p):      # «Langnau i. E.», «Muri b. B.»: der Punkt gehört zur Abkürzung
        return p
    return p if re.search(r"\b[A-Za-z]{1,5}\.$", p) and "," in p else p.rstrip(".")


def same_in_capitals(raw: str, place: str) -> bool:
    """Überschrift oder Kolumnentitel in Versalien, die den laufenden Ort meinen: «GENEVE» unter «Genève» (der Akzent
    fehlt) und, in Band 1 1914, «CLAUSANNE», «PLAUSANNE» unter «Lausanne»: der Buchstabe des Abschnitts («C LAUSANNE»)
    ist ohne Leerzeichen gelesen."""
    raw = raw.strip(" —-,")
    if not place or not raw.isupper() or len(raw) < 4:
        return False
    k, kp = key(raw), key(place)
    return k == kp or (k[1:] == kp and raw[:1].isalpha())


def resolve(pages, front=None, dots=False):
    rows, place, net, name = [], "", "", ""
    for n in sorted(pages):
        entries, meta = pages[n]
        if front and front[0] <= n <= front[1]:             # Seiten vor dem Verzeichnis: der Ort steht fest, Zwischentitel sind keine Orte
            for e in entries:
                e["place"], e["net"] = "", ""
            place, net, name = front[2], "", ""
        if re.match(r"(?i)\s*pro memoria", meta.get("header", "")):     # Merkblatt auf dem Umschlag (Polizei, Feuerwache): kein Verzeichnis
            continue
        town = header_town(meta.get("header", ""))
        if town and key(town) != key(place) and entries and not entries[0]["place"] and not same_in_capitals(
                meta.get("header", ""), place) and not (
                key(place).startswith(key(town)) and re.match(r"\s*(,|[bi]\. )", place[len(town):])):   # «Langnau» im Titel, «Langnau i. E.» als Ort
            place, net, name = town, "", ""             # Stadtblock: der Kolumnentitel nennt den Ort
        for e in entries:
            if e["place"] and key(e["place"]) == key(meta.get("header", "")) and not town and is_span(meta.get("header", "")):
                e["place"] = ""                             # Kolumnentitel «Gersau-Giubiasco» als Ort gelesen: weitertragen
            if e["place"]:
                p = heading(e["place"], dots)
                if same_in_capitals(e["place"], place):
                    p = place                               # «GENEVE» unter «Genève», «CLAUSANNE» unter «Lausanne»
                if key(p) != key(place):
                    name = ""                               # neuer Ort: kein Zeichen greift über die Überschrift
                place, net = p, e["net"].strip(" ().,")
                if dots and re.search(r"(?:^|[ .])[A-Za-z]$", net):   # «Langnau i. E.», «Biel, B.»: der Punkt gehört zur Abkürzung (nicht in Band 2b: dort steht «S.» für den Sommerbetrieb)
                    net += "."
            while e["rest"].startswith("» ") and "«" not in e["rest"]:   # Zeichen des Namens, in den Rest gerutscht
                e["name"], e["rest"] = e["name"] + " »", e["rest"][2:]
            toks, ptoks = e["name"].split(), name.split()
            if (len(toks) >= 2 and set(toks) == {"»"} and len(ptoks) > len(toks) and e["rest"][:1].isalpha()
                    and HEADWORD.match(ptoks[0])):           # nur unter einem Gattungswort; «» » Güterbahnhof» unter «Hediger & Co.» bleibt die Firma
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
        started = started or WHOLE or key(r["place"]) != "basel"
        if started and r["place"]:
            r["locality"] = f"{r['place']} ({r['net']})" if r["net"] else r["place"]
            keep.append(r)
    return keep


def source_pages(vol):
    """Zeilen der Quelle (Charge B) je gedruckter Seite: {Seite: [(Nummer, Name1)]}."""
    pages = {}
    for path in sorted(glob.glob(os.path.join(SOURCE, "b*.tsv"))):
        with open(path, newline="", encoding="utf-8-sig", errors="replace") as f:
            for r in csv.DictReader(f, delimiter="\t", quoting=csv.QUOTE_NONE):
                if (r.get("File") or "").strip() == f"P-260-1_{vol}" and (r.get("Page") or "").strip().isdigit():
                    pages.setdefault(int(r["Page"]), []).append((" ".join((r.get("PhoneNumber") or "").split()), key(r.get("EntityName1") or "")))
    return pages


def witness(rows, vol):
    """Die Quelle als vierte Stimme. Sie ist eine unabhängige Texterkennung: liest sie den Namen wie einer der drei
    Läufe, gilt diese Lesart, auch gegen die beiden anderen. Zugeordnet wird über Seite und Rufnummer; die Seite
    der Quelle ist die gedruckte, der Versatz zum Bild wird je Bild aus den gemeinsamen Nummern bestimmt.
    Steht ein Name in der Quelle bei der Nummer der Nachbarzeile und umgekehrt, sind die Nummern der Neulesung
    um eine Zeile verrutscht: dann gilt die Nummer der Quelle (Check «nummer-quelle»)."""
    src, n = source_pages(vol), {"quelle": 0, "quelle-bestätigt": 0}
    by = {}
    for r in rows:
        by.setdefault(r["image"], []).append(r)
    for img, rs in by.items():
        phones = {key(r["phone"]) for r in rs if r["phone"]}
        page = max(range(img - offset(vol)[1] + 1, img - offset(vol)[0] + 1), key=lambda p: len(phones & {key(ph) for ph, _ in src.get(p, [])}))
        s_by, s_name, fmt = {}, {}, {}
        for raw, nm in src.get(page, []):
            ph = key(raw)
            fmt[ph] = raw
            s_by.setdefault(ph, set()).add(nm)
            s_name.setdefault(nm, set()).add(ph)
        if len(phones & set(s_by)) < 0.5 * len(phones):
            n["bilder ohne quelle"] = n.get("bilder ohne quelle", 0) + 1
            continue                                        # Seite fehlt in der Quelle
        for i, r in enumerate(rs):
            ph, nm = key(r["phone"]), key(r["name"])
            if not ph or not nm:
                continue
            if nm in s_by.get(ph, ()):
                if r["check"] in ("uneins", "zwei-lesungen", "nur-A"):
                    r["check"] = ""                         # die unabhängige Lesung bestätigt
                    n["quelle-bestätigt"] += 1
                continue
            alt = next((a for a in r.get("alts", []) if key(a[0]) in s_by.get(ph, ())), None)
            if alt:
                r["name"], r["rest"] = alt
                r["check"] = ""
                n["quelle"] += 1
                continue
            there = s_name.get(nm, set())
            near = {key(x["name"]) for x in rs[max(0, i - 2):i + 3] if x is not r}
            if len(there) == 1 and s_by.get(ph, set()) & near and not there & {key(x["phone"]) for x in rs if x is not r and key(x["name"]) == nm}:
                r["newphone"] = next(iter(there))
        moved = [r for r in rs if r.get("newphone")]
        if len(moved) >= 2:                                 # eine einzelne Zeile verrutscht nicht
            for r in moved:
                r["phone"] = fmt[r["newphone"]]
                r["check"] = "nummer-quelle"
    return n


def main():
    vol, year, out = sys.argv[1], sys.argv[2], sys.argv[3]
    runs = {run: volume(vol, run) for run in "ABC"}
    empty = invented(runs)
    dots = not vol.startswith("2b")
    A = resolve(runs["A"], FRONT.get(vol), dots)
    others = []
    for run in ("B", "C"):
        by = {}
        for r in resolve(runs[run], FRONT.get(vol), dots):
            by.setdefault(r["image"], []).append(r)
        others.append(by)
    stats = {"entries": 0, "voted": {f: 0 for f in ("name", "rest", "place")}, "uneins": 0, "nur-A": 0, "ergänzt": 0}
    rows, seen = [], {}
    for r in A:
        m = [match(r, by.get(r["image"], [])) if r["phone"] else None for by in others]
        have = [x for x in m if x]
        r["alts"] = [(r["name"], r["rest"])] + [(x["name"], x["rest"]) for x in have]
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
    if SOURCE:
        stats.update(witness(rows, vol))
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
        print(json.dumps({"gelesen": total, "erfundene seiten": empty, **stats, "orte": len({r["locality"] for r in rows})}, ensure_ascii=False))


if __name__ == "__main__":
    main()

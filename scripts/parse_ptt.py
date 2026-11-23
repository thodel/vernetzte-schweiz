"""Telefonbuch-Einträge zerlegen: Art, Name, Vorname/Initialen, Titel, Beruf, Strasse, Nummer.

Die Spalten der Quelle sind in Charge B oft verrutscht (Strasse im Zusatz, Hausnummer in der
Strassenspalte, Vorname im Namen: «Comte. Jos.»). Darum liest der Zerleger den Rest des
Eintrags (name2, supplement, street) als Folge von Abschnitten: die Adresse von hinten, Titel
wo sie stehen, Vornamen von vorn; was bleibt, ist Beruf oder Zusatz.

Vornamen erkennt er an Abkürzungen («Joh.», «A.») und an einer Liste, die aus den Daten
selbst gebaut wird (data/ref/forenames.csv): Vornamen der Adressbücher und häufige
Einzelwörter der Vornamenspalte, ohne Wörter, die häufiger als Name stehen («Müller») oder
Titel und Einrichtungen sind («Frau», «Postbureau»).

Zeilen wie «Wohnung | St. Karlistr. 30» sind zweite Zeilen des vorangehenden Abonnenten:
Art `zusatz`, `parent_id` zeigt auf den Haupteintrag.

Vor Ortsauflösung und Zerlegung repariert `repair()` drei Lesefehler der gesamtschweizerischen Bände:
Führungspunkte («Spirgi Erwin . . . .»), die abgetrennte zweite Hälfte der Rufnummer am Zeilenanfang
(«16 Biscuiterie nationale», Nummer «64» → «64.16») und Zahlen aus der Taxspalte. Der Name in drei
durch Punkte getrennten Teilen («Münzer. J.. Bijoutier») ist eine Person mit Zusatz, keine Einrichtung.
"""

from __future__ import annotations

import csv
import re
from collections import Counter

from common import NORM, ROOT, open_csv

PARSE_FIELDS = [
    "entity_type", "parent_id", "surname", "alliance_name", "forename", "initials", "title",
    "occupation", "street_name", "house_no", "street_key", "phone_norm", "parse_flags",
]

FIRM = re.compile(
    r"&|\b(Co|Cie|Comp|AG|A\.-G|S\.\s?A|Gebr|Gebrüder|Frères|Fratelli|Söhne|Société|Soc|Ges)\b\.?|"
    r"(?i:fabri[kq]|werke?\b|handlung|hdlg|druckerei|brauerei|bank\b|banque|gesellschaft|genossenschaft|"
    r"verein\b|käserei|molkerei|mühle\b|h[oô]tel|restaurant|café\b|brasserie|pension\b|garage|apothe[kc]|"
    r"pharmacie|comptoir|agence|magasin|maison\b|caisse|kasse\b|atelier|imprimerie|spinnerei|weberei|"
    r"ziegelei|laboratoire|konsum|gasthof|gasthaus|wirtschaft|verlag|versicherung|assurance|"
    r"elektrizitätswerk|gaswerk|wasserwerk|sägerei|zeitung|journal\b|tagblatt|anzeiger|sanatori|klinik|"
    r"clinique|clinica|institut|albergo|ristorante|osteria|trattoria|grotto\b|birreria|banca\b|società|"
    r"negozio|macelleria|farmacia|tipografia|stabilimento|officina|magazzin|impresa\b|\bvilla\s|\bcasa\s|"
    r"\bcroce\s|eredi\b|ditta\b|giornale|cooperativa|consorzio|ferrovi[ae]|tramvi[ae]|funicolare|"
    r"navigazione|cinema|teatro|kursaal\b(?!-)|bazar\b)"
)
AMT = re.compile(
    r"(?i:station\b|b[uü]reau|polizei|schule\b|schulhaus|spital|hôpital|kaserne|zeughaus|verwaltung|"
    r"direktion|gericht|kanzlei|gemeinde|kanton|eidg|bahnhof|\bpost(bureau|ablage|amt|gebäude|halter|"
    r"büro)?\b|telegraph|telephon|zoll|pfarr|\bcure\b|mairie|\bcommune\b|feuerwehr|forsthaus|regierung|"
    r"bundes|stadthaus|rathaus|amtshaus|\bamt\b|departement|département|école|ecole|\bgare\b|douane|"
    r"sprechstation|anstalt|asyl|museum|bibliothek|kirche|friedhof|schlachthaus|abattoir|ufficio|uffizio|"
    r"\bstazione|municipi|comune\b|scuol[ae]|ospedale|dogana|gendarmeria|polizia|tribunale|pretura|"
    r"commissari|cantonale|federal[ei]|parrocchi|caserma|arsenale|macello|deposito postale|liceo|ginnasio|"
    r"seminario|governo|direzione|amministrazione|ispettor|telegrafic|posta\b|poste\b)"
)
CONT = {
    "wohnung", "domicile", "privatwohnung", "privat", "logement", "abitazione", "filiale", "magazin",
    "magasin", "lager", "werkstätte", "werkstatt", "atelier", "bureau", "bureaux", "comptoir", "laden",
    "geschäft", "fabrik", "derselbe", "dieselben", "dieselbe", "le même", "les mêmes", "idem", "dito",
    "ders", "usine", "entrepôt", "dépôt", "succursale", "chantier", "privé", "appartement",
}
TITLE_RX = re.compile(
    r"^(Dr\.?(\s?(med|jur|phil|med\.\s?vet|rer\.\s?pol)\.?)?|Prof\.?|Wwe\.?|Witwe|Frau|Fr\.|Frl\.|"
    r"Fräulein|Mme\.?|Mlle\.?|Mlles|Mmes|Mad\.|Vve\.?|Veuve|Herr|Hr\.|Pfr\.|Pfarrer|Notar|"
    r"Fürsprech|Oberst|Major|Hauptm\.?|Ing\.?|Arch\.?|dott\.?|avv\.?|Dott\.?|Avv\.?)$",
    re.IGNORECASE,
)
HOUSE_NO = re.compile(r"^(\d{1,4}\s?[a-hA-H]?)(\s*[-/]\s*\d{1,4}[a-h]?)?\.?$")
ABBR = re.compile(r"^[A-ZÄÖÜÉÈ][a-zäöüéèçë]{0,4}\.$|^[A-ZÄÖÜÉÈ]\.?$|^[A-ZÄÖÜ][a-z]?\.-[A-ZÄÖÜ][a-z]?\.$")
CONNECT = {"u.", "und", "et", "&", "e"}
STREET_WORD = re.compile(
    r"(strasse|straße|str\.|str\b|gasse|g\.$|weg\b|platz|pl\.|rain\b|vorstadt|vorst\.|graben|quai|"
    r"halde|steig|matte|allee|ring\b|^r\.|^rue\b|^av\.|^avenue\b|^bd\b|^boulev|^ch\.|^chemin\b|"
    r"^route\b|^rte\b|^via\b|^viale\b|^place\b|^quai\b|^q\.|^rampe|^cours\b|^promenade|^passage|"
    r"^sentier|^bourg\b|^petite rue|^grand'?rue|^corraterie|^molard|^fusterie|^piazza\b|^corso\b|^riva\b|"
    r"^vicolo\b|^contrada\b|^salita\b)",
    re.IGNORECASE,
)
STREET_ABBR = [
    (r"straße|strasse|\bstr\b\.?|str\.", "strasse"), (r"\bg\.$", "gasse"), (r"vorst\.", "vorstadt"),
    (r"^r\.\s*", "rue "), (r"^av\.\s*", "avenue "), (r"^bd\.?\s+", "boulevard "), (r"^pl\.\s*", "place "),
    (r"^ch\.\s*", "chemin "), (r"^rte\.?\s+", "route "), (r"^q\.\s*", "quai "),
]
NOT_GIVEN = {
    "frau", "mme", "mlle", "mlles", "mmes", "vve", "wwe", "witwe", "dr", "gebrüder", "geschwister", "familie",
    "söhne", "sohn", "schwestern", "fratelli", "brothers", "la", "le", "direktor", "direktion", "filiale",
    "wohnung", "derselbe", "dieselben", "tell", "herr", "cité", "famiglia", "flli", "eredi", "vedova", "sorelle", "coniugi", "conjugi", "ved", "fils", "père", "jun", "sen", "junior", "senior",
}
BUSINESS_WORD = re.compile(
    r"(erei|ung|amt|rat|gebäude|depot|institut|techniker|arzt|meister|händler|geschäft|handlung|"
    r"ität|schaft|haus|platz|gasse|berg|vorstadt|graben)$"
)
FORENAMES: set[str] = set()
SURNAMES: set[str] = set()      # Wörter, die allein als Namenszeile stehen: «Tami Fulgenzio» ist dann Name + Vorname
PAIR_MIN = 3                    # Vorname aus Namenspaaren: nach so vielen verschiedenen Familiennamen belegt
ONE_FIELD: set[str] = set()     # Bände, die Name und Vorname im selben Feld führen (Tessin, Neulesungen)
ONE_FIELD_SHARE = 0.3           # … erkannt daran, dass so viele Namenszeilen «Name Vorname» sind


def build_forenames(rows: list[dict]) -> set[str]:
    """Vornamenliste aus Adressbüchern und Telefonbüchern; schreibt data/ref/forenames.csv."""
    word = re.compile(r"^[A-ZÄÖÜÉÈ][a-zäöüéèàçë]+$")
    cap = r"[A-ZÄÖÜÉÈ][a-zäöüéèàçë]+"
    ab_rows = open_csv(NORM / "ab_entries.csv.gz")
    ab = Counter(t for r in ab_rows for t in re.findall(cap, r["forename"]))
    n2 = Counter(r["name2"] for r in rows if word.match(r["name2"]) and len(r["name1"].split()) == 1)
    n1 = Counter(r["name1"] for r in rows if word.match(r["name1"]))
    # Berufe und Geschäftsbezeichnungen, die in die Vornamenspalte gerutscht sind («Wirt»,
    # «Comestibles»): häufiger als Beruf im Adressbuch oder als Zusatz im Telefonbuch
    occ = Counter(t for r in ab_rows for t in re.findall(cap, r["occupation"]))
    sup = Counter(t for r in rows for t in re.findall(cap, r["supplement"]))
    # Bände, die Name und Vorname in einem Feld führen («Tami Fulgenzio», Tessin): das zweite Wort ist Vorname,
    # wenn es nach mehreren verschiedenen Familiennamen steht
    # Familienname: steht mindestens zweimal allein im Namensfeld, mit Vornamen oder Initiale im Feld daneben
    given = re.compile(rf"^(?:[A-ZÄÖÜÉÈ][a-zäöüéè]{{0,3}}\.\s?)+$|^{cap}$")
    sn = Counter(r["name1"] for r in rows if word.match(r["name1"]) and given.match(r["name2"])
                 and (r["name2"].endswith(".") or ab[r["name2"]] >= 2))
    SURNAMES.clear()
    SURNAMES.update(t for t, n in sn.items() if n >= 2 and not (FIRM.search(t) or AMT.search(t) or BUSINESS_WORD.search(t.lower())))
    firsts: dict = {}
    seconds: dict = {}
    for r in rows:
        m = re.fullmatch(rf"({cap}) ({cap})", r["name1"])
        if m:
            seconds.setdefault(m.group(1), set()).add(m.group(2))
            if m.group(1) in SURNAMES:
                firsts.setdefault(m.group(2), set()).add(m.group(1))
    pair = Counter({t: len(v) for t, v in firsts.items()})
    out = []
    for t in set(ab) | set(n2) | set(pair):
        if t.lower() in NOT_GIVEN or FIRM.search(t) or AMT.search(t) or t.lower() in CONT:
            continue
        seen = ab[t] + n2[t] + pair[t]
        if sup[t] >= 20 * seen or occ[t] > seen or (BUSINESS_WORD.search(t.lower()) and ab[t] < 5):
            continue
        if (ab[t] >= 2 or n2[t] >= 15 or pair[t] >= PAIR_MIN) and n1[t] < max(n2[t], ab[t], pair[t]):
            out.append({"forename": t, "adressbuch": ab[t], "telefonbuch": n2[t], "namenspaar": pair[t], "als_name": n1[t]})
    # … und umgekehrt: wer einmal mit bekanntem Vornamen steht («Uboldi Luigi»), ist Familienname
    known = {r["forename"] for r in out}
    SURNAMES.update(t for t, v in seconds.items() if v & known and t not in known
                    and not (FIRM.search(t) or AMT.search(t) or BUSINESS_WORD.search(t.lower())))
    out.sort(key=lambda r: (-(r["adressbuch"] + r["telefonbuch"]), r["forename"]))
    path = ROOT / "data" / "ref" / "forenames.csv"
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(out[0]), lineterminator="\n")
        w.writeheader()
        w.writerows(out)
    return {r["forename"] for r in out}


def street_key(s: str) -> str:
    s = s.strip().lower()
    for rx, rep in STREET_ABBR:
        s = re.sub(rx, rep, s)
    s = s.replace("ß", "ss").replace("'", " ")
    s = re.sub(r"\b(du|de|des|la|le|les|d)\b", " ", s)
    return " ".join(re.sub(r"[^a-z0-9äöüéèàç ]+", " ", s).split())


def segments(*parts: str) -> list[str]:
    out = []
    for p in parts:
        for seg in re.split(r",\s+|;\s*|\s+\(|\)\s*|\(", p or ""):
            seg = seg.strip(" ,;:()")
            if seg and seg != ".":
                out.append(seg)
    return out


def is_street(seg: str) -> bool:
    words = seg.split()
    if not words or len(words) > 6 or HOUSE_NO.match(seg):
        return False
    return bool(STREET_WORD.search(seg)) or bool(re.match(r"^[A-ZÄÖÜ][\w\-äöüé.]+\s+\d{1,4}[a-h]?\.?$", seg))


def _subseq(short: str, long: str) -> bool:
    it = iter(long)
    return all(c in it for c in short)


_ABBR_CACHE: dict[str, bool] = {}


def is_abbreviation(t: str) -> bool:
    """«A.», «C.-F.» immer; «Joh.», «Ls.», «Chs.» nur, wenn die Buchstaben in dieser Reihenfolge
    in einem Vornamen der Liste stehen (nicht «Rest.» für Restaurant)."""
    if not ABBR.match(t):
        return False
    stem = t.rstrip(".")
    if len(stem) <= 1 or "-" in stem:
        return True
    if stem not in _ABBR_CACHE:
        _ABBR_CACHE[stem] = any(f[0] == stem[0] and _subseq(stem[1:].lower(), f[1:].lower()) for f in FORENAMES)
    return _ABBR_CACHE[stem]


def is_given_token(t: str) -> bool:
    return is_abbreviation(t) or t.rstrip(".") in FORENAMES or t in CONNECT


def given_tokens(seg: str) -> bool:
    toks = re.sub(r"\.(?=[^\s\-])", ". ", seg).split()      # «A.-J.» bleibt ein Wort
    return bool(toks) and len(toks) <= 5 and all(is_given_token(t) for t in toks) and not all(t in CONNECT for t in toks)


LEADERS = re.compile(r"\.{4,}|(?:\s\.){2,}(?=\s|$)|…+")
LEAD_NO = re.compile(r"^\.?((?:\d[\d.,]*\s+)+)(?=[»«\"„“]?\s*[A-Za-zÀ-ÿ])")
ONLY_NO = re.compile(r"^[\d.,\s]+$")
PARTICLE = r"(?:[Dd]e la|[Dd]e|[Dd]u|[Vv]on|[Vv]an|[Dd]i|[Dd]ella|[Vv]\.)"
ONE_NAME = r"[A-ZÄÖÜÉÈ][\w'’äöüéèà]+"
# «Wyss-von Wattenwyl», «de Saussure», «Siegrist-Moll»: ein Familienname, auch mit Adelspartikel und Allianzname
HEAD = rf"((?:{PARTICLE}\s)?{ONE_NAME}(?:-(?:{PARTICLE}\s?)?{ONE_NAME})*)"


def unlead(v: str) -> str:
    """Führungspunkte weg; «J.. Bijoutier» und «I... combustibles»: der zweite Punkt trennt."""
    v = LEADERS.sub(" ", v)
    v = re.sub(r"\.{2,3}", ". ", v)
    return " ".join(v.split()).strip()


def repair(r: dict) -> list[str]:
    """Lesefehler in den Spalten der Quelle beheben (ändert `r`), gibt die Merker zurück.

    Eine Zahl vor dem Namen ist in den gesamtschweizerischen Bänden die zweite Hälfte der Rufnummer,
    wenn die Nummernspalte nur ein oder zwei Ziffern hat («64» + «16» → «64.16»); sonst Taxspalte.
    """
    flags = []
    raw = r["name1"]
    for col in ("name1", "name2", "supplement"):
        v = unlead(r[col])
        if v != r[col]:
            r[col] = "" if v == "." else v
            flags.append("fuehrungspunkte")
    m = LEAD_NO.match(r["name1"])
    if m:
        lead = m.group(1).split()
        if len(lead) == 1 and re.fullmatch(r"\d{2}", lead[0]) and re.fullmatch(r"\d{1,2}", r["phone"]):
            r["phone"] = f"{r['phone']}.{lead[0]}"
            flags.append("nummer-zusammengesetzt")
        else:
            flags.append("zahl-im-namen")
        r["name1"] = r["name1"][m.end():].lstrip("»« ").strip()
    if r["name1"] != raw:
        r["_name1_raw"] = raw                # der Namensabgleich der Orte (places.py) ist an der Quelle geeicht
    return list(dict.fromkeys(flags))


def strip_titles(seg: str) -> tuple[list[str], str]:
    toks = seg.split()
    titles = [t for t in toks if TITLE_RX.match(t)]
    return titles, " ".join(t for t in toks if not TITLE_RX.match(t))


def name_parts(name1: str, loose: bool = False) -> tuple[str, str, list[str], list[str]]:
    """Name, Vorname, Titel und Rest einer Namenszeile.

    «Comte. Jos.» → Comte, Jos.; «Beretta Stefano» → Beretta, Stefano; «Cattori dott. Leone» → Cattori, Leone,
    [dott.]; «Münzer. J.. Bijoutier», «Goldschmidt. Gustave. Riant Coteau» → Name, Vorname, Rest. Ohne
    erkennbaren Vornamen (oder Titel) bleibt die Zeile ganz: ("Zoologischer Garten", "", [], []).
    `loose` (Bände in ONE_FIELD): ein unbekanntes Wort nach bekanntem Familiennamen ist Vorname («Tami Fulgenzio»).
    """
    m = re.match(rf"^{HEAD}[.,]?\s+(.+)$", name1)
    if not m:
        return name1, "", [], []
    head, rest = m.group(1), m.group(2)
    titles, given = strip_titles(rest)
    if given_tokens(given) or (titles and not given):
        return head, given, titles, []
    if (loose and head in SURNAMES and re.fullmatch(ONE_NAME, given) and given not in SURNAMES and not titles
            and given.lower() not in NOT_GIVEN and not FIRM.search(given) and not AMT.search(given)):
        return head, given, titles, []                    # seltener Vorname nach bekanntem Familiennamen
    if re.match(rf"^{HEAD}\.\s", name1):
        parts = []
        for p in re.split(r"\.\s+", rest):
            if parts and re.search(r"(^|\s)[a-zäöüéè]{1,2}$", parts[-1]):   # «Conditorei u. Caféhalle», «r. du Stand»
                parts[-1] += ". " + p.strip()
            else:
                parts.append(p.strip())
        titles, given = strip_titles(parts[0] + ".")
        given = given.rstrip(".") + "." if given and not given.rstrip(".") in FORENAMES else given.rstrip(".")
        if (given and given_tokens(given)) or (titles and not given.strip(".")):
            return head, given.strip() if given.strip(".") else "", titles, [p for p in parts[1:] if p.strip(" .")]
    return name1, "", [], []


def split_name(name1: str) -> tuple[str, str]:
    """«Comte. Jos.» → ("Comte", "Jos."); «Beretta Stefano» → ("Beretta", "Stefano")."""
    head, given, titles, rest = name_parts(name1)
    return (head, given) if given and not rest else (name1, "")


def initials_of(given: str) -> str:
    return "".join(t[0] for t in re.split(r"[\s.\-]+", given) if t and t[0].isupper())


def continuation(name1: str) -> str | None:
    """«Wohnung. Nägelistr. 9», «Derselbe (Wohnung)»: zweite Zeile des Abonnenten; gibt den Rest zurück."""
    m = re.match(r"^([A-Za-zÀ-ÿ ]+?)(?:\.\s+|\s*\(|$)(.*)$", name1.strip(" ."))
    if not m or m.group(1).lower() not in CONT:
        return None
    first = re.split(r"\.\s+", m.group(2))[0].strip(" .")
    if first and given_tokens(first + "."):               # «Privat. Gaston» ist Herr Privat
        return None
    return m.group(2)


def entity_type(name1: str, loose: bool = False) -> str:
    if continuation(name1) is not None or ONLY_NO.match(name1):
        return "zusatz"
    head, given, titles, rest = name_parts(name1, loose)
    if rest:                       # «Rutishauser. W. Conditorei»: der Betrieb ist Zusatz, die Art folgt dem Namen
        name1 = f"{head} {given}"  # … samt Vornamenfeld: «Intern. A.-G. Aeberli» bleibt Firma
    if FIRM.search(name1):
        return "firma"
    if AMT.search(name1):
        return "amt"
    words = name1.split()
    if len(words) >= 2 and not (given or titles) and not re.fullmatch(HEAD, name1.rstrip(".")):
        # mehrere Wörter ohne Vornamen: Einrichtung («Zoologischer Garten»)
        return "firma"
    return "person"


def parse(r: dict) -> dict:
    flags: list[str] = list(r.get("_repair") or [])
    name1 = r["name1"].strip(" ,;")
    loose = r.get("refcode") in ONE_FIELD
    etype = entity_type(name1, loose)
    surname, from_name, name_titles, rest = name_parts(name1, loose) if etype == "person" else (name1, "", [], [])
    if from_name:
        flags.append("vorname-im-namen")
    if rest:
        flags.append("zusatz-im-namen")
    if etype == "zusatz":
        rest = [x for p in re.split(r"\.\s+", continuation(name1) or "") for x in segments(p)]
    segs = rest + segments(r["name2"], r["supplement"], r["street"])

    # Adresse von hinten: Strasse [+ Nummer als eigener Abschnitt]
    street_name = house_no = ""
    for i in range(len(segs) - 1, -1, -1):
        seg = segs[i]
        if HOUSE_NO.match(seg) and i > 0 and is_street(segs[i - 1]):
            street_name, house_no = segs[i - 1], seg
            del segs[i - 1: i + 1]
            break
        if is_street(seg):
            m = re.match(r"^(.*?)[\s,]+(\d{1,4}\s?[a-hA-H]?)\.?$", seg)
            street_name, house_no = (m.group(1), m.group(2)) if m else (seg, "")
            del segs[i]
            break
    if street_name and r["street"] and street_key(street_name) not in street_key(r["street"]):
        flags.append("strasse-umgestellt")
    elif r["street"] and not street_name:
        # Strassenspalte ohne Strassenwort (Hausname, Quartier): so übernehmen
        m = re.match(r"^(.*?)[\s,]+(\d{1,4}\s?[a-hA-H]?)\.?$", r["street"])
        street_name, house_no = (m.group(1), m.group(2)) if m else (r["street"], "")
        rest = set(segments(r["street"]))
        segs = [s for s in segs if s not in rest]

    titles = name_titles + [s for s in segs if TITLE_RX.match(s)]
    segs = [s for s in segs if not TITLE_RX.match(s)]
    given = from_name
    if etype == "person" and not given and segs and given_tokens(segs[0]):
        given = segs.pop(0)
    elif etype == "zusatz" and segs and given_tokens(segs[0]):
        given = segs.pop(0)
    occupation = "; ".join(s.rstrip(".") for s in segs)

    alliance = ""
    if etype == "person":
        m = re.fullmatch(rf"((?:{PARTICLE}\s)?{ONE_NAME})-((?:{PARTICLE}\s?)?{ONE_NAME})", surname)
        if m:
            surname, alliance = m.group(1), m.group(2)
        if name_titles:                                   # «Koch's Wwe.»
            surname = re.sub(r"['’]s$", "", surname)
    gtoks = re.sub(r"\.(?=\S)", ". ", given).split()
    forename = " ".join(t for t in gtoks if t in FORENAMES)
    return {
        "entity_type": etype,
        "parent_id": "",
        "surname": surname.strip(" .") if etype == "person" else "",
        "alliance_name": alliance,
        "forename": forename,
        "initials": initials_of(given),
        "title": " ".join(titles),
        "occupation": occupation,
        "street_name": street_name,
        "house_no": house_no.replace(" ", "").rstrip("."),
        "street_key": street_key(street_name) if street_name else "",
        "phone_norm": re.sub(r"\D", "", r["phone"]),
        "parse_flags": ";".join(flags),
    }


def parse_all(rows: list[dict]) -> Counter:
    FORENAMES.clear()
    FORENAMES.update(build_forenames(rows))            # füllt auch SURNAMES
    _ABBR_CACHE.clear()
    per: dict = {}
    for r in rows:
        c = per.setdefault(r["refcode"], [0, 0])
        c[0] += 1
        c[1] += bool(split_name(r["name1"])[1])
    ONE_FIELD.clear()
    ONE_FIELD.update(k for k, (n, g) in per.items() if g >= ONE_FIELD_SHARE * n)
    stats: Counter = Counter({"vornamenliste": len(FORENAMES), "bände mit name und vorname in einem feld": len(ONE_FIELD)})
    parent = {}
    for r in rows:
        p = parse(r)
        r.pop("_repair", None)
        r.update(p)
        if p["entity_type"] == "zusatz":
            r["parent_id"] = parent.get(r["refcode"], "")
        else:
            parent[r["refcode"]] = r["id"]
        stats[f"art {p['entity_type']}"] += 1
        stats["mit strasse"] += bool(p["street_name"])
        stats["mit hausnummer"] += bool(p["house_no"])
        stats["mit vorname/initiale"] += bool(p["initials"])
    return stats

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
    r"elektrizitätswerk|gaswerk|wasserwerk|sägerei|zeitung|journal\b|tagblatt|anzeiger)"
)
AMT = re.compile(
    r"(?i:station\b|b[uü]reau|polizei|schule\b|schulhaus|spital|hôpital|kaserne|zeughaus|verwaltung|"
    r"direktion|gericht|kanzlei|gemeinde|kanton|eidg|bahnhof|\bpost(bureau|ablage|amt|gebäude|halter|"
    r"büro)?\b|telegraph|telephon|zoll|pfarr|\bcure\b|mairie|\bcommune\b|feuerwehr|forsthaus|regierung|"
    r"bundes|stadthaus|rathaus|amtshaus|\bamt\b|departement|département|école|ecole|\bgare\b|douane|"
    r"sprechstation|anstalt|asyl|museum|bibliothek|kirche|friedhof|schlachthaus|abattoir)"
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
    r"Fürsprech|Oberst|Major|Hauptm\.?|Ing\.?|Arch\.?)$",
    re.IGNORECASE,
)
HOUSE_NO = re.compile(r"^(\d{1,4}\s?[a-hA-H]?)(\s*[-/]\s*\d{1,4}[a-h]?)?\.?$")
ABBR = re.compile(r"^[A-ZÄÖÜÉÈ][a-zäöüéèçë]{0,4}\.$|^[A-ZÄÖÜÉÈ]\.?$|^[A-ZÄÖÜ][a-z]?\.-[A-ZÄÖÜ][a-z]?\.$")
CONNECT = {"u.", "und", "et", "&", "e"}
STREET_WORD = re.compile(
    r"(strasse|straße|str\.|str\b|gasse|g\.$|weg\b|platz|pl\.|rain\b|vorstadt|vorst\.|graben|quai|"
    r"halde|steig|matte|allee|ring\b|^r\.|^rue\b|^av\.|^avenue\b|^bd\b|^boulev|^ch\.|^chemin\b|"
    r"^route\b|^rte\b|^via\b|^viale\b|^place\b|^quai\b|^q\.|^rampe|^cours\b|^promenade|^passage|"
    r"^sentier|^bourg\b|^petite rue|^grand'?rue|^corraterie|^molard|^fusterie)",
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
    "wohnung", "derselbe", "dieselben", "tell", "herr", "fils", "père", "jun", "sen", "junior", "senior",
}
FORENAMES: set[str] = set()


def build_forenames(rows: list[dict]) -> set[str]:
    """Vornamenliste aus Adressbüchern und Telefonbüchern; schreibt data/ref/forenames.csv."""
    word = re.compile(r"^[A-ZÄÖÜÉÈ][a-zäöüéèàçë]+$")
    ab = Counter(t for r in open_csv(NORM / "ab_entries.csv") for t in re.findall(r"[A-ZÄÖÜÉÈ][a-zäöüéèàçë]+", r["forename"]))
    n2 = Counter(r["name2"] for r in rows if word.match(r["name2"]) and len(r["name1"].split()) == 1)
    n1 = Counter(r["name1"] for r in rows if word.match(r["name1"]))
    out = []
    for t in set(ab) | set(n2):
        if t.lower() in NOT_GIVEN or FIRM.search(t) or AMT.search(t) or t.lower() in CONT:
            continue
        if (ab[t] >= 2 or n2[t] >= 15) and n1[t] < max(n2[t], ab[t]):
            out.append({"forename": t, "adressbuch": ab[t], "telefonbuch": n2[t], "als_name": n1[t]})
    out.sort(key=lambda r: -(r["adressbuch"] + r["telefonbuch"]))
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
    toks = re.sub(r"\.(?=\S)", ". ", seg).split()
    return bool(toks) and len(toks) <= 5 and all(is_given_token(t) for t in toks) and not all(t in CONNECT for t in toks)


def split_name(name1: str) -> tuple[str, str]:
    """«Comte. Jos.» → ("Comte", "Jos."); «Beretta Stefano» → ("Beretta", "Stefano")."""
    m = re.match(r"^([A-ZÄÖÜÉÈ][\w'\-äöüéèà]+)[.,]?\s+(.+)$", name1)
    if m and given_tokens(m.group(2)):
        return m.group(1), m.group(2)
    return name1, ""


def initials_of(given: str) -> str:
    return "".join(t[0] for t in re.split(r"[\s.\-]+", given) if t and t[0].isupper())


def entity_type(name1: str) -> str:
    low = name1.lower().strip(" .")
    if low in CONT:
        return "zusatz"
    if FIRM.search(name1):
        return "firma"
    if AMT.search(name1):
        return "amt"
    surname, given = split_name(name1)
    words = name1.split()
    if len(words) >= 2 and not given and not re.match(r"^[A-ZÄÖÜÉÈ][\w'äöüéè]+(-[A-ZÄÖÜÉÈ][\w'äöüéè]+)?$", name1):
        # mehrere Wörter ohne Vornamen: Einrichtung («Zoologischer Garten»)
        return "firma"
    return "person"


def parse(r: dict) -> dict:
    flags: list[str] = []
    name1 = r["name1"].strip(" ,;")
    etype = entity_type(name1)
    surname, from_name = (split_name(name1) if etype == "person" else (name1, ""))
    if from_name:
        flags.append("vorname-im-namen")
    segs = segments(r["name2"], r["supplement"], r["street"])

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

    titles = [s for s in segs if TITLE_RX.match(s)]
    segs = [s for s in segs if not TITLE_RX.match(s)]
    given = from_name
    if etype == "person" and not given and segs and given_tokens(segs[0]):
        given = segs.pop(0)
    elif etype == "zusatz" and segs and given_tokens(segs[0]):
        given = segs.pop(0)
    occupation = "; ".join(s.rstrip(".") for s in segs)

    alliance = ""
    if etype == "person":
        m = re.match(r"^([A-ZÄÖÜÉÈ][\wäöüéè']+)-([A-ZÄÖÜÉÈ][\wäöüéè']+)$", surname)
        if m:
            surname, alliance = m.group(1), m.group(2)
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
    FORENAMES.update(build_forenames(rows))
    _ABBR_CACHE.clear()
    stats: Counter = Counter({"vornamenliste": len(FORENAMES)})
    parent = {}
    for r in rows:
        p = parse(r)
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

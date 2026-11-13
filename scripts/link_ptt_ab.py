"""M2: Telefonbuch-Einträge mit Adressbuch-Einträgen derselben Stadt verknüpfen.

    python scripts/link_ptt_ab.py

Für jede Stadt mit Adressbuch und jeden Band: die Telefonbuch-Einträge der Gemeinde 1914
(Ort `hoch` oder `mittel`) werden nach Familienname (Firmen: Leitname) geblockt und gegen
die Einträge des Bandes verglichen. Einträge desselben Bandes, die dieselbe Person meinen
(Einwohner-, Berufs-, Gebäudeverzeichnis), bilden eine Gruppe; verknüpft wird nur, wenn
genau eine Gruppe am besten passt. Merkmale und Stufen: docs/verknuepfung.md.

Ausgabe: links/ptt_ab.csv (ein Paar je Zeile) und data/norm/link_stats.json.
"""

from __future__ import annotations

import json
import re
import sys
import unicodedata
from collections import Counter, defaultdict
from functools import lru_cache
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from common import NORM, ROOT, config, open_csv, write_csv  # noqa: E402
from parse_ptt import FIRM, street_key  # noqa: E402

LINKS = ROOT / "links"
LINK_FIELDS = [
    "ptt_id", "ab_id", "city", "ptt_year", "ab_volume", "year_gap", "tier", "score", "evidence",
    "ptt_name", "ab_name", "ptt_address", "ab_address",
]
TIERS = ("sicher", "wahrscheinlich", "möglich")

# Wörter, die vor oder in einem Vornamenfeld stehen, aber keine Vornamen sind
NOT_FORENAME = {
    "wwe", "witwe", "wb", "frau", "fräulein", "frl", "jgfr", "igfr", "jungfer", "hr", "herr", "dr",
    "prof", "mme", "mlle", "vve", "gebr", "gebruder", "gebrueder", "geschw", "geschwister", "sel",
    "sohn", "sohne", "soehne", "cie", "co", "comp", "und", "u", "et", "jun", "sen", "jgr", "ae", "jünger",
    "alt", "vater", "familie", "erben", "pfr", "med", "jur", "phil",
}
NAME_PARTICLES = {"von", "v", "de", "la", "le", "du", "van", "zum", "zur", "im", "in", "a", "di", "da"}
INITIAL_EQUIV = {"k": "c", "j": "i"}
# Konkordanz alter und neuer Hausnummern: eine Hausnummer zählt nur, wenn beide Seiten im
# selben System nummerieren. Aarau zählte bis zur Umnummerierung die Gebäude der ganzen
# Stadt durch (Nummern bis gegen 1400); eine neue Strassennummer ist kleiner.
OLD_GLOBAL = {"aarau": 150}


def nkey(s: str) -> str:
    """Namensschlüssel: ohne Akzente, gängige Schreibvarianten eingeebnet."""
    s = (s or "").lower().replace("ß", "ss")
    for a, b in (("ä", "ae"), ("ö", "oe"), ("ü", "ue")):
        s = s.replace(a, b)
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
    s = re.sub(r"[^a-z]", "", s)
    for a, b in (("ae", "a"), ("oe", "o"), ("ue", "u"), ("ss", "s"), ("ck", "k"), ("th", "t"),
                 ("y", "i"), ("dt", "t"), ("tz", "z"), ("ph", "f"), ("ff", "f"), ("ll", "l"),
                 ("mm", "m"), ("nn", "n"), ("rr", "r"), ("tt", "t")):
        s = s.replace(a, b)
    return s


# «Kramg.», «Bärenpl.»: abgekürzte Gasse und Platz (Adressbücher Bern, Basel); nicht -weg, -berg …
ABBR_GASSE = re.compile(r"(?<=[a-zäöü])(?<!we)(?<!ber)(?<!bur)(?<!stei)(?<!rin)(?<!ste)g\.?$")
ABBR_PLATZ = re.compile(r"(?<=[a-zäöü])pl\.?$")


def skey(street: str) -> str:
    """Strassenschlüssel, unempfindlich gegen Bindestriche, St./Sankt, -thor/-tor, «-g.» für -gasse."""
    street = (street or "").strip()
    street = ABBR_PLATZ.sub("platz", ABBR_GASSE.sub("gasse", street))
    k = street_key(street)
    k = re.sub(r"^(st|sankt|ste|saint)\s+", "", k)
    k = re.sub(r"^(im|in der|in|an der|am|auf der|auf dem|vor dem|beim|bei der|zum|zur)\s+", "", k)
    k = k.replace(" ", "")
    return nkey(k)


def num(no: str) -> str:
    return re.match(r"\d*", no).group()


def house(no: str) -> str:
    return re.sub(r"[^0-9a-z]", "", (no or "").lower())


# Vornamen in den Sprachformen der Bücher (Charles = Carl, Jules = Julius …)
VARIANTS = [
    "carl karl charles carlo", "ludwig louis luigi lodovico", "julius jules giulio",
    "johann johannes jean hans giovanni jan", "jakob jacob jacques giacomo", "georg george georges giorgio",
    "heinrich henri henry enrico", "wilhelm guillaume william guglielmo", "friedrich frederic fritz federico",
    "emil emile emilio", "august auguste augusto", "rudolf rudolph rodolphe rodolfo", "eduard edouard edoardo",
    "ernst ernest ernesto", "franz francois francesco", "josef joseph giuseppe", "peter pierre pietro",
    "paul paolo", "theodor theodore teodoro", "gustav gustave gustavo", "albert alberto", "alfred alfredo",
    "adolf adolphe adolfo", "eugen eugene eugenio", "leopold leopoldo", "konrad conrad corrado",
    "nikolaus nicolas niklaus nicola", "samuel samuele", "daniel daniele", "emanuel emmanuel manuel",
    "marie maria", "luise louise luisa", "elise elisa", "anna anne", "katharina catherine caterina",
]
CANON = {nkey(w).replace("k", "c"): line.split()[0] for line in VARIANTS for w in line.split()}


def _lexicon() -> set[str]:
    path = ROOT / "data" / "ref" / "forenames.csv"
    names = {r["forename"] for r in open_csv(path)} if path.exists() else set()
    return {nkey(n).replace("k", "c") for n in names} | set(CANON)


LEXICON = _lexicon()
# Einträge der Vornamenliste, die Anfang eines längeren Namens und selbst keine Sprachform
# sind, stehen für Abkürzungen ohne Punkt («Andr», «Rud», «Friedr»)
ABBREVIATED = {a for a in LEXICON if a not in CANON and len(a) <= 4
               and any(b != a and b.startswith(a) for b in LEXICON)} - {
    "oto", "max", "ida", "ema", "rosa", "lina", "elsa", "olga", "hans", "jean", "anna", "marc", "beat",
    "fanie", "emi", "lili", "mina", "nina", "dora", "bertha", "berta", "jos"}

DOUBLE_NAME = re.compile(r"^[A-ZÄÖÜ][\wäöüéè']+-[A-ZÄÖÜ][\wäöüéè']+$")
WIDOW = re.compile(r"\b(Wwe|Witwe|Wittwe|Wb|Vve|Veuve|Ved)\b\.?")


def fkey(word: str) -> str:
    """Vornamenschlüssel: Namensschlüssel mit k = c, Sprachformen zusammengeführt."""
    k = nkey(word).replace("k", "c")
    return nkey(CANON[k]).replace("k", "c") if k in CANON else k


def forename_tokens(s: str) -> list[tuple[str, bool]]:
    """[(Schlüssel, abgekürzt?)] der Vornamen eines Feldes; Titel, Floskeln und der
    Geburtsname nach «geb.» fallen weg."""
    out, skip = [], False
    for raw in re.findall(r"[A-Za-zÀ-ÿ]+\.?", s or ""):
        bare = raw.rstrip(".")
        if skip:
            skip = False
            continue
        if bare.lower() in ("geb", "geborne", "geborene", "née", "nee"):
            skip = True
            continue
        k = nkey(bare)
        if not k or k in NOT_FORENAME or bare.lower() in NOT_FORENAME or not bare[:1].isupper():
            continue
        kc = k.replace("k", "c")
        known = kc in LEXICON and kc not in ABBREVIATED
        short = (raw.endswith(".") and len(bare) <= 7) or len(bare) <= 3 or (not known and len(bare) <= 6)
        if not short and not known:
            continue  # Beruf oder Zusatz im Vornamenfeld («Julius. Weinhandlung»)
        out.append((k.replace("k", "c") if short else fkey(bare), short))
    return out


def initial(k: str) -> str:
    c = k[:1]
    return INITIAL_EQUIV.get(c, c)


def _subseq(short: str, long: str) -> bool:
    """«hch» in «heinrich», «friedr» in «friedrich»: gleicher Anfang, Buchstaben in Folge."""
    if not short or not long or short[0] != long[0]:
        return False
    it = iter(long)
    return all(c in it for c in short)


def token_match(a: tuple[str, bool], b: tuple[str, bool]) -> str:
    """Vergleich zweier Vornamen: `gleich`, `abkürzung`, `initiale` oder ''."""
    (ka, sa), (kb, sb) = a, b
    if len(ka) == 1 or len(kb) == 1:
        ia, ib = (INITIAL_EQUIV.get(ka[0], ka[0]), INITIAL_EQUIV.get(kb[0], kb[0]))
        return "initiale" if ia == ib else ""
    if not sa and not sb:
        if ka == kb or (min(len(ka), len(kb)) >= 4 and (ka + "e" == kb or kb + "e" == ka)):
            return "gleich"
        return ""
    if sa and sb:
        # zwei Abkürzungen: die kürzere muss der Anfang der längeren sein (Fr./Friedr., nicht Ad./Andr.)
        return "initiale" if ka.startswith(kb) or kb.startswith(ka) else ""
    short, full = (ka, kb) if sa else (kb, ka)
    forms = {full} | {w for w in CANON if nkey(CANON[w]).replace("k", "c") == full}
    # Abkürzung = Anfang des Namens (Friedr., Jos.); Zusammenziehung nur aus Konsonanten
    # (Hch., Gg., Chs.) = Buchstaben in Folge
    contraction = short[0] not in "aeiou" and not re.search(r"[aeiou]", short[1:])
    if any(f.startswith(short) or (contraction and _subseq(short, f)) for f in forms):
        return "abkürzung" if len(short) >= 3 else "initiale"
    return ""


RANK = {"gleich": 3, "abkürzung": 2, "initiale": 1, "": 0}


def compare_forenames(ptt: list[tuple[str, bool]], ab: list[tuple[str, bool]]) -> str:
    return _compare(tuple(ptt), tuple(ab))


@lru_cache(maxsize=None)
def _compare(ptt: tuple, ab: tuple) -> str:
    """`gleich`, `abkürzung`, `initiale`, `widerspruch` oder '' (eine Seite ohne Vornamen).
    Ein späterer Vorname kann der Rufname sein: es genügt ein passendes Paar."""
    if not ab or not ptt:
        return ""
    best = max((token_match(x, y) for x in ptt for y in ab), key=RANK.get)
    return best or "widerspruch"


def stems(s: str) -> set[str]:
    return {nkey(w)[:5] for w in re.findall(r"[A-Za-zÀ-ÿ]{5,}", s or "")} - {"privat", "priva"}


def firm_key(name: str) -> str:
    """Leitname einer Firma: erstes Namenswort, ohne Partikel («von Speyr & Co.» → speyr)."""
    for w in re.findall(r"[A-Za-zÀ-ÿ]+", name or ""):
        k = nkey(w)
        if k and w.lower() not in NAME_PARTICLES and len(k) >= 2:
            return k
    return ""


# ── Adressbuch ────────────────────────────────────────────────────────────

def ab_index(entries: list[dict]) -> dict:
    """{(Gemeinde, Band): {Namensschlüssel: [Eintrag]}} mit vorbereiteten Merkmalen."""
    idx: dict = defaultdict(lambda: defaultdict(list))
    for r in entries:
        sk = nkey(r["surname"])
        if not sk:
            continue
        r["_sk"], r["_ak"] = sk, nkey(r["alliance_name"])
        r["_mk"] = nkey(r["maiden_name"])
        r["_st"], r["_no"] = skey(r["street"]), house(r["building_no"])
        r["_occ"] = stems(r["occupation"])
        r["_firm"] = r["entry_type"] == "firma" or bool(FIRM.search(f"{r['surname']} {r['forename']}"))
        r["_fn"] = forename_tokens(r["forename"])
        r["_widow"] = bool(WIDOW.search(r["text"]))
        r["_group"] = (sk, r["_ak"], initial(r["_fn"][0][0]) if r["_fn"] else "")
        # nur unter dem Familiennamen: der Allianzname ist der Name der Ehefrau (bzw. des
        # Ehemanns) und gehört zu einer anderen Familie
        idx[(r["municipality"], r["volume"])][sk].append(r)
        # Firmen auch unter ihrem Leitnamen («Jenny & Weigel» → jenny)
        fk = firm_key(r["surname"]) if r["_firm"] else ""
        if fk and fk != sk:
            idx[(r["municipality"], r["volume"])][fk].append(r)
    return idx


def building(city: str, a: str, b: str) -> bool:
    """Gleiche Gebäudenummer im alten, stadtweiten System (nur wo die Stadt eines kannte)."""
    lim = OLD_GLOBAL.get(city)
    return bool(lim and a and a == b and int(num(a) or 0) > lim)


def same_numbering(city: str, a: str, b: str) -> bool:
    lim = OLD_GLOBAL.get(city)
    if not lim:
        return True
    na, nb = int(num(a) or 0), int(num(b) or 0)
    return (na > lim) == (nb > lim)


# ── Vergleich ─────────────────────────────────────────────────────────────

# Leitwörter, die viele verschiedene Firmen teilen («Schweizerische Depeschenagentur» ≠
# «Schweizerische Möbelindustrie», «Café Turm» ≠ «Café du Théâtre»): nur mit gleicher Strasse
GENERIC_FIRM = {nkey(w) for w in (
    "schweizerische", "schweizerischer", "schweizer", "eidg", "eidgenössische", "kantonale", "kantonal",
    "bernische", "basler", "aargauische", "allgemeine", "café", "cafe", "hotel", "hôtel", "restaurant",
    "gasthof", "gasthaus", "pension", "bank", "banque", "société", "compagnie", "caisse", "union",
    "internationale", "neue", "erste", "grand", "grande", "la", "le", "les", "zum", "zur", "aux", "au",
    "bureau", "büreau", "gesellschaft", "verein", "comptoir", "direktion", "verwaltung", "agentur",
    "magasin", "maison", "atelier", "fabrik", "fabrique", "depot", "dépôt", "konsum", "volks")}


def score(p: dict, c: dict, city: str) -> tuple[int, list[str]] | None:
    """Punkte und Belege eines Kandidaten, None bei Widerspruch."""
    ev, s = [], 0
    if p["_firm"] and p["_sk"] in GENERIC_FIRM and not (p["_st"] and p["_st"] == c["_st"]):
        return None
    if p["_firm"]:
        if c["_firm"]:
            s += 2
            ev.append("firma")
        else:
            fn = compare_forenames(p["_fn"], c["_fn"])
            if fn == "widerspruch":
                return None
            if fn:
                s += 2
                ev.append(f"vorname:{fn}")
            ev.append("firma-person")
    else:
        fn = compare_forenames(p["_fn"], c["_fn"])
        if fn == "widerspruch":
            return None
        if p["_widow"] and not c["_widow"]:
            return None  # die Witwe, nicht ihr verstorbener Mann
        s += {"gleich": 4, "abkürzung": 3, "initiale": 2, "": 0}[fn]
        if fn:
            ev.append(f"vorname:{fn}")
        if p["_ak"] and c["_ak"]:
            if p["_ak"] == c["_ak"]:
                s += 3
                ev.append("allianzname")
            else:
                return None  # andere Ehe
        if c["_firm"] and not p["_firm"]:
            s -= 1
    if building(city, p["_no"], c["_no"]):
        # alte, über die ganze Stadt laufende Gebäudenummer: bezeichnet das Haus allein
        s += 6
        ev += ["strasse", "hausnummer"] if p["_st"] == c["_st"] else ["gebäudenummer"]
    elif p["_st"] and c["_st"] and p["_st"] == c["_st"]:
        s += 3
        ev.append("strasse")
        if p["_no"] and c["_no"] and same_numbering(city, p["_no"], c["_no"]):
            if p["_no"] == c["_no"]:
                s += 3
                ev.append("hausnummer")
            elif num(p["_no"]) and num(c["_no"]) and num(p["_no"]) != num(c["_no"]):
                s -= 1
    if p["_occ"] & c["_occ"]:
        s += 1
        ev.append("beruf")
    if c["phone_flag"] == "1":
        s += 1
        ev.append("telefonzeichen")
    return s, ev


# Mehr verschiedene Personen dieses Namens im Band: Initiale und Telefonzeichen allein tragen
# nichts mehr (Bern 1900: «Müller, R.» mit ☎ ist nicht «Müller-Berger, Frau R.»)
COMMON_SURNAME = 5


def tier_for(ev: list[str], groups_at_top: int, n_surname: int, gap: int) -> str:
    """Stufe aus den Belegen. Über eine halbe Generation (mehr als 15 Jahre) braucht es
    einen ausgeschriebenen Vornamen oder die Hausnummer, über eine ganze (mehr als 30)
    zusätzlich die gleiche Adresse: Sohn und Nachfolger tragen oft Name und Geschäft weiter."""
    if groups_at_top != 1:
        return ""
    fn = next((e.split(":")[1] for e in ev if e.startswith("vorname:")), "")
    street = "strasse" in ev or "gebäudenummer" in ev
    number = "hausnummer" in ev or "gebäudenummer" in ev
    strong_fn = fn in ("gleich", "abkürzung")
    firm = "firma" in ev
    if "firma-person" in ev:
        # Firma gegen den Inhaber: Vorname aus der Firma oder gleiches Haus und Geschäft
        if gap > 15 or not (street and (fn or number or "beruf" in ev)):
            return ""
        return "wahrscheinlich" if fn and number else "möglich"
    if (fn and street) or (firm and street) or (strong_fn and "allianzname" in ev):
        t = 0
    elif strong_fn or (fn and ("beruf" in ev or "allianzname" in ev)) \
            or (fn and "telefonzeichen" in ev and n_surname <= COMMON_SURNAME) \
            or number or (firm and n_surname == 1):
        t = 1
    elif street or "allianzname" in ev or (n_surname == 1 and (fn or gap <= 10)):
        t = 2
    else:
        return ""
    if gap > 15 and not (fn or "allianzname" in ev or firm):
        return ""  # nach 15 Jahren trägt die Adresse allein nicht
    if gap > 15:
        if strong_fn and (street or "allianzname" in ev or "beruf" in ev) or (fn and number) or (firm and number):
            t = max(t, 1)
        else:
            t = 2
    if gap > 30:
        if not (street and fn):
            return ""
        t = 2
    return TIERS[t]


def ptt_forenames(r: dict) -> list[tuple[str, bool]]:
    """Vornamen des Telefonbuch-Eintrags: wie gedruckt (Spalte 2), wenn die Zerlegung sie
    dort gefunden hat, sonst ausgeschriebene Vornamen und Initialen der Zerlegung."""
    printed = forename_tokens(r["name2"])
    if printed:
        return printed
    out = [(fkey(w), False) for w in r["forename"].split()]
    out += [(c.lower(), True) for c in r["initials"] if c.isalpha()][len(out):]
    if not out and re.search(r"\bFr\.", r["title"]):
        out = [("f", True)]  # «Fr.» ohne weiteren Vornamen: Friedrich, nicht Frau
    return out


def prepare_ptt(r: dict) -> dict | None:
    if r["entity_type"] == "person":
        sk = nkey(r["surname"])
        r["_firm"] = False
    elif r["entity_type"] == "firma" and DOUBLE_NAME.match(r["name1"]) \
            and not re.search(r"&|\b(Co|Cie|AG|Gebr|Söhne|Frères)\b", r["name1"] + " " + r["name2"]):
        # «Preiswerk-Groben»: Familien- und Allianzname, als Firma gelesen
        sk, alliance = (nkey(x) for x in r["name1"].split("-", 1))
        r["_firm"] = False
        r["alliance_name"] = r["name1"].split("-", 1)[1]
    elif r["entity_type"] == "firma":
        sk = firm_key(r["name1"])
        r["_firm"] = True
    else:
        return None
    if not sk or len(sk) < 2 or sk == nkey(r["municipality_1914"]):
        return None  # Preiszeilen der Bände («Aarau | 75 Cts.»)
    r["_sk"], r["_ak"] = sk, nkey(r["alliance_name"])
    r["_fn"] = ptt_forenames(r) if not r["_firm"] else forename_tokens(
        " ".join(re.findall(r"\b[A-ZÄÖÜ][a-zäöü]{0,4}\.", r["name1"] + " " + r["name2"])))
    r["_widow"] = bool(WIDOW.search(" ".join((r["name2"], r["supplement"], r["title"]))))
    r["_st"], r["_no"] = skey(r["street_name"]), house(r["house_no"])
    r["_occ"] = stems(r["occupation"])
    return r


def same_person(a: dict, b: dict) -> bool:
    """Zwei Einträge desselben Bandes meinen dieselbe Person (Einwohner-, Berufs-,
    Gebäudeverzeichnis): gleicher Vornamen-Anfang, Allianzname gleich oder fehlend,
    Hausnummer gleich oder fehlend, und mindestens Vorname oder Hausnummer vorhanden."""
    fa, fb = a["_group"][2], b["_group"][2]
    if fa and fb and compare_forenames(a["_fn"], b["_fn"]) == "widerspruch":
        return False
    if a["_ak"] and b["_ak"] and a["_ak"] != b["_ak"]:
        return False
    if a["_no"] and b["_no"] and num(a["_no"]) != num(b["_no"]):
        return False
    return bool((fa and fb) or (a["_no"] and b["_no"]))


def same_house_or_name(a: dict, b: dict) -> bool:
    """Weiterer Eintrag derselben Person im Band nur bei gleicher Strasse oder Hausnummer oder
    gleichem ausgeschriebenem Vornamen: in Bern teilen viele «J. Gerber» Initiale und Namen."""
    if a["_st"] and a["_st"] == b["_st"]:
        return True
    if a["_no"] and b["_no"] and num(a["_no"]) == num(b["_no"]):
        return True
    full = lambda r: [k for k, initial in r["_fn"] if not initial]
    return bool(full(a)) and full(a) == full(b)


def persons(rows: list[dict]) -> int:
    """Anzahl verschiedener Personen unter Einträgen gleichen Namens (verkettend gebündelt)."""
    parent = list(range(len(rows)))

    def find(i: int) -> int:
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i
    for i in range(len(rows)):
        for j in range(i + 1, len(rows)):
            if same_person(rows[i], rows[j]):
                parent[find(i)] = find(j)
    return len({find(i) for i in range(len(rows))})


def link_city(city: dict, ptt: list[dict], idx: dict, volumes: dict[str, list[str]]) -> tuple[list[dict], Counter]:
    """volumes: Bände je Gemeinde; ein Telefonbucheintrag sucht nur in den Bänden seiner Gemeinde."""
    out, stats = [], Counter()
    surname_persons: dict = {}
    for p in ptt:
        muni = p["municipality_1914"]
        for vol in volumes.get(muni, []):
            cands = idx[(muni, vol)].get(p["_sk"], [])
            if not cands:
                stats["kein-name"] += 1
                continue
            scored = []
            for c in cands:
                res = score(p, c, city["id"])
                if res:
                    scored.append((res[0], res[1], c))
            if not scored:
                stats["widerspruch"] += 1
                continue
            top = max(s for s, _, _ in scored)
            best = [(s, ev, c) for s, ev, c in scored if s == top]
            n_groups = persons([c for _, _, c in best])
            key = (muni, vol, p["_sk"])
            if key not in surname_persons:
                surname_persons[key] = persons(cands)
            n_surname = surname_persons[key]
            gap = abs(int(p["year"]) - int(vol))
            t = tier_for(best[0][1], n_groups, n_surname, gap)
            if not t:
                stats["mehrdeutig" if n_groups > 1 else "zu-schwach"] += 1
                continue
            stats[t] += 1
            # alle Einträge der gefundenen Person in diesem Band (Einwohner-, Berufs-,
            # Gebäudeverzeichnis), nicht nur der mit den meisten Punkten
            ids = {c["id"] for _, _, c in best}
            top_c = best[0][2]
            best += [(sc, ev + ["zusatz"], c) for sc, ev, c in scored
                     if c["id"] not in ids and same_person(c, top_c) and same_house_or_name(c, top_c)]
            for s, ev, c in best:
                out.append({
                    "ptt_id": p["id"], "ab_id": c["id"], "city": city["id"], "ptt_year": p["year"],
                    "ab_volume": vol, "year_gap": gap, "tier": t, "score": s, "evidence": ";".join(ev),
                    "ptt_name": ", ".join(x for x in (p["name1"], p["name2"], p["supplement"]) if x),
                    "ab_name": ", ".join(x for x in (c["surname"] + (f"-{c['alliance_name']}" if c["alliance_name"] else ""),
                                                     c["forename"], c["occupation"]) if x),
                    "ptt_address": p["street"], "ab_address": f"{c['street']} {c['building_no']}".strip(),
                })
    return out, stats


def main() -> None:
    cfg = config()
    entries = open_csv(NORM / "ab_entries.csv")
    idx = ab_index(entries)
    volumes: dict = defaultdict(lambda: defaultdict(set))  # Stadt → Gemeinde → Bände
    city_of = {}
    for r in entries:
        volumes[r["city"]][r["municipality"]].add(r["volume"])
        city_of[r["municipality"]] = r["city"]
    cities = {c["id"]: c for c in cfg["city"]}
    by_city = defaultdict(list)
    for r in open_csv(NORM / "ptt_entries.csv.gz"):
        c = cities.get(city_of.get(r["municipality_1914"], ""))
        if c and r["place_confidence"] in ("hoch", "mittel") and prepare_ptt(r):
            by_city[c["id"]].append(r)
    links, report = [], {}
    for c in cfg["city"]:
        ptt = by_city[c["id"]]
        rows, stats = link_city(c, ptt, idx, {m: sorted(v) for m, v in volumes[c["id"]].items()})
        links += rows
        linked = {r["ptt_id"] for r in rows}
        report[c["id"]] = {
            "ptt_entries": len(ptt), "ptt_linked": len(linked), "pairs": len(rows),
            "decisions": dict(stats),
            "by_tier": dict(Counter(r["tier"] for r in rows)),
        }
        print(f"{c['id']}: {len(ptt)} Telefonbuch-Einträge, {len(linked)} verknüpft, {len(rows)} Paare", dict(stats))
    links.sort(key=lambda r: (r["city"], r["ptt_id"], r["ab_volume"], r["ab_id"]))
    write_csv(LINKS / "ptt_ab.csv", LINK_FIELDS, links)
    (NORM / "link_stats.json").write_text(json.dumps(report, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()

"""M7: unscharfer Namensvergleich für die Suche (gleich gerechnet in site/assets/pages.js).

Zwei Stufen:
1. **Namensschlüssel** `fkey()`: ohne Akzente (œ = oe, æ = ae), dann die Schreibvarianten aus
   M2 eingeebnet (y/i, ss/ß, th/t, ck/k, dt/t, tz/z, ph/f, Doppelkonsonanten, ä/ae).
   Meyer = Meier, Bürgi = Bürgy, Schmidt ≈ Schmid (Distanz 1).
2. **Gewichtete Damerau-Levenshtein-Distanz** `dist()` auf dem Schlüssel: Einfügen,
   Löschen, Ersetzen und Vertauschen kosten 1; typische Verwechslungen der Texterkennung
   kosten 0,5 (`OCR_PAIRS`), «ii» und «rn» werden vorher als «u» und «m» gelesen.

Die Schwelle hängt von der Länge des Schlüssels ab (`threshold()`); gemessen in
docs/suche.md.
"""

from __future__ import annotations

import re
import unicodedata

OCR_PAIRS = {frozenset(p) for p in (
    "bh", "hn", "ce", "il", "lt", "ft", "nu", "ao", "eo", "un", "cg", "bp", "do", "mn", "rn", "ij", "kh", "ec",
    "gc", "hk", "ei", "lr", "fl", "fs",
)}


def fkey(s: str) -> str:
    """Namensschlüssel für die unscharfe Suche."""
    s = (s or "").lower().replace("ß", "ss").replace("œ", "oe").replace("æ", "ae")
    for a, b in (("ä", "ae"), ("ö", "oe"), ("ü", "ue")):
        s = s.replace(a, b)
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
    s = re.sub(r"[^a-z]", "", s)
    for a, b in (("ae", "a"), ("oe", "o"), ("ue", "u"), ("ss", "s"), ("ck", "k"), ("th", "t"),
                 ("y", "i"), ("dt", "t"), ("tz", "z"), ("ph", "f"), ("ff", "f"), ("ll", "l"),
                 ("mm", "m"), ("nn", "n"), ("rr", "r"), ("tt", "t")):
        s = s.replace(a, b)
    return s


def ocr(s: str) -> str:
    return s.replace("ii", "u").replace("rn", "m")


def dist(a: str, b: str, cap: float = 3.0) -> float:
    """Gewichtete Damerau-Levenshtein-Distanz zweier Schlüssel (abgebrochen über `cap`)."""
    a, b = ocr(a), ocr(b)
    if abs(len(a) - len(b)) > cap:
        return cap + 1
    prev2, prev = None, list(range(len(b) + 1))
    for i in range(1, len(a) + 1):
        cur = [float(i)] + [0.0] * len(b)
        for j in range(1, len(b) + 1):
            x, y = a[i - 1], b[j - 1]
            sub = 0 if x == y else (0.5 if frozenset((x, y)) in OCR_PAIRS else 1)
            cur[j] = min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + sub)
            if prev2 is not None and i > 1 and j > 1 and x == b[j - 2] and a[i - 2] == y:
                cur[j] = min(cur[j], prev2[j - 2] + 1)
        if min(cur) > cap:
            return cap + 1
        prev2, prev = prev, cur
    return prev[-1]


def threshold(key: str, level: str = "normal") -> float:
    """Erlaubte Distanz nach Länge des Schlüssels."""
    n = len(key)
    table = {"eng": ((4, 0.5), (7, 1.0), (99, 1.5)), "normal": ((3, 0.5), (6, 1.0), (99, 2.0))}[level]
    return next(t for limit, t in table if n <= limit)


def key_of_label(label: str, kind: str) -> str:
    """Namensschlüssel einer Zeile des Suchindex (wie keyOfLabel() in pages.js): Personen
    «Familienname-Allianzname, Vorname» → Familienname; Firmen → erstes Wort ohne Partikel."""
    label = re.sub(r"^(von|v\.|de|du|la|le|van|zum|zur)\s+", "", (label or "").strip(), flags=re.I)
    word = label.split(",")[0].split("-")[0] if kind == "p" else (label.split() or [""])[0]
    return fkey(word)

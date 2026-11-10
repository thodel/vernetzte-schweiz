"""Berufsklassen für Einheiten (M6): Schlüsselwörter über Beruf, Zusatz und Firmennamen.

Die Telefonbücher geben den Beruf als freien Text, deutsch, französisch, italienisch,
abgekürzt und oft mit dem Geschäft statt dem Beruf («Metzgerei», «Hôtel du Lac»). Die
Klassen sind grob und für Karten gedacht, nicht für Sozialgeschichte im Einzelnen. Die
erste passende Klasse in der Reihenfolge von CLASSES gewinnt; ohne Treffer bleibt die
Klasse leer. Gemessen in docs/karten.md.
"""

from __future__ import annotations

import re

CLASSES: list[tuple[str, str, str]] = [
    # (Schlüssel, Bezeichnung, Muster); Reihenfolge = Vorrang
    ("medizin", "Medizin und Apotheken",
     r"\barzt|ärzt|\bdr\.? ?m[ée]d|krankenhaus|médecin|medecin|docteur|chirurg|zahnarzt|dentist|tierarzt|vétérinaire|veterinär"
     r"|apothek|pharmac|ocul|augenarzt|drogerie|droguerie|spital|klinik|clinique|hebamme|sage-femme|krankenpfleg|masseu"),
    ("gast", "Gastgewerbe",
     r"hotel|hôtel|gasthof|gasthaus|wirtschaft|\bwirt\b|wirtin|restaurant|café|cafe\b|pension|brasserie|auberge"
     r"|albergo|osteria|trattoria|pinte|\brest\.|\b(z\.?|zum|zur) ?(löwen|rössli|ochsen|kreuz|sternen|bären|adler|hirschen|krone|engel|schwanen|rebstock|traube|linde|hecht|falken|frohsinn|post|bahnhof|sonne|hirsch|leuen)|kurhaus|bad\b|erholungs"),
    ("bank", "Bank und Versicherung",
     r"\bbank|banque|banquier|bankier|kantonalbank|sparkasse|leihkasse|kreditanstalt|versicherung|assurance|assicuraz"),
    ("recht", "Recht und Verwaltung",
     r"notar|notaire|advokat|avocat|fürsprech|rechtsanw|patentanw|jurist|gericht|richter|juge|amt\b|ämter|kanzlei|chancellerie"
     r"|gemeinde|commun|sekretariat|secrétariat|polizei|police|gendarm|regierung|staatskanzl|staatskasse|bundes|fédéral|eidg|verwaltung|administration"
     r"|betreibung|grundbuch|zoll|douane|stadtrat|präsident|weibel|einnehmer|feuerwehr|major|oberst|hauptmann"
     r"|militär|militaire|kaserne|caserne|zeughaus|arsenal|artill|infanter"),
    ("verkehr", "Post, Bahn und Transport",
     r"\bpost\b|postbureau|postfiliale|bureau des postes|telegraph|télégraph|telephon|bahnhof|\bgare\b|s\.? ?b\.? ?b"
     r"|güterexpedition|eisenbahn|tramway|strassenbahn|fuhrhalter|fuhrhalterei|voiturier|camionn|spedition|speditor"
     r"|transport|navigation|schiff|garage|automobil|taxi|dampfschiff|lohnkutsch|bahnw|bahnv|stationsvorst|chef de gare"),
    ("uhren", "Uhren",
     r"horlog|uhren|uhrmach|montres|\bboîtes\b|boites|cadrans|pierristes|assortiments|échappements|spiraux"),
    ("textil", "Textil und Stickerei",
     r"stick|broderie|weberei|tissage|spinnerei|filature|posament|seide|soie|tuch|zwirn|färberei|teinturerie"
     r"|bleicherei|ferggerei|textil|bonneterie|tricot|bandfabr|rubans"),
    ("lebensmittel", "Lebensmittel und Getränke",
     r"metzg|boucher|charcut|bäck|backer|boulang|konditor|confiseur|confiserie|pâtiss|comestibles|spezerei|épicer"
     r"|kolonialw|lebensmittel|milch|lait|molkerei|laiterie|käse|fromag|wein|\bvins?\b|eaux|bier|brauerei|brasserie|mühle|moulin|müller\b"
     r"|schokolad|chocolat|zucker|teigwaren|konserven|honig|mineralwasser|liqueur|spirituosen"),
    ("bau", "Bau und Architektur",
     r"baumeister|baugeschäft|bauunternehm|entrepreneur|architekt|architecte|ingenieur|ingénieur|\bentrepr|zimmerm|zimmerei"
     r"|\bing\b|bauführer|schreiner|menuisier|maler|peintre|gipser|gypser|plâtrier|spengler|ferblant|dachdeck|steinhauer|marbrier"
     r"|ziegelei|tuilerie|zement|ciment|holzhandl|sägerei|scierie|installat|sanitär|hafner|ofenbau"),
    ("industrie", "Industrie und Fabriken",
     r"fabri|fabrik|\bfabr\b|usine|\bwerke?\b|werkstätte|giesserei|fonderie|maschinen|machines|mechan|mécan|elektri|électri"
     r"|electri|chemisch|chimique|\ba\.?-?g\.?(?![a-zäöü])|société anonyme|unternehmer|\bs\.? ?a\.?\b|aktiengesellschaft|gaswerk|wasserwerk|kraftwerk"),
    ("druck", "Druck, Presse und Fotografie",
     r"druckerei|imprimerie|buchdruck|lithograph|redaktion|rédaction|zeitung|journal|verlag|éditeur|editeur|buchhandl"
     r"|librairie|buchbind|buchh|papeter|photograph|photographe|fotograf|\bphot\b|xylogr|clich"),
    ("bildung", "Bildung, Kirche und Kultur",
     r"lehrer|instituteur|professeur|\bprof\b|prof\.|schule|école|ecole|gymnas|seminar|institut|pfarr|pasteur|curé"
     r"|kirche|église|kloster|mission|anstalt|vorsteher|musik|musique|theater|théâtre|museum|bibliothek|künstler|bildhauer|sculpteur"),
    ("handwerk", "Handwerk",
     r"schneider|tailleur|couturi|modiste|schuhmach|cordonn|sattler|sellier|tapezier|tapissier|coiffeur|friseur"
     r"|schlosser|serrurier|schmied|maréchal|wagner|charron|küfer|tonnelier|glaser|vitrier|drechsler|goldschmied"
     r"|bijout|orfèvre|optiker|opticien|kaminfeger|ramoneur|gärtner|jardinier|horticult|blumen|näherin|lingère|repasseuse"
     r"|wäscher|glätter|blanchiss|doreur|vergolder"),
    ("handel", "Handel und Agenturen",
     r"kaufm|négociant|negociant|commerçant|marchand|handlung|handel|magasin|magazin|laden|bazar|agent|agence|vertret"
     r"|représent|commis|import|export|en gros|grosshandl|eisenwaren|quincaill|mercerie|cigarren|tabac|konsum|consomm"
     r"|kaufhaus|manufaktur|commerce|kiosk|kiosque|ventes|chiffons|lumpen|depot|dépôt|schuhwaren|chaussures|genossenschaft|coopérative"),
    ("privat", "Privat und Rentner",
     r"privat|rentier|rentière|partikul|particul|\bpart\b|propriétaire|\bpropr\b|vermögl"),
    ("land", "Landwirtschaft",
     r"landwirt|agricult|viehhänd|bauer\b|bauern|forestier|käserei|fromagerie|alp\b|weinbau|vigneron|förster|forst|baumschul"),
]
_PATTERNS = [(k, re.compile(p, re.I)) for k, _, p in CLASSES]
LABELS = {k: label for k, label, _ in CLASSES}


def classify(*texts: str) -> str:
    """Erste passende Klasse für Beruf, Zusatz und Name, sonst ''."""
    text = " ".join(t for t in texts if t)
    for key, pat in _PATTERNS:
        if pat.search(text):
            return key
    return ""

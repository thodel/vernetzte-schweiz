"""Durchdringung des Telefons im Kanton Bern, gemessen an BERNHIST (docs/durchdringung_bern.md).

    python scripts/durchdringung_bern.py                  # rechnet, schreibt Tabellen und den Block im Bericht
    python scripts/durchdringung_bern.py --stichprobe 20  # zieht die Stichprobe 3 neu (20 Einträge je Jahr, ohne Urteile)
    python scripts/durchdringung_bern.py site             # site/data/durchdringung_bern.json.gz für #/infrastruktur

Liest nur: data/norm/ptt_entries.csv.gz, data/norm/ab_entries.csv.gz, links/ptt_ab.csv.gz und data/ref/bernhist/
(scripts/ref_bernhist.py). Baut keine abgeleiteten Daten neu.

Zwei Teile:

1. Gemeinden: Telefoneinträge je 100 Einwohner um 1910 (bestes Jahr 1909–1914, wie infrastruktur.durchdringung)
   je BERNHIST-Einheit, gegen Grösse und Erwerbsstruktur 1910 → data/norm/durchdringung_bern_gemeinden.csv
2. Stadt Bern: Wer hat 1885, 1900 und 1910 ein Telefon? Art des Eintrags, Frauen und Witwen, Sektor und einzelne
   Gruppen, gegen Nenner aus BERNHIST; daneben die Adressbuchquoten aus adressbuecher-bern (1883–84, 1900) und
   die Personen des Adressbuchs, die über links/ptt_ab.csv.gz ein Telefon haben
   → data/norm/durchdringung_bern_stadt.csv

Die Zuordnung der Berufsangaben zu Sektoren ist die von adressbuecher-bern (scripts/85_abdeckung.py, Commit
20b0405), damit Telefon und Adressbuch dieselben Gruppen messen; TEL_* ergänzt, was nur im Telefonbuch vorkommt
(Geschäftsbezeichnungen statt Berufe). Geprüft an data/review/durchdringung_bern_stichprobe.csv.
"""

from __future__ import annotations

import argparse
import gzip
import json
import random
import re
import statistics
import sys
from collections import Counter, defaultdict

from common import NORM, ROOT, open_csv, write_csv

REF = ROOT / "data" / "ref" / "bernhist"
DOC = ROOT / "docs" / "durchdringung_bern.md"
STICHPROBE = ROOT / "data" / "review" / "durchdringung_bern_stichprobe.csv"        # 1: Regeln danach angepasst
STICHPROBE_2 = ROOT / "data" / "review" / "durchdringung_bern_stichprobe_2.csv"    # 2: nach den Regeln gezogen
STICHPROBE_3 = ROOT / "data" / "review" / "durchdringung_bern_stichprobe_3.csv"    # 3: nach den letzten Änderungen gezogen
SEED = {1: 20261123, 2: 20261124, 3: 20261125}
ADRESSBUCH = ROOT / "data" / "ref" / "bernhist" / "adressbuch_bern.csv"
OUT_GEMEINDEN = NORM / "durchdringung_bern_gemeinden.csv"
OUT_STADT = NORM / "durchdringung_bern_stadt.csv"
OUT_JSON = NORM / "durchdringung_bern.json"

END_YEARS = range(1909, 1915)       # «um 1910»: bestes gelesenes Jahr in diesem Fenster
MAX_RATE = 25.0                     # Einträge je 100 Einwohner darüber: Ortszuordnung falsch (wie infrastruktur.MAX_DENSITY)
SIZE_CLASSES = ((0, 499), (500, 999), (1000, 1999), (2000, 4999), (5000, 10**7))
STADT = "Bern"
BAND = {1885: "P-260-1_Bern_Biel_1885", 1900: "P-260-1_Bern_1900_2", 1910: "P-260-1_Bern_1910"}
AB_BAND = {1885: "1883", 1900: "1900"}          # Adressbuch, das neben dem Telefonbuch steht
AB_JAHRE = {"1883": (1884, 1885, 1886), "1900": (1900, 1901)}   # Telefonbücher, die als «gleichzeitig» gelten
STUFEN = ("sicher", "wahrscheinlich")


# ── Zuordnung der Berufsangaben (aus adressbuecher-bern, scripts/85_abdeckung.py) ────────────────────
WITWE = re.compile(r"\bWwe\b|\bWit+we\b|\bveuve\b|\bVve\b", re.I)
FRAEULEIN = re.compile(r"\bFrl\b|\bFräul|\bJgfr\b|\bjgr\b|\bJungfer|\bMlle\b|\bMesdemoiselles\b|\bSchw(?:\b|est)|\bGeschw", re.I)
FRAU = re.compile(r"\bFrau(?:en)?\b|\bMme\b|\bMad\b|\bgeb\.", re.I)      # «Fr.» ist im Telefonbuch Fritz oder Friedrich
WEIBL_BERUF = re.compile(r"^(?:gew\. )?[\w.\- ]*?(?:erin|rinnen|istin|lerin|frau|tochter|magd|amme|ière|ières|iére|"
                         r"euse|köchin|modiste|lingère|fleuriste|wirtin|wirthin|ärztin|vorgängerin)\b", re.I)
VORNAMEN_W = {
    "marie", "anna", "rosa", "elise", "emma", "luise", "louise", "bertha", "marg", "sophie", "lina", "ros", "maria",
    "ida", "elisab", "kath", "emilie", "martha", "magd", "julie", "sus", "adele", "verena", "karol", "rosina",
    "magdal", "soph", "lse", "mina", "fanny", "elisabeth", "pauline", "karoline", "klara", "frieda", "céc",
    "josephine", "henr", "johanna", "ver", "barb", "hedw", "elis", "augusta", "mathilde", "math", "clara",
    "lisette", "susanna", "barbara", "helene", "lydia", "therese", "charlotte", "caroline", "henriette", "olga",
    "alice", "hedwig", "agnes", "amalie", "margaritha", "margaretha", "katharina", "rosalie", "albertine", "jenny",
    "laura", "marianne", "marianna", "elisa", "lea", "flora", "wilhelmine", "friederike", "cäcilie", "antoinette",
    "magdalena", "rosine", "emilia", "berta", "nanette", "mar", "luisa", "lisa", "frida", "hélène",
}
OHNE = re.compile(r"^privati|^privat\.?$|^priv\.?$|^rent|^particul|^partikul|\bstud\b|student|pensionär|\bcand\b|"
                  r"^(?:sohn|vater|tochter|mutter|jun|sen)\b|^gew(?:es)?\b|^alt\b|^alt-|^a\. ", re.I)
KEINE = re.compile(r"^(?:schwestern|schwest|geschw|jgr|jgfr|frl|frau|wwe|wit+we)\.?$", re.I)
ANGEHOERIG = re.compile(r"^(?:d\.|des|der) ", re.I)
S1 = re.compile(r"landw|handelsgärtn|gärtner(?!in\b)|(?<!kinder)gärtnerin|gärtnerei|^pächter|küher|förster|bannwart|"
                r"lehenmann|gutsbesitz|\bfischer\b|melker|holzhauer|holzspalt|\bbauer\b|karrer\b.*gut|"
                r"landarbeit|rebmann|^oekonom", re.I)
HANDEL = re.compile(
    r"handel|handl|hdl|ändl|haendl|negt|\bneg\b|negot|\bi\. fa\b|\bfirma\b|\bfma\b|drog|confection|konfektion|"
    r"dépot|dépôt|verlag|verleger|lumpensamml|sensal|\bkfm\b|négoc|negoc|kaufm|commis|kommis|krämer|grempl|trödl|hausier|"
    r"agent|reisend|bank|banq|prokur|procur|buchhalt|buchh\b|korrespond|versicher|assekur|makler|comptoir|"
    r"magaz|ladent|ladend|verkäuf|geschäft|gesch\b|spezier|spezer|spezier|mercer|quincaill|bonneter|"
    r"drogu|comestibl|cigarr|zigarr|tabak|waaren\b|waren\b|artikel|lager\b|depot|antiquar|exped|kolonial|"
    r"colonial|associé|\bin fa\b|\bin firma\b|vertret|repräsent|kommission|commission|import|export|"
    r"\ben gros\b|bazar|papeterie|librairie|kiosk|krämerei|\bladen\b|marktfahr", re.I)
S3 = re.compile(
    r"\bpost|bahn|kindergärt|erzieh|vorgänger|halter|brief|concierge|evangelist|pharmac|hausvater|hausmutter|"
    r"copist|kopist|umbiet|geistlich|bischof|theolog|assistent|si[e]?grist|küster|\bbad|lehr\b|brasserie|"
    r"gouvern|institutr|vorst\b|subst\b|telegr|teleph|tram|kondukt|conduct|lokomotiv|locomotiv|zugf|weichen|brems|\bheizer|kutscher|"
    r"droschk|fuhr|camion|\bkarrer|dienstm|diensm|packer|träger|spedit|schiff|manöv|rangier|visiteur|"
    r"beamt|sekret|\bsekr\b|kanzl|revis|adjunkt|\br[aä]th?\b|rath?\b|richter|notar|fürspr|advok|anwalt|weibel|"
    r"polizi|polizei|landjäg|inspekt|inspect|direkt|direct|verwalt|schreiber|kassier|kontrol|control|statist|"
    r"registr|archiv|bibliothek|offiz|oberst|major|hauptm|lieut|leutn|instrukt|instruct|gesandt|attaché|konsul|"
    r"consul|bundes|eidg|kanton|gemeinde|städt|\bstadt|zoll|ohmgeld|kommiss|commiss|präsident|schaffner|"
    r"einnehmer|verweser|vorsteher|aufseher|chef\b|aktuar|substitut|rechnungsf|sachwalt|geometer|ingenieur|"
    r"\bingen\b|techniker|topograph|kartograph|übersetz|planton|korporal|wachtm|soldat|feldweibel|kommand|"
    r"lehrer|lehrerin|professor|\bprof\b|dozent|docent|rektor|pfarrer|\bpfr\b|prediger|mission|vikar|pastor|"
    r"helfer\b|sigrist|\barzt|ärzt|arzt\b|hebamme|apoth|wärter|zahn|pfleg|diakon|masseu|schröpf|"
    r"\bwirt|wirth|wirtschaft|wirtin|hotel|hôtel|pension(?!är)|restaur|kostgeb|café|cafe\b|kaffee|gasthof|"
    r"gasthaus|kellner|\bkoch\b|köchin|portier|pörtner|speise|zimmerverm|logis|"
    r"magd|knecht|diener|bedient|haushält|abwart|abwärt|hauswart|hauswärt|wächter|ausläufer|bureau|büro|"
    r"angestellt|angest\b|gehülf|gehilf|\bgeh\b|"
    r"musik|sänger|pianist|organist|kapellm|journal|redakt|redact|schriftstell|kunstmaler|bildhauer|künstler|"
    r"schauspiel|chemiker|mathemat|gelehrt|korrektor|stenogr|dolmetsch|leichenbitt|totengräb|kaminfeger|"
    r"zuchtmeister|wegmeister|wegknecht|bereiter|pferdew|pferded|stallm|badw|bademeist|nachtwäch", re.I)
S2 = re.compile(
    r"macher|münzarb|bandag|orthop|müller\b|hobler|unternehm|conditor|brod(?:eu|ier)|käser|kässalz|kuttler|"
    r"\bmech\b|stereotyp|kübler|tapez|tischler|silberarb|goldarb|gold- u|schnitzl|graph\b|graphie|"
    r"stein(?:br|me)|parkett|zuschn|zusn|damenschn|destill|gräber|faktor|\bhut(?:arb|rüst|riest|-)|schuhm|schuster|cordonn|schneid|taill|näh|schreiner|ebenist|schlosser|schmied|schmid\b|spengler|"
    r"maler|lackier|gipser|gypser|gyser|maurer|zimmerm|zimmerp|zimmerg|zimmermstr|steinh|dachdeck|hafner|küfer|"
    r"wagner|sattler|tapezier|drechsler|glaser|buchbind|buchdr|setzer|schrifts|drucker|lithogr|typogr|xylogr|"
    r"graveur|stecher|mechanik|mechan\b|monteur|giesser|dreher|bäcker|bäck\b|metzg|\bmüller|brauer|konditor|"
    r"confis|zuckerb|pâtiss|coiff|barbier|wäscher|wascher|wasch|glätter|calandr|lingère|lingere|modist|weber|"
    r"spinner|färber|gerber|seiler|bürsten|korb|flecht|pfläst|cement|parquet|bodenleg|asphalt|elektr|installat|"
    r"uhrenm|uhrm|goldarb|büchsenm|fabrik|geselle|\bges\b|meister|mstr\b|polier|vergold|optiker|strick|stick|"
    r"kürschn|posament|photogr|bauunter|baumeist|architek|architec|\barchit\b|bautechn|bauführ|bauzeichn|"
    r"zeichner|gasarb|gasanz|bauamt|zeughausarb|schleifer|feiler|feilenh|säger|brenner|ziegler|zügler|gürtler|"
    r"kupfer|zinng|blech|kessler|nagler|schäfte|chemis|kleider|schirm|kappen|handarbeiterin|einleger|"
    r"maschin|heizer\b.*fabrik|fumiste|marbrier|bijout|goldschm|instrumentenm|klavierst|orgelb|wagenb|"
    r"vorarbeiter|werkführ|bleich|appret|gilet|corset|korsett|blumenm|fleurist|feger|kunstwasch|"
    r"buchdruckerei|bäckerei|metzgerei|schlosserei|schreinerei|giesserei|brauerei|gerberei|färberei|weberei|"
    r"spinnerei|ziegelei|mühle\b|werkstätte|atelier|manufact|manufakt", re.I)
UNBESTIMMT = re.compile(r"taglöhn|tagl\b|handlang|arbeiter|arb\b|lehrling|lehrtochter|gehülfe|aushülf", re.I)

# Ergänzungen für das Telefonbuch: Geschäftsbezeichnungen und Abkürzungen, die im Adressbuch nicht vorkommen
TEL_LEER = re.compile(r"^\(?(?:wohn(?:un)?g?|wohg|privatwohnung|privat|domicile|appartement|villa|landhaus|landsitz|"
                      r"sommerwohnung|stadtwohnung|campagne|bureau und wohnung|derselbe|dieselbe|filiale|[ivx]+\. stock|"
                      r"& ?(?:co|cie|comp|söhne|sohn|fils)\.?|gebr(?:üder)?\.?|frères|fils|söhne|geschwister|a\.-?g\.?)\)?\.?$", re.I)
TEL_LEITUNG = re.compile(r"^(?:direktor|direktion|verwalter|prokurist|geschäftsführer|gérant|inhaber|teilhaber|chef|"
                         r"betriebsleiter|vertreter)\w* (?:der|des|d\.|von|v\.|bei|de la|du|de) (.+)", re.I)
TEL_HANDLUNG = re.compile(r"(?:handlung(?:en)?|händler|handel|hdlg)\b", re.I)
TEL_VORGAENGER = re.compile(r"^(?:vorm(?:als)?\b|nachf|succ|inh\b)", re.I)
TEL_STAND = re.compile(r"^(?:(?:frau|fr[äa]ulein|frl|wwe|wit+we|mme|mlle|veuve|vve|fam)\b\.?\s*)+(?:[a-zäöüé]\.?\s*)?", re.I)
TEL_S1 = re.compile(r"baumschul|gutsverwalt|\bgut\b|landgut|molkereigenoss|käsereigenoss|\bmilch(?:lief|produ)", re.I)
TEL_HANDEL = re.compile(r"\bwein|\bbier(?:depot|dépôt|handl)|kohlen|\bholz\b|brennmat|\beisen\b|leder\b|tuch\b|möbel(?!fab)|"
                        r"\bnegt\b|mercerie|épicer|denrées|quincail|bijouterie|\buhren\b|\bbuchh|musikalien|"
                        r"sparkasse|kasse\b|wechselstube|\bcr[eé]dit|hypothek|inkasso|incasso|annonc|auskunft|"
                        r"liegenschaft|immobil|treuhand|\bpatent|\bsamen\b|futter|getreide|mehl\b|\bbutter|\bkäse\b|"
                        r"delikat|südfr|\bobst|gemüse|\bblumen\b|\bschuhe\b|\bglas\b|porzellan|\bstoffe\b|nouveaut|"
                        r"\bmode|\bweiss|aussteuer|\bkonsum|consum|genossenschaft|soierie|seidenhaus|lingerie|"
                        r"chapellerie|garderobe|verkaufslokal|warenhalle|warenhaus|eisenhalle|photohaus", re.I)
TEL_S3 = re.compile(r"\bdr\b|\bmed\b|\bjur\b|doctor|\bklinik|sanator|spital|krankenh|anstalt|institut|schule\b|pensionat|"
                    r"cantin|kantin|professeur|laborato|experte|ministerresident|"
                    r"redaktion|zeitung|tagblatt|anzeiger|\bbund\b|intelligenz|theater|théâtre|kino|museum|kirch|"
                    r"\bpfarr|verein|verband|gesellschaft|société|\bclub\b|\bklub|zunft|loge\b|sekretariat|"
                    r"gesandtschaft|légation|legation|ambassade|\bconsulat|konsulat|département|departement|"
                    r"direktion|direction|administration|\bkaserne|zeughaus|\bgericht|\bamt\b|amt$|polizei|"
                    r"feuerwehr|sanität|\bgarage|automobil|\btaxi|transport|umzug|bestattung|leichen|"
                    r"hebamme|masseur|pédicure|pedicure|coiffeuse|krankenpfleg|privatklinik|speisehaus|bierhalle|"
                    r"buffet|kursaal|casino|kasino|kegelbahn|schwimm|badanstalt|\bbäder|wäscherei.*anstalt", re.I)
TEL_S2 = re.compile(r"graphische anstalt|kunstanstalt|lichtdruck|charcut|fondeur|decker\b|untern\b|kraftwerk|druckerei|\bbau(?:geschäft|gesch|untern)|baugeschäft|zimmerei|gipserei|malerei|glaserei|"
                    r"spenglerei|sattlerei|wagnerei|schmiede\b|schmitte|sägerei|\bsäge\b|ziegel|cement|zement|"
                    r"konstruktion|construction|werkstatt|\bwerke?\b|\bfabr\b|usine|chocol|schokol|teigwaren|"
                    r"konserven|mineralwasser|limonad|brennerei|destillat|\bmolkerei|käserei|\bmühle|"
                    r"wäscherei|färberei|kleiderreinig|chem\.? ?wasch|schneiderei|couture|\brobes\b|modes\b|"
                    r"hutgesch|uhrmacher|horloger|elektrizit|licht- u|kraftanlag|heizung|sanitär|installation|"
                    r"gas- u|wasserversorg|gaswerk|photograph|\bphot\b|buchbinderei|stempel|clich|gravier", re.I)


def erste_angabe(beruf: str) -> str:
    """Die Berufsangabe bis zum ersten Komma; «Milch-, Anken- u. Käsehändler» bleibt ganz."""
    teile, out = re.split(r"[,(;]", beruf.strip()), []
    for t in teile:
        out.append(t.strip())
        if not t.strip().endswith("-"):
            break
    return " ".join(out).strip()


def sektor(beruf: str, titel: str = "", witwe: bool = False, telefon: bool = False) -> str:
    """'1', '2', '3', 'ohne' (kein Erwerb genannt: Privatier, «gew.»), 'unbestimmt' (Angabe ohne Sektor) oder ''.

    telefon=False ist die Regel von adressbuecher-bern unverändert; telefon=True nimmt die Ergänzungen TEL_* dazu
    und liest «Wohnung», «Bureau und Wohnung» als keine Angabe.
    """
    kopf = erste_angabe(beruf).lower()
    kopf = re.sub(r"(\w)-\s+(?=[a-zäöü])(?!u\.|und\b)", r"\1", kopf)
    if telefon:
        kopf = TEL_STAND.sub("", kopf).strip()
        if TEL_LEER.match(kopf) or re.fullmatch(r"[a-zäöü]\.?", kopf):
            kopf = ""
        if m := TEL_LEITUNG.match(kopf):          # «Direktor der Möbelfabrik»: der Erwerbszweig des Betriebs gilt
            if (s := sektor(m[1], telefon=True)) in ("1", "2", "3"):
                return s
        if TEL_HANDLUNG.search(kopf):            # «Velo- und Nähmaschinenhandlung»: Handel, auch wenn die Ware zuerst steht
            return "3"
    if not kopf:
        t = titel.lower()
        return "3" if re.search(r"dr\b|prof|pfr|pfarrer|notar|r[aä]th?\b|oberst|major|hauptm|direkt|richter|ingen", t) else ""
    if KEINE.match(kopf):
        return ""
    if ANGEHOERIG.match(kopf):
        if witwe:
            return "ohne"
        kopf = ANGEHOERIG.sub("", kopf)
    if OHNE.search(kopf):
        return "ohne"
    regeln = [(S1, "1"), (HANDEL, "3"), (S3, "3"), (S2, "2")]
    if telefon:
        regeln += [(TEL_S1, "1"), (TEL_HANDEL, "3"), (TEL_S3, "3"), (TEL_S2, "2")]
    treffer = [(m.start(), rang, s) for rang, (rx, s) in enumerate(regeln) if (m := rx.search(kopf))]
    if treffer:
        return min(treffer)[2]
    return "unbestimmt"


def frau(stand: str, vorname: str, beruf: str = "", text: str = "") -> str:
    """witwe, fraeulein, frau (so bezeichnet), weiblich (nur an Vorname oder Berufsform erkannt) oder ''."""
    s = f"{stand} {vorname}"
    if WITWE.search(s) or (ANGEHOERIG.match(beruf.strip()) and WITWE.search(text)):
        return "witwe"
    if FRAEULEIN.search(s):
        return "fraeulein"
    if FRAU.search(s):
        return "frau"
    v = re.split(r"[ .]", vorname.strip().lower())[0]
    if v in VORNAMEN_W or WEIBL_BERUF.match(beruf.split(",")[0].split(";")[0].split(" u. ")[0].strip()):
        return "weiblich"
    return ""


GRUPPEN = {
    "aerzte": re.compile(r"arzt\b|ärztin|aerztin|\bärzte\b|\baerzte\b|médecin", re.I),
    "spezerei": re.compile(r"spez[ei]r|kolonial|colonial|épicer", re.I),
    "gastgewerbe": re.compile(r"\bwirt|wirth|wirtschaft|hotel|hôtel|pension(?!är|at)|restaur|kostgeb|café|cafe\b|kaffee|"
                              r"gasthof|gasthaus|brasserie|bierhalle|speisehaus|buffet|kursaal|\bkeller\b|"
                              r"temperenz|auberge", re.I),
    "nahrung": re.compile(r"bäck|boulang|metzg|boucher|charcut|kondit|conditor|confis|zuckerb|pâtiss|brauer|"
                          r"\bmüller\b|\bmühle|käser|molkerei|chocol|schokol|teigwaren|konserven|mineralwasser|"
                          r"limonad|brennerei|destill|wursterei|biscuit|\bessig", re.I),
    "druck": re.compile(r"buchdr|druckerei|lithogr|typogr|xylogr|schriftgiess|clich|stereotyp|imprimerie|"
                        r"schriftsetz|buchbind|lichtdruck", re.I),
}
NICHT_ARZT = re.compile(r"zahn|tier|thier|vieh|pferde|dent|vét|vet\b", re.I)


def gruppe(name: str, text: str, titel: str = "") -> bool:
    """Einzelne Gruppen mit Nenner in BERNHIST. text: Berufsangabe, bei Firmen mit dem Namen davor."""
    if name == "aerzte":
        return bool(GRUPPEN[name].search(text) and not NICHT_ARZT.search(text))
    if name == "aerzte_med":
        return gruppe("aerzte", text) or bool(re.search(r"\bmed\b", titel, re.I) and not re.search(
            r"cand|vet|dent", titel, re.I) and not NICHT_ARZT.search(text))
    return bool(GRUPPEN[name].search(text))


# ── Telefonbucheintrag lesen ─────────────────────────────────────────────────────────────────────────
AMT = re.compile(r"direktion|direction|departement|département|verwaltung|administration|kanzlei|chancellerie|"
                 r"amt\b|ämter|\beidg|\bkant\b|kanton|städt|stadt(?:polizei|kasse|kanzlei|bau|schreib|gärtn)|"
                 r"bundes|polizei|\bpost(?:bureau|filiale|amt|verwalt|direktion)|telegraph|telephon|zoll|"
                 r"gericht|\bschule\b|schulhaus|gymnasium|universität|hochschule|seminar\b|spital|kaserne|zeughaus|"
                 r"consulat|konsulat|gesandtschaft|légation|legation|ambassade|\bbureau (?:für|des|der|du|de)\b|"
                 r"internat|sprechstation|gemeindestation|bahnhof(?!buffet|restaur|str|pl)|\bs\. ?b\. ?b|"
                 r"regierungs|statthalter|staats|waisenhaus|burgerrat|burgerl|burgergem|kirchgem|"
                 r"einwohnergem|waffenplatz|kriegs|militär|section |oberkrieg|landestopo|münzstätte|alkoholverw", re.I)
# Amtsstellen und Anstalten, die das Buch unter ihrer Bezeichnung führt und die ohne Vornamen als Person gelesen sind
FUNKTION = re.compile(r"\w{3,}(?:arzt|richter|ingenieur|inspektor|inspektorat|direktor|verwalter|kommissär|kommissariat|"
                      r"sekretär|sekretariat|kassier|anstalt|kommando|adjunkt|präsident|anwalt|geometer|kontrolle|"
                      r"depot|magazin|station|wache|posten|bureau|büro|chef)\b(?: [IVX]+| (?:der|des) .+)?$", re.I)
BETRIEB = re.compile(r"h[oô]tels?\b|caf[eé]s?\b|restaur|pension\b|gasth|wirtschaft|brasserie|bierhalle|apotheken?\b", re.I)
AMT_ZUSATZ = re.compile(r"^(?:eidg|kant|städt|ausserordentl|ordentl)|irrenanstalt|strafanstalt|kaserne|verwaltung", re.I)
NAMENSFIRMA = re.compile(r"&|\bCie\b|\bCo\b|\bGebr|\bSöhne\b|\bErben\b|frères|\bfils\b", re.I)   # Name aus Familiennamen
PERSONENFIRMA = re.compile(r"&|\bCie\b|\bCo\b\.?|\bComp\b|\bGebr(?:\b|ü)|\bSöhne\b|\bErben\b|frères|\bfils\b|A\.-?G\.|"
                           r"Aktienges|Genossensch|\bS\. ?A\.", re.I)


def art(x: dict) -> str:
    """person, firma, amt oder zusatz («Derselbe, Wohnung»).

    Geht von entity_type aus und berichtigt, was die Messung braucht: Ämter und Anstalten, die als Firma oder als
    Person ohne Vornamen gelesen sind («Direktion des Gemeindewesens», «Bauamt, Sekretariat»), und Firmen, die als
    Person gelesen sind («Weibel, Gebr.», «Pulver, B. & F.»).
    """
    t = x["entity_type"]
    if t == "zusatz" or re.match(r"(?:derselbe|dieselbe)\b", x["name1"], re.I):
        return "zusatz"
    kopf = f"{x['name1']} {x['name2']}"
    ohne_vorname = not (x["forename"] or x["initials"])
    if t == "amt" or (t == "firma" and (AMT.search(x["name1"]) or FUNKTION.search(x["name1"].strip()))) or (
            t == "person" and ohne_vorname and (AMT.search(x["name1"]) or FUNKTION.search(x["name1"].strip())
                                                or AMT_ZUSATZ.search(x["supplement"].strip()))):
        return "amt"
    if t == "person" and (PERSONENFIRMA.search(kopf) or re.match(r"\(?gebr", x["supplement"].strip(), re.I)):
        return "firma"
    if t == "person" and ohne_vorname and BETRIEB.search(f"{x['name1']}, {x['supplement']}"):
        return "firma"                           # «Falken, (Blau), Hôtels», «Schweizerhof, Hôtel»
    return t


def angabe(x: dict) -> str:
    """Berufs- oder Geschäftsangabe eines Eintrags.

    Personen: die Angabe, wie sie steht (es gilt die erste, wie im Adressbuch). Firmen: der erste Teil der Angabe,
    der einen Sektor nennt («A., & Co., Buchdruckerei» → Buchdruckerei), sonst der Name («Café Ratskeller»).
    """
    b = x["occupation"].replace(";", ",").strip() or x["supplement"].strip()
    if art(x) != "firma":
        teile = [t.strip() for t in b.split(",")]
        while len(teile) > 1 and (TEL_VORGAENGER.match(teile[0]) or not TEL_STAND.sub("", teile[0]).strip(" .")):
            teile.pop(0)                         # «vorm. Hausmann & Co., Fabrik»; «Frau Wwe., Droguerie»
        return ", ".join(teile)
    name = x["name1"].strip()
    teile = [t.strip() for t in re.split(r"[,(]", b) if t.strip()]
    if teile and sektor(teile[0], telefon=True) in ("1", "2", "3"):
        return ", ".join(teile)                  # «Schweizer Bauer, Administration»: die Angabe gilt vor dem Namen
    if not NAMENSFIRMA.search(name) and sektor(name, telefon=True) in ("1", "2", "3"):
        return name + (", " + b if b else "")    # «Kasino, Café»: der Name nennt den Betrieb
    for i, t in enumerate(teile):
        if sektor(t, telefon=True) not in ("", "unbestimmt"):
            return ", ".join(teile[i:])          # «A., & Co., Buchdruckerei»
    return b


def inhaber(x: dict) -> tuple:
    """Dieselbe Person steht mit Geschäft und Wohnung, 1885 auch im Branchenteil mehrmals im Buch: einmal zählen."""
    a = art(x)
    if a == "person":
        return ("p", x["surname"].lower(), (x["forename"] or x["initials"]).lower()[:1])
    return (a[0], re.sub(r"[^a-zäöüéèàâç0-9]+", "", x["name1"].lower()))


def lies_eintrag(x: dict) -> dict:
    a = art(x)
    b = angabe(x)
    text = b if a != "firma" else f"{x['name1']}, {b}"
    stand = f"{x['title']} {x['name2']} {x['supplement'].split(',')[0]}"
    f = frau(stand, x["forename"] or x["name2"], x["occupation"]) if a == "person" else ""
    s = "" if a in ("amt", "zusatz") else sektor(b, x["title"], f == "witwe", telefon=True)
    return {"art": a, "frau": f, "sektor": s, "angabe": b,
            "gruppen": [g for g in ("aerzte", "aerzte_med", "spezerei", "gastgewerbe", "nahrung", "druck")
                        if a in ("person", "firma") and gruppe(g, text, x["title"])]}


# ── Teil 1: Gemeinden ────────────────────────────────────────────────────────────────────────────────
def sektorgruppe(s1: float, s2: float, s3: float) -> str:
    """Erwerbsstruktur 1910 in vier Gruppen (Anteile in Prozent der Erwerbstätigen)."""
    if s3 >= 25:
        return "Dienstleistung (3. Sektor ab 25 %)"
    if s1 >= 60:
        return "bäuerlich (1. Sektor ab 60 %)"
    if s2 >= 50:
        return "gewerblich-industriell (2. Sektor ab 50 %)"
    return "gemischt"


SEKTORGRUPPEN = ("bäuerlich (1. Sektor ab 60 %)", "gemischt", "gewerblich-industriell (2. Sektor ab 50 %)",
                 "Dienstleistung (3. Sektor ab 25 %)")


def groessenklasse(n: int) -> str:
    for lo, hi in SIZE_CLASSES:
        if lo <= n <= hi:
            return f"{lo}–{hi}" if hi < 10**6 else f"ab {lo}"
    return ""


def gemeinden(P: list[dict]) -> list[dict]:
    """Je BERNHIST-Einheit: Einträge im besten Jahr 1909–1914, je 100 Einwohner 1910, Erwerbsstruktur 1910."""
    einh = open_csv(REF / "einheiten.csv")
    einheit = {r["hist_code"]: r["einheit_id"] for r in open_csv(REF / "gemeinden_1914.csv") if r["einheit_id"]}
    abweichend = {n for r in open_csv(REF / "vergleich_bfs.csv") if r["ueber_schwelle"] for n in r["einheiten"].split(";")}
    per_book: Counter = Counter()
    for x in P:
        if x["hist_code_1914"] in einheit and int(x["year"]) in END_YEARS:
            per_book[(x["hist_code_1914"], int(x["year"]), x["refcode"])] += 1
    best: dict = {}
    for (m, y, ref), n in per_book.items():      # je Gemeinde und Jahr der Band mit den meisten Einträgen
        if n > best.get((m, y), (0, ""))[0]:
            best[(m, y)] = (n, ref)
    ent: Counter = Counter()
    nums: dict = defaultdict(set)
    for x in P:
        m, y = x["hist_code_1914"], int(x["year"])
        if m not in einheit or y not in END_YEARS or x["place_confidence"] == "unsicher" or best[(m, y)][1] != x["refcode"]:
            continue
        ent[(einheit[m], y)] += 1
        if x["phone_norm"]:
            nums[(einheit[m], y)].add((m, x["phone_norm"]))
    out = []
    for e in einh:
        u = e["einheit_id"]
        if not e["bev_1910"] or not e["hist_codes"]:
            continue
        y = max(END_YEARS, key=lambda y: (ent[(u, y)], y))
        bev, n = int(e["bev_1910"]), ent[(u, y)]
        erw = int(e["erw_1910"]) if e["s1_1910"] != "" else 0
        s = [round(100 * int(e[f"s{k}_1910"]) / erw, 1) if erw else "" for k in "123"]
        rate = round(100 * n / bev, 2)
        grund = ("Bevölkerung weicht von der BFS-Tabelle ab" if e["name"] in abweichend else
                 "Ortszuordnung unplausibel (über 25 Einträge je 100 Einwohner)" if rate > MAX_RATE else
                 "ohne Erwerbsstruktur" if not erw else
                 "Erwerbstätige über 60 % der Bevölkerung (Baustelle oder Anstalt)" if erw / bev > 0.6 else "")
        out.append({"einheit_id": u, "name": e["name"], "gemeinden_1914": e["gemeinden_1914"], "bev_1910": bev,
                    "jahr": y if n else "", "eintraege": n, "nummern": len(nums[(u, y)]), "je_100_einwohner": rate,
                    "erw_1910": erw or "", "s1_prozent": s[0], "s2_prozent": s[1], "s3_prozent": s[2],
                    "groessenklasse": groessenklasse(bev),
                    "sektorgruppe": sektorgruppe(*s) if erw else "", "ausgeschlossen": grund})
    return out


def zelle(rows: list[dict]) -> dict:
    """Kennzahlen einer Gruppe von Einheiten."""
    n = len(rows)
    if not n:
        return {"n": 0}
    raten = sorted(r["je_100_einwohner"] for r in rows)
    bev = sum(r["bev_1910"] for r in rows)
    return {"n": n, "mit_telefon": sum(1 for r in rows if r["eintraege"]),
            "anteil_mit_telefon": round(100 * sum(1 for r in rows if r["eintraege"]) / n),
            "bev": bev, "eintraege": sum(r["eintraege"] for r in rows),
            "je_100": round(100 * sum(r["eintraege"] for r in rows) / bev, 2),
            "median": round(statistics.median(raten), 2)}


def rang_korrelation(xs: list[float], ys: list[float]) -> float:
    """Spearman: Korrelation der Ränge (Bindungen mit mittlerem Rang)."""
    def rang(v: list[float]) -> list[float]:
        o = sorted(range(len(v)), key=lambda i: v[i])
        r = [0.0] * len(v)
        i = 0
        while i < len(o):
            j = i
            while j + 1 < len(o) and v[o[j + 1]] == v[o[i]]:
                j += 1
            for k in range(i, j + 1):
                r[o[k]] = (i + j) / 2 + 1
            i = j + 1
        return r
    if len(xs) < 3:
        return float("nan")
    a, b = rang(xs), rang(ys)
    ma, mb = sum(a) / len(a), sum(b) / len(b)
    za = sum((x - ma) * (y - mb) for x, y in zip(a, b))
    n = (sum((x - ma) ** 2 for x in a) * sum((y - mb) ** 2 for y in b)) ** 0.5
    return round(za / n, 2) if n else float("nan")


def kreuztabelle(rows: list[dict]) -> dict:
    """Grösse × Sektorgruppe und, je Grössenklasse, Hälften nach dem Anteil des 3. und des 1. Sektors."""
    ok = [r for r in rows if not r["ausgeschlossen"]]
    klassen = [groessenklasse(lo) for lo, _ in SIZE_CLASSES]
    out = {"n": len(ok), "ausgeschlossen": [[r["name"], r["ausgeschlossen"]] for r in rows if r["ausgeschlossen"]],
           "gesamt": zelle(ok), "klassen": {}, "sektorgruppen": {}, "kreuz": {}, "haelften": {}, "rang": {}}
    for k in klassen:
        rk = [r for r in ok if r["groessenklasse"] == k]
        out["klassen"][k] = zelle(rk)
        out["kreuz"][k] = {g: zelle([r for r in rk if r["sektorgruppe"] == g]) for g in SEKTORGRUPPEN}
        if len(rk) >= 8:
            for feld in ("s3_prozent", "s1_prozent", "s2_prozent"):
                m = statistics.median(r[feld] for r in rk)
                out["haelften"].setdefault(k, {})[feld] = {
                    "median": m, "unter": zelle([r for r in rk if r[feld] < m]), "ab": zelle([r for r in rk if r[feld] >= m])}
            out["rang"][k] = {f: rang_korrelation([r[f] for r in rk], [r["je_100_einwohner"] for r in rk])
                              for f in ("bev_1910", "s1_prozent", "s2_prozent", "s3_prozent")}
    for g in SEKTORGRUPPEN:
        out["sektorgruppen"][g] = zelle([r for r in ok if r["sektorgruppe"] == g])
    out["rang"]["alle"] = {f: rang_korrelation([r[f] for r in ok], [r["je_100_einwohner"] for r in ok])
                           for f in ("bev_1910", "s1_prozent", "s2_prozent", "s3_prozent")}
    # Grösse bei gleicher Struktur und Struktur bei gleicher Grösse: Spannweite der Mediane
    out["ohne_bern"] = zelle([r for r in ok if r["name"] != "Bern (ab 1920 mit Bümpliz)" and r["bev_1910"] >= 5000])
    return out


# ── Teil 2: Stadt Bern ───────────────────────────────────────────────────────────────────────────────
def interpoliere(j0: float, w0: float, j1: float, w1: float, j: float) -> float:
    """Linear zwischen zwei Stichjahren (wie adressbuecher-bern); ausserhalb wird nicht extrapoliert."""
    if not min(j0, j1) <= j <= max(j0, j1):
        raise ValueError(f"{j} liegt nicht zwischen {j0} und {j1}")
    return w0 if j0 == j1 else w0 + (w1 - w0) * (j - j0) / (j1 - j0)


def stadt_werte() -> dict[str, float]:
    """Werte der Stadt Bern (Ort 457) aus data/ref/bernhist/werte.csv; Erwerbstätige 1910 aus einheiten.csv."""
    w: dict = {}
    for r in open_csv(REF / "werte.csv"):
        if r["bernhist_id"] == "457":
            k = r["reihe"] if r["rang"] == "0" else f"{r['reihe']}_rang{r['rang']}"
            w[k] = float(r["wert"])
    e = next(r for r in open_csv(REF / "einheiten.csv") if r["einheit_id"] == "457")
    w.update({"erw_1910": float(e["erw_1910"]), "erw_s1_1910": float(e["s1_1910"]),
              "erw_s2_1910": float(e["s2_1910"]), "erw_s3_1910": float(e["s3_1910"])})
    w["erw_1856"] = w.get("erw_1856_rang1", w["erw_1856"])     # zweite Reihe 1856 (11 701), wie adressbuecher-bern
    return w


def nenner(w: dict[str, float], j: int) -> dict[str, tuple[float, str, str]]:
    """Nenner für ein Jahr: Name → (Wert, Art, Herleitung). Art: direkt, interpoliert, geschätzt.

    Dieselbe Herleitung wie adressbuecher-bern (85_abdeckung.nenner), mit einem Unterschied: Die Erwerbstätigen
    1910 sind die der Stadt im Gebiet von 1910 (35 250, Reihe A), nicht die mit Bümpliz (37 247).
    """
    if j in (1900, 1910):
        bev = (w[f"bev_{j}"], "direkt", f"Volkszählung {j}")
    else:
        bev = (interpoliere(1880, w["bev_1880"], 1888, w["bev_1888"], j), "interpoliert",
               f"Volkszählungen 1880 und 1888, linear auf {j}")
    b = bev[0]
    hg = w["bev_1888"] / w["haushalte_1888"]
    direkt = j == 1910
    erw_q = interpoliere(1856, w["erw_1856"] / w["bev_1856"], 1910, w["erw_1910"] / w["bev_1910"], j)
    erw = b * erw_q
    art_ = "direkt" if direkt else "geschätzt"
    n = {
        "bevoelkerung": bev,
        "haushalte": (b / hg, "geschätzt", f"Bevölkerung {j} durch die Haushaltsgrösse von 1888 ({hg:.2f} Personen)"),
        "erwerbstaetige": (erw, art_, "Volkszählung 1910 (Reihe A)" if direkt else
                           f"Bevölkerung {j} mal Erwerbsquote, zwischen 1856 und 1910 interpoliert ({100 * erw_q:.1f} %)"),
        "frauen": (b * interpoliere(1856, w["frauen_1856"] / w["bev_1856"], 1930, w["frauen_1930"] / w["bev_1930"], j),
                   "geschätzt", "Bevölkerung mal Frauenanteil, zwischen 1856 und 1930 interpoliert"),
        "aerzte": (interpoliere(1856, w["aerzte_1856"], 1910, w["aerzte_1910"], j), "direkt" if direkt else "interpoliert",
                   "Ärzte 1910" if direkt else "Zahl der Ärzte 1856 und 1910, linear"),
    }
    verw = interpoliere(1856, w["verwitwet_1856"] / w["bev_1856"], 1910, w["verwitwet_1910"] / w["bev_1910"], j)
    n["witwen"] = (b * verw * w["witwen_1846"] / (w["witwen_1846"] + w["witwer_1846"]), "geschätzt",
                   ("Verwitwete 1910" if direkt else "Bevölkerung mal Anteil der Verwitweten, zwischen 1856 und 1910 interpoliert")
                   + " mal Frauenanteil der Verwitweten 1846")
    for s in "123":
        n[f"sektor{s}"] = (erw * w[f"erw_s{s}_1910"] / w["erw_1910"], art_,
                           f"Volkszählung 1910 (Reihe A{', 3. Sektor als Rest' if s == '3' else ''})" if direkt else
                           f"geschätzte Erwerbstätige mal Anteil des {s}. Sektors 1910")
    if j >= 1900:
        b1901 = interpoliere(1900, w["bev_1900"], 1910, w["bev_1910"], 1901)
        b1909 = interpoliere(1900, w["bev_1900"], 1910, w["bev_1910"], 1909)
        n["spezerei"] = ((b * w["spezerei_1901"] / b1901, "geschätzt", "Spezereigeschäfte 1901, mit der Bevölkerung auf 1900 umgerechnet")
                         if j == 1900 else
                         (b * w["spezerei_1909"] / b1909, "geschätzt", "Spezereigeschäfte 1909, mit der Bevölkerung auf 1910 umgerechnet"))
    if direkt:
        for k, t in (("gastgewerbe", "Gastgewerbe"), ("nahrung", "Nahrungs- und Genussmittel"), ("druck", "Polygraphisches Gewerbe")):
            n[k] = (w[f"{k}_1910"], "direkt", f"Erwerbstätige 1910: {t}")
    return n


def quote(z: float, n: float) -> float:
    return round(100 * z / n, 1 if 100 * z / n >= 1 else 2)


def stadt_zaehlen(P: list[dict], jahr: int) -> dict:
    """Zähler aus dem Telefonbuch eines Jahres für die Stadt Bern."""
    E = [x for x in P if x["municipality_1914"] == STADT and int(x["year"]) == jahr and x["refcode"] == BAND[jahr]
         and x["place_confidence"] != "unsicher"]
    z: Counter = Counter()
    z["eintraege"] = len(E)
    z["nummern"] = len({x["phone_norm"] for x in E if x["phone_norm"]})
    je: dict = {}
    for x in E:
        r = lies_eintrag(x)
        z[f"eintraege_{r['art']}"] += 1
        if r["art"] == "zusatz":
            continue
        k = inhaber(x)
        cur = je.setdefault(k, {"art": r["art"], "frau": "", "sektor": "", "gruppen": set(), "wohnung": False})
        cur["gruppen"].update(r["gruppen"])
        if r["frau"] and not cur["frau"]:
            cur["frau"] = r["frau"]
        rang = {"1": 3, "2": 3, "3": 3, "ohne": 2, "unbestimmt": 1, "": 0}
        if rang[r["sektor"]] > rang[cur["sektor"]]:        # die erste Angabe mit Sektor gilt
            cur["sektor"] = r["sektor"]
        if re.search(r"wohnung|privat|domicile|appartement", f"{x['occupation']} {x['supplement']}", re.I):
            cur["wohnung"] = True
    for v in je.values():
        z[v["art"]] += 1
        if v["art"] == "amt":
            continue
        if v["art"] == "person":
            if v["frau"]:
                z["frauen"] += 1
                z[f"frau_{v['frau']}"] += 1
            if v["wohnung"]:
                z["person_wohnung"] += 1
        z[f"sektor_{v['sektor'] or 'keine'}"] += 1
        if v["art"] == "person":
            z[f"person_sektor_{v['sektor'] or 'keine'}"] += 1
        for g in v["gruppen"]:
            z[g] += 1
    return dict(sorted(z.items()))               # feste Reihenfolge: die Gruppen kommen aus einer Menge


def stadt_zeilen(w: dict, z: dict[int, dict]) -> list[dict]:
    """Ergebnistabelle: je Jahr und Gruppe Zähler, Nenner und Quote."""
    spec = [
        ("Einträge im Telefonbuch", "eintraege", "bevoelkerung", "alle Zeilen der Stadt im Band"),
        ("verschiedene Rufnummern", "nummern", "bevoelkerung", "1885 nennt das Buch keine Nummern"),
        ("Personen mit Eintrag je Einwohner", "person", "bevoelkerung", "jede Person einmal (Geschäft und Wohnung zusammen)"),
        ("Personen mit Eintrag je Haushalt", "person", "haushalte", "Obergrenze für den Anteil der Haushalte mit Telefon"),
        ("Personen mit Wohnungsanschluss", "person_wohnung", "haushalte", "Eintrag nennt «Wohnung», «Privat», «domicile»"),
        ("Firmen", "firma", "", "Personenfirmen (&, Cie., Gebr.), Gesellschaften, Betriebe mit eigenem Namen"),
        ("Ämter und Anstalten", "amt", "", "Bund, Kanton, Stadt, Schulen, Spitäler, Gesandtschaften"),
        ("Frauen", "frauen", "frauen", "erkannt an Stand, Vorname oder Berufsform: Untergrenze"),
        ("Witwen", "frau_witwe", "witwen", ""),
        ("Fräulein", "frau_fraeulein", "", ""),
        ("Personen und Firmen mit Sektor je Erwerbstätige", "_sektor_alle", "erwerbstaetige", ""),
        ("1. Sektor", "sektor_1", "sektor1", "Personen und Firmen"),
        ("2. Sektor", "sektor_2", "sektor2", "Personen und Firmen"),
        ("3. Sektor", "sektor_3", "sektor3", "Personen und Firmen, ohne Ämter"),
        ("ohne Erwerb (Privatier, Rentier)", "sektor_ohne", "", ""),
        ("Angabe ohne Sektor", "sektor_unbestimmt", "", ""),
        ("keine Angabe (nur Name, «Wohnung»)", "sektor_keine", "", ""),
        ("Ärzte (Angabe nennt «Arzt»)", "aerzte", "aerzte", "ohne Zahn- und Tierärzte"),
        ("Ärzte (dazu Titel «Dr. med.»)", "aerzte_med", "aerzte", ""),
        ("Spezereihandlungen", "spezerei", "spezerei", "Nenner: Arbeitsstätten 1901 und 1909"),
        ("Gastgewerbe: Anschlüsse je 100 Erwerbstätige", "gastgewerbe", "gastgewerbe", "Betriebe gegen Beschäftigte, keine Quote der Betriebe"),
        ("Nahrungs- und Genussmittel: Anschlüsse je 100 Erwerbstätige", "nahrung", "nahrung", "Betriebe gegen Beschäftigte"),
        ("Druck und Buchbinderei: Anschlüsse je 100 Erwerbstätige", "druck", "druck", "Betriebe gegen Beschäftigte"),
    ]
    rows = []
    for j in sorted(z):
        n = nenner(w, j)
        zz = dict(z[j])
        zz["_sektor_alle"] = sum(zz.get(f"sektor_{s}", 0) for s in "123")
        for name, zk, nk, bem in spec:
            wert = zz.get(zk, 0)
            if zk == "nummern" and not wert:
                continue
            nv = n.get(nk)
            if nk and not nv:
                continue
            rows.append({"jahr": j, "gruppe": name, "zaehler": wert,
                         "nenner": round(nv[0]) if nv else "", "nenner_art": nv[1] if nv else "",
                         "nenner_herleitung": nv[2] if nv else "", "quote_prozent": quote(wert, nv[0]) if nv else "",
                         "bemerkung": bem})
    return rows


# ── Verknüpfte Einheiten: Wer aus dem Adressbuch hat ein Telefon? ────────────────────────────────────
def adressbuch_mit_telefon(A: list[dict], links: list[dict]) -> list[dict]:
    """Personen im Einwohnerverzeichnis 1883–84 und 1900, die über links/ptt_ab.csv.gz (sicher, wahrscheinlich) in
    einem gleichzeitigen Telefonbuch stehen, nach Gruppe. Untergrenze: nicht jede Person wird wiedergefunden."""
    hat: dict = defaultdict(set)
    for l in links:
        if l["city"] == "bern" and l["tier"] in STUFEN and int(l["ptt_year"]) in AB_JAHRE.get(l["ab_volume"], ()):
            hat[l["ab_volume"]].add(l["ab_id"])
    rows = []
    for band in ("1883", "1900"):
        z: Counter = Counter()
        t: Counter = Counter()
        for a in A:
            if a["city"] != "bern" or a["volume"] != band or a["kind"] != "einwohner" or a["entry_type"] != "person":
                continue
            f = frau(f"{a['civil_status']} {a['title']}", a["forename"], a["occupation"], a["text"])
            s = sektor(a["occupation"], a["title"], f == "witwe")
            gr = ["Personen im Einwohnerverzeichnis", {"1": "1. Sektor", "2": "2. Sektor", "3": "3. Sektor", "ohne": "ohne Erwerb (Privatier, Rentier)",
                                                         "unbestimmt": "Angabe ohne Sektor", "": "keine Angabe"}[s]]
            if f:
                gr.append("Frauen")
            if f == "witwe":
                gr.append("Witwen")
            if gruppe("aerzte_med", erste_angabe(a["occupation"]), a["title"]):
                gr.append("Ärzte (mit Titel «Dr. med.»)")
            if gruppe("spezerei", erste_angabe(a["occupation"])):
                gr.append("Spezereihandlungen")
            for g in gr:
                z[g] += 1
                t[g] += a["id"] in hat[band]
        for g in ("Personen im Einwohnerverzeichnis", "1. Sektor", "2. Sektor", "3. Sektor", "ohne Erwerb (Privatier, Rentier)",
                  "Angabe ohne Sektor", "keine Angabe", "Frauen", "Witwen", "Ärzte (mit Titel «Dr. med.»)", "Spezereihandlungen"):
            rows.append({"band": "1883–84" if band == "1883" else band, "telefonbuecher": "/".join(map(str, AB_JAHRE[band])),
                         "gruppe": g, "personen": z[g], "mit_telefon": t[g],
                         "anteil_prozent": quote(t[g], z[g]) if z[g] else ""})
    return rows


# ── Stichprobe ───────────────────────────────────────────────────────────────────────────────────────
SP_FELDER = ["id", "jahr", "entity_type", "name1", "name2", "supplement", "surname", "forename", "initials", "title",
             "occupation", "art", "frau", "sektor", "soll_art", "soll_frau", "soll_sektor", "richtig", "bemerkung"]


def stichprobe_ziehen(P: list[dict], n: int, seed: int, ohne: set[str] = frozenset()) -> list[dict]:
    rng = random.Random(seed)
    out = []
    for j in sorted(BAND):
        E = sorted((x for x in P if x["municipality_1914"] == STADT and int(x["year"]) == j and x["refcode"] == BAND[j]),
                   key=lambda x: x["id"])
        for x in rng.sample([x for x in E if x["id"] not in ohne], n):
            r = lies_eintrag(x)
            out.append({**{k: x[k] for k in SP_FELDER if k in x}, "jahr": j, "art": r["art"], "frau": r["frau"], "sektor": r["sektor"],
                        "soll_art": "", "soll_frau": "", "soll_sektor": "", "richtig": "", "bemerkung": ""})
    return out


def trefferquote(pfad=None, damals: bool = False) -> dict:
    """Beurteilte Stichprobe: Die Zuordnung wird aus den gespeicherten Feldern neu gerechnet und mit soll_* verglichen.

    damals=True vergleicht stattdessen die Zuordnung, die beim Ziehen galt (Spalten art, frau, sektor).
    «unbestimmt» und leer gelten beide als «kein Sektor erkennbar».
    """
    pfad = pfad or STICHPROBE_3
    rows = [r for r in open_csv(pfad) if r["soll_art"]] if pfad.exists() else []
    out = {"n": len(rows), "art": 0, "frau": 0, "sektor": 0, "alle": 0, "fehler": []}

    def kein(v: str) -> str:
        return "" if v == "unbestimmt" else v
    for r in rows:
        x = {k: r[k] for k in ("art", "frau", "sektor")} if damals else lies_eintrag(r)
        ok = [x["art"] == r["soll_art"], x["frau"] == r["soll_frau"], kein(x["sektor"]) == kein(r["soll_sektor"])]
        out["art"] += ok[0]
        out["frau"] += ok[1]
        out["sektor"] += ok[2]
        out["alle"] += all(ok)
        if not all(ok):
            out["fehler"].append([r["id"], f"{r['name1']} {r['name2']} | {r['supplement']}",
                                  f"{x['art']}/{x['frau']}/{x['sektor']}", f"{r['soll_art']}/{r['soll_frau']}/{r['soll_sektor']}"])
    return out


# ── Ausgabe ──────────────────────────────────────────────────────────────────────────────────────────
def zahl(x) -> str:
    """1 234 und 12,3 (Schweizer Schreibweise mit schmalem Leerzeichen als Tausendertrenner)."""
    if x == "" or x is None:
        return "–"
    if isinstance(x, float):
        return (f"{x:.2f}" if abs(x) < 1 else f"{x:.1f}").replace(".", ",")
    return f"{int(x):,}".replace(",", " ")


def tabellen(g: dict, st: list[dict], ab: list[dict], adr: list[dict], tq: dict, stand: dict) -> str:
    L = []
    L.append(f"Stand der Daten: `data/norm/ptt_entries.csv.gz` mit {zahl(stand['ptt_eintraege'])} Einträgen, davon "
             f"{zahl(stand['ptt_be_fenster'])} im Kanton Bern 1909–1914.\n")
    L.append("**Gemeinden um 1910: Grössenklasse**\n")
    L.append("| Einwohner 1910 | Einheiten | mit Telefon | Einwohner | Einträge | Einträge je 100 Einw. | Median der Einheiten |")
    L.append("|---|---:|---:|---:|---:|---:|---:|")
    for k, c in g["klassen"].items():
        L.append(f"| {k} | {c['n']} | {c['mit_telefon']} ({c['anteil_mit_telefon']} %) | {zahl(c['bev'])} | {zahl(c['eintraege'])} | {zahl(float(c['je_100']))} | {zahl(float(c['median']))} |")
    c = g["gesamt"]
    L.append(f"| alle | {c['n']} | {c['mit_telefon']} ({c['anteil_mit_telefon']} %) | {zahl(c['bev'])} | {zahl(c['eintraege'])} | {zahl(float(c['je_100']))} | {zahl(float(c['median']))} |")
    c = g["ohne_bern"]
    L.append(f"\nAb 5000 Einwohnern ohne die Stadt Bern: {c['n']} Einheiten, {zahl(float(c['je_100']))} Einträge je 100 Einwohner (Median {zahl(float(c['median']))}).")
    L.append("\n**Gemeinden um 1910: Erwerbsstruktur**\n")
    L.append("| Erwerbsstruktur 1910 | Einheiten | mit Telefon | Einwohner | Einträge je 100 Einw. | Median der Einheiten |")
    L.append("|---|---:|---:|---:|---:|---:|")
    for k, c in g["sektorgruppen"].items():
        L.append(f"| {k} | {c['n']} | {c['mit_telefon']} ({c['anteil_mit_telefon']} %) | {zahl(c['bev'])} | {zahl(float(c['je_100']))} | {zahl(float(c['median']))} |")
    L.append("\n**Grösse × Erwerbsstruktur: Median der Einträge je 100 Einwohner (Zahl der Einheiten); in Klammern nichts, wenn weniger als 5**\n")
    L.append("| Einwohner 1910 | " + " | ".join(s.split(" (")[0] for s in SEKTORGRUPPEN) + " |")
    L.append("|---|" + "---:|" * len(SEKTORGRUPPEN))
    for k, zeile in g["kreuz"].items():
        L.append(f"| {k} | " + " | ".join(
            (f"{zahl(float(c['median']))} ({c['n']})" if c["n"] >= 5 else f"– ({c['n']})") for c in zeile.values()) + " |")
    L.append("\n**Grösse × Erwerbsstruktur: Einträge je 100 Einwohner, alle Einheiten der Zelle zusammen**\n")
    L.append("| Einwohner 1910 | " + " | ".join(s.split(" (")[0] for s in SEKTORGRUPPEN) + " |")
    L.append("|---|" + "---:|" * len(SEKTORGRUPPEN))
    for k, zeile in g["kreuz"].items():
        L.append(f"| {k} | " + " | ".join((zahl(float(c["je_100"])) if c["n"] >= 5 else "–") for c in zeile.values()) + " |")
    L.append("\n**Innerhalb der Grössenklasse: Hälfte unter und ab dem Median des Sektoranteils (Einträge je 100 Einwohner, zusammen / Median)**\n")
    L.append("| Einwohner 1910 | 3. Sektor: Median | darunter | ab Median | 1. Sektor: Median | darunter | ab Median |")
    L.append("|---|---:|---:|---:|---:|---:|---:|")
    for k, h in g["haelften"].items():
        def paar(c: dict) -> str:
            return f"{zahl(float(c['je_100']))} / {zahl(float(c['median']))}"
        L.append(f"| {k} | {zahl(float(h['s3_prozent']['median']))} % | {paar(h['s3_prozent']['unter'])} | {paar(h['s3_prozent']['ab'])} | "
                 f"{zahl(float(h['s1_prozent']['median']))} % | {paar(h['s1_prozent']['unter'])} | {paar(h['s1_prozent']['ab'])} |")
    L.append("\n**Rangkorrelation (Spearman) der Einträge je 100 Einwohner mit Grösse und Sektoranteilen**\n")
    L.append("| Einwohner 1910 | Einwohner | 1. Sektor | 2. Sektor | 3. Sektor |")
    L.append("|---|---:|---:|---:|---:|")
    for k, r in g["rang"].items():
        L.append(f"| {k} | " + " | ".join(zahl(float(r[f])) for f in ("bev_1910", "s1_prozent", "s2_prozent", "s3_prozent")) + " |")
    L.append("\n**Stadt Bern: Telefon nach Gruppen**\n")
    jahre = sorted({r["jahr"] for r in st})
    L.append("| Gruppe | " + " | ".join(f"{j}: Buch | Nenner | Quote" for j in jahre) + " |")
    L.append("|---|" + "---:|---:|---:|" * len(jahre))
    for name in dict.fromkeys(r["gruppe"] for r in st):
        zellen = []
        for j in jahre:
            r = next((r for r in st if r["jahr"] == j and r["gruppe"] == name), None)
            zellen.append(f"{zahl(r['zaehler'])} | {zahl(r['nenner'])} | {zahl(float(r['quote_prozent'])) + ' %' if r['quote_prozent'] != '' else '–'}"
                          if r else "– | – | –")
        L.append(f"| {name} | " + " | ".join(zellen) + " |")
    L.append("\n**Stadt Bern: Telefon neben Adressbuch**\n")
    L.append("| Gruppe | Adressbuch 1883–84 | Quote | Telefon 1885 | Quote | Telefon je 100 im Adressbuch | Adressbuch 1900 | Quote | Telefon 1900 | Quote | Telefon je 100 im Adressbuch |")
    L.append("|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|")
    for r in ab:
        L.append("| " + r["gruppe"] + " | " + " | ".join(
            f"{zahl(r[f'ab_{b}'])} | {zahl(r[f'ab_quote_{b}'])}{' %' if r[f'ab_quote_{b}'] != '' else ''} | {zahl(r[f'tel_{j}'])} | "
            f"{zahl(r[f'tel_quote_{j}'])}{' %' if r[f'tel_quote_{j}'] != '' else ''} | {zahl(r[f'je_100_{j}'])}"
            for b, j in (("1883", 1885), ("1900", 1900))) + " |")
    L.append("\n**Stadt Bern: Personen des Adressbuchs mit Telefon (über die Verknüpfung, Stufen sicher und wahrscheinlich)**\n")
    L.append("| Gruppe | 1883–84: Personen | mit Telefon 1884–86 | Anteil | 1900: Personen | mit Telefon 1900–01 | Anteil |")
    L.append("|---|---:|---:|---:|---:|---:|---:|")
    for name in dict.fromkeys(r["gruppe"] for r in adr):
        a, b = (next(r for r in adr if r["gruppe"] == name and r["band"] == bd) for bd in ("1883–84", "1900"))
        L.append(f"| {name} | {zahl(a['personen'])} | {zahl(a['mit_telefon'])} | {zahl(a['anteil_prozent'])} % | "
                 f"{zahl(b['personen'])} | {zahl(b['mit_telefon'])} | {zahl(b['anteil_prozent'])} % |")
    L.append("\n**Stichproben zur Zuordnung (Art des Eintrags, Frau/Witwe, Sektor)**\n")
    L.append("| Stichprobe | Einträge | Art richtig | Frau/Witwe richtig | Sektor richtig | alle drei | Quote |")
    L.append("|---|---:|---:|---:|---:|---:|---:|")
    for k, name in (("1_damals", "1, mit den Regeln beim Ziehen"), ("2_damals", "2, mit den Regeln beim Ziehen"),
                    ("3_damals", "3, mit den Regeln beim Ziehen (gültige Messung)"),
                    ("1", "1, mit den heutigen Regeln"), ("2", "2, mit den heutigen Regeln"), ("3", "3, mit den heutigen Regeln")):
        t = tq[k]
        if t["n"]:
            L.append(f"| {name} | {t['n']} | {t['art']} | {t['frau']} | {t['sektor']} | {t['alle']} | {zahl(round(100 * t['alle'] / t['n'], 1))} % |")
    return "\n".join(L)


def neben_adressbuch(st: list[dict]) -> list[dict]:
    """Telefonquote neben der Adressbuchquote aus adressbuecher-bern, wo die Gruppen übereinstimmen."""
    ab = {(r["band"], r["gruppe"]): r for r in open_csv(ADRESSBUCH)}
    tel = {(r["jahr"], r["gruppe"]): r for r in st}
    paare = [("Personen je Einwohner", "Personen je Einwohner", "Personen mit Eintrag je Einwohner"),
             ("Personen je Haushalt", "Personen je Haushalt", "Personen mit Eintrag je Haushalt"),
             ("Firmen", "Firmen", "Firmen"),
             ("Frauen", "Frauen", "Frauen"), ("Witwen", "Witwen", "Witwen"),
             ("1. Sektor", "1. Sektor", "1. Sektor"), ("2. Sektor", "2. Sektor", "2. Sektor"), ("3. Sektor", "3. Sektor", "3. Sektor"),
             ("Ärzte (mit Titel «Dr. med.»)", "Ärzte (dazu Titel «Dr. med.»)", "Ärzte (dazu Titel «Dr. med.»)"),
             ("Spezereihandlungen", "Spezereihandlungen (Rubrik im Berufsregister)", "Spezereihandlungen")]
    rows = []
    for name, ga, gt in paare:
        row = {"gruppe": name}
        for band, j in (("1883", 1885), ("1900", 1900)):
            a, t = ab.get((band, ga)), tel.get((j, gt))
            row[f"ab_{band}"] = int(a["zaehler"]) if a else ""
            row[f"ab_quote_{band}"] = float(a["quote_prozent"]) if a and a["quote_prozent"] else ""
            row[f"tel_{j}"] = t["zaehler"] if t else ""
            row[f"tel_quote_{j}"] = float(t["quote_prozent"]) if t and t["quote_prozent"] != "" else ""
            row[f"je_100_{j}"] = round(100 * t["zaehler"] / int(a["zaehler"]), 1) if a and t and int(a["zaehler"]) else ""
        rows.append(row)
    return rows


SITE_GRUPPEN = dict(zip(SEKTORGRUPPEN, ("bauer", "gemischt", "gewerbe", "dienst")))
SITE_ZEILEN = (("hh", "Personen mit Eintrag je Haushalt"), ("wohnung", "Personen mit Wohnungsanschluss"),
               ("s2", "2. Sektor"), ("s3", "3. Sektor"), ("aerzte", "Ärzte (dazu Titel «Dr. med.»)"), ("frauen", "Frauen"))


def site_daten(kreuz: dict, st: list[dict], tq: dict) -> dict:
    """Auszug für die Seite (#/infrastruktur): Kreuztabelle Grösse × Erwerbsstruktur und die Stadt Bern nach Gruppen."""
    jahre = sorted({int(r["jahr"]) for r in st})
    zeile = {(int(r["jahr"]), r["gruppe"]): r for r in st}
    return {
        "n": kreuz["n"],
        "gruppen": list(SITE_GRUPPEN.values()),
        "kreuz": [[k, [[c["median"], c["n"]] if c["n"] else [None, 0] for c in (z[g] for g in SEKTORGRUPPEN)]]
                  for k, z in kreuz["kreuz"].items()],
        "jahre": jahre,
        "stadt": [[key, [[int(zeile[(j, g)]["zaehler"]), int(zeile[(j, g)]["nenner"]), zeile[(j, g)]["nenner_art"]]
                         for j in jahre]] for key, g in SITE_ZEILEN],
        "stichprobe": [tq["alle"], tq["n"]],
    }


def site() -> None:
    """site/data/durchdringung_bern.json.gz aus den abgelegten Ergebnissen (rechnet nichts neu)."""
    daten = json.loads(OUT_JSON.read_text(encoding="utf-8"))
    path = ROOT / "site" / "data" / "durchdringung_bern.json.gz"
    path.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(path, "wt", encoding="utf-8") as f:
        json.dump(site_daten(daten["gemeinden"], open_csv(OUT_STADT), daten["stichprobe"]["3_damals"]), f,
                  ensure_ascii=False, separators=(",", ":"))
    print(path.relative_to(ROOT))


def ersetze_block(text: str, block: str) -> str:
    a, b = "<!-- TABELLEN:START -->", "<!-- TABELLEN:ENDE -->"
    if a not in text or b not in text:
        return text
    return text[:text.index(a) + len(a)] + "\n" + block + "\n" + text[text.index(b):]


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--stichprobe", type=int, default=0, help="Stichprobe 3 neu ziehen: Einträge je Jahr (überschreibt die Urteile)")
    args = ap.parse_args()
    P = open_csv(NORM / "ptt_entries.csv.gz")
    if args.stichprobe:
        ohne = {r["id"] for p in (STICHPROBE, STICHPROBE_2) if p.exists() for r in open_csv(p)}
        write_csv(STICHPROBE_3, SP_FELDER, stichprobe_ziehen(P, args.stichprobe, SEED[3], ohne))
        print("Stichprobe gezogen:", STICHPROBE_3)
        return
    stand = {"ptt_eintraege": len(P),
             "ptt_be_fenster": sum(1 for x in P if x["canton"] == "BE" and int(x["year"]) in END_YEARS)}
    gem = gemeinden(P)
    write_csv(OUT_GEMEINDEN, list(gem[0]), gem)
    kreuz = kreuztabelle(gem)
    w = stadt_werte()
    z = {j: stadt_zaehlen(P, j) for j in BAND}
    st = stadt_zeilen(w, z)
    write_csv(OUT_STADT, list(st[0]), st)
    ab = neben_adressbuch(st)
    adr = adressbuch_mit_telefon(open_csv(NORM / "ab_entries.csv.gz"), open_csv(ROOT / "links" / "ptt_ab.csv.gz"))
    tq = {"1_damals": trefferquote(STICHPROBE, damals=True), "2_damals": trefferquote(STICHPROBE_2, damals=True),
          "3_damals": trefferquote(STICHPROBE_3, damals=True), "1": trefferquote(STICHPROBE), "2": trefferquote(STICHPROBE_2),
          "3": trefferquote(STICHPROBE_3)}
    OUT_JSON.write_text(json.dumps({"stand": stand, "gemeinden": kreuz, "stadt_zaehler": z, "neben_adressbuch": ab,
                                    "adressbuch_mit_telefon": adr, "stichprobe": tq},
                                   ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    block = tabellen(kreuz, st, ab, adr, tq, stand)
    if DOC.exists():
        DOC.write_text(ersetze_block(DOC.read_text(encoding="utf-8"), block), encoding="utf-8")
    print(block)


if __name__ == "__main__":
    sys.exit(site() if sys.argv[1:] == ["site"] else main())

"""Feine Berufsliste für die Wanderungen (M10): einzelne Berufe statt Berufsklassen.

Die Klassen in scripts/occupations.py sind für Karten gedacht und zu grob, um zu sagen, ob
zwei Einträge dieselbe Person sein können: «Metzger» und «Bäcker» stehen beide unter
Lebensmittel, «Schuhmacher» und «Küfer» beide unter Handwerk. Hier steht jeder Beruf für
sich, deutsch, französisch und italienisch, mit den üblichen Abkürzungen, und mit einer
Gruppe verwandter Berufe, zwischen denen ein Wechsel naheliegt (Bäcker ↔ Konditor,
Fürsprecher ↔ Richter, Wirt ↔ Hotelier ↔ Pension).

`fine(text)` gibt die Berufe eines Textes als Menge zurück; Strassennamen («Schneiderg.»,
«Metzgergasse») werden vorher entfernt. `compare(a, b)` sagt `gleich`, `verwandt`, `anders`
oder `""` (eine Seite ohne erkannten Beruf).

Allgemeine Angaben (Commis, Kaufmann, Handlanger, Privat …) stehen in WEAK: sie zählen bei
Gleichheit weniger, weil sie für viele Menschen gelten.
"""

from __future__ import annotations

import re

# (Schlüssel, Gruppe, Muster). Muster ohne führendes \b greifen auch in Zusammensetzungen
# («Damenschneiderin», «Schreinermeister»).
FINE: list[tuple[str, str, str]] = [
    # Medizin
    ("arzt", "medizin", r"\barzt|ärztin|chefarzt|\bdr\.? ?med|\bmed\.? ?dr|médecin|medecin|docteur|medico|\bméd\b|chirurg|spezialarzt|augenarzt|frauenarzt|kinderarzt"),
    ("zahnarzt", "zahn", r"zahnarzt|zahnärzt|dentist|zahntechn|médecin-dentiste|chirurgien-dentiste|odontoiatra"),
    ("tierarzt", "tier", r"tierarzt|vétérinaire|veterinär|veterinario|\bvet\.|hufschmied"),
    ("apotheker", "apotheke", r"apothek|pharmac|farmac"),
    ("drogist", "apotheke", r"drogist|drogerie|droguerie|droguiste|drogheria"),
    ("hebamme", "pflege", r"hebamme|sage-femme|levatrice"),
    ("pflege", "pflege", r"krankenpfleg|krankenwärter|infirmi|diakonisse|masseu|wärterin"),
    # Recht, Verwaltung, Militär
    ("fürsprecher", "recht", r"fürsprech|advokat|avocat|avvocato|rechtsanw|\bjur\.|jurist|\blic\.? ?jur|procureur|procuratore"),
    ("notar", "recht", r"notar|notaire|notaio"),
    ("richter", "recht", r"richter|\bjuge\b|giudice|gerichtspräs|président du tribunal|bundesricht|oberricht|amtsrichter"),
    ("gerichtsschreiber", "recht", r"gerichtsschreib|greffier|cancelliere|gerichtssubst"),
    ("polizist", "polizei", r"polizist|polizei|landjäger|gendarm|agent de police|guardia|stadtpolizist|detektiv"),
    ("weibel", "verwaltung", r"weibel|huissier|usciere|abwart|concierge|portier|hauswart"),
    ("kanzlist", "verwaltung", r"kanzlist|registrator|commis de chancellerie|kanzleisekr|copiste|archivar"),
    ("beamter", "verwaltung", r"beamt|fonctionnaire|funzionario|verwalter|administrateur|amtsschreib|einnehmer|receveur|steuerbeamt"),
    ("sekretär", "verwaltung", r"sekretär|secrétaire|secretaire|segretario"),
    ("staatsrat", "politik", r"regierungsrat|staatsrat|conseiller d.?[ée]tat|consigliere di stato|nationalrat|ständerat|conseiller national|cons\.? ?naz|bundesrat"),
    ("gemeindepräsident", "politik", r"gemeindepräs|gemeindeammann|stadtpräs|syndic|sindaco|maire\b|gemeinderat|stadtrat|conseiller municipal|municipal"),
    ("zoll", "verwaltung", r"zoll|douan|dogan|grenzwächt|garde-frontière"),
    ("offizier", "militär", r"instruktor|instructeur|istruttore|oberst|colonel|major\b|hauptmann|capitaine|capitano|oberleutn|leutnant|lieutenant|kreiskommand|offizier|officier|adjutant|feldweibel|tambour|trompeter"),
    # Post, Bahn, Verkehr
    ("post", "post", r"postcommis|postbeamt|posthalter|postverwalt|buraliste|commis postal|commis de poste|ufficiale postale|postangest|postpacker|postgehilf|postillon"),
    ("briefträger", "post", r"briefträg|facteur|portalettere|briefbot|postbote"),
    ("telegraph", "post", r"telegraph|télégraph|telegraf|telephonist|téléphoniste|telefonist"),
    ("bahn", "bahn", r"kondukteur|conducteur|weichenwärt|wagenwärt|bahnwärt|stationsvorst|chef de gare|capostazione|bahnarbeit|rangier|zugführer|bremser|stationsbeamt|bahnangest|expedient|güterarb|employé (?:aux|de) c\.? ?f\.? ?f|s\.? ?b\.? ?b\.?-?angest"),
    ("lokomotivführer", "bahn", r"lokomotivf|mécanicien de locomotive|macchinista|heizer|chauffeur de locomotive"),
    ("tram", "bahn", r"tramkondukt|tramführer|wattman|wagenführer|tramangest"),
    ("fuhrhalter", "fuhr", r"fuhrhalter|fuhrhalterei|voiturier|vetturale|camionn|fuhrmann|lohnkutsch|charretier|carrettiere|kutscher|cocher|fahrknecht|fuhrknecht"),
    ("spediteur", "fuhr", r"spedit|speditor|expéditeur|expéditions|spedizion|transitaire|transporte"),
    ("chauffeur", "fuhr", r"chauffeur|autoführer|taxi|garage|automobil|autovermiet"),
    ("schiffer", "fuhr", r"schiffer|schiffmann|batelier|barcaiolo|dampfschiff|navigation|matrose"),
    ("dienstmann", "fuhr", r"dienstmann|commissionnaire|facchino|packträger|gepäckträg"),
    # Bildung, Kirche, Kunst
    ("lehrer", "lehre", r"lehrer|lehrerin|instituteur|institutrice|maestro|maestra|\bregent|schulmeister|arbeitslehrer|sekundarlehr|bezirkslehr"),
    ("professor", "lehre", r"professor|professeur|professore|\bprof\b|\bprof\.|dozent|privatdozent|rektor|recteur|gymnasiallehr"),
    ("pfarrer", "kirche", r"pfarrer|\bpfr\.|pasteur|\bcuré|parroco|pastor|vikar|vicaire|prediger|kaplan|chapelain|evangelist|missionar|missionnaire|diakon|sigrist|sakristan|sacristain"),
    ("musiker", "kunst", r"musiker|musicien|musicista|musiklehr|maître de musique|organist|kapellmeist|klavierlehr|pianist|violin|gesanglehr|sänger|chanteur|cantante"),
    ("kunstmaler", "kunst", r"kunstmaler|artiste peintre|pittore|\bartiste\b|künstler|graveur|graveuse|xylogr|ziseleur|ciseleur"),
    ("bildhauer", "kunst", r"bildhauer|sculpteur|scultore|marmor|marbrier|marmista|steinmetz|grabstein"),
    ("photograph", "kunst", r"photogr|fotogr|\bphot\b|\bphot\."),
    ("zeichner", "technik", r"zeichner|dessinateur|disegnatore|lithogr|plankopist|technischer zeichner"),
    ("journalist", "presse", r"redaktor|redakteur|rédacteur|redattore|journalist|giornalist|schriftsteller|écrivain|publizist"),
    # Technik, Bau
    ("ingenieur", "technik", r"ingenieur|ingénieur|ingegnere|\bing\.|\bing\b|ingen\."),
    ("techniker", "technik", r"techniker|technicien|tecnico|bautechn|\btechn\."),
    ("geometer", "technik", r"geometer|géomètre|geometra|grundbuchgeom|vermesser|konkordatsgeom"),
    ("architekt", "technik", r"architekt|architecte|architetto|\barch\.|\barchit\.|métreur"),
    ("baumeister", "bau", r"baumeister|baugeschäft|baugesch|bauunternehm|entrepreneur|impresario|imprenditore|bauführer|maurermeister|polier|pulier|contremaître|capomastro"),
    ("maurer", "bau", r"maurer|maçon|macon|muratore|pflästerer|paveur|selciatore|cementier|betonier"),
    ("steinhauer", "bau", r"steinhauer|tailleur de pierre|scalpellino|steinbrech|carrier"),
    ("gipser", "maler", r"gipser|gypser|plâtrier|platrier|gessatore|stuck"),
    ("maler", "maler", r"\bmaler|flachmaler|malermeister|dekorationsmal|zimmermaler|schildermal|\bpeintre\b|peintre en bâtiment|imbianchino|verniciatore|lackierer|vernisseur"),
    ("zimmermann", "holz", r"zimmerm|zimmerei|zimmerer|charpent|carpentiere|falegname carpentiere"),
    ("schreiner", "holz", r"schreiner|menuisier|ébéniste|ebeniste|falegname|tischler|möbelschr|modellschr|bauschreiner|parkett|parquet(?:eur|ier|erie)"),
    # Glaser eigener Beruf (Messung Berufsübersetzung: 6 von 12 Treffern für «Schreiner» waren Glaser)
    ("glaser", "holz", r"glaser|vitrier|vitrerie|vetraio|vetreria|bleiglas|glashandl|miroitier"),
    ("drechsler", "holz", r"drechsler|tourneur|tornitore"),
    ("küfer", "holz", r"küfer|kuefer|tonnelier|bottaio|kübler|böttcher|fassbind"),
    ("wagner", "holz", r"wagner(?!-)|charron|carradore|carrossier|wagenbau|sattler und wagner"),
    ("säger", "holz", r"säger|sägerei|scierie|segheria|holzhandl|holzhänd|commerce de bois|marchand de bois"),
    ("holzschnitzer", "holz", r"holzschnitz|bildschnitz|sculpteur sur bois"),
    ("dachdecker", "bau", r"dachdeck|couvreur|copritetto|schieferdeck"),
    ("hafner", "bau", r"hafner|ofenbau|poêlier|poelier|fumiste|stufaio"),
    ("spengler", "metall", r"spengler|ferblant|lattoniere|stagnino|klempner|flaschner"),
    ("installateur", "elektro", r"installat|sanitär|appareilleur|idraulico|gas- und wasser|wasserleitung"),
    ("elektriker", "elektro", r"elektrik|électricien|electricien|elettricista|elektromont|monteur-électr|elektrotechn|électrotechn|elektr\.? install"),
    ("mechaniker", "metall", r"mechanik|mécanicien|mecanicien|meccanico|\bmech\.|\bmécan\.|\bmecan\.|maschinenbau|velohandl|cycles|vélos|motos|feinmechan"),
    ("schlosser", "metall", r"schlosser|serrurier|fabbro|bauschloss|kunstschloss"),
    ("schmied", "metall", r"schmied|maréchal|marechal|forgeron|maniscalco|hufbeschlag"),
    ("dreher", "metall", r"dreher|eisendreher|tourneur sur métaux|tornitore in ferro"),
    ("giesser", "metall", r"giesser|gießer|fondeur|fonditore|giesserei|fonderie"),
    ("zinngiesser", "metall", r"zinngiess|potier d.?étain|kupferschmied|chaudronnier|calderaio|gürtler"),
    ("maschinist", "metall", r"maschinist|machiniste|monteur|heizer|chauffeur de chaudière"),
    ("uhrmacher", "uhren", r"uhrmach|horloger|orologiaio|horlogerie|rhabilleur|régleur|regleuse|remonteur|repasseur|termineur"),
    ("uhrenbestandteile", "uhren", r"boîtier|boitier|boîtes|boites|cadran|pierriste|assortiment|échappement|spiraux|ressorts|aiguilles|polisseu|finisseu|emboît|sertisseu|doreur de|graveur de"),
    ("goldschmied", "uhren", r"goldschmied|bijout|orfèvre|orfevre|orefice|juwelier|joaillier|silberarb"),
    ("optiker", "uhren", r"optiker|opticien|ottico|optique"),
    # Kleider, Textil
    ("schneider", "kleider", r"schneider|tailleur(?! de pierre)|tailleuse|couturi|coutur\.|sarto|sarta|confection|konfektion"),
    ("näherin", "kleider", r"näherin|weissnäh|weißnäh|lingère|lingere|cucitrice|flickerin|lingerie"),
    ("modistin", "kleider", r"modist|modes\b|modiste|chapeli|hutmach|hutgesch|chapeaux|cappellaio|pelzhand|kürschner|fourreur|pellicciaio"),
    ("glätterin", "wäsche", r"glätter|glaetter|repasseuse|stiratrice|wäscher|blanchiss|lavandaia|wäscherei|färber|teintur|tintor|chemische wasch|appreteur|apprêteur"),
    ("strickerin", "kleider", r"strickerin|tricot|maglier|bonneteri|wirkerin"),
    ("schuhmacher", "schuh", r"schuhmach|schuster|cordonn|calzolaio|schuhhandl|schuhwaren|chaussures|calzature|schuhgesch"),
    ("sattler", "leder", r"sattler|sellier|sellaio|tapezier|tapissier|tappezziere|polster|ameublement|tapisserie|riemer|bourrelier"),
    ("gerber", "leder", r"gerber|tanneur|conciatore|lederhandl|cuirs|pelleter"),
    ("sticker", "textil", r"sticker|stickerei|brod(?:erie|eur|euse)|ricam|stickfabr|nachstick|ferggerei|fergger|stickereifabr|broderies"),
    ("weber", "textil", r"weber|weberei|tisserand|tissage|tessitor|spinner|spinnerei|filateur|filature|seidenwind|zettler|zwirner|winderin|ferggerin|posament|bandweber|rubans|passementier"),
    ("tuchhändler", "textil", r"tuchhandl|tuchgesch|draperie|drapier|tessuti|stoffe|manufaktur|manufactur|nouveautés|weisswar|weißwar|leinen|aussteuer|trousseau|mercerie|merceria|kurzwar|bonneterie"),
    # Lebensmittel
    ("metzger", "fleisch", r"metzg|boucher|boucherie|charcut|macellaio|salumier|wurster|schlächter|fleischhandl"),
    # Viehhändler und Viehinspektor eigene Berufe (Messung: «Metzger» fand Viehhändler und Viehinspektoren)
    ("viehhändler", "fleisch", r"viehhänd|viehhandl|pferdehänd|pferdehandl|marchand de bétail|commerce de bétail|marchand de chevaux|commerciante di bestiame|negoziante di bestiame"),
    ("viehinspektor", "verwaltung", r"viehinspekt|inspecteur du bétail|ispettore del bestiame"),
    ("bäcker", "back", r"bäck|baeck|backer|boulang|panettiere|prestinaio|panificio"),
    ("konditor", "back", r"konditor|conditor|confiseur|confiserie|pâtiss|patiss|pasticc|zuckerbäck|chocolat"),
    ("müller", "mühle", r"\bmüller\b|mühle|mühlenbes|meunier|moulin|mugnaio|mulino|getreide|grains|farines"),
    ("käser", "milch", r"käser|käserei|fromag|casaro|caseificio|senn\b|milchhändl|milchhandl|milchgesch|laiti|latteria|molkerei|butter"),
    ("spezierer", "laden", r"spezer|épicer|epicer|droghier|kolonialw|lebensmittel|comestible|krämer|krämerei|denrées|consum|konsum|viktualien|negozio|négociant en denrées|droguerie et épicerie"),
    ("weinhändler", "getränke", r"weinhand|weinhändl|marchand de vins|négociant en vins|vins\b|commerce de vins|vinicolt|vini\b|weinbau|vigneron|weinbauer|küferei und wein|liqueur|spirituos|liquori|distill|brennerei"),
    ("bierbrauer", "getränke", r"bierbrau|brauerei|brasseur|birrer|bierdepot|bierdépôt|bierhandl|mineralwass|eaux gazeuses|limonad|acque gazose"),
    ("gemüsehändler", "laden", r"gemüse|légumes|primeur|ortolan|fruchthandl|obsthandl|fruits|frutta|südfrücht|geflügel|volaille|wildpret|comestibles fins|fischhandl|poissonn|eierhandl"),
    # Gastgewerbe
    ("wirt", "gast", r"\bwirt|\bwirth|speisewirt|gastwirt|weinwirt|aubergiste|cafetier|café|cafe\b|cafés|restaurant|restaurat|\brest\.|osteria|oste\b|trattoria|bierhalle|weinstube|pinte|brasserie|buvette|gasthaus|gasthof|auberge|albergo|\b(?:z\.?|zum|zur) ?(?:löwen|leuen|rössli|ochsen|kreuz|sternen|bären|adler|hirschen|krone|engel|schwanen|rebstock|traube|linde|hecht|falken|frohsinn|sonne|hirsch|post|bahnhof|rose|schäfli|lamm|storchen|rabe|baum|freihof|sternen|kreuz)"),
    ("hotelier", "gast", r"hotel|hôtel|hotelier|hôtelier|albergatore|kurhaus|gasthof und|hotel garni"),
    ("pension", "gast", r"pension|kosthalter|kosthaus|kostgeber|pensionshalt|pensionnat|famille|gîte"),
    ("koch", "gast", r"\bkoch\b|köchin|cuisinier|cuisinière|cuoco|cuoca|traiteur"),
    ("kellner", "gast", r"kellner|sommelier|sommelière|cameriere|serviertochter|buffetdame|garçon de café"),
    # Druck und Papier
    ("schriftsetzer", "druck", r"setzer|typograph|typographe|tipografo|compositeur|buchdruck|imprim|druckerei|stampatore|tipograf|maschinenmeister|drucker"),
    ("buchbinder", "druck", r"buchbind|relieur|legatore|cartonn|kartonag|papeter|cartoler|papierhandl"),
    ("buchhändler", "druck", r"buchhandl|buchhändl|libraire|librairie|libraio|libreria|verlag|éditeur|editeur|antiquar|musikalienhandl"),
    # Handel und Büro
    ("kaufmann", "büro", r"kaufm|\bkfm|négociant|negociant|\bnég\.|\bnegoz|commerçant|commerciante|handelsmann|grosshändl|grossist|marchand(?! de (?:vins|bois|bétail))|\bmarch\."),
    ("commis", "büro", r"commis(?! (?:postal|de poste|de chancellerie))|\bcommis\b|handlungsgehilf|kontorist|comptoir|bureauangest|büroangest|employé de bureau|impiegato|angestellt|employé|\bempl\.|\bemployée"),
    ("buchhalter", "büro", r"buchhalt|comptable|contabile|kassier|caissier|cassiere|revisor|kassierer|prokurist|fondé de pouvoir|procuratore"),
    ("reisender", "büro", r"reisend|voyageur|viaggiatore|geschäftsreis|handelsreis|commis-voyageur"),
    ("vertreter", "agentur", r"vertreter|représent|rappresent|agent\b|agentur|agence|agenzia|courtier|makler|sensale|liegenschaftsverm|immobili|vermittl|commissionn|generalagent|versicherungsagent"),
    ("bankangestellter", "bank", r"bankangest|bankbeamt|banquier|bankier|banchiere|employé de banque|bankkassier|sparkassa|bankdirekt|bankprokur"),
    ("versicherung", "agentur", r"versicherung|assurance|assicuraz"),
    ("direktor", "leitung", r"direktor|directeur|direttore|\bdir\.|geschäftsführ|gérant|gerente|leiter|vorsteher|chef de|chef du|verwalter|administrat"),
    ("fabrikant", "fabrik", r"fabrikant|fabricant|fabbricante|\bfabr\b|\bfabr\.|\bfab\.|fabrikbes|industriel|industriale"),
    ("fabrikarbeiter", "arbeit", r"fabrikarb|ouvrier de fabrique|operaio|fabrikarbeit|arbeiterin\b|ouvrière|ouvrier\b|arbeiter\b|fabr\.-arb"),
    ("magaziner", "arbeit", r"magazin(?:er|ier)|magasinier|magazziniere|lagerist|packer|emballeur|imballatore|ausläuf|commissionnaire|laufbursch|ausgeher"),
    ("verkäuferin", "laden", r"verkäufer|ladentocht|vendeuse|vendeur|commessa|commesso|demoiselle de magasin|filialleit"),
    ("eisenhändler", "laden", r"eisenhandl|eisenwar|quincaill|ferramenta|ferronnerie|werkzeug|outils|haushaltung|haushaltungsart"),
    ("kohlenhändler", "laden", r"kohlen|charbon|carbone|brennmaterial|combustibles|brennholz|holz- und kohlen"),
    ("tabakhändler", "laden", r"cigarr|zigarr|cigare|tabak|tabac|tabacch|kiosk|kiosque|zeitungsverk"),
    ("hausierer", "laden", r"hausier|colporteur|merciaio ambulante|marktfahr|marktkräm|forain"),
    ("coiffeur", "coiffeur", r"coiffeu|friseu|frisör|barbier|parrucch|perruqu|haarschneid"),
    ("gärtner", "garten", r"gärtner|gaertner|jardinier|giardinier|horticult|handelsgärt|blumenhandl|fleuriste|fiorai|baumschul|pépiniér|kunstgärt"),
    ("landwirt", "land", r"landwirt|landwirth|agricult|agricoltore|cultivateur|contadino|\bbauer\b|bäuerin|fermier|pächter|gutsbesitz|gutsverwalt|landmann|paysan|viehzücht|melker|vacher|sennen"),
    ("förster", "land", r"förster|forstmeist|forestier|forstverwalt|bannwart|garde-forestier|guardaboschi|forstwart"),
    ("knecht", "arbeit", r"knecht|magd|domestique|domest\.|\bdom\.|dienstmagd|dienstbot|servante|serva|domestico|haushälter|ménagère|ménag\.|gouvernante|bonne d.?enfant|kindermädch|zimmermädch|femme de chambre|femme de ménage|putzfrau|spetter|hausmeist|hausknecht|portier"),
    ("handlanger", "arbeit", r"handlanger|taglöhner|tagelöhner|taglohn|journalier|giornaliero|erdarbeit|erdarb\.|manœuvre|manoeuvre|manovale|bauarbeit|ouvrier\b|arbeiter\b|hilfsarbeit|gelegenheitsarb|steinbrecher"),
    ("privat", "privat", r"privat|rentier|rentière|rentiere|\brent\.|partikul|particul|\bpart\b|\bpart\.|propriétaire|\bpropr\.?\b|possidente|vermöglich|pensionierte?\b|retraité|ancien\b|\banc\.|\balt\b|gew\.|gewesen|veuve|witwe"),
    ("student", "lehre", r"\bstud\b|\bstud\.|student|étudiant|studente|schüler|élève|lehrling|apprenti|apprendista|lehrtochter"),
]

WEAK = {"kaufmann", "commis", "handlanger", "knecht", "privat", "landwirt", "fabrikarbeiter", "magaziner",
        "beamter", "sekretär", "direktor", "vertreter", "student", "verkäuferin", "reisender"}

_PATTERNS = [(k, re.compile(p, re.I)) for k, _, p in FINE]
GROUP = {k: g for k, g, _ in FINE}
# Strassen im Berufsfeld: «Schneiderg. 30», «Metzgergasse», «Bäckerstr.», «r. des Boulangers»
_STREET = re.compile(
    r"[\wäöüéèà-]+(?:gasse|gässli|strasse|straße|str\.|erg\.|weg\b|platz|graben|quai)"
    r"|\b(?:rue|r\.|av\.|avenue|ch\.|chemin|via|vicolo|place|pl\.|route|rte)\s+(?:de |des |du |de la |d.)?[\wäöüéèà'-]+", re.I)


def clean(text: str) -> str:
    return _STREET.sub(" ", text or "")


_NEXT_ENTRY = re.compile(r";\s*\d+[a-z]?\b")


def fine(text: str) -> set[str]:
    """Berufe im Text. Je Teil (durch «|» getrennt) nur bis zur ersten Hausnummer nach «;»:
    dahinter stehen in manchen Telefonbuch-Zeilen die Nachbarzeilen («archit.-métreur; av. de
    Lancy; 15 Fontana; Léon-P; architecte; …»)."""
    t = clean(" | ".join(_NEXT_ENTRY.split(part)[0] for part in (text or "").split("|")))
    return {k for k, p in _PATTERNS if p.search(t)}


def compare(a: set[str], b: set[str]) -> str:
    """`gleich`, `verwandt`, `anders`, oder `""` wenn eine Seite keinen erkannten Beruf hat.

    «Privat» allein sagt nichts über den Beruf: steht er nur auf einer Seite, wird er nicht
    als Widerspruch gezählt (Rentner, Witwen und Partikulare hatten vorher einen Beruf).
    """
    if not a or not b:
        return ""
    if a & b:
        return "gleich"
    if {GROUP[k] for k in a} & {GROUP[k] for k in b}:
        return "verwandt"
    if a <= {"privat", "student"} or b <= {"privat", "student"}:
        return ""
    return "anders"


# Bezeichnung je Beruf für die Seite (Suche: «Übersetzungen mitsuchen», Anzeige «≈ Beruf»):
# deutsch, französisch, italienisch, englisch. Die Suche selbst geht über die Muster oben.
LABELS: dict[str, tuple[str, str, str, str]] = {
    "arzt": ("Arzt", "médecin", "medico", "physician"),
    "zahnarzt": ("Zahnarzt", "dentiste", "dentista", "dentist"),
    "tierarzt": ("Tierarzt", "vétérinaire", "veterinario", "veterinarian"),
    "apotheker": ("Apotheker", "pharmacien", "farmacista", "pharmacist"),
    "drogist": ("Drogist", "droguiste", "droghiere", "druggist"),
    "hebamme": ("Hebamme", "sage-femme", "levatrice", "midwife"),
    "pflege": ("Krankenpflege", "infirmier", "infermiere", "nurse"),
    "fürsprecher": ("Fürsprecher", "avocat", "avvocato", "lawyer"),
    "notar": ("Notar", "notaire", "notaio", "notary"),
    "richter": ("Richter", "juge", "giudice", "judge"),
    "gerichtsschreiber": ("Gerichtsschreiber", "greffier", "cancelliere", "court clerk"),
    "polizist": ("Polizist", "agent de police", "agente di polizia", "police officer"),
    "weibel": ("Weibel, Abwart", "huissier, concierge", "usciere, custode", "usher, caretaker"),
    "kanzlist": ("Kanzlist", "commis de chancellerie", "cancellista", "chancery clerk"),
    "beamter": ("Beamter", "fonctionnaire", "funzionario", "civil servant"),
    "sekretär": ("Sekretär", "secrétaire", "segretario", "secretary"),
    "staatsrat": ("Regierungsrat", "conseiller d'État", "consigliere di Stato", "cantonal councillor"),
    "gemeindepräsident": ("Gemeindepräsident", "syndic", "sindaco", "mayor"),
    "zoll": ("Zollbeamter", "douanier", "doganiere", "customs officer"),
    "offizier": ("Offizier, Instruktor", "officier, instructeur", "ufficiale, istruttore", "officer, instructor"),
    "post": ("Postbeamter", "employé postal", "impiegato postale", "post-office clerk"),
    "briefträger": ("Briefträger", "facteur", "portalettere", "postman"),
    "telegraph": ("Telegraphist", "télégraphiste", "telegrafista", "telegraphist"),
    "bahn": ("Bahnangestellter", "employé de chemin de fer", "ferroviere", "railway employee"),
    "lokomotivführer": ("Lokomotivführer", "mécanicien de locomotive", "macchinista", "engine driver"),
    "tram": ("Trambahnangestellter", "employé de tramway", "tranviere", "tram employee"),
    "fuhrhalter": ("Fuhrhalter", "voiturier", "vetturale", "carter"),
    "spediteur": ("Spediteur", "expéditeur", "spedizioniere", "forwarding agent"),
    "chauffeur": ("Chauffeur, Garage", "chauffeur, garage", "autista, garage", "driver, garage"),
    "schiffer": ("Schiffer", "batelier", "barcaiolo", "boatman"),
    "dienstmann": ("Dienstmann", "commissionnaire", "facchino", "porter"),
    "lehrer": ("Lehrer", "instituteur", "maestro", "teacher"),
    "professor": ("Professor", "professeur", "professore", "professor"),
    "pfarrer": ("Pfarrer", "pasteur, curé", "parroco", "clergyman"),
    "musiker": ("Musiker", "musicien", "musicista", "musician"),
    "kunstmaler": ("Kunstmaler", "artiste peintre", "pittore", "artist"),
    "bildhauer": ("Bildhauer", "sculpteur", "scultore", "sculptor"),
    "photograph": ("Photograph", "photographe", "fotografo", "photographer"),
    "zeichner": ("Zeichner", "dessinateur", "disegnatore", "draughtsman"),
    "journalist": ("Redaktor", "rédacteur", "redattore", "editor, journalist"),
    "ingenieur": ("Ingenieur", "ingénieur", "ingegnere", "engineer"),
    "techniker": ("Techniker", "technicien", "tecnico", "technician"),
    "geometer": ("Geometer", "géomètre", "geometra", "surveyor"),
    "architekt": ("Architekt", "architecte", "architetto", "architect"),
    "baumeister": ("Baumeister", "entrepreneur", "impresario edile", "building contractor"),
    "maurer": ("Maurer", "maçon", "muratore", "mason"),
    "steinhauer": ("Steinhauer", "tailleur de pierre", "scalpellino", "stonecutter"),
    "gipser": ("Gipser", "plâtrier", "gessatore", "plasterer"),
    "maler": ("Maler", "peintre en bâtiment", "imbianchino", "house painter"),
    "zimmermann": ("Zimmermann", "charpentier", "carpentiere", "carpenter"),
    "schreiner": ("Schreiner", "menuisier", "falegname", "joiner"),
    "glaser": ("Glaser", "vitrier", "vetraio", "glazier"),
    "drechsler": ("Drechsler", "tourneur", "tornitore", "turner"),
    "küfer": ("Küfer", "tonnelier", "bottaio", "cooper"),
    "wagner": ("Wagner", "charron", "carradore", "wheelwright"),
    "säger": ("Säger, Holzhändler", "scieur, marchand de bois", "segantino, commerciante di legname", "sawyer, timber merchant"),
    "holzschnitzer": ("Holzschnitzer", "sculpteur sur bois", "intagliatore", "woodcarver"),
    "dachdecker": ("Dachdecker", "couvreur", "copritetto", "roofer"),
    "hafner": ("Hafner", "poêlier", "stufaio", "stove fitter"),
    "spengler": ("Spengler", "ferblantier", "lattoniere", "tinsmith"),
    "installateur": ("Installateur", "appareilleur", "idraulico", "plumber"),
    "elektriker": ("Elektriker", "électricien", "elettricista", "electrician"),
    "mechaniker": ("Mechaniker", "mécanicien", "meccanico", "mechanic"),
    "schlosser": ("Schlosser", "serrurier", "fabbro", "locksmith"),
    "schmied": ("Schmied", "maréchal-ferrant", "maniscalco", "blacksmith"),
    "dreher": ("Dreher", "tourneur sur métaux", "tornitore in ferro", "lathe operator"),
    "giesser": ("Giesser", "fondeur", "fonditore", "founder"),
    "zinngiesser": ("Zinngiesser, Kupferschmied", "potier d'étain, chaudronnier", "calderaio", "pewterer, coppersmith"),
    "maschinist": ("Maschinist, Monteur", "machiniste, monteur", "macchinista, montatore", "machinist, fitter"),
    "uhrmacher": ("Uhrmacher", "horloger", "orologiaio", "watchmaker"),
    "uhrenbestandteile": ("Uhrenbestandteile", "parties de la montre", "parti d'orologio", "watch parts"),
    "goldschmied": ("Goldschmied", "bijoutier", "orefice", "goldsmith"),
    "optiker": ("Optiker", "opticien", "ottico", "optician"),
    "schneider": ("Schneider", "tailleur", "sarto", "tailor"),
    "näherin": ("Näherin", "lingère", "cucitrice", "seamstress"),
    "modistin": ("Modistin, Hutmacher", "modiste, chapelier", "modista, cappellaio", "milliner, hatter"),
    "glätterin": ("Glätterin, Wäscherin", "repasseuse, blanchisseuse", "stiratrice, lavandaia", "ironer, laundress"),
    "strickerin": ("Strickerin", "tricoteuse", "magliaia", "knitter"),
    "schuhmacher": ("Schuhmacher", "cordonnier", "calzolaio", "shoemaker"),
    "sattler": ("Sattler, Tapezierer", "sellier, tapissier", "sellaio, tappezziere", "saddler, upholsterer"),
    "gerber": ("Gerber", "tanneur", "conciatore", "tanner"),
    "sticker": ("Sticker", "brodeur", "ricamatore", "embroiderer"),
    "weber": ("Weber", "tisserand", "tessitore", "weaver"),
    "tuchhändler": ("Tuchhändler", "drapier", "commerciante di tessuti", "draper"),
    "metzger": ("Metzger", "boucher", "macellaio", "butcher"),
    "viehhändler": ("Vieh- und Pferdehändler", "marchand de bétail", "commerciante di bestiame", "cattle dealer"),
    "viehinspektor": ("Viehinspektor", "inspecteur du bétail", "ispettore del bestiame", "livestock inspector"),
    "bäcker": ("Bäcker", "boulanger", "panettiere", "baker"),
    "konditor": ("Konditor", "confiseur, pâtissier", "pasticciere", "confectioner"),
    "müller": ("Müller", "meunier", "mugnaio", "miller"),
    "käser": ("Käser, Milchhändler", "fromager, laitier", "casaro, lattaio", "cheesemaker, dairyman"),
    "spezierer": ("Spezierer", "épicier", "droghiere", "grocer"),
    "weinhändler": ("Weinhändler", "marchand de vins", "commerciante di vini", "wine merchant"),
    "bierbrauer": ("Bierbrauer", "brasseur", "birraio", "brewer"),
    "gemüsehändler": ("Gemüsehändler", "marchand de légumes", "ortolano", "greengrocer"),
    "wirt": ("Wirt", "aubergiste, cafetier", "oste", "innkeeper"),
    "hotelier": ("Hotelier", "hôtelier", "albergatore", "hotelier"),
    "pension": ("Pension", "pension", "pensione", "boarding house"),
    "koch": ("Koch", "cuisinier", "cuoco", "cook"),
    "kellner": ("Kellner", "sommelier", "cameriere", "waiter"),
    "schriftsetzer": ("Buchdrucker, Setzer", "imprimeur, typographe", "tipografo", "printer, compositor"),
    "buchbinder": ("Buchbinder", "relieur", "legatore", "bookbinder"),
    "buchhändler": ("Buchhändler", "libraire", "libraio", "bookseller"),
    "kaufmann": ("Kaufmann", "négociant", "commerciante", "merchant"),
    "commis": ("Commis, Angestellter", "commis, employé", "impiegato", "clerk"),
    "buchhalter": ("Buchhalter", "comptable", "contabile", "bookkeeper"),
    "reisender": ("Handelsreisender", "voyageur de commerce", "viaggiatore di commercio", "commercial traveller"),
    "vertreter": ("Vertreter, Agent", "représentant, agent", "rappresentante", "agent"),
    "bankangestellter": ("Bankangestellter", "employé de banque", "impiegato di banca", "bank clerk"),
    "versicherung": ("Versicherung", "assurance", "assicurazione", "insurance"),
    "direktor": ("Direktor", "directeur", "direttore", "director"),
    "fabrikant": ("Fabrikant", "fabricant", "fabbricante", "manufacturer"),
    "fabrikarbeiter": ("Fabrikarbeiter", "ouvrier de fabrique", "operaio", "factory worker"),
    "magaziner": ("Magaziner", "magasinier", "magazziniere", "warehouseman"),
    "verkäuferin": ("Verkäuferin", "vendeuse", "commessa", "shop assistant"),
    "eisenhändler": ("Eisenhändler", "quincaillier", "ferramenta", "ironmonger"),
    "kohlenhändler": ("Kohlenhändler", "marchand de charbon", "commerciante di carbone", "coal merchant"),
    "tabakhändler": ("Tabakhändler", "marchand de tabac", "tabaccaio", "tobacconist"),
    "hausierer": ("Hausierer", "colporteur", "venditore ambulante", "pedlar"),
    "coiffeur": ("Coiffeur", "coiffeur", "parrucchiere", "hairdresser"),
    "gärtner": ("Gärtner", "jardinier", "giardiniere", "gardener"),
    "landwirt": ("Landwirt", "agriculteur", "agricoltore", "farmer"),
    "förster": ("Förster", "forestier", "guardaboschi", "forester"),
    "knecht": ("Knecht, Magd, Dienstbote", "domestique", "domestico", "servant"),
    "handlanger": ("Handlanger, Taglöhner", "manœuvre, journalier", "manovale, giornaliero", "labourer"),
    "privat": ("Privat, Rentier", "rentier, propriétaire", "possidente", "private means"),
    "student": ("Student, Lehrling", "étudiant, apprenti", "studente, apprendista", "student, apprentice"),
}
assert set(LABELS) == {k for k, _, _ in FINE}, set(LABELS) ^ {k for k, _, _ in FINE}

"""Il nome pulito della struttura, lo stesso in titolo, testata, piede e testi.

Il nome di Google spesso porta con sé altro: il nome e cognome del titolare ("Val del Prato di Mario Rossi"), il codice CIN,
la ragione sociale ("Azienda Agricola", "S.r.l."), una coda dopo il trattino o la virgola ("Locanda Since 1800 - Ristorante"),
il tutto maiuscolo. Il nome pulito:
1. toglie il codice CIN o CIR, le ragioni sociali e "di" seguito da nome e cognome in fondo;
2. tiene la prima parte prima di " - ", " | ", " · ", "," o "(" (se la prima parte è solo il tipo, tiene quella dopo);
3. scrive in maiuscolo solo le iniziali, se il nome era tutto maiuscolo;
4. aggiunge il tipo di attività davanti al nome quando manca, una volta sola ("Heidi Park" diventa "Agriturismo Heidi Park").
"""

import re

TIPI = {"HOT": "Hotel", "BEB": "B&B", "AGR": "Agriturismo", "CAV": "Casa vacanze"}
PAROLE_DEI_TIPI = re.compile(r"\b(hotel|albergo|b\s*&\s*b|bnb|bed\s*(and|&)\s*breakfast|agriturismo|agritur|casa\s+vacanz[ae]|case\s+vacanz[ae]|"
                             r"affittacamere|residence|locanda|relais|resort|ostello|guest\s*house|masseria|cascina|tenuta|chalet|"
                             r"appartament[oi]|suites?|rooms?|camere|villa|dimora|podere|maso|kmetija)\b", re.I)
CODICI = re.compile(r"[\s,\-–|]*\b(CIN|CIR|CUSR|CITR)\b\s*[:.\-]?\s*[A-Z0-9\-]{5,}|[\s,\-–|]*\bIT\d{3}[A-Z0-9]{6,}\b", re.I)
RAGIONI_SOCIALI = re.compile(r"\b(azienda\s+agricola|azienda\s+agrituristica|az\.?\s*agr\.?|societ[aà]\s+agricola|soc\.?\s*agr\.?|impresa\s+agricola|"
                             r"s\.?\s*r\.?\s*l\.?s?|s\.?\s*a\.?\s*s\.?|s\.?\s*n\.?\s*c\.?|s\.?\s*p\.?\s*a\.?|&\s*c\.?)(?=\s|$|[,.\-])", re.I)
TITOLARE_IN_FONDO = re.compile(r"\s+(di|dei|della)\s+[A-ZÀ-Ý][\w'’]+(\s+(e\s+)?[A-ZÀ-Ý][\w'’]+){0,2}\s*$")
SEPARATORI = re.compile(r"\s+[-–—|·]\s+|\s*,\s*|\s*\(|\s*/\s*")
# le attività in più dopo il nome ("AgriRiggio Salumificio", "Verdarancio ... Ristorante Pizzeria con Forno a Legna"): il nome si ferma prima
CODA_DI_ATTIVITA = re.compile(r"\s+(ristorante|pizzeria|trattoria|osteria|salumificio|macelleria|caseificio|cantina|vini|bar|"
                              r"enoteca|fattoria\s+didattica|con\s)\b.*$", re.I)
MINUSCOLE = {"di", "da", "del", "della", "dei", "degli", "delle", "e", "ed", "al", "alla", "alle", "ai", "il", "lo", "la", "le", "i", "gli",
             "in", "a", "con", "sul", "sulla", "tra", "fra"}


def _maiuscoleIniziali(testo):
    parole = []
    for numero, parola in enumerate(testo.lower().split()):
        if numero and parola in MINUSCOLE:
            parole.append(parola)
        elif parola in ("b&b", "bnb"):
            parole.append("B&B")
        else:
            parole.append(re.sub(r"^([\W]*)(\w)", lambda m: m.group(1) + m.group(2).upper(), parola))
    return " ".join(parole)


def nomePulitoDellaStruttura(nome, codiceTipo=""):
    """codiceTipo: HOT, BEB, AGR o CAV (dal codice del cliente). Restituisce il nome pulito, mai vuoto se il nome non lo è."""
    originale = " ".join(str(nome or "").split())
    if not originale:
        return ""
    testo = CODICI.sub("", originale)
    # una ragione sociale in mezzo al nome porta dietro di sé il titolare ("alla Madonna Azienda Agricola Paolo Vidoz"): il nome si
    # ferma lì; in testa al nome si toglie soltanto ("Azienda Agrituristica Torre Scifo" diventa "Torre Scifo")
    ragione = RAGIONI_SOCIALI.search(testo)
    if ragione and ragione.start() > 0 and PAROLE_DEI_TIPI.sub("", testo[:ragione.start()]).strip(" /,.-–&"):
        testo = testo[:ragione.start()]
    testo = RAGIONI_SOCIALI.sub(" ", testo)
    testo = " ".join(testo.split())
    parti = [p.strip(" .-–") for p in SEPARATORI.split(testo) if p and p.strip(" .-–")]
    if parti:
        testo = parti[0]
        # la prima parte è solo il tipo ("Agriturismo - La Massaria"): il nome è la parte dopo
        if len(parti) > 1 and not PAROLE_DEI_TIPI.sub("", testo).strip(" &"):
            testo = parti[0] + " " + parti[1]
    testo = TITOLARE_IN_FONDO.sub("", testo).strip(" ,.-")
    corto = CODA_DI_ATTIVITA.sub("", testo).strip(" ,.-")
    if PAROLE_DEI_TIPI.sub("", corto).strip(" &"):
        testo = corto
    lettere = [c for c in testo if c.isalpha()]
    if lettere and sum(c.isupper() for c in lettere) / len(lettere) > 0.7:
        testo = _maiuscoleIniziali(testo)
    tipo = TIPI.get(str(codiceTipo or "").upper(), "") or next(
        (nomeDelTipo for parola, nomeDelTipo in (("agritur", "Agriturismo"), ("b&b", "B&B"), ("bed", "B&B"), ("hotel", "Hotel"),
                                                 ("albergo", "Hotel"), ("casa", "Casa vacanze")) if parola in str(codiceTipo or "").lower()), "")
    if tipo and not PAROLE_DEI_TIPI.search(testo):
        testo = f"{tipo} {testo}"
    return testo or originale

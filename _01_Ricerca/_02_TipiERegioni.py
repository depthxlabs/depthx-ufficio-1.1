"""TIPI E REGIONI, Linea 1.1 Outbound Websites, Ricerca clienti.

I quattro tipi dell'ospitalità con le parole cercate su Google Maps, i tipi di Google che appartengono a ciascuno,
le sottocategorie del CRM con le parole che le riconoscono, e la regione di ogni provincia.
"""
import re

TIPI = {
    "HOT": {"nome": "Hotel", "parole": ["hotel", "albergo"],
            "google": {"hotel", "resort_hotel", "motel", "inn", "extended_stay_hotel", "budget_japanese_inn"}},
    "BEB": {"nome": "B&B", "parole": ["bed and breakfast", "b&b"],
            "google": {"bed_and_breakfast", "guest_house"}},
    "AGR": {"nome": "Agriturismi", "parole": ["agriturismo"],
            "google": {"farmstay", "farm"}},
    "CAV": {"nome": "Case Vacanze", "parole": ["casa vacanze", "appartamenti vacanze"],
            "google": {"cottage", "private_guest_room", "vacation_rental", "campground", "lodging"}},
}

# sottocategorie del CRM: la prima regola vera vince, l'ultima è quella di base
SOTTOCATEGORIE = {
    "HOT": [(r"\bspa\b|terme|termal|benessere", "Hotel con spa e terme"), (r"\blago\b|lake", "Hotel al lago"),
            (r"montagna|dolomit|\bsci\b|\bski\b|alpi", "Hotel di montagna"), (None, "Hotel di città")],
    "BEB": [(r"piscina|\bspa\b|idromassaggio|jacuzzi", "B&B con piscina, spa o idromassaggio"), (r"\blago\b|lake", "B&B al lago"),
            (r"montagna|dolomit|\bsci\b|\bski\b|alpi", "B&B di montagna"), (r"campagna|collin|vigne", "B&B di campagna"), (None, "B&B di città")],
    "AGR": [(r"matrimoni|cerimoni|\beventi\b", "Agriturismo con sala per eventi e matrimoni"), (r"\bspa\b|benessere", "Agriturismo con spa o centro benessere"),
            (r"piscina", "Agriturismo con piscina"), (r"cantina|degustazion", "Agriturismo con cantina e degustazioni"),
            (r"\blago\b|lake", "Agriturismo al lago"), (r"montagna|dolomit|alpi", "Agriturismo in montagna"), (None, "Agriturismo con ristorante")],
    "CAV": [(r"chalet|baita", "Casa vacanza chalet e baita"), (r"villa.{0,40}piscina|piscina.{0,40}villa", "Villa con piscina"),
            (r"fronte mare|sul mare|accesso diretto|sulla spiaggia|fronte lago", "Casa vacanza con accesso diretto al mare o al lago"),
            (r"\bspa\b|sauna|idromassaggio", "Casa vacanza con spa, sauna o idromassaggio"), (r"piscina", "Casa vacanza con piscina"),
            (r"\blago\b|lake", "Casa vacanza al lago"), (r"montagna|dolomit|alpi", "Casa vacanza in montagna"),
            (r"campagna|collin|vigne", "Casa vacanza in campagna"), (r"giardino|terrazza panoramica", "Casa vacanza con giardino o terrazza panoramica"),
            (None, "Casa vacanza in città e centro storico")],
}


def sottocategoria(tipo, testo):
    t = (testo or "").lower()
    for regola, nome in SOTTOCATEGORIE[tipo]:
        if regola is None or re.search(regola, t):
            return nome


REGIONI = {
    "ABR": "AQ CH PE TE", "BAS": "MT PZ", "CAL": "CZ CS KR RC VV", "CAM": "AV BN CE NA SA",
    "EMR": "BO FE FC MO PR PC RA RE RN", "FVG": "GO PN TS UD", "LAZ": "FR LT RI RM VT", "LIG": "GE IM SP SV",
    "LOM": "BG BS CO CR LC LO MN MI MB PV SO VA", "MAR": "AN AP FM MC PU", "MOL": "CB IS",
    "PIE": "AL AT BI CN NO TO VB VC", "PUG": "BA BT BR FG LE TA", "SAR": "CA NU OR SS SU OT OG VS CI",
    "SIC": "AG CL CT EN ME PA RG SR TP", "TOS": "AR FI GR LI LU MS PI PT PO SI", "TAA": "BZ TN",
    "UMB": "PG TR", "VDA": "AO", "VEN": "BL PD RO TV VE VR VI",
}
REGIONE_DELLA_PROVINCIA = {p: r for r, ps in REGIONI.items() for p in ps.split()}

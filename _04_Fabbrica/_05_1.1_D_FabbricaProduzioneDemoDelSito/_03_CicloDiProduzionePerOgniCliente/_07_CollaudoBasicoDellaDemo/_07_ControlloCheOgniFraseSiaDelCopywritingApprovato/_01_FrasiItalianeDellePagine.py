"""Le frasi italiane che il visitatore legge nelle pagine: il testo tra i tag, senza script, stili, commenti e attributi.

Restituisce l'elenco delle frasi, con gli spazi ridotti.
"""

import html
import re
from pathlib import Path


def frasiItalianeDellePagine(sito):
    frasi = []
    for pagina in sorted(Path(sito).glob("*.html")):
        codice = pagina.read_text(encoding="utf-8-sig", errors="ignore")
        codice = re.sub(r"<!--.*?-->|<(script|style|svg|noscript)\b.*?</\1\s*>", "", codice, flags=re.S | re.I)
        corpo = re.search(r"<body\b.*", codice, re.S | re.I)
        for testo in re.split(r"<[^>]*>", corpo.group(0) if corpo else codice):
            testo = " ".join(html.unescape(testo).split())
            # un paragrafo con più frasi approvate si legge frase per frase (Michele, 9/11/2026): "Nella casa. Cosa trovate."
            # sono due frasi del copy, non una frase sconosciuta
            for pezzo in re.split(r"(?<=[.!?])\s+(?=[A-ZÀ-Ý«\"“])", testo):
                if pezzo.strip():
                    frasi.append(pezzo.strip())
    return frasi

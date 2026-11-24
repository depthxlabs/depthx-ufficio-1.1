"""Le frasi che il visitatore legge nelle pagine del sito: il testo tra i tag, l'inglese in data-en, i testi delle foto e dei
pulsanti (alt, title, aria-label, placeholder) e la descrizione per Google. Script, stili e commenti non contano.

Restituisce l'elenco delle frasi.
"""

import html
import re
from pathlib import Path

ATTRIBUTI_VISIBILI = re.compile(r'\s(?:data-en|alt|title|aria-label|placeholder)="([^"]*)"')
DESCRIZIONE = re.compile(r'<meta\b[^>]*\bname="(?:description|og:description)"[^>]*\bcontent="([^"]*)"', re.I)


def frasiVisibiliDelSito(sito):
    frasi = []
    for pagina in sorted(Path(sito).glob("*.html")):
        codice = pagina.read_text(encoding="utf-8-sig", errors="ignore")
        codice = re.sub(r"<!--.*?-->|<(script|style)\b.*?</\1\s*>", "", codice, flags=re.S | re.I)
        frasi += ATTRIBUTI_VISIBILI.findall(codice) + DESCRIZIONE.findall(codice)
        frasi += [testo for testo in re.split(r"<[^>]*>", codice) if testo.strip()]
    return [html.unescape(frase).strip() for frase in frasi if frase.strip()]

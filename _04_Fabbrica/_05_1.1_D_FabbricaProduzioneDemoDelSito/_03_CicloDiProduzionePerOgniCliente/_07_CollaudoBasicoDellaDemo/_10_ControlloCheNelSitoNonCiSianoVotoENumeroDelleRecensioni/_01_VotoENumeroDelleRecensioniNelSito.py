"""Passo 7.10: nel sito non ci sono né il voto né il numero delle recensioni.

Un numero scritto nel sito non segue Google quando cambia: delle recensioni restano solo i testi degli ospiti
(Michele, 8/11/2026). Si guardano le pagine e gli script, i valori del file di configurazione compresi: un voto (per
esempio 4,7) vicino a Google, recensioni o stelle, o un numero seguito da recensioni, è un problema. Negli stili i numeri
sono misure e non contano. Restituisce l'elenco dei problemi trovati.
"""

import re
from pathlib import Path

VICINO_ALLE_RECENSIONI = r"(?:\bgoogle\b|recension|\breviews?\b|\bstell[ae]\b|\bstars?\b|\u2605|/\s*5\b|\bvoto\b)"
VOTO = re.compile(r"(?<![\d.,])([1-5][.,]\d)(?![\d.,])")
NUMERO_DELLE_RECENSIONI = re.compile(r"(?<![\d.,])(\d{1,5})\s*(?:\+\s*)?(?:recensioni|reviews|valutazioni)", re.I)


def votoENumeroDelleRecensioniNelSito(codici):
    problemi = set()
    for percorso, codice in codici.items():
        file = Path(percorso).name
        if file.endswith(".css"):
            continue
        # i numeri del disegno delle icone (<svg>) non sono voti (Michele, 11/11/2026: "3.5" dell'icona del telefono)
        codice = re.sub(r"<svg\b.*?</svg\s*>", " ", codice, flags=re.S | re.I)
        for trovato in VOTO.finditer(codice):
            intorno = codice[max(0, trovato.start() - 60):trovato.end() + 60].lower()
            if re.search(VICINO_ALLE_RECENSIONI, intorno):
                problemi.add(f"{file}: voto delle recensioni nel sito \"{trovato.group(1)}\"")
        for trovato in NUMERO_DELLE_RECENSIONI.finditer(codice):
            problemi.add(f"{file}: numero delle recensioni nel sito \"{trovato.group(0).strip()}\"")
    return sorted(problemi)

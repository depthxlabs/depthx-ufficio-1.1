"""Passo 7.8: la struttura parla con il noi e chiama l'ospite con il voi. Nessuna frase con io, mio, ho... (prima persona
singolare) o con tu, ti, tuo... (l'ospite chiamato con il tu). I testi delle recensioni sono degli ospiti e non contano,
anche tra le virgolette « » della pagina (Michele, 8/11/2026: prima le virgolette li facevano sembrare testi nostri).
Restituisce l'elenco dei problemi trovati.
"""

import re

from .._07_ControlloCheOgniFraseSiaDelCopywritingApprovato._01_FrasiItalianeDellePagine import frasiItalianeDellePagine
from .._07_ControlloCheOgniFraseSiaDelCopywritingApprovato._02_FrasiFuoriDalCopywritingApprovato import eTestoDiUnOspite

PAROLE_DELL_IO_E_DEL_TU = re.compile(r"(?<![\wà-ÿ'])(io|mio|mia|miei|mie|ho|tu|ti|tuo|tua|tuoi|tue)(?![\wà-ÿ'])", re.I)


def frasiInPrimaPersonaSingolareOConIlTu(sito, recensioni):
    problemi = []
    for frase in sorted(set(frasiItalianeDellePagine(sito))):
        trovata = PAROLE_DELL_IO_E_DEL_TU.search(frase)
        if trovata and not eTestoDiUnOspite(frase, recensioni):
            problemi.append(f"frase con \"{trovata.group(1)}\" invece del noi e del voi: \"{frase[:120]}\"")
    return problemi

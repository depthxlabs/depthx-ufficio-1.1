"""Passo 7.2: nessuna parola vietata nelle frasi visibili del sito. Le parole vietate sono in _01_ParoleVietateNeiTestiDelleDemo.json.
Una parola conta solo intera: non scatta quando è dentro una parola più lunga. Le parole vietate valgono per i testi di
DepthX, non per le recensioni degli ospiti, che non contano (Michele, 8/11/2026). Restituisce l'elenco dei problemi trovati.
"""

import json
import re
from pathlib import Path

from ._02_FrasiVisibiliDelSito import frasiVisibiliDelSito
from .._07_ControlloCheOgniFraseSiaDelCopywritingApprovato._02_FrasiFuoriDalCopywritingApprovato import eTestoDiUnOspite

FILE_DELLE_PAROLE_VIETATE = Path(__file__).absolute().parent / "_01_ParoleVietateNeiTestiDelleDemo.json"


def paroleVietateNeiTestiDelSito(sito, recensioni=()):
    parole = json.loads(FILE_DELLE_PAROLE_VIETATE.read_text(encoding="utf-8-sig"))["parole"]
    frasi = " \n ".join(frase for frase in frasiVisibiliDelSito(sito) if not eTestoDiUnOspite(frase, recensioni)).lower()
    problemi = []
    for parola in parole:
        trovata = re.search(r"(?<![\wà-ÿ])" + re.escape(parola.lower()) + r"(?![\wà-ÿ])", frasi)
        if trovata:
            contesto = re.sub(r"\s+", " ", frasi[max(0, trovata.start() - 40):trovata.end() + 40]).strip()
            problemi.append(f"parola vietata nei testi: \"{parola}\" in \"...{contesto}...\"")
    return problemi

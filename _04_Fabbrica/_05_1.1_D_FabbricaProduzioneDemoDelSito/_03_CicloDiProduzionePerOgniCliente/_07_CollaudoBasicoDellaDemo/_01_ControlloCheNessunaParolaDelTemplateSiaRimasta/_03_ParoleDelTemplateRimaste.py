"""Passo 7.1: nessuna parola del template rimasta (nome, luoghi e contatti dell'esempio, dal contratto del template) e nessuna
frase da sito dimostrativo (_01_FrasiDaSitoDimostrativo.json).

Le graffe del contratto ("{" e "}") si controllano come segnaposto rimasti nelle pagine ({nomestruttura}...): negli stili e
negli script le graffe sono codice. Restano solo i segnaposto del modulo WhatsApp, che si completano quando l'ospite scrive.
Restituisce l'elenco dei problemi trovati.
"""

import html
import json
import re
from pathlib import Path

FILE_DELLE_FRASI_DA_SITO_DIMOSTRATIVO = Path(__file__).absolute().parent / "_01_FrasiDaSitoDimostrativo.json"
SEGNAPOSTO_DEL_MODULO = {"arrivo", "partenza", "ospiti"}


def paroleDelTemplateRimaste(codici, contratto):
    regole = json.loads(Path(contratto).read_text(encoding="utf-8-sig"))
    # implementare post template: ogni contratto chiama l'elenco in modo diverso (Hotel paroleDelTemplateMaiInUnaDemo, con
    # una spiegazione tra parentesi; B&B anche paroleVietateNellaDemo); nei template definitivi un solo nome.
    parole = regole.get("paroleDelTemplate") or regole.get("paroleDelTemplateMaiInUnaDemo") or []
    parole = [parola.split(" (")[0].strip() for parola in parole + regole.get("paroleVietateNellaDemo", [])]
    tutto = html.unescape("\n".join(codici.values())).lower()
    problemi = []
    if "{" in parole or "}" in parole:
        pagine = "\n".join(codice for percorso, codice in codici.items() if percorso.endswith(".html"))
        rimasti = sorted({nome for nome in re.findall(r"\{(\w+)\}", pagine) if nome not in SEGNAPOSTO_DEL_MODULO})
        problemi += [f"è rimasto il segnaposto del template {{{nome}}}" for nome in rimasti]
    problemi += [f"è rimasta la parola del template \"{parola}\"" for parola in parole
                 if parola not in ("{", "}") and parola and parola.lower() in tutto]
    frasi = json.loads(FILE_DELLE_FRASI_DA_SITO_DIMOSTRATIVO.read_text(encoding="utf-8-sig"))["frasi"]
    problemi += [f"è rimasta la frase da sito dimostrativo \"{frase}\"" for frase in frasi if frase.lower() in tutto]
    return problemi

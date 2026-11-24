"""Passo 7.7: ogni frase visibile è una frase verificata: del copywriting approvato (passo 5.8.2, _02_CopywritingDellOspitalità)
con i fatti tra graffe completati, oppure del sito attuale del cliente, e in tutti e due i casi verificata dal materiale
del cliente nel passo 5.8.4 (frasiVerificate.json nella cartella del cliente in corso, accanto al sito).

Le frasi del copy si usano solo quando sono verificate (Michele, 8/11/2026): una frase del copywriting che non è
nell'elenco delle verificate si ferma, anche se l'ha messa la correzione del passo 10. Contano le frasi di almeno quattro
parole: nomi, numeri, orari e voci di menu non sono frasi. I testi delle recensioni sono degli ospiti e non si
confrontano. Restituisce l'elenco dei problemi trovati.
"""

import json
import re
from pathlib import Path

from ._01_FrasiItalianeDellePagine import frasiItalianeDellePagine

CARTELLA_DEL_COPYWRITING = (Path(__file__).absolute().parents[2] / "_05_PersonalizzazioneDelTemplateConLidentitàDelCliente"
                            / "_08_TestiPerOgniCliente" / "_02_CopywritingDellOspitalità")
NOME_DELLE_FRASI_VERIFICATE = "frasiVerificate.json"
PAROLE_DI_UNA_FRASE = 4
normale = lambda testo: " ".join(testo.lower().replace("’", "'").split()).rstrip(".!?:; ")


def modelliDelCopywriting():
    modelli = []
    for file in sorted(CARTELLA_DEL_COPYWRITING.glob("*.md")):
        for riga in re.findall(r"^\s*(?:\d+\.|-)\s+(.*?\S)\s*(?:\[prova:[^\]]*\])?\s*$", file.read_text(encoding="utf-8-sig"), re.M):
            parti = re.split(r"\{\w+\}", normale(riga))
            modelli.append(re.compile("^" + ".+?".join(re.escape(parte) for parte in parti) + "$"))
    return modelli


def eTestoDiUnOspite(frase, recensioni):
    """Vero se la frase è il testo (o un pezzo del testo) di una recensione: le parole degli ospiti non sono testi di DepthX
    e non contano per i controlli del collaudo sui nostri testi (Michele, 8/11/2026)."""
    dellOspite = normale(frase).strip("«»\"“”'… ").rstrip(".!?:; ")
    return bool(dellOspite) and any(dellOspite in normale(voce.get("testo") or "") for voce in recensioni)


def frasiFuoriDalCopywritingApprovato(sito, recensioni):
    modelli = modelliDelCopywriting()
    file = Path(sito).parent / NOME_DELLE_FRASI_VERIFICATE
    verificate = {normale(frase) for frase in json.loads(file.read_text(encoding="utf-8"))} if file.is_file() else set()
    problemi, viste = [], set()
    for frase in frasiItalianeDellePagine(sito):
        testo = normale(frase)
        # le righe dei dati legali (IVA, CIN, CIR, codice fiscale) sono dati del cliente, non frasi (Michele, 9/11/2026)
        if re.match(r"^(p\.?\s*iva|iva|cin|cir|c\.?\s*f\.?|codice fiscale)\b", testo):
            continue
        if len(re.findall(r"[a-zà-ÿ']+", testo)) < PAROLE_DI_UNA_FRASE or testo in viste:
            continue
        viste.add(testo)
        # un pezzo di una frase verificata è verificato: la pagina si legge frase per frase, e "Preferite parlarne a voce?
        # Chiamateci al ..." o un nome con il punto ("Un ospite di Az. Agrituristica ...") si spezzano (Michele, 11/11/2026)
        if eTestoDiUnOspite(frase, recensioni) or testo in verificate or any(testo in intera for intera in verificate):
            continue
        if any(modello.match(testo) for modello in modelli):
            problemi.append(f"frase del copywriting non verificata dal materiale del cliente: \"{frase[:120]}\"")
        else:
            problemi.append(f"frase fuori dal copywriting approvato e non verificata: \"{frase[:120]}\"")
    return problemi

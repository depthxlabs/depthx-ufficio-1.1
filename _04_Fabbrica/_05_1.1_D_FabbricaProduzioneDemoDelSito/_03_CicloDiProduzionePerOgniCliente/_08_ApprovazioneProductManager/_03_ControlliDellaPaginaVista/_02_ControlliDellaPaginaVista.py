"""Passo 8.3: i controlli della pagina come la vede il visitatore, sul computer e sul telefono.

Legge le misure che Chrome ha preso nel passo 8.1 accanto a ogni fotografia di ogni pagina (<pagina>_<forma>.json) e le confronta con
_01_RegoleDellaPaginaVista.json:
- l'apertura: la foto grande del primo schermo si vede intera, non tagliata a metà dal bordo dello schermo;
- la prima sezione dopo l'apertura non è spoglia: ha almeno le parole e le frasi delle regole;
- ogni frase che nomina WhatsApp ha nella sua sezione un pulsante o un link WhatsApp visibile.
Restituisce l'elenco dei problemi trovati.
"""

import json
from pathlib import Path

FILE_DELLE_REGOLE = Path(__file__).absolute().parent / "_01_RegoleDellaPaginaVista.json"


def controlliDellaPaginaVista(fotografie):
    regole = json.loads(FILE_DELLE_REGOLE.read_text(encoding="utf-8-sig"))
    problemi = []
    for forma, fotografia in fotografie.items():
        file = Path(fotografia).with_suffix(".json")
        if not file.is_file():
            problemi.append(f"{forma}: mancano le misure della pagina vista")
            continue
        misure = json.loads(file.read_text(encoding="utf-8"))
        for foto in misure.get("apertura") or []:
            if foto["parteVista"] < regole["parteVistaMinimaDellaFotoDiApertura"]:
                problemi.append(f"{forma}: la foto dell'apertura è tagliata dal bordo dello schermo, se ne vede il {foto['parteVista']}%")
        sezioni = misure.get("sezioni") or []
        # la prima sezione dopo l'apertura si guarda nella home; le altre pagine aprono con il loro titolo (Michele, 11/11/2026)
        if sezioni and "|" not in forma:
            prima = sezioni[0]
            if prima["parole"] < regole["paroleMinimeDellaPrimaSezione"] or prima["frasi"] < regole["frasiMinimeDellaPrimaSezione"]:
                problemi.append(f"{forma}: la prima sezione \"{prima['titolo']}\" è spoglia ({prima['parole']} parole, "
                                f"{prima['frasi']} frasi): \"{prima['testo'][:120]}\"")
        for voce in misure.get("whatsapp") or []:
            if not voce["pulsante"]:
                problemi.append(f"{forma}: la frase \"{voce['frase'][:120]}\" nomina WhatsApp ma lì non c'è nessun pulsante WhatsApp")
        # nessuna scritta dell'oggetto 3D esce dalla sua faccia (Michele, 11/11/2026)
        for voce in misure.get("oggetto3d") or []:
            problemi.append(f"{forma}: nell'oggetto 3D la scritta esce dalla faccia ({voce['alta']} px su {voce['spazio']}): \"{voce['testo']}\"")
    return sorted(set(problemi))

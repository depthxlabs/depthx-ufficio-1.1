"""Passo 6.3.1: la scheda della demo con la sua scadenza, a giorniDiScadenzaDellaDemo giorni da adesso (_01_RegoleDellaScadenza.json).

Se la demo dello stesso cliente era già stata inviata, la data di invio resta: le aperture si continuano a contare.
"""

import datetime
import json
from pathlib import Path

from _01_StrumentiDellaFabbrica._04_RegistroLogDellaFabbrica._00_RegistroDellaFabbrica import stessoCliente

FILE_DELLE_REGOLE = Path(__file__).absolute().parent / "_01_RegoleDellaScadenza.json"
formato = lambda momento: momento.isoformat().replace("+00:00", "Z")


def calcolaLaScadenzaDellaDemo(idCliente, schedaPrecedente):
    giorni = int(json.loads(FILE_DELLE_REGOLE.read_text(encoding="utf-8-sig"))["giorniDiScadenzaDellaDemo"])
    ora = datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0)
    invio = (schedaPrecedente or {}).get("invio") if stessoCliente((schedaPrecedente or {}).get("cliente"), idCliente) else None
    return {"cliente": idCliente, "pubblicata": formato(ora), "scadenza": formato(ora + datetime.timedelta(days=giorni)),
            "invio": invio}

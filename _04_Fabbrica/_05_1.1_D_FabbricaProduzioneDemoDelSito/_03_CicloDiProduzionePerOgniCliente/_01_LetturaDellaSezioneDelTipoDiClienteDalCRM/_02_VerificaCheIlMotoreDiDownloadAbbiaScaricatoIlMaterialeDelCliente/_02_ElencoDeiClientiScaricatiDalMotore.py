"""Passo 1.2: gli ID dei clienti che il motore ha scaricato con esito GO o PARZIALE.

L'ordine è quello dei fogli del CRM (sezione, tipo, categoria, regione) e poi dell'ID.
"""

import json
from pathlib import Path

MOTORE_DI_DOWNLOAD = Path(r"C:\_02_DepthXSoftware\_01_CentroGestioneDepthX\V1.0(161126_1124)\_01_StrumentiDiLavoroPerIlServer\_03_MemoriaDatiDelCentroGestione\_12_MotoreDiDownload")
FILE_DELLO_STATO_DEL_MOTORE = MOTORE_DI_DOWNLOAD / "stato.json"
ESITI_SCARICATI = ("GO", "PARZIALE")


def elencoDeiClientiScaricatiDalMotore():
    with open(FILE_DELLO_STATO_DEL_MOTORE, encoding="utf-8-sig") as file:
        clienti = json.load(file).get("clienti", {})
    scaricati = [(voce.get("industria", ""), idCliente) for idCliente, voce in clienti.items() if voce.get("esito") in ESITI_SCARICATI]
    return [idCliente for _, idCliente in sorted(scaricati)]

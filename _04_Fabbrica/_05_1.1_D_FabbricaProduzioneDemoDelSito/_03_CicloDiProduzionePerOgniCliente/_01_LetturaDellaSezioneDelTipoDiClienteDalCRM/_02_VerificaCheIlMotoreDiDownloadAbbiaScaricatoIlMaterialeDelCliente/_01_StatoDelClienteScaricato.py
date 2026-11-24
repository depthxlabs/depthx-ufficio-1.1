"""Passo 1.2: lo stato del cliente nel motore di download, con esito GO o PARZIALE.

Lo stato del motore è un dato del motore: la fabbrica lo legge e non lo modifica mai.
"""

import json
from pathlib import Path

MOTORE_DI_DOWNLOAD = Path(r"C:\_02_DepthXSoftware\_01_CentroGestioneDepthX\V1.0(161126_1124)\_01_StrumentiDiLavoroPerIlServer\_03_MemoriaDatiDelCentroGestione\_12_MotoreDiDownload")
FILE_DELLO_STATO_DEL_MOTORE = MOTORE_DI_DOWNLOAD / "stato.json"
ESITI_SCARICATI = ("GO", "PARZIALE")


def statoDelClienteScaricato(idCliente):
    with open(FILE_DELLO_STATO_DEL_MOTORE, encoding="utf-8-sig") as file:
        stato = json.load(file).get("clienti", {}).get(idCliente, {})
    if stato.get("esito") not in ESITI_SCARICATI:
        raise RuntimeError(f"{idCliente}: il cliente non è scaricato dal motore (esito {stato.get('esito') or 'nessuno'})")
    return stato

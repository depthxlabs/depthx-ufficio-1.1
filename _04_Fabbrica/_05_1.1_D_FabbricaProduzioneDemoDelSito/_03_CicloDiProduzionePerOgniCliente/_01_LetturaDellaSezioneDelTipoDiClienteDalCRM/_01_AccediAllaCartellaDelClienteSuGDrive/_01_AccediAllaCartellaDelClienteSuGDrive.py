"""Passo 1.1: la cartella del cliente su Google Drive.

Si legge dall'elenco che il motore di download scrive quando carica un cliente su Drive: per ogni cliente l'ID della cartella,
il nome della cartella, la sezione del CRM e il tipo di struttura. È un dato del motore: la fabbrica lo legge e non lo modifica mai.
"""

import json
from pathlib import Path

MOTORE_DI_DOWNLOAD = Path(r"C:\_02_DepthXSoftware\_01_CentroGestioneDepthX\V1.0(161126_1124)\_01_StrumentiDiLavoroPerIlServer\_03_MemoriaDatiDelCentroGestione\_12_MotoreDiDownload")
FILE_DELLE_CARTELLE_DEI_CLIENTI = MOTORE_DI_DOWNLOAD / "_02_CartelleDeiClientiSuDrive.json"


def accediAllaCartellaDelClienteSuGDrive(idCliente):
    with open(FILE_DELLE_CARTELLE_DEI_CLIENTI, encoding="utf-8-sig") as file:
        voce = json.load(file).get(idCliente)
    if not voce or not voce.get("idDrive"):
        raise RuntimeError(f"{idCliente}: il cliente non ha la cartella su Drive")
    return voce

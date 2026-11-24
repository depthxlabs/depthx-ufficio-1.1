"""Passo 1.1: la cartella del cliente su Google Drive.

Si legge dall'elenco che il motore di download scrive quando carica un cliente su Drive: per ogni cliente l'ID della cartella,
il nome della cartella, la sezione del CRM e il tipo di struttura. È un dato del motore: la fabbrica lo legge e non lo modifica mai.
"""

import json
from pathlib import Path

MOTORE_DI_DOWNLOAD = Path(__file__).absolute().parents[4] / "_03_1.1_C_DownloadMaterialeClienti"
FILE_DELLE_CARTELLE_DEI_CLIENTI = MOTORE_DI_DOWNLOAD / "_06_CaricamentoSuDrive" / "_02_CartelleDeiClientiSuDrive.json"


def accediAllaCartellaDelClienteSuGDrive(idCliente):
    with open(FILE_DELLE_CARTELLE_DEI_CLIENTI, encoding="utf-8-sig") as file:
        voce = json.load(file).get(idCliente)
    if not voce or not voce.get("idDrive"):
        raise RuntimeError(f"{idCliente}: il cliente non ha la cartella su Drive")
    return voce

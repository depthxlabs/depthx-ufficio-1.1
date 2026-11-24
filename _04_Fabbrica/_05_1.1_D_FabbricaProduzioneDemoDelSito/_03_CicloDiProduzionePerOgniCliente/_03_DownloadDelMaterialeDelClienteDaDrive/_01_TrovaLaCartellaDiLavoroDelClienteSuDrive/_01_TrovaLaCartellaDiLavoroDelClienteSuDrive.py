"""Passo 3.1: la cartella di lavoro del cliente su Drive.

Dentro la cartella del cliente (idDrive del passo 1) c'è _01_RaccoltaMateriale con le sue sottocartelle.
Se manca la raccolta, il cliente si ferma. Drive si legge soltanto, con rclone.
"""

import subprocess

RCLONE = r"C:\_02_DepthXSoftware\_02_RCloneDepthX\rclone.exe"
CONFIGURAZIONE = r"C:\_02_DepthXSoftware\_02_RCloneDepthX\rclone.conf"
RACCOLTA = "_01_RaccoltaMateriale"


def trovaLaCartellaDiLavoroDelClienteSuDrive(idDrive):
    esito = subprocess.run([RCLONE, "lsf", "--dirs-only", f"gdrive:{RACCOLTA}", "--drive-root-folder-id", idDrive,
                            "--config", CONFIGURAZIONE], capture_output=True, text=True, encoding="utf-8")
    sottocartelle = [riga.rstrip("/") for riga in esito.stdout.splitlines() if riga.strip()]
    if esito.returncode != 0 or not sottocartelle:
        raise RuntimeError(f"nella cartella del cliente su Drive manca {RACCOLTA} o è vuota (idDrive {idDrive})")
    return {"idDrive": idDrive, "raccolta": RACCOLTA, "sottocartelle": sottocartelle}

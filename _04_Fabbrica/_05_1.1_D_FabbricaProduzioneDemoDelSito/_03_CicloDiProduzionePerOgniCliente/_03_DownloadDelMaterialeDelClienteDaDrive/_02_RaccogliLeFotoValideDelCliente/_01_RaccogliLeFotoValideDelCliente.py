"""Passo 3.2: le foto valide del cliente, dal riconoscimento delle foto fatto dal motore di download.

Il file è _01_RaccoltaMateriale/_09_RiconoscimentoDelleFoto/_01_RiconoscimentoDelleFoto.json.
Ogni foto: id su Drive, nome, fonte, categoria (camere, bagni, logo...), qualità, nitidezza, larghezza e altezza.
Senza foto valide il cliente si ferma: una demo senza foto vere del cliente non si fa.
Pitstop 8 (Michele, 12/11/2026, task #613): il file si prende dalla lettura unica del materiale
(_07_LeggiIFileDelMaterialeInUnaSolaLettura.py); se non c'è, si legge da Drive come prima. Copia di prima: .copiaPrimaVelocita.
"""

import json
import subprocess

from .._07_LeggiIFileDelMaterialeInUnaSolaLettura import fileLetto

RCLONE = r"C:\_02_DepthXSoftware\_02_RCloneDepthX\rclone.exe"
CONFIGURAZIONE = r"C:\_02_DepthXSoftware\_02_RCloneDepthX\rclone.conf"
FILE_DEL_RICONOSCIMENTO = "_09_RiconoscimentoDelleFoto/_01_RiconoscimentoDelleFoto.json"


def raccogliLeFotoValideDelCliente(cartellaDiLavoro):
    letto, contenuto = fileLetto(cartellaDiLavoro, FILE_DEL_RICONOSCIMENTO)
    if letto:
        if contenuto is None:
            raise RuntimeError(f"su Drive manca il riconoscimento delle foto del cliente ({FILE_DEL_RICONOSCIMENTO})")
        valide = contenuto.get("valide") or []
        if not valide:
            raise RuntimeError("il cliente non ha foto valide riconosciute")
        return valide
    esito = subprocess.run([RCLONE, "cat", f"gdrive:{cartellaDiLavoro['raccolta']}/{FILE_DEL_RICONOSCIMENTO}",
                            "--drive-root-folder-id", cartellaDiLavoro["idDrive"], "--config", CONFIGURAZIONE],
                           capture_output=True)
    if esito.returncode != 0:
        raise RuntimeError(f"su Drive manca il riconoscimento delle foto del cliente ({FILE_DEL_RICONOSCIMENTO})")
    valide = json.loads(esito.stdout.decode("utf-8-sig")).get("valide") or []
    if not valide:
        raise RuntimeError("il cliente non ha foto valide riconosciute")
    return valide

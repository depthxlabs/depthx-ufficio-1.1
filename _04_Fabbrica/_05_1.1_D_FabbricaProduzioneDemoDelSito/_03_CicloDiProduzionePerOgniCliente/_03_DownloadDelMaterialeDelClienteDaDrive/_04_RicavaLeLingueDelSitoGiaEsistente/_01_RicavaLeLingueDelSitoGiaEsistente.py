"""Passo 3.4: le lingue del sito già esistente del cliente.

Il file è _01_RaccoltaMateriale/_04_AttualeSitoWeb/_01_PagineDelSito.json.
Le lingue si ricavano dai link delle pagine (/en/, ?lang=de...): l'italiano c'è sempre.
Senza sito le pagine sono zero e la lingua è solo l'italiano.
Pitstop 8 (Michele, 12/11/2026, task #613): il file si prende dalla lettura unica del materiale
(_07_LeggiIFileDelMaterialeInUnaSolaLettura.py); se non c'è, si legge da Drive come prima. Copia di prima: .copiaPrimaVelocita.
"""

import json
import re
import subprocess

from .._07_LeggiIFileDelMaterialeInUnaSolaLettura import fileLetto

RCLONE = r"C:\_02_DepthXSoftware\_02_RCloneDepthX\rclone.exe"
CONFIGURAZIONE = r"C:\_02_DepthXSoftware\_02_RCloneDepthX\rclone.conf"
FILE_DELLE_PAGINE = "_04_AttualeSitoWeb/_01_PagineDelSito.json"
LINGUA_NEL_LINK = re.compile(r"(?:/|[?&]lang=)(en|de|fr|es|nl)(?=/|$|&|#)", re.I)


def ricavaLeLingueDelSitoGiaEsistente(cartellaDiLavoro):
    letto, contenuto = fileLetto(cartellaDiLavoro, FILE_DELLE_PAGINE)
    if letto:
        pagine = (contenuto or {}).get("pagine", [])
    else:
        esito = subprocess.run([RCLONE, "cat", f"gdrive:{cartellaDiLavoro['raccolta']}/{FILE_DELLE_PAGINE}",
                                "--drive-root-folder-id", cartellaDiLavoro["idDrive"], "--config", CONFIGURAZIONE],
                               capture_output=True)
        pagine = json.loads(esito.stdout.decode("utf-8-sig")).get("pagine", []) if esito.returncode == 0 else []
    lingue = {"it"} | {trovata.lower() for voce in pagine for trovata in LINGUA_NEL_LINK.findall(voce.get("url") or "")}
    return {"pagine": len(pagine), "lingue": sorted(lingue)}

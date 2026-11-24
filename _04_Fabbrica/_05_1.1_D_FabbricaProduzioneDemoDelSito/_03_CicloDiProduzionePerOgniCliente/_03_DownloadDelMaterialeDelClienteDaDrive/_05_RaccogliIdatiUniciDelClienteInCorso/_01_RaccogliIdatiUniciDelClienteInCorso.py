"""Passo 3.5: i dati unici del cliente in corso, i fatti veri per le graffe dei testi.

- i dati del CRM (nome, via, telefono, email...): _10_IlRestoDeiDati/_01_DatiDalCrm.json
- la scheda Google (voto, place id, orari...): _01_SchedaDiGoogle/_02_SchedaGoogle.json
- il rapporto di unicità, cosa ha di vero e di diverso il cliente: _10_IlRestoDeiDati/_05_RapportoDiUnicita.json
- il testo del sito attuale del cliente, le pagine in italiano: _04_AttualeSitoWeb/_01_PagineDelSito.json (8/11/2026:
  è la fonte più ricca dei fatti veri, come il numero delle camere, le distanze e i servizi)
Senza i dati del CRM il cliente si ferma: il nome giusto e i contatti giusti sono la base.
Pitstop 8 (Michele, 12/11/2026, task #613): il file si prende dalla lettura unica del materiale
(_07_LeggiIFileDelMaterialeInUnaSolaLettura.py); se non c'è, si legge da Drive come prima. Copia di prima: .copiaPrimaVelocita.
"""

import json
import re
import subprocess
from concurrent.futures import ThreadPoolExecutor

from .._07_LeggiIFileDelMaterialeInUnaSolaLettura import fileLetto

RCLONE = r"C:\_02_DepthXSoftware\_02_RCloneDepthX\rclone.exe"
CONFIGURAZIONE = r"C:\_02_DepthXSoftware\_02_RCloneDepthX\rclone.conf"
FILE_DEI_DATI = {"crm": "_10_IlRestoDeiDati/_01_DatiDalCrm.json",
                 "schedaGoogle": "_01_SchedaDiGoogle/_02_SchedaGoogle.json",
                 "unicita": "_10_IlRestoDeiDati/_05_RapportoDiUnicita.json",
                 "pagineDelSito": "_04_AttualeSitoWeb/_01_PagineDelSito.json"}
CARATTERI_DEL_SITO = 15000


def leggiDaDrive(cartellaDiLavoro, file):
    letto, contenuto = fileLetto(cartellaDiLavoro, file)
    if letto:
        return contenuto or {}
    esito = subprocess.run([RCLONE, "cat", f"gdrive:{cartellaDiLavoro['raccolta']}/{file}",
                            "--drive-root-folder-id", cartellaDiLavoro["idDrive"], "--config", CONFIGURAZIONE],
                           capture_output=True)
    return json.loads(esito.stdout.decode("utf-8-sig")) if esito.returncode == 0 and esito.stdout.strip() else {}


def raccogliIdatiUniciDelClienteInCorso(cartellaDiLavoro):
    """I file dei dati si leggono da Drive tutti insieme, per la velocità."""
    with ThreadPoolExecutor(max_workers=len(FILE_DEI_DATI)) as insieme:
        letture = {chiave: insieme.submit(leggiDaDrive, cartellaDiLavoro, file) for chiave, file in FILE_DEI_DATI.items()}
        dati = {chiave: lettura.result() for chiave, lettura in letture.items()}
    if not dati["crm"]:
        raise RuntimeError(f"su Drive mancano i dati del CRM del cliente ({FILE_DEI_DATI['crm']})")
    dati["sitoAttuale"] = testoDelSitoAttuale(dati.pop("pagineDelSito", {}))
    return dati


def testoDelSitoAttuale(pagineDelSito):
    """Il testo delle pagine italiane del sito attuale del cliente, senza privacy e cookie, fino a CARATTERI_DEL_SITO."""
    testi, totale = [], 0
    for pagina in pagineDelSito.get("pagine") or []:
        indirizzo = (pagina.get("url") or "").lower()
        if re.search(r"/(en|de|es|fr|nl|ru|zh|ja)/|privacy|cookie", indirizzo):
            continue
        righe = []
        for riga in (pagina.get("testo") or "").splitlines():
            riga = " ".join(riga.split())
            if len(riga) > 2 and riga not in righe:
                righe.append(riga)
        testo = f"[{pagina.get('titolo') or indirizzo}]\n" + "\n".join(righe)
        testi.append(testo[:CARATTERI_DEL_SITO - totale])
        totale += len(testi[-1])
        if totale >= CARATTERI_DEL_SITO:
            break
    return "\n\n".join(testi)

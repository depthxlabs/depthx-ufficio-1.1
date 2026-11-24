"""Pitstop 8 (Michele, 12/11/2026, task #613): i file JSON del materiale del cliente letti da Drive in UNA sola lettura.

Prima ogni file era una chiamata di rclone a sé (rclone cat): il riconoscimento delle foto, le recensioni, le pagine del
sito (due volte, per le lingue e per i dati), i dati del CRM, la scheda Google e il rapporto di unicità, 7 chiamate da
circa 8,9 secondi l'una con le fabbriche accese. Ora una sola chiamata (rclone copy con l'elenco dei file) li porta tutti
in una cartella temporanea dal percorso corto; i passi 3.2, 3.3, 3.4 e 3.5 li leggono da qui (letti[file]).
Un file che su Drive non c'è resta fuori, come prima con rclone cat. Se la lettura unica non riesce, ogni passo torna a
leggere il suo file da Drive come prima. Drive si legge soltanto.
"""

import json
import subprocess
import tempfile
from pathlib import Path

RCLONE = r"C:\_02_DepthXSoftware\_02_RCloneDepthX\rclone.exe"
CONFIGURAZIONE = r"C:\_02_DepthXSoftware\_02_RCloneDepthX\rclone.conf"
FILE_DEL_MATERIALE = ["_09_RiconoscimentoDelleFoto/_01_RiconoscimentoDelleFoto.json",
                      "_03_RecensioniDaGoogleMaps/_01_RecensioniGoogle.json",
                      "_04_AttualeSitoWeb/_01_PagineDelSito.json",
                      "_10_IlRestoDeiDati/_01_DatiDalCrm.json",
                      "_01_SchedaDiGoogle/_02_SchedaGoogle.json",
                      "_10_IlRestoDeiDati/_05_RapportoDiUnicita.json"]


def leggiIFileDelMaterialeInUnaSolaLettura(cartellaDiLavoro):
    """Restituisce file -> testo del file (senza BOM), solo per i file che ci sono; None se la lettura non riesce."""
    with tempfile.TemporaryDirectory(prefix="dxmat_", ignore_cleanup_errors=True) as corta:
        elenco = Path(corta) / "elenco.txt"
        elenco.write_text("\n".join(FILE_DEL_MATERIALE) + "\n", encoding="utf-8")
        esito = subprocess.run([RCLONE, "copy", f"gdrive:{cartellaDiLavoro['raccolta']}", str(Path(corta) / "m"),
                                "--files-from-raw", str(elenco), "--no-traverse", "--transfers", "8", "--checkers", "8",
                                "--drive-root-folder-id", cartellaDiLavoro["idDrive"], "--config", CONFIGURAZIONE],
                               capture_output=True, text=True, encoding="utf-8", errors="ignore")
        if esito.returncode != 0:
            return None
        letti = {}
        for file in FILE_DEL_MATERIALE:
            percorso = Path(corta) / "m" / file
            if percorso.is_file():
                letti[file] = percorso.read_bytes().decode("utf-8-sig")
        return letti


def fileLetto(cartellaDiLavoro, file):
    """Il contenuto JSON di un file già letto nella lettura unica: (True, oggetto o {} se vuoto/rotto, come rclone cat),
    oppure (False, None) se il file non è stato letto e il passo lo deve leggere da Drive come prima."""
    letti = cartellaDiLavoro.get("letti")
    if letti is None:
        return False, None
    testo = letti.get(file)
    if testo is None or not testo.strip():
        return True, None  # il file su Drive non c'è: come rclone cat con errore
    try:
        return True, json.loads(testo)
    except ValueError:
        return True, None

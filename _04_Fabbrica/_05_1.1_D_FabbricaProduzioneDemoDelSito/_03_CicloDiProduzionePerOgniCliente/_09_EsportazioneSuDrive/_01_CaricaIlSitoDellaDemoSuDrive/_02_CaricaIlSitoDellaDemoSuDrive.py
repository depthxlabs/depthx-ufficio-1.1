"""Passo 9.1: tutti i file del sito della demo su Drive, nella cartella del cliente (Michele, 11/11/2026, task #581).

Il sito va in _02_ProduzioneDelSitoDemo/_04_DemoDelSito della cartella del cliente su Drive, trovata con il suo idDrive:
solo Advanced, nessuna cartella divisa per pacchetto o per tipologia. rclone copia soltanto (mai sync) e confronta ogni
file con l'impronta di Drive; la data delle cartelle non si imposta (dentro una cartella indicata per ID rclone non trova
le cartelle appena create); poi rclone check verifica che su Drive ci sia ogni file del sito, uguale. Le regole sono in
_01_DriveDelleDemoPronteDaInviare.json. Restituisce quanti file ha il sito.
"""

import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

FILE_DEL_DRIVE = Path(__file__).absolute().parent / "_01_DriveDelleDemoPronteDaInviare.json"
# Pitstop 5 (task #610, 12/11/2026): rclone di suo aspetta 100 ms tra una chiamata a Drive e l'altra; con 10 ms e una scorta
# di 200 chiamate il sito sale circa 7 secondi prima (misurato: 52 s -> 45 s per 193 file), stessi file e stesse impronte
RITMO_DI_DRIVE = ["--drive-pacer-min-sleep", "10ms", "--drive-pacer-burst", "200"]
COPIA_VELOCE = ["--transfers", "32", "--checkers", "32", "--no-update-dir-modtime", "--drive-chunk-size", "8M", *RITMO_DI_DRIVE]


def rclone(regole, idDrive, *argomenti):
    return subprocess.run([regole["rclone"], *argomenti, "--drive-root-folder-id", idDrive, "--config", regole["configurazione"]],
                          capture_output=True, text=True, encoding="utf-8", errors="ignore", timeout=int(regole["secondiMassimi"]),
                          creationflags=subprocess.CREATE_NO_WINDOW)


def caricaIlSitoDellaDemoSuDrive(sito, idDrive):
    regole = json.loads(FILE_DEL_DRIVE.read_text(encoding="utf-8-sig"))
    arrivo = f"{regole['remoto']}:{regole['cartellaDelSito']}"
    # Pitstop 5 (task #610, 11/11/2026): più trasferimenti insieme; rclone confronta l'impronta MD5 di ogni file caricato con
    # quella che Drive calcola, quindi la seconda lettura completa con rclone check non serve più
    esito = rclone(regole, idDrive, "copy", str(sito), arrivo, *COPIA_VELOCE)
    if esito.returncode != 0:
        raise RuntimeError("sito non caricato su Drive: " + (esito.stderr or esito.stdout).strip()[-300:])
    return sum(1 for file in Path(sito).rglob("*") if file.is_file())


def _collegaOCopia(origine, destinazione):
    try:
        os.link(origine, destinazione)  # stesso disco: nessuna copia dei byte
    except OSError:
        shutil.copy2(origine, destinazione)


def caricaIlSitoEIlResocontoSuDrive(sito, cartellaDelResoconto, idDrive):
    """Pitstop 5 (task #610, 12/11/2026): il sito e il resoconto (già preparato in cartellaDelResoconto) salgono con UNA sola
    copia di rclone nella cartella che li contiene (_02_ProduzioneDelSitoDemo), così il resoconto non aspetta la fine del sito.
    Un solo processo rclone: due rclone insieme sulla stessa cartella di Drive creano cartelle doppie (provato). Su Drive il
    risultato è identico a prima: il sito in cartellaDelSito, il resoconto in cartellaDelResoconto. Restituisce quanti file ha il sito."""
    regole = json.loads(FILE_DEL_DRIVE.read_text(encoding="utf-8-sig"))
    cartellaSito, cartellaResoconto = Path(regole["cartellaDelSito"]), Path(regole["cartellaDelResoconto"])
    if cartellaSito.parent != cartellaResoconto.parent:  # cartelle non sorelle: le due copie di prima, una dopo l'altra
        quanti = caricaIlSitoDellaDemoSuDrive(sito, idDrive)
        esito = rclone(regole, idDrive, "copy", str(cartellaDelResoconto), f"{regole['remoto']}:{regole['cartellaDelResoconto']}",
                       *COPIA_VELOCE)
        if esito.returncode != 0:
            raise RuntimeError("resoconto non caricato su Drive: " + (esito.stderr or esito.stdout).strip()[-300:])
        return quanti
    with tempfile.TemporaryDirectory(prefix="dxesportazione_", ignore_cleanup_errors=True) as cartellaTemporanea:
        insieme = Path(cartellaTemporanea)
        shutil.copytree(sito, insieme / cartellaSito.name, copy_function=_collegaOCopia)
        shutil.copytree(cartellaDelResoconto, insieme / cartellaResoconto.name, copy_function=_collegaOCopia)
        esito = rclone(regole, idDrive, "copy", str(insieme), f"{regole['remoto']}:{cartellaSito.parent.as_posix()}", *COPIA_VELOCE)
        if esito.returncode != 0:
            raise RuntimeError("sito e resoconto non caricati su Drive: " + (esito.stderr or esito.stdout).strip()[-300:])
    return sum(1 for file in Path(sito).rglob("*") if file.is_file())

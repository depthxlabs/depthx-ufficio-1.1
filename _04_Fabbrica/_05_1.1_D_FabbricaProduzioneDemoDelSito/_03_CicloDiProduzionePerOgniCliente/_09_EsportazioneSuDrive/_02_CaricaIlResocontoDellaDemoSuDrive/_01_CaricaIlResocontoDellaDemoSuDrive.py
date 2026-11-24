"""Passo 9.2: il resoconto della demo su Drive, nella cartella del cliente (Michele, 11/11/2026, task #581).

_01_ResocontoDellaDemo.json: nome e link della demo, scadenza, pacchetto, le prove delle frasi (ogni frase con il fatto,
la citazione e la fonte che la provano), esito e problemi del collaudo (passo 7), esito e note del product manager
(passo 8). Nella cartella fotografie: le fotografie di tutte le pagine sul computer e sul telefono. Tutto va in
_02_ProduzioneDelSitoDemo/_05_CollaudoDelSito della cartella del cliente su Drive.
Il JSON si prepara in un file temporaneo e si carica con rclone copyto. Restituisce il link della demo e i nomi dei file caricati.
"""

import json
import tempfile
from pathlib import Path

from .._01_CaricaIlSitoDellaDemoSuDrive._02_CaricaIlSitoDellaDemoSuDrive import FILE_DEL_DRIVE, rclone

NOME_DEL_RESOCONTO = "_01_ResocontoDellaDemo.json"


def preparaIlResoconto(cartella, pubblicazione, collaudo, approvazione, prove):
    """Pitstop 5 (task #610, 12/11/2026): il resoconto e le fotografie preparati in cartella, pronti per la copia unica con il
    sito (passo 9.1). Restituisce i nomi dei file, come caricaIlResocontoDellaDemoSuDrive."""
    import shutil
    cartella = Path(cartella)
    resoconto = {"idCliente": pubblicazione["idCliente"], "nomeDellaDemo": pubblicazione["nomeDellaDemo"], "pacchetto": "Advanced",
                 "link": pubblicazione["link"], "scadenza": pubblicazione["scadenza"], "proveDelleFrasi": prove,
                 "collaudo": {"esito": collaudo["esito"], "controlli": collaudo["controlli"]},
                 "approvazione": {"esito": approvazione["esito"], "note": approvazione.get("note", {})}}
    (cartella / NOME_DEL_RESOCONTO).write_text(json.dumps(resoconto, ensure_ascii=False, indent=1), encoding="utf-8")
    (cartella / "fotografie").mkdir()
    caricati = [NOME_DEL_RESOCONTO]
    for percorso in (approvazione.get("fotografie") or {}).values():
        shutil.copy2(percorso, cartella / "fotografie" / Path(percorso).name)
        caricati.append(f"fotografie/{Path(percorso).name}")
    return caricati


def caricaIlResocontoDellaDemoSuDrive(idDrive, pubblicazione, collaudo, approvazione, prove):
    regole = json.loads(FILE_DEL_DRIVE.read_text(encoding="utf-8-sig"))
    # Pitstop 5 (task #610, 11/11/2026): il resoconto e le fotografie si preparano in una cartella temporanea e salgono con una
    # sola copia di rclone, invece di una chiamata per file. Il passo 9 ora usa preparaIlResoconto + la copia unica con il sito.
    with tempfile.TemporaryDirectory(prefix="dxresoconto_", ignore_cleanup_errors=True) as cartellaTemporanea:
        cartella = Path(cartellaTemporanea)
        caricati = preparaIlResoconto(cartella, pubblicazione, collaudo, approvazione, prove)
        esito = rclone(regole, idDrive, "copy", str(cartella), f"{regole['remoto']}:{regole['cartellaDelResoconto']}",
                       "--transfers", "16", "--no-update-dir-modtime")
        if esito.returncode != 0:
            raise RuntimeError("resoconto non caricato su Drive: " + (esito.stderr or esito.stdout).strip()[-300:])
    return {"link": pubblicazione["link"], "resoconto": caricati}

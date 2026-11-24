"""Manager del passo 9: l'esportazione su Drive della demo approvata, nella cartella del cliente (Michele, 11/11/2026, task #581).

Riceve la copia del template del passo 2, la pubblicazione del passo 6 (nome, link, scadenza), il collaudo del passo 7,
l'approvazione del passo 8 e le prove delle frasi del passo 5.8 (frase -> fatto, citazione e fonte). Si esporta solo
Advanced, nella cartella del cliente su Drive, senza cartelle divise per pacchetto: il sito e il resoconto con le
fotografie del product manager.
Pitstop 5 (task #610, 12/11/2026): il resoconto si prepara prima (passo 9.2) e sale insieme al sito con una sola copia di
rclone (passo 9.1); su Drive stessi file e stesse cartelle di prima. Misurato sulla stessa demo (193 file): 52 s -> 38 s.
"""

import json
import tempfile

from .._01_LetturaDellaSezioneDelTipoDiClienteDalCRM._01_AccediAllaCartellaDelClienteSuGDrive._01_AccediAllaCartellaDelClienteSuGDrive import \
    accediAllaCartellaDelClienteSuGDrive
from ._01_CaricaIlSitoDellaDemoSuDrive._02_CaricaIlSitoDellaDemoSuDrive import FILE_DEL_DRIVE, caricaIlSitoEIlResocontoSuDrive
from ._02_CaricaIlResocontoDellaDemoSuDrive._01_CaricaIlResocontoDellaDemoSuDrive import preparaIlResoconto


def esportazioneSuDriveManager(copiaDelTemplate, pubblicazione, collaudo, approvazione, prove=None):
    regole = json.loads(FILE_DEL_DRIVE.read_text(encoding="utf-8-sig"))
    idDrive = accediAllaCartellaDelClienteSuGDrive(pubblicazione["idCliente"])["idDrive"]
    with tempfile.TemporaryDirectory(prefix="dxresoconto_", ignore_cleanup_errors=True) as cartellaDelResoconto:
        caricati = preparaIlResoconto(cartellaDelResoconto, pubblicazione, collaudo, approvazione, prove or {})
        sito = caricaIlSitoEIlResocontoSuDrive(copiaDelTemplate["sito"], cartellaDelResoconto, idDrive)
    return {"idCliente": pubblicazione["idCliente"], "pacchetto": "Advanced", "cartellaSuDrive": regole["cartellaDelSito"],
            "fileDelSito": sito, "link": pubblicazione["link"], "resoconto": caricati}

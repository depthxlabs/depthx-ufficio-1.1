"""Passo 2.2: la copia del template originale per il cliente in corso.

Riceve la cartella del modello di business scelta nel passo 2.1 (per esempio _01_TemplateSitiPerModelloDiBusiness/_02_BeB).
L'originale non si tocca mai. Si copia la sua cartella template in _02_SitoDelClienteInCorso/sito, senza le foto e i video
del template: nella demo tutto quello che si vede è del cliente. Accanto al sito si copia il contratto.json del modello.
Banco di lavoro per cliente (Michele, 11/11/2026, task #571): ogni cliente ha la sua cartella
_02_SitoDelClienteInCorso/<idCliente>, al posto dell'unica cartella che si rifaceva a ogni cliente. Così, se la fabbrica si
ferma, il cliente riparte dall'ultimo passo GO, e più fabbriche possono lavorare su clienti diversi. Quando la copia si
rifà, nella cartella del cliente si toglie tutto tranne _passi (i risultati dei passi, gestiti dal coordinatore).
La cartella del cliente si svuota dopo l'esportazione su Drive (passo 9), dal coordinatore.
"""

import shutil
from pathlib import Path

CARTELLA_DEI_CLIENTI_IN_CORSO = Path(__file__).absolute().parent / "_02_SitoDelClienteInCorso"
RISULTATI_DEI_PASSI = "_passi"
fotoOVideoDelTemplate = lambda relativa: relativa.parent.name in ("foto", "video") and relativa.parent.parent.name == "media"


def togliLaCartella(cartella):
    for voce in sorted(cartella.rglob("*"), key=lambda p: len(p.parts), reverse=True):
        voce.rmdir() if voce.is_dir() else voce.unlink()
    cartella.rmdir()


def creazioneCopiaDelTemplatePerIlCliente(idCliente, cartellaDelTemplate):
    origine = Path(cartellaDelTemplate) / "template"
    contratto = Path(cartellaDelTemplate) / "contratto.json"
    if not (origine / "index.html").is_file():
        raise RuntimeError(f"{idCliente}: il template non ha index.html: {origine}")
    CARTELLA_DEL_CLIENTE_IN_CORSO = CARTELLA_DEI_CLIENTI_IN_CORSO / idCliente
    CARTELLA_DEL_CLIENTE_IN_CORSO.mkdir(parents=True, exist_ok=True)
    for voce in list(CARTELLA_DEL_CLIENTE_IN_CORSO.iterdir()):
        if voce.name != RISULTATI_DEI_PASSI:
            togliLaCartella(voce) if voce.is_dir() else voce.unlink()
    sito =CARTELLA_DEL_CLIENTE_IN_CORSO / "sito"
    sito.mkdir(parents=True)
    for voce in sorted(origine.rglob("*")):
        relativa = voce.relative_to(origine)
        if "__pycache__" in relativa.parts or voce.suffix == ".pyc" or (voce.is_file() and fotoOVideoDelTemplate(relativa)):
            continue
        arrivo = sito / relativa
        if voce.is_dir():
            arrivo.mkdir(parents=True, exist_ok=True)
        else:
            arrivo.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(voce, arrivo)
    (sito / "media" / "foto").mkdir(parents=True, exist_ok=True)
    (sito / "media" / "video").mkdir(parents=True, exist_ok=True)
    if contratto.is_file():
        shutil.copy2(contratto, CARTELLA_DEL_CLIENTE_IN_CORSO / "contratto.json")
    return {"idCliente": idCliente, "cartellaDelClienteInCorso": str(CARTELLA_DEL_CLIENTE_IN_CORSO), "sito": str(sito),
            "contratto": str(CARTELLA_DEL_CLIENTE_IN_CORSO / "contratto.json")}

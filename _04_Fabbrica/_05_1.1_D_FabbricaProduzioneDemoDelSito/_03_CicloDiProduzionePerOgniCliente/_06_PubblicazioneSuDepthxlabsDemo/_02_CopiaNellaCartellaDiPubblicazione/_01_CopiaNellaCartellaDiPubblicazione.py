"""Passo 6.2: il sito finito del cliente copiato in _02_CartellaDiPubblicazioneDelleDemo/<nome>.

Il sito del cliente in corso (passo 2.2) si cancella dopo ogni cliente; la cartella di pubblicazione invece tiene tutte le demo
valide, ed è quella che il Worker porta online. Una copia vecchia con lo stesso nome si rifà da capo.
"""

import shutil
from pathlib import Path

CARTELLA_DI_PUBBLICAZIONE = Path(__file__).absolute().parent / "_02_CartellaDiPubblicazioneDelleDemo"


def togliLaCartella(cartella):
    for voce in sorted(cartella.rglob("*"), key=lambda p: len(p.parts), reverse=True):
        voce.rmdir() if voce.is_dir() else voce.unlink()
    cartella.rmdir()


def copiaNellaCartellaDiPubblicazione(sito, nome, cartella=CARTELLA_DI_PUBBLICAZIONE):
    arrivo = Path(cartella) / nome
    if arrivo.is_dir():
        togliLaCartella(arrivo)
    arrivo.mkdir(parents=True)
    for voce in sorted(Path(sito).rglob("*")):
        destinazione = arrivo / voce.relative_to(sito)
        if voce.is_dir():
            destinazione.mkdir(parents=True, exist_ok=True)
        else:
            destinazione.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(voce, destinazione)
    return str(arrivo)

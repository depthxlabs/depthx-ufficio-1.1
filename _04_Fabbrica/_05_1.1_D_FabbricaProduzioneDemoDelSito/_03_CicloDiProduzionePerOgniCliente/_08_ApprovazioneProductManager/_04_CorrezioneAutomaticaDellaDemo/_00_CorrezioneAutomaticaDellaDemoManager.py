"""Manager del passo 8.4: la correzione automatica della demo con i problemi del collaudo e del product manager."""

from ._03_CorrezioneAutomaticaDellaDemo import correzioneAutomaticaDellaDemo


def correzioneAutomaticaDellaDemoManager(copiaDelTemplate, collaudo, approvazione, identita, giriPrecedenti=()):
    return correzioneAutomaticaDellaDemo(copiaDelTemplate["sito"], collaudo, approvazione, identita["testi"], giriPrecedenti)

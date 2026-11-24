"""Manager del passo 5.8.7: ogni sezione con 2 o 3 frasi verificate, o fuori dalla pagina; con le foto del cliente non esce mai."""

from ._01_DueOTreFrasiPerOgniSezione import dueOTreFrasiPerOgniSezione


def dueOTreFrasiPerOgniSezioneManager(sito, completate, sceneConFoto=()):
    return dueOTreFrasiPerOgniSezione(sito, completate, sceneConFoto)

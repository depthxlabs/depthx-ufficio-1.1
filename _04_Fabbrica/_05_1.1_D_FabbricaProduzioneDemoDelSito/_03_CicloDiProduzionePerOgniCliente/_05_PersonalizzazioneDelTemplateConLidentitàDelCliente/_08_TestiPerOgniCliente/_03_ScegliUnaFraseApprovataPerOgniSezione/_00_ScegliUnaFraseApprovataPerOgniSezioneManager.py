"""Manager del passo 5.8.3: le frasi approvate che possono andare al posto di ogni frase del template."""

from ._01_ScegliUnaFraseApprovataPerOgniSezione import scegliUnaFraseApprovataPerOgniSezione


def scegliUnaFraseApprovataPerOgniSezioneManager(sito):
    return scegliUnaFraseApprovataPerOgniSezione(sito)

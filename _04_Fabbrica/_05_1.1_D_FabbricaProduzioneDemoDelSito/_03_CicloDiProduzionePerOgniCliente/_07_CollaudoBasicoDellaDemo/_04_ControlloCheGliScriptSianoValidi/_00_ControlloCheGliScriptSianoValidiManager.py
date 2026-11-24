"""Manager del passo 7.4: ogni script del sito è JavaScript valido."""

from ._01_ScriptNonValidi import scriptNonValidi


def controlloCheGliScriptSianoValidiManager(sito):
    return scriptNonValidi(sito)

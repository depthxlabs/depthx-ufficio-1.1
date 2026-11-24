"""Manager del passo 5.15: le pagine dalla lista Advanced (Michele, 11/11/2026, task #576).

Gira in due momenti del passo 5: dopo le aree del passo 5.7 sceglie le pagine che nascono; alla fine del passo 5 toglie
le pagine rimaste senza materiale.
"""

from ._01_LePagineDallaListaAdvanced import primaSezioneRicca, scegliLePagine, togliLePagineVuote


def scegliLePagineDallaListaAdvancedManager(sito, contratto, aree):
    return scegliLePagine(sito, contratto, aree)


def togliLePagineVuoteManager(sito, contratto, aree):
    return togliLePagineVuote(sito, contratto, aree)


def primaSezioneRiccaManager(sito):
    return primaSezioneRicca(sito)

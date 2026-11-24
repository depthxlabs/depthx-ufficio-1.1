"""Manager del passo 5.8.6: le frasi non verificate si sostituiscono con frasi verificate, del sito o senza fatti; quelle
senza una sostituta escono dalla pagina (Michele, 9/11/2026)."""

from ._01_TogliLeSezioniSenzaUnaFraseCompleta import sostituisciLeFrasiNonVerificate, togliLeSezioniSenzaUnaFraseCompleta


def sostituisciLeFrasiNonVerificateManager(sito, completate):
    return sostituisciLeFrasiNonVerificate(sito, completate)


def togliLeSezioniSenzaUnaFraseCompletaManager(sito, frasi, fatti, sceneConFoto=()):
    return togliLeSezioniSenzaUnaFraseCompleta(sito, frasi, fatti, sceneConFoto)

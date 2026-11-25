"""Manager del passo 8.2: il giudizio estetico del modello gratuito, come product manager, sulle fotografie e sui testi della demo."""

from ._03_GiudizioEsteticoAI import giudizioEsteticoAI


def giudizioEsteticoAIManager(sito, fotografie, recensioni):
    return giudizioEsteticoAI(sito, fotografie, recensioni)

"""Manager del passo 8.2: il giudizio estetico di Claude, come product manager, sulle fotografie e sui testi della demo."""

from ._03_GiudizioEsteticoDiClaude import giudizioEsteticoDiClaude


def giudizioEsteticoDiClaudeManager(sito, fotografie, recensioni):
    return giudizioEsteticoDiClaude(sito, fotografie, recensioni)

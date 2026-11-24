"""Manager del passo 7.7: ogni frase visibile è una frase del copywriting approvato, con i fatti tra graffe completati."""

from ._02_FrasiFuoriDalCopywritingApprovato import frasiFuoriDalCopywritingApprovato


def controlloCheOgniFraseSiaDelCopywritingApprovatoManager(sito, recensioni):
    return frasiFuoriDalCopywritingApprovato(sito, recensioni)

"""Manager del passo 7.12: ogni pagina ha l'icona del cliente nella scheda del browser."""

from ._01_PagineSenzaIcona import pagineSenzaIcona


def controlloDellIconaInOgniPaginaManager(sito):
    return pagineSenzaIcona(sito)

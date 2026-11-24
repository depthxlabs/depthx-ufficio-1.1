"""Manager del passo 4.3: il centro del soggetto della foto."""

from ._01_TrovaIlCentroDelSoggettoDellaFoto import trovaIlCentroDelSoggettoDellaFoto


def trovaIlCentroDelSoggettoDellaFotoManager(immagine, soggetto=None):
    return trovaIlCentroDelSoggettoDellaFoto(immagine, soggetto)

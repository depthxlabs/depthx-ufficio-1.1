"""Manager del passo 7.3: ogni file richiamato dal sito esiste, foto delle scene comprese."""

from .._01_ControlloCheNessunaParolaDelTemplateSiaRimasta._02_CodiceDelSitoSenzaCommenti import codiceDelSitoSenzaCommenti
from .._01_ControlloCheNessunaParolaDelTemplateSiaRimasta._04_ValoriDelFileDiConfigurazione import \
    valoriDelFileDiConfigurazione
from ._01_FileRichiamatiMancanti import fileRichiamatiMancanti


def controlloCheTuttiIFileChiamatiEsistonoManager(sito, fotoSalvate):
    return fileRichiamatiMancanti(sito, codiceDelSitoSenzaCommenti(sito), valoriDelFileDiConfigurazione(sito), fotoSalvate)

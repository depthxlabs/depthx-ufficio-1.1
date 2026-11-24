"""Manager del passo 7.10: nel sito non ci sono né il voto né il numero delle recensioni."""

from .._01_ControlloCheNessunaParolaDelTemplateSiaRimasta._02_CodiceDelSitoSenzaCommenti import codiceDelSitoSenzaCommenti
from ._01_VotoENumeroDelleRecensioniNelSito import votoENumeroDelleRecensioniNelSito


def controlloCheNelSitoNonCiSianoVotoENumeroDelleRecensioniManager(sito):
    return votoENumeroDelleRecensioniNelSito(codiceDelSitoSenzaCommenti(sito))

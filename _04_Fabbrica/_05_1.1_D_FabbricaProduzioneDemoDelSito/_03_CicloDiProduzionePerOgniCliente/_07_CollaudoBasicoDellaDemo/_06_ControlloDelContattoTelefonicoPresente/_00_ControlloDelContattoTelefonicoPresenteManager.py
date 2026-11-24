"""Manager del passo 7.6: il telefono del cliente compare nel sito."""

from .._01_ControlloCheNessunaParolaDelTemplateSiaRimasta._02_CodiceDelSitoSenzaCommenti import codiceDelSitoSenzaCommenti
from ._01_TelefonoDelClienteNelSito import telefonoDelClienteNelSito


def controlloDelContattoTelefonicoPresenteManager(sito, crm):
    return telefonoDelClienteNelSito(codiceDelSitoSenzaCommenti(sito), crm)

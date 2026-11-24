"""Manager del passo 7.5: le scene del cliente sono nel config.js e gli script leggono ancora la configurazione del template."""

from .._01_ControlloCheNessunaParolaDelTemplateSiaRimasta._02_CodiceDelSitoSenzaCommenti import codiceDelSitoSenzaCommenti
from ._01_ConfigurazioneDelleScene import configurazioneDelleScene


def controlloDellaConfigurazioneDelleScenePresentiManager(sito):
    return configurazioneDelleScene(sito, codiceDelSitoSenzaCommenti(sito))

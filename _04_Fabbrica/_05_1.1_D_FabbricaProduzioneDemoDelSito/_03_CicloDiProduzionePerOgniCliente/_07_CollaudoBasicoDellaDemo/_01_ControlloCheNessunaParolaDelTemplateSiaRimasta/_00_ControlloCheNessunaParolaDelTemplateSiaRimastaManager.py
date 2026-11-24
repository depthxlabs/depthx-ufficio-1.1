"""Manager del passo 7.1: nessuna parola del template rimasta e nessuna frase da sito dimostrativo."""

from ._02_CodiceDelSitoSenzaCommenti import codiceDelSitoSenzaCommenti
from ._03_ParoleDelTemplateRimaste import paroleDelTemplateRimaste


def controlloCheNessunaParolaDelTemplateSiaRimastaManager(sito, contratto):
    return paroleDelTemplateRimaste(codiceDelSitoSenzaCommenti(sito), contratto)

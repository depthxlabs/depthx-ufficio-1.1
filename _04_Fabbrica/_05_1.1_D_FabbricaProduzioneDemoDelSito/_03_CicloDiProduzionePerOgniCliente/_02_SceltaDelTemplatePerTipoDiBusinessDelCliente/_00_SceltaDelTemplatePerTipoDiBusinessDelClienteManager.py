# ## Commento di Michele
# scritto il 7 nov alle 12:08
#
# il piano e finire tutte le cartelle del ciclo di produzione, e poi sistemare i template in modo definitivo
# quindi prima si rendono operative tutte le cartelle del ciclo, e poi si sistemano in modo definitivo i template

"""Manager del passo 2: la scelta del template per il tipo di business del cliente e la sua copia per il cliente in corso.

Riceve la scheda del cliente del passo 1. Il passo 2.1 sceglie il modello dal tipo del CRM, il passo 2.2 ne fa la copia.
Restituisce la copia (sito, contratto, cartella del cliente in corso) con il nome del modello (per esempio _02_BeB).
"""

from pathlib import Path

from ._01_TemplateSitiPerModelloDiBusiness._00_TemplateSitiPerModelloDiBusinessManager import \
    templateSitiPerModelloDiBusinessManager
from ._02_CreazioneCopiaDelTemplateOriginalePerIlClienteInCorso._00_CreazioneCopiaDelTemplateOriginalePerIlClienteInCorsoManager import \
    creazioneCopiaDelTemplateOriginalePerIlClienteInCorsoManager


def sceltaDelTemplatePerTipoDiBusinessDelClienteManager(schedaDelCliente):
    cartellaDelModello = templateSitiPerModelloDiBusinessManager(schedaDelCliente["tipo"])
    copia = creazioneCopiaDelTemplateOriginalePerIlClienteInCorsoManager(schedaDelCliente["idCliente"], cartellaDelModello)
    return {**copia, "modello": Path(cartellaDelModello).name}

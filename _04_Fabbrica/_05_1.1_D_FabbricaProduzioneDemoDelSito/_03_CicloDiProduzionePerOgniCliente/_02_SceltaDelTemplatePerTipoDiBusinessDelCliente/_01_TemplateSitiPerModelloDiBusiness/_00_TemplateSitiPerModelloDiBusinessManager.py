"""Manager del passo 2.1: il template del modello di business del cliente.

Il tipo del CRM porta il numero del modello tra parentesi quadre ("[01] Hotel", "[02] B&B", "[03] Agriturismo",
"[04] Casa Vacanza"): il template è la cartella di questo passo con lo stesso numero (_01_Hotel, _02_BeB...).
Restituisce il percorso della cartella del modello.
"""

import re
from pathlib import Path

CARTELLA_DEI_MODELLI = Path(__file__).absolute().parent


def templateSitiPerModelloDiBusinessManager(tipo):
    numero = re.search(r"\[(\d+)\]", tipo or "")
    if not numero:
        raise RuntimeError(f"il tipo del cliente non dice il modello di business: \"{tipo}\"")
    modelli = [cartella for cartella in sorted(CARTELLA_DEI_MODELLI.iterdir())
               if cartella.is_dir() and cartella.name.startswith(f"_{int(numero.group(1)):02d}_")]
    if not modelli:
        raise RuntimeError(f"nessun template per il tipo \"{tipo}\"")
    return str(modelli[0])

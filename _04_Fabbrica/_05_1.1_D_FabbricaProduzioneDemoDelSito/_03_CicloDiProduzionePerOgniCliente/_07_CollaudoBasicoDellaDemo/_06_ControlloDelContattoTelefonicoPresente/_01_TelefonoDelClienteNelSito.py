"""Passo 7.6: il telefono del cliente, quando c'è nel CRM, compare nel sito (si confrontano le ultime 9 cifre).
Restituisce l'elenco dei problemi trovati.
"""

import re


def telefonoDelClienteNelSito(codici, crm):
    telefono = re.sub(r"\D", "", crm.get("telefono") or crm.get("cellulare") or "")[-9:]
    if telefono and telefono not in re.sub(r"\D", "", "\n".join(codici.values())):
        return ["il telefono del cliente non compare nel sito"]
    return []

"""Passo 6.1: il nome della demo nel link depthxlabs.com/demo/<nome>/.

Il nome del cliente senza spazi, accenti e simboli, al massimo 40 caratteri. Se il nome è già di un altro cliente nel registro
delle demo su Cloudflare, o di una delle 4 demo dei template, si aggiungono le cifre dell'ID del cliente.
"""

import re
import unicodedata

from .._04_PubblicazioneDellaDemoSulLink._03_SchedaDellaDemoSuCloudflare import schedaDellaDemoSuCloudflare
from _01_StrumentiDellaFabbrica._04_RegistroLogDellaFabbrica._00_RegistroDellaFabbrica import stessoCliente

NOMI_DEI_TEMPLATE = {"hotelmiralago", "dafnebnb", "agriturismoilcrepuscolo", "apulialux"}


def nomeDellaDemo(schedaDelCliente):
    idCliente = schedaDelCliente["idCliente"]
    base = unicodedata.normalize("NFKD", schedaDelCliente.get("nome") or idCliente).encode("ascii", "ignore").decode().lower()
    base = re.sub(r"[^a-z0-9]", "", base)[:40] or idCliente.lower().replace("_", "")
    if base in NOMI_DEI_TEMPLATE or not stessoCliente((schedaDellaDemoSuCloudflare(base) or {}).get("cliente", idCliente), idCliente):
        base += re.sub(r"\D", "", idCliente)
    return base

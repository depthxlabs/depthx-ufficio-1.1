"""Manager del passo 6.3: la scadenza della demo, calcolata e scritta nel registro delle demo su Cloudflare."""

from .._04_PubblicazioneDellaDemoSulLink._03_SchedaDellaDemoSuCloudflare import schedaDellaDemoSuCloudflare
from ._01_CalcolaLaScadenzaDellaDemo._00_CalcolaLaScadenzaDellaDemoManager import calcolaLaScadenzaDellaDemoManager
from ._02_ScriviLaSchedaDellaDemoSuCloudflare._00_ScriviLaSchedaDellaDemoSuCloudflareManager import \
    scriviLaSchedaDellaDemoSuCloudflareManager


def impostaLaScadenzaDellaDemoManager(idCliente, nome):
    scheda = calcolaLaScadenzaDellaDemoManager(idCliente, schedaDellaDemoSuCloudflare(nome))
    return scriviLaSchedaDellaDemoSuCloudflareManager(nome, scheda)

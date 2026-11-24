"""Manager del passo 6: la demo del cliente pubblicata su depthxlabs.com/demo/<nome>/.

Riceve la scheda del cliente del passo 1 (idCliente, nome) e la copia del template del passo 2.2 con il sito finito del passo 5.
"""

from ._01_PreparaNomeDellaDemoPerIlLink._00_PreparaNomeDellaDemoPerIlLinkManager import preparaNomeDellaDemoPerIlLinkManager
from ._02_CopiaNellaCartellaDiPubblicazione._00_CopiaNellaCartellaDiPubblicazioneManager import \
    copiaNellaCartellaDiPubblicazioneManager
from ._03_ImpostaLaScadenzaDellaDemo._00_ImpostaLaScadenzaDellaDemoManager import impostaLaScadenzaDellaDemoManager
from ._04_PubblicazioneDellaDemoSulLink._00_PubblicazioneDellaDemoSulLinkManager import pubblicazioneDellaDemoSulLinkManager


MINUTI_TRA_UN_TENTATIVO_E_L_ALTRO = 10


def finchéCloudflareRisponde(lavoro):
    """Se Cloudflare non risponde o rifiuta per un limite, la demo non va NOTGO: resta in attesa di pubblicazione
    e si riprova ogni 10 minuti, finché Cloudflare risponde. Gli altri errori passano come prima."""
    import re
    import time
    while True:
        try:
            return lavoro()
        except Exception as errore:
            if not re.search(r"Cloudflare|R2|timed out|Connection|urlopen|50\d|429", str(errore), re.I):
                raise
            print(f"in attesa di pubblicazione: Cloudflare non risponde ({str(errore)[:120]}), si riprova fra {MINUTI_TRA_UN_TENTATIVO_E_L_ALTRO} minuti", flush=True)
            time.sleep(MINUTI_TRA_UN_TENTATIVO_E_L_ALTRO * 60)


def pubblicazioneSuDepthxlabsDemoManager(schedaDelCliente, copiaDelTemplate):
    nome = preparaNomeDellaDemoPerIlLinkManager(schedaDelCliente)
    copiaNellaCartellaDiPubblicazioneManager(copiaDelTemplate["sito"], nome)
    scheda = finchéCloudflareRisponde(lambda: impostaLaScadenzaDellaDemoManager(schedaDelCliente["idCliente"], nome))
    pubblicazione = finchéCloudflareRisponde(lambda: pubblicazioneDellaDemoSulLinkManager(nome))
    return {"idCliente": schedaDelCliente["idCliente"], "nomeDellaDemo": nome, "link": pubblicazione["link"],
            "scadenza": scheda["scadenza"], "versione": pubblicazione["versione"],
            "demoScaduteTolte": pubblicazione["demoScaduteTolte"], "pagineOnline": pubblicazione["pagineOnline"]}

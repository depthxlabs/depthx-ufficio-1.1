"""Passo 6.3.2: la scheda della demo scritta nel registro delle demo su Cloudflare, chiave demo:<nome>.

Il Worker la legge a ogni apertura: dopo la scadenza la demo non si apre più, dopo l'invio le aperture si registrano per il
Centro Gestione. La scadenza si scrive anche nell'etichetta della chiave, così il passo 6.4 trova le demo scadute con una sola
lettura del registro. Pitstop 4 (task #609, 12/11/2026): si scrive con una chiamata diretta alle API di Cloudflare, meno di un
secondo, invece di avviare wrangler.
"""

from ..._04_PubblicazioneDellaDemoSulLink._09_ApiDiCloudflare import scriviNelRegistro


def scriviLaSchedaDellaDemoSuCloudflare(nome, scheda):
    try:
        scriviNelRegistro(f"demo:{nome}", scheda, {"scadenza": scheda["scadenza"]})
    except Exception as errore:
        raise RuntimeError(f"scheda della demo {nome} non scritta su Cloudflare: {errore}") from errore
    return scheda

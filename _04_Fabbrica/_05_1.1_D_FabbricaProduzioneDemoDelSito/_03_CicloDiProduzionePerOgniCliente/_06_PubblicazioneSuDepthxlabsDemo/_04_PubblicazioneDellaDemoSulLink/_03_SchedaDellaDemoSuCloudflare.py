"""La scheda di una demo nel registro delle demo su Cloudflare (chiave demo:<nome>): cliente, pubblicata, scadenza, invio.

Restituisce None se la demo non ha una scheda. Pitstop 4 (task #609, 12/11/2026): si legge con una chiamata diretta alle API di
Cloudflare, meno di un secondo, invece di avviare wrangler (4-10 secondi).
"""

from ._09_ApiDiCloudflare import leggiDalRegistro


def schedaDellaDemoSuCloudflare(nome):
    try:
        return leggiDalRegistro(f"demo:{nome}")
    except Exception as errore:
        raise RuntimeError(f"scheda della demo {nome} non letta da Cloudflare: {errore}") from errore

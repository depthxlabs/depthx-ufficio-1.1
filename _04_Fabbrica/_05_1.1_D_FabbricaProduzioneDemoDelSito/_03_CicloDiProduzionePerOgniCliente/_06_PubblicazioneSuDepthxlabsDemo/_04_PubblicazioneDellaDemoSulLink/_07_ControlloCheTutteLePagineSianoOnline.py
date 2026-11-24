"""Il controllo di pubblicazione su tutte le pagine del sito, non solo la prima (Michele, 11/11/2026, task #578).

Dopo la pubblicazione del Worker, ogni pagina .html della demo nella cartella di pubblicazione si apre sul suo link e deve
rispondere 200 con lo stesso titolo della pagina pubblicata. Cloudflare può metterci qualche secondo: si riprova fino a
TENTATIVI volte, con ATTESA secondi tra un giro e l'altro. Restituisce le pagine controllate; se una pagina non è online
il passo si ferma con la causa.
"""

import html
import re
import time
import urllib.error
import urllib.request
from pathlib import Path

from .._02_CopiaNellaCartellaDiPubblicazione._01_CopiaNellaCartellaDiPubblicazione import CARTELLA_DI_PUBBLICAZIONE

TENTATIVI = 30  # Pitstop 4 (task #609): giri più fitti, stessa finestra di 60 secondi
ATTESA = 2
TITOLO = re.compile(r"<title\b[^>]*>(.*?)</title\s*>", re.S | re.I)


def titoloDellaPagina(codice):
    trovato = TITOLO.search(codice)
    return " ".join(html.unescape(trovato.group(1)).split()) if trovato else ""


def rispostaDellaPagina(indirizzo):
    richiesta = urllib.request.Request(indirizzo, headers={"User-Agent": "DepthX-Fabbrica/1.0", "Cache-Control": "no-cache"})
    try:
        with urllib.request.urlopen(richiesta, timeout=30) as risposta:
            return risposta.status, risposta.read().decode("utf-8", errors="ignore")
    except urllib.error.HTTPError as errore:
        return errore.code, ""
    except (urllib.error.URLError, TimeoutError, OSError):
        return 0, ""


def controlloCheTutteLePagineSianoOnline(nome, link):
    cartella = Path(CARTELLA_DI_PUBBLICAZIONE) / nome
    pagine = {pagina.name: titoloDellaPagina(pagina.read_text(encoding="utf-8-sig", errors="ignore"))
              for pagina in sorted(cartella.glob("*.html"))}
    if "index.html" not in pagine:
        raise RuntimeError(f"la demo {nome} non ha la home index.html nella cartella di pubblicazione")
    mancanti = dict(pagine)
    for volta in range(TENTATIVI):
        for file, titolo in list(mancanti.items()):
            stato, codice = rispostaDellaPagina(link + ("" if file == "index.html" else file))
            if stato == 200 and titoloDellaPagina(codice) == titolo:
                mancanti.pop(file)
        if not mancanti:
            return sorted(pagine)
        time.sleep(ATTESA)
    raise RuntimeError("pagine della demo non online dopo la pubblicazione: " + ", ".join(sorted(mancanti)))

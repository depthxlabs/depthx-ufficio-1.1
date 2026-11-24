"""Passo 7.13: il logo del cliente compare quando si apre la home.

Il campo logo del file di configurazione porta a un file che esiste (passo 5.12); se è vuoto, il passo 5.13 ha scritto
il nome del cliente come logo. La home (index.html) esiste. Restituisce l'elenco dei problemi trovati.
"""

from pathlib import Path

from .._01_ControlloCheNessunaParolaDelTemplateSiaRimasta._04_ValoriDelFileDiConfigurazione import \
    valoriDelFileDiConfigurazione

NOME_COME_LOGO = "DepthX, fabbrica dei siti: senza logo usabile si scrive il nome."


def logoMancanteNellaHome(sito):
    radice = Path(sito)
    if not (radice / "index.html").is_file():
        return ["manca la home index.html"]
    configurazione = radice / "assets" / "js" / "config.js"
    if not configurazione.is_file():
        return ["manca il file di configurazione con il logo"]
    logo = (valoriDelFileDiConfigurazione(sito, "logo") or [""])[0]
    if logo:
        percorso = logo.split("?")[0].lstrip("/")
        if not logo.startswith("data:") and not any((base / percorso).is_file()
                                                    for base in (radice, radice / "media", radice / "media" / "foto")):
            return [f"il logo {logo} non c'è"]
        return []
    if NOME_COME_LOGO not in configurazione.read_text(encoding="utf-8-sig", errors="ignore"):
        return ["la home non ha né il logo del cliente né il nome scritto come logo"]
    return []

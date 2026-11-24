"""Passo 7.5: la configurazione delle scene c'è. Il config.js contiene il blocco delle aree del cliente scritto nel passo 5.7,
e gli altri script del template leggono ancora la configurazione del template (window.HOTEL_CONFIG e simili).
Restituisce l'elenco dei problemi trovati.
"""

import re
from pathlib import Path

BLOCCO_DELLE_AREE = "DepthX, fabbrica dei siti: le aree della struttura con le foto del cliente."


def configurazioneDelleScene(sito, codici):
    file = Path(sito) / "assets" / "js" / "config.js"
    if not file.is_file():
        return ["manca il file di configurazione assets/js/config.js"]
    configurazione = file.read_text(encoding="utf-8-sig", errors="ignore")
    problemi = [] if BLOCCO_DELLE_AREE in configurazione else ["nel config.js mancano le aree del cliente"]
    variabile = re.search(r"window\.(\w+)\s*=", configurazione)
    if not variabile:
        return problemi + ["nel config.js manca la configurazione del template"]
    altriScript = [codice for percorso, codice in codici.items() if percorso.endswith(".js") and Path(percorso) != file]
    if not any(f"window.{variabile.group(1)}" in codice for codice in altriScript):
        problemi.append(f"gli script non leggono più la configurazione window.{variabile.group(1)}")
    return problemi

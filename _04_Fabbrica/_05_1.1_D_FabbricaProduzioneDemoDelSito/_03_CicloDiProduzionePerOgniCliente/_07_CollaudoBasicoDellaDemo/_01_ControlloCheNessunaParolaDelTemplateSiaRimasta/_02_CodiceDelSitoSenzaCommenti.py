"""Il codice di ogni pagina, stile e script del sito senza i commenti: i controlli del collaudo guardano solo quello che il
visitatore riceve. Le foto e i video della cartella media non si leggono. Il file di configurazione conta con i valori che
riceve il sito (_04_ValoriDelFileDiConfigurazione.py), uno per riga.

Restituisce percorso del file -> codice senza commenti.
"""

import re
from pathlib import Path

from ._04_ValoriDelFileDiConfigurazione import valoriDelFileDiConfigurazione

TIPI_DI_CODICE = (".html", ".js", ".css")


def codiceDelSitoSenzaCommenti(sito):
    codici = {}
    for file in sorted(Path(sito).rglob("*")):
        if not file.is_file() or file.suffix.lower() not in TIPI_DI_CODICE or "media" in file.relative_to(sito).parts:
            continue
        if file == Path(sito) / "assets" / "js" / "config.js":
            codici[str(file)] = "\n".join(valoriDelFileDiConfigurazione(sito))
            continue
        codice = file.read_text(encoding="utf-8-sig", errors="ignore")
        codice = re.sub(r"/\*.*?\*/", "", codice, flags=re.S)
        codice = re.sub(r"<!--.*?-->", "", codice, flags=re.S)
        if file.suffix.lower() == ".js":
            codice = re.sub(r"(?m)^\s*//.*$", "", codice)
        codici[str(file)] = codice
    return codici

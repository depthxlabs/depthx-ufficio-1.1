"""Passo 7.12: ogni pagina ha l'icona del cliente nella scheda del browser: un <link rel="icon"> verso un file che esiste.
Restituisce l'elenco dei problemi trovati.
"""

import re
from pathlib import Path


def pagineSenzaIcona(sito):
    problemi = []
    for pagina in sorted(Path(sito).glob("*.html")):
        codice = re.sub(r"<!--.*?-->", "", pagina.read_text(encoding="utf-8-sig", errors="ignore"), flags=re.S)
        icone = [re.search(r'\bhref="([^"]+)"', tag).group(1) for tag in re.findall(r"<link\b[^>]*>", codice, re.I)
                 if re.search(r'\brel="[^"]*\bicon\b', tag, re.I) and re.search(r'\bhref="([^"]+)"', tag)]
        if not icone:
            problemi.append(f"{pagina.name}: manca l'icona nella scheda del browser")
        for icona in icone:
            percorso = icona.split("?")[0].lstrip("/")
            if not icona.startswith("data:") and not (pagina.parent / percorso).is_file() and not (Path(sito) / percorso).is_file():
                problemi.append(f"{pagina.name}: l'icona {icona} non c'è")
    return problemi

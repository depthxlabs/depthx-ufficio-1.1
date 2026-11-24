"""Passo 7.11: il link alle recensioni porta alla pagina delle recensioni Google, mai a Google Maps.

Si guardano il campo del link delle recensioni nel file di configurazione (i campi sono quelli del passo 5.5) e ogni link
delle pagine che parla di recensioni. Restituisce l'elenco dei problemi trovati.
"""

import html
import json
import re
from pathlib import Path

from .._01_ControlloCheNessunaParolaDelTemplateSiaRimasta._04_ValoriDelFileDiConfigurazione import \
    valoriDelFileDiConfigurazione

VERSO_MAPS = re.compile(r"google\.[a-z.]+/maps|maps\.google|maps\.app\.goo\.gl|goo\.gl/maps", re.I)
RECENSIONI = re.compile(r"recension|review", re.I)
FILE_DEI_CAMPI = (Path(__file__).absolute().parents[2] / "_05_PersonalizzazioneDelTemplateConLidentitàDelCliente"
                  / "_05_ScriviIlLinkDelleRecensioniNelFileDiConfigurazione" / "_01_CampiNelFileDiConfigurazione.json")


def linkDelleRecensioniVersoMaps(sito):
    problemi = []
    for pagina in sorted(Path(sito).glob("*.html")):
        codice = re.sub(r"<!--.*?-->", "", pagina.read_text(encoding="utf-8-sig", errors="ignore"), flags=re.S)
        for collegamento in re.finditer(r"<a\b([^>]*)>(.*?)</a\s*>", codice, re.S | re.I):
            href = re.search(r'\bhref="([^"]*)"', collegamento.group(1))
            if href and RECENSIONI.search(html.unescape(collegamento.group(0))) and VERSO_MAPS.search(href.group(1)):
                problemi.append(f"{pagina.name}: il link delle recensioni porta a Google Maps: {href.group(1)[:100]}")
    configurazione = Path(sito) / "assets" / "js" / "config.js"
    if configurazione.is_file():
        variabile = re.search(r"window\.(\w+)\s*=", configurazione.read_text(encoding="utf-8-sig", errors="ignore"))
        campi = json.loads(FILE_DEI_CAMPI.read_text(encoding="utf-8-sig")).get(variabile.group(1) if variabile else "", {})
        if campi.get("link"):
            valore = valoriDelFileDiConfigurazione(sito, campi["link"])
            if valore and VERSO_MAPS.search(valore[0]):
                problemi.append(f"config.js: il link delle recensioni porta a Google Maps: {valore[0][:100]}")
    return problemi

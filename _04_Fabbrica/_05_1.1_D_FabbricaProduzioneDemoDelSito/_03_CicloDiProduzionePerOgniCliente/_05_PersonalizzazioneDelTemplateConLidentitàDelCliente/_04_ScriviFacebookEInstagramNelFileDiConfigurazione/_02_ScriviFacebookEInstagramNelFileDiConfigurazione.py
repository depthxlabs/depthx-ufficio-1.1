"""Passo 5.4: Facebook e Instagram del cliente nel file di configurazione (assets/js/config.js).

I link vengono dai dati del CRM e si scrivono con https. Se mancano, i campi restano vuoti e il template li toglie
dal piede. I campi di ogni template sono in _01_CampiNelFileDiConfigurazione.json.
"""

import json
import re
from pathlib import Path

FILE_DEI_CAMPI = Path(__file__).absolute().parent / "_01_CampiNelFileDiConfigurazione.json"


def scriviFacebookEInstagramNelFileDiConfigurazione(sito, datiUnici):
    crm = datiUnici["crm"]
    valori = {}
    for social in ("facebook", "instagram"):
        link = (crm.get(social) or "").strip()
        valori[social] = ("https://" + re.sub(r"^(https?://)?", "", link)) if link else ""
    file = Path(sito) / "assets" / "js" / "config.js"
    variabile = re.search(r"window\.(\w+)\s*=", file.read_text(encoding="utf-8-sig")).group(1)
    campi = json.loads(FILE_DEI_CAMPI.read_text(encoding="utf-8-sig"))[variabile]
    righe = [f"window.{variabile}.{campi[campo]} = {json.dumps(valore, ensure_ascii=False)};"
             for campo, valore in valori.items() if campi.get(campo) and valore]
    with file.open("a", encoding="utf-8") as config:
        config.write("\n/* DepthX, fabbrica dei siti: Facebook e Instagram del cliente. */\n" + "\n".join(righe) + "\n")
    # implementare post template: Casa Vacanza non ha i campi dei social nel file di configurazione.
    return valori

"""Passo 5.6: le lingue della demo nel file di configurazione.

Pacchetto Advanced (Michele, 11/11/2026): il sito è sempre in italiano e in inglese, qualunque lingua abbia il sito attuale
del cliente. La terza lingua (tedesco, francese o spagnolo) la sceglie il cliente dopo l'acquisto: nella demo non c'è.
"""

import json
import re
from pathlib import Path

LINGUE_DELL_ADVANCED = ["it", "en"]


def scriviLeLingueDellaDemoNelFileDiConfigurazione(sito, schedaDelCliente, sitoGiaEsistente):
    lingue = list(LINGUE_DELL_ADVANCED)
    file = Path(sito) / "assets" / "js" / "config.js"
    variabile = re.search(r"window\.(\w+)\s*=", file.read_text(encoding="utf-8-sig")).group(1)
    with file.open("a", encoding="utf-8") as config:
        config.write(f"\n/* DepthX, fabbrica dei siti: le lingue della demo. */\nwindow.{variabile}.lingue = {json.dumps(lingue)};\n")
    return lingue

"""Passo 5.13: senza un logo usabile, il nome del cliente scritto come logo.

Il campo logo del file di configurazione resta vuoto: con il logo vuoto ogni template scrive il nome della struttura
nel suo carattere con grazie, in testata, apertura e piede. Con un logo usabile (passo 5.12) non fa niente.
"""

import json
import re
from pathlib import Path


def scriviIlNomeComeLogoSeIlLogoManca(sito, logo):
    if logo:
        return False
    file = Path(sito) / "assets" / "js" / "config.js"
    variabile = re.search(r"window\.(\w+)\s*=", file.read_text(encoding="utf-8-sig")).group(1)
    with file.open("a", encoding="utf-8") as config:
        config.write(f"\n/* DepthX, fabbrica dei siti: senza logo usabile si scrive il nome. */\nwindow.{variabile}.logo = {json.dumps('')};\n")
    # implementare post template: i caratteri di _01_CaratteriPerIlLogoInTesto, se i template definitivi useranno per il
    # nome un carattere diverso dal loro. Oggi nessun template li usa.
    return True

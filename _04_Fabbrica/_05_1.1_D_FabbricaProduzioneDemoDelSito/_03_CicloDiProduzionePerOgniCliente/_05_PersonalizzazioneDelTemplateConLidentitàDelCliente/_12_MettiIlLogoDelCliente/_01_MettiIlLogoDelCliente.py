"""Passo 5.12: il logo del cliente in testata, apertura e piede, se è usabile.

Usabile vuol dire con lo sfondo trasparente (PNG, WebP o SVG): un logo su un riquadro bianco o in una foto non si usa.
Il logo usabile si salva in assets/logo/logo.png (o logo.svg) e il campo logo del file di configurazione punta lì.
Restituisce il percorso del logo nel sito, oppure "" se il cliente non ha un logo usabile.
"""

import json
import re
import shutil
from pathlib import Path

from PIL import Image


def mettiIlLogoDelCliente(sito, fotoInOrdine, fotoScaricate):
    voce = next((voce for voce in fotoInOrdine if voce.get("categoria") == "logo" and voce["id"] in fotoScaricate), None)
    if not voce:
        return ""
    origine = Path(fotoScaricate[voce["id"]])
    cartella = Path(sito) / "assets" / "logo"
    cartella.mkdir(parents=True, exist_ok=True)
    if origine.suffix.lower() == ".svg":
        shutil.copy2(origine, cartella / "logo.svg")
        logo = "assets/logo/logo.svg"
    else:
        with Image.open(origine) as immagine:
            immagine = immagine.convert("RGBA")
            trasparente = immagine.getchannel("A").getextrema()[0] < 128
            if not trasparente:
                return ""
            immagine.save(cartella / "logo.png", "PNG", optimize=True)
        logo = "assets/logo/logo.png"
    file = Path(sito) / "assets" / "js" / "config.js"
    variabile = re.search(r"window\.(\w+)\s*=", file.read_text(encoding="utf-8-sig")).group(1)
    with file.open("a", encoding="utf-8") as config:
        config.write(f"\n/* DepthX, fabbrica dei siti: il logo del cliente. */\nwindow.{variabile}.logo = {json.dumps(logo)};\n")
    return logo

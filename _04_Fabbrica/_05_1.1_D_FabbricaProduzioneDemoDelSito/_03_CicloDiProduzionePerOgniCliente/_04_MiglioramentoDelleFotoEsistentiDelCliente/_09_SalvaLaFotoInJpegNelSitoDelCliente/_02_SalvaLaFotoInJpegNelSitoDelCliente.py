"""Passo 4.9: il salvataggio nella cartella media/foto del sito del cliente in corso.

La foto base è <area>_<forma>.jpg (per esempio casa_16x9.jpg), con il lato lungo massimo di _01_RegoleDelSalvataggio.json.
Accanto si salvano le larghezze che tutti i template chiedono, in JPEG e in WebP: <area>_<forma>-<larghezza>.jpg e .webp
(per esempio casa_16x9-1280.webp). Una foto non si ingrandisce mai: se l'originale è più piccolo, la larghezza resta la
sua. La nitidezza (passo 4.8) si dà a ogni misura dopo il rimpicciolimento, perché rimpicciolire la toglie (Michele,
8/11/2026). Restituisce il nome della foto base.
"""

import json
from pathlib import Path

from PIL import Image

from .._08_SistemaLaNitidezza._00_SistemaLaNitidezzaManager import sistemaLaNitidezzaManager

FILE_DELLE_REGOLE = Path(__file__).absolute().parent / "_01_RegoleDelSalvataggio.json"


def rimpicciolita(immagine, scala):
    if scala < 1:
        immagine = immagine.resize((round(immagine.width * scala), round(immagine.height * scala)), Image.LANCZOS)
    return sistemaLaNitidezzaManager(immagine)


def salvaLaFotoInJpegNelSitoDelCliente(immagine, sito, idArea, forma):
    regole = json.loads(FILE_DELLE_REGOLE.read_text(encoding="utf-8-sig"))
    immagine = immagine.convert("RGB")
    base = rimpicciolita(immagine, int(regole["latoLungoDelleFoto"]) / max(immagine.size))
    cartella = Path(sito) / "media" / "foto"
    cartella.mkdir(parents=True, exist_ok=True)
    qualitaJpeg, qualitaWebp = int(regole["qualitaJpegDelleFoto"]), int(regole["qualitaWebpDelleFoto"])
    nome = f"{idArea}_{forma}.jpg"
    base.save(cartella / nome, "JPEG", quality=qualitaJpeg, optimize=True, progressive=True)
    for larghezza in regole["larghezzeDelleFoto"].get(forma, []):
        variante = rimpicciolita(immagine, larghezza / immagine.width)
        variante.save(cartella / f"{idArea}_{forma}-{larghezza}.jpg", "JPEG", quality=qualitaJpeg, optimize=True, progressive=True)
        variante.save(cartella / f"{idArea}_{forma}-{larghezza}.webp", "WEBP", quality=qualitaWebp, method=int(regole.get("metodoWebp", 4)))
    return nome

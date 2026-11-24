"""Quanta parte della foto è luce bruciata: punti quasi bianchi (250 su 255) senza più dettaglio, come un cielo o una finestra sovraesposti.

Il valore va da 0 a 1 (0,02 vuol dire il 2% dei punti). Si calcola su una copia piccola della foto e si tiene per il resto del lavoro.
"""

from PIL import Image

MEMORIA_DELLA_LUCE = {}


def luceBruciataDiUnaFoto(percorso):
    if percorso not in MEMORIA_DELLA_LUCE:
        with Image.open(percorso) as immagine:
            immagine.draft("L", (512, 512))
            piccola = immagine.convert("L")
        piccola.thumbnail((512, 512))
        istogramma = piccola.histogram()
        MEMORIA_DELLA_LUCE[percorso] = sum(istogramma[250:]) / max(1, sum(istogramma))
    return MEMORIA_DELLA_LUCE[percorso]

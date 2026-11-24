"""L'impronta di una foto: la foto ridotta a 16x16 punti grigi, ognuno acceso se più chiaro della media.

Due foto con impronte quasi uguali sono la stessa foto, anche se arrivano da fonti diverse (Google Maps, Instagram, sito)
o hanno grandezze diverse. Si calcola una volta sola per foto e si tiene per il resto del lavoro.
"""

from PIL import Image, ImageOps

MEMORIA_DELLE_IMPRONTE = {}


def improntaDiUnaFoto(percorso):
    if percorso not in MEMORIA_DELLE_IMPRONTE:
        with Image.open(percorso) as immagine:
            punti = ImageOps.exif_transpose(immagine).convert("L").resize((16, 16)).tobytes()
        media = sum(punti) / len(punti)
        MEMORIA_DELLE_IMPRONTE[percorso] = [punto > media for punto in punti]
    return MEMORIA_DELLE_IMPRONTE[percorso]

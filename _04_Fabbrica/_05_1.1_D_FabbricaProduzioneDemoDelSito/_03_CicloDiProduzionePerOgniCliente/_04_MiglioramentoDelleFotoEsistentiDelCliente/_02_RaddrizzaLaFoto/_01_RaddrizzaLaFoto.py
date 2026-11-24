"""Passo 4.2: la foto originale aperta e girata nel verso giusto secondo i dati della fotocamera.

Una foto fatta col telefono in verticale resta verticale.
"""

from PIL import Image, ImageOps


def raddrizzaLaFoto(percorso):
    with Image.open(percorso) as originale:
        return ImageOps.exif_transpose(originale).convert("RGB")

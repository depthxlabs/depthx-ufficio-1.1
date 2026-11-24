"""Manager del passo 4.5: le foto piccole ingrandite con l'intelligenza artificiale."""

from ._03_IngrandisciLeFotoPiccole import ingrandisciLeFotoPiccole


def ingrandisciLeFotoPiccoleManager(immagine, conScritte=False, idArea=""):
    return ingrandisciLeFotoPiccole(immagine, conScritte, idArea)

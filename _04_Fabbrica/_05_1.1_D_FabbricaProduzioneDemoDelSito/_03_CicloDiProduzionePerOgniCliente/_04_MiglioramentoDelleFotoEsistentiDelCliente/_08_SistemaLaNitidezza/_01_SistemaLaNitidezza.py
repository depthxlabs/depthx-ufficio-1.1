"""Passo 4.8: nitidezza leggera, che ridà definizione ai dettagli senza aloni intorno ai bordi.

Si usa nel salvataggio (passo 4.9) su ogni misura già rimpicciolita, con un raggio piccolo adatto ai punti finali.
"""

from PIL import ImageFilter


def sistemaLaNitidezza(immagine):
    return immagine.filter(ImageFilter.UnsharpMask(radius=0.8, percent=70, threshold=2))

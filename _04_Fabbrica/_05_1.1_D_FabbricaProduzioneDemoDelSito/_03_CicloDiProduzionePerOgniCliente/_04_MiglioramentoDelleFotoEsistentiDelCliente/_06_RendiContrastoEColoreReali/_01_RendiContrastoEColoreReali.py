"""Passo 4.6: contrasto e colore appena più vivi, metà della correzione automatica, per restare fedeli alla foto del cliente."""

from PIL import Image, ImageEnhance, ImageOps


def rendiContrastoEColoreReali(immagine):
    # Michele, 11/11/2026: un cielo al tramonto diventava giallo. L'autocontrasto canale per canale cambiava le tinte della foto;
    # ora si stira solo la luminosità (preserve_tone) e le tinte restano quelle vere
    corretta = ImageOps.autocontrast(immagine, cutoff=0.5, preserve_tone=True)
    return ImageEnhance.Color(Image.blend(immagine, corretta, 0.5)).enhance(1.05)

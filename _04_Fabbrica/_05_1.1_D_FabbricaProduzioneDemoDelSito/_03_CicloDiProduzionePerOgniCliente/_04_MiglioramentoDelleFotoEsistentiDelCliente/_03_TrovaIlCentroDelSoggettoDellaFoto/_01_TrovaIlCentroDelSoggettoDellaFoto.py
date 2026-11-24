"""Passo 4.3: il centro del soggetto della foto, dove si concentrano bordi e dettagli (la facciata, il letto, la piscina),
come frazioni da 0 a 1.

Il centro si avvicina a metà strada verso quello della foto: i tagli seguono il soggetto senza tagliare via i bordi importanti.
Quando il modello ha dato il riquadro del soggetto (passo 4.1, Michele 8/11/2026) il centro è quello del riquadro: i bordi
del fogliame o del selciato non spostano più il taglio.
"""

from PIL import ImageFilter


def trovaIlCentroDelSoggettoDellaFoto(immagine, soggetto=None):
    if soggetto:
        return (soggetto[0] + soggetto[2]) / 2, (soggetto[1] + soggetto[3]) / 2
    piccola = immagine.convert("L")
    piccola.thumbnail((160, 160))
    bordi = piccola.filter(ImageFilter.FIND_EDGES)
    larghezza, altezza = bordi.size
    valori = bordi.tobytes()
    totale = sommaX = sommaY = 0
    for y in range(1, altezza - 1):
        for x in range(1, larghezza - 1):
            valore = valori[y * larghezza + x]
            totale += valore
            sommaX += x * valore
            sommaY += y * valore
    if not totale:
        return 0.5, 0.45
    centroX, centroY = sommaX / totale / larghezza, sommaY / totale / altezza
    return 0.5 + (centroX - 0.5) * 0.5, 0.45 + (centroY - 0.45) * 0.5

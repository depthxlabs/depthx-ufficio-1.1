"""Passo 4.7: le zone quasi bianche si abbassano appena, così un cielo o una finestra bruciati non sono più macchie bianche piatte.

Vale solo per le foto con almeno l'1% di luce bruciata; i toni sotto 215 non cambiano.
"""

CURVA_DELLE_LUCI = [valore if valore <= 215 else round(215 + (valore - 215) * 0.8) for valore in range(256)]


def sistemaLeLuciBruciate(immagine):
    istogramma = immagine.convert("L").histogram()
    if sum(istogramma[250:]) / max(1, sum(istogramma)) < 0.01:
        return immagine
    return immagine.point(CURVA_DELLE_LUCI * 3)

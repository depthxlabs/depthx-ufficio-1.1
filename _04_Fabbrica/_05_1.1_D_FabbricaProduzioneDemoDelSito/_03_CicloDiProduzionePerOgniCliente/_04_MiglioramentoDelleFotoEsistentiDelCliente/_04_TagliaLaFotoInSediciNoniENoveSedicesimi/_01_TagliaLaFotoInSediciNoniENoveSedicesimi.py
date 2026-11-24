"""Passo 4.4: i tagli nelle forme dell'area della struttura, 16x9 per computer e riquadri larghi, 9x16 per telefono e riquadri verticali.

Ogni taglio sta intorno al centro del soggetto (passo 4.3) e sempre dentro la foto. Il taglio non ingrandisce niente.
Restituisce forma -> immagine tagliata.
"""

RAPPORTI = {"16x9": 16 / 9, "9x16": 9 / 16}


def tagliaLaFotoInSediciNoniENoveSedicesimi(immagine, centro, forme):
    larghezza, altezza = immagine.size
    tagli = {}
    for forma in forme:
        rapporto = RAPPORTI[forma]
        if larghezza / altezza > rapporto:
            nuovaLarghezza = int(altezza * rapporto)
            sinistra = min(max(0, int(centro[0] * larghezza - nuovaLarghezza / 2)), larghezza - nuovaLarghezza)
            tagli[forma] = immagine.crop((sinistra, 0, sinistra + nuovaLarghezza, altezza))
        else:
            nuovaAltezza = int(larghezza / rapporto)
            alto = min(max(0, int(centro[1] * altezza - nuovaAltezza / 2)), altezza - nuovaAltezza)
            tagli[forma] = immagine.crop((0, alto, larghezza, alto + nuovaAltezza))
    return tagli

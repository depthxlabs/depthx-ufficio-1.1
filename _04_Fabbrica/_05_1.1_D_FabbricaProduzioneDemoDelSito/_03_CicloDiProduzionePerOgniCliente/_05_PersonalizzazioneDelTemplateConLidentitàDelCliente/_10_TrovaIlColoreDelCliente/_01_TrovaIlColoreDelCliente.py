"""Passo 5.10: il colore del cliente, cioè la tinta più viva e più presente nel suo logo o, senza logo, nelle prime tre
foto delle aree della struttura (passo 4).

Restituisce la tinta (da 0 a 1, None se le immagini sono tutte grigie) e se viene dal logo.
"""

import colorsys

from PIL import Image


def trovaIlColoreDelCliente(fotoInOrdine, fotoScaricate, aree):
    logo = next((voce for voce in fotoInOrdine if voce.get("categoria") == "logo" and voce["id"] in fotoScaricate), None)
    percorsi = [fotoScaricate[logo["id"]]] if logo else [area["percorso"] for area in list(aree.values())[:3]]
    voti = {}
    for percorso in percorsi:
        with Image.open(percorso) as immagine:
            piccola = immagine.convert("RGB").resize((64, 64)).quantize(colors=8).convert("RGB")
        for quanti, (rosso, verde, blu) in piccola.getcolors(4096) or []:
            tinta, chiarezza, forza = colorsys.rgb_to_hls(rosso / 255, verde / 255, blu / 255)
            if 0.18 < chiarezza < 0.82 and forza > 0.22:
                chiave = round(tinta * 24) / 24
                voti[chiave] = voti.get(chiave, 0) + quanti * forza
    return {"tinta": max(voti, key=voti.get) if voti else None, "dalLogo": bool(logo)}

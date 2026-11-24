"""Passo 5.11: ogni colore del template in :root (assets/css/style.css) prende la tinta del cliente, mantenendo chiarezza
e forza del template.

Così armonia e leggibilità restano quelle del template; i neutri chiari ricevono appena un riflesso del cliente.
La tinta cambia però la luce che l'occhio vede: ogni colore scuro (i testi) deve avere un contrasto di almeno 5,5 a 1
con il più scuro dei colori chiari (gli sfondi, fasce comprese), altrimenti si scurisce finché ci arriva (la norma ne chiede 4,5).
Senza tinta (immagini tutte grigie) restano i colori del template. Restituisce nome del colore -> nuovo valore.
"""

import colorsys
import re
from pathlib import Path

CONTRASTO_DEI_TESTI = 5.5


def luce(colore):
    canali = [c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4 for c in colore]
    return 0.2126 * canali[0] + 0.7152 * canali[1] + 0.0722 * canali[2]


def contrasto(a, b):
    chiaro, scuro = sorted((luce(a), luce(b)), reverse=True)
    return (chiaro + 0.05) / (scuro + 0.05)


def coloraIlSitoConIlColoreDelCliente(sito, tinta):
    if tinta is None:
        return {}
    percorso = Path(sito) / "assets" / "css" / "style.css"
    stile = percorso.read_text(encoding="utf-8-sig")
    radice = re.search(r":root\s*\{([^}]*)\}", stile)
    if not radice:
        return {}
    colori = {}
    for nome, valore in re.findall(r"(--[\w-]+)\s*:\s*(#[0-9a-fA-F]{6})\b", radice.group(1)):
        rosso, verde, blu = (int(valore[i:i + 2], 16) / 255 for i in (1, 3, 5))
        _, chiarezza, forza = colorsys.rgb_to_hls(rosso, verde, blu)
        forza = min(forza + 0.04, 0.12) if forza < 0.12 else forza
        colori[nome] = [chiarezza, forza]
    rgb = lambda voce: colorsys.hls_to_rgb(tinta, voce[0], voce[1])
    if colori:
        chiari = [rgb(voce) for voce in colori.values() if luce(rgb(voce)) > 0.6]
        sfondo = min(chiari, key=luce) if chiari else rgb(max(colori.values(), key=lambda voce: luce(rgb(voce))))
        for voce in colori.values():
            if luce(rgb(voce)) < 0.18:
                while contrasto(rgb(voce), sfondo) < CONTRASTO_DEI_TESTI and voce[0] > 0.02:
                    voce[0] -= 0.02
    nuovi = {nome: "#%02x%02x%02x" % tuple(round(c * 255) for c in rgb(voce)) for nome, voce in colori.items()}
    with percorso.open("a", encoding="utf-8") as file:
        file.write("\n/* DepthX, fabbrica dei siti: i colori del cliente, con la stessa chiarezza del template. */\n:root{"
                   + ";".join(f"{k}:{v}" for k, v in nuovi.items()) + "}\n")
    return nuovi

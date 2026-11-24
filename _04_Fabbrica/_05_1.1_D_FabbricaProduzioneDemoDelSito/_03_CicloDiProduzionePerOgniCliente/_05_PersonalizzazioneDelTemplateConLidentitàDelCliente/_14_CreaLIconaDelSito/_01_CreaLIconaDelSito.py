"""Passo 5.14: l'icona del sito sulla scheda del browser, in ogni pagina.

Con un logo usabile (passo 5.12) l'icona è il logo del cliente. Senza logo è l'iniziale del nome nel colore del cliente
(assets/logo/icona.svg); l'iniziale salta le parole del tipo di struttura (Hotel Rossi -> R).
Ogni pagina punta alla nuova icona, al posto delle icone del template. Restituisce il percorso dell'icona nel sito.
"""

import colorsys
import html
import re
from pathlib import Path

PAROLE_DEL_TIPO = re.compile(r"^(hotel|albergo|ristorante|pizzeria|locanda|b&b|bnb|bed and breakfast|agriturismo|"
                             r"casa vacanze?|casa|villa|residence|affittacamere)\s+", re.I)
COLLEGAMENTO_DELL_ICONA = re.compile(r'<link\b[^>]*\brel="(?:shortcut )?icon"[^>]*>\s*')


def creaLIconaDelSito(sito, nome, tinta, logo):
    if logo:
        icona, tipo = logo, ("image/svg+xml" if logo.endswith(".svg") else "image/png")
    else:
        rosso, verde, blu = colorsys.hls_to_rgb(tinta if tinta is not None else 0.58, 0.32, 0.45)
        colore = "#%02x%02x%02x" % (round(rosso * 255), round(verde * 255), round(blu * 255))
        senzaTipo = nome.strip()
        while PAROLE_DEL_TIPO.match(senzaTipo):
            senzaTipo = PAROLE_DEL_TIPO.sub("", senzaTipo, count=1)
        iniziale = html.escape((senzaTipo or nome or "D")[:1].upper())
        cartella = Path(sito) / "assets" / "logo"
        cartella.mkdir(parents=True, exist_ok=True)
        (cartella / "icona.svg").write_text(
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64"><rect width="64" height="64" rx="14" fill="{colore}"/>'
            f'<text x="32" y="44" font-family="Georgia,serif" font-size="36" text-anchor="middle" fill="#ffffff">{iniziale}</text></svg>',
            encoding="utf-8")
        icona, tipo = "assets/logo/icona.svg", "image/svg+xml"
    for pagina in Path(sito).glob("*.html"):
        codice = pagina.read_text(encoding="utf-8-sig")
        collegamenti = list(COLLEGAMENTO_DELL_ICONA.finditer(codice))
        if not collegamenti:
            continue
        nuovo = f'<link rel="icon" href="{icona}" type="{tipo}">\n'
        codice = codice[:collegamenti[0].start()] + nuovo + COLLEGAMENTO_DELL_ICONA.sub("", codice[collegamenti[0].start():])
        pagina.write_text(codice, encoding="utf-8")
    return icona

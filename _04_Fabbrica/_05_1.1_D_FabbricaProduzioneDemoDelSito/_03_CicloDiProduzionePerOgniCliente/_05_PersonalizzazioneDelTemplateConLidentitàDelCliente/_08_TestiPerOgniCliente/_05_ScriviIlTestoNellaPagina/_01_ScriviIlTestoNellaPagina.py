"""Passo 5.8.5: le frasi scelte e completate scritte nella pagina, al posto delle frasi del template.

L'italiano va tra i tag, l'inglese in data-en. Se la frase è cambiata, l'inglese è quello scritto nella verifica (passo
5.8.4, Michele 8/11/2026); se manca anche quello, data-en si toglie.
Alla fine le graffe rimaste negli attributi (alt, title, content, link...) si completano con i fatti veri che ci sono:
solo dentro i tag, mai nel testo, perché una frase senza tutti i suoi fatti deve restare intatta e il passo 5.8.6 la toglie.
"""

import html
import re
from pathlib import Path

GRAFFA = re.compile(r"\{(\w+)\}")


def scriviIlTestoNellaPagina(sito, completate):
    pagine = {str(p): p.read_text(encoding="utf-8-sig") for p in Path(sito).glob("*.html")}
    for frase in completate["frasi"]:
        if not frase["scelta"]:
            continue
        attributi = frase["attributi"]
        # prima l'inglese di Claude: quello del template completato terrebbe i fatti in italiano
        inglese = (completate.get("inglese") or {}).get(frase["italiano"]) or frase["ingleseCompleto"]
        if inglese:
            attributi = re.sub(r'(\sdata-en=")[^"]*(")', lambda m: m.group(1) + inglese + m.group(2), attributi)
        else:
            attributi = re.sub(r'\sdata-en="[^"]*"', "", attributi)
        spazi = re.match(r"\s*", frase["testo"]).group(0), re.search(r"\s*$", frase["testo"]).group(0)
        nuovo = f"<{frase['tag']}{attributi}>{spazi[0]}{frase['italiano']}{spazi[1]}"
        pagine[frase["pagina"]] = pagine[frase["pagina"]].replace(frase["originale"], nuovo, 1)
    fatti = completate["fatti"]
    for percorso, codice in pagine.items():
        riempi = lambda testo: GRAFFA.sub(lambda m: html.escape(fatti[m.group(1)], quote=True) if m.group(1) in fatti
                                          else m.group(0), testo)
        codice = re.sub(r"<[a-zA-Z][^>]*>", lambda m: riempi(m.group(0)), codice)
        Path(percorso).write_text(codice, encoding="utf-8")
    return len([frase for frase in completate["frasi"] if frase["scelta"]])

"""Passo 7.14: nella demo c'è tutto quello che ha il pacchetto Advanced (Michele, 11/11/2026, task #579); se manca qualcosa, NOTGO.

La lista è quella della pagina Prodotti del sito, scritta nel contratto del template (listaAdvanced):
sito multipagina fino a 5 sezioni, italiano e inglese, 3 animazioni di transizione, 1 elemento 3D di codice, 6 recensioni
Google nel sito, pulsante WhatsApp e chiamata animati, pulsante Prenota con la finestra delle date, mappa e indicazione della
sede animata, preparazione completa per Google, galleria di foto statica.
Il controllo guarda il codice che riceve il visitatore, senza i commenti. Restituisce l'elenco delle voci mancanti.
"""

import re
from pathlib import Path

from .._01_ControlloCheNessunaParolaDelTemplateSiaRimasta._04_ValoriDelFileDiConfigurazione import \
    valoriDelFileDiConfigurazione

RECENSIONI_DELL_ADVANCED = 6
SEZIONI_MASSIME = 5


def senzaCommenti(codice):
    return re.sub(r"<!--.*?-->|/\*.*?\*/", "", codice, flags=re.S)


def vociMancantiDellaListaAdvanced(sito):
    radice = Path(sito)
    pagine = {p.name: senzaCommenti(p.read_text(encoding="utf-8-sig", errors="ignore")) for p in sorted(radice.glob("*.html"))}
    stile = senzaCommenti((radice / "assets" / "css" / "style.css").read_text(encoding="utf-8-sig", errors="ignore")) \
        if (radice / "assets" / "css" / "style.css").is_file() else ""
    script = {n: senzaCommenti((radice / "assets" / "js" / n).read_text(encoding="utf-8-sig", errors="ignore"))
              for n in ("main.js", "pacchetto.js", "foto.js") if (radice / "assets" / "js" / n).is_file()}
    mancano = []
    if "index.html" not in pagine:
        return ["manca la home index.html"]

    # 1. sito multipagina fino a 5 sezioni: le voci del menu portano a pagine che esistono, al massimo 5
    voci = sorted(set(re.findall(r'data-voce-pagina="([\w.-]+)"', pagine["index.html"])))
    if len(pagine) < 2:
        mancano.append("il sito non è multipagina")
    if len(voci) > SEZIONI_MASSIME:
        mancano.append(f"il menu ha {len(voci)} sezioni, l'Advanced ne ha al massimo {SEZIONI_MASSIME}")
    for nome, codice in pagine.items():
        for voce in set(re.findall(r'data-voce-pagina="([\w.-]+)"', codice)):
            if voce not in pagine:
                mancano.append(f"{nome}: il menu porta alla pagina {voce}, che non c'è")
    if "dove-siamo.html" not in pagine:
        mancano.append("manca la pagina Dove siamo e contatti")

    # 2. italiano e inglese
    lingue = valoriDelFileDiConfigurazione(sito, "lingue")
    if "it" not in lingue or "en" not in lingue:
        mancano.append("il sito non è in italiano e in inglese")
    for nome, codice in pagine.items():
        if 'data-lingua="en"' not in codice or "data-en=" not in codice:
            mancano.append(f"{nome}: manca l'inglese")

    # 3. tre animazioni di transizione: comparsa dei blocchi, velo tra le pagine, tendina del titolo
    if not ("[data-rivela]" in stile and "pk-velo" in stile and "pk-tendina" in stile and "pk-velo" in script.get("pacchetto.js", "")):
        mancano.append("mancano le 3 animazioni di transizione")
    for nome, codice in pagine.items():
        if "assets/js/pacchetto.js" not in codice:
            mancano.append(f"{nome}: manca lo script del pacchetto Advanced")

    # 4. un elemento 3D di codice
    if not any("data-3d" in codice for codice in pagine.values()) or "[data-3d]" not in script.get("pacchetto.js", ""):
        mancano.append("manca l'elemento 3D")

    # 5. sei recensioni Google nel sito, con il link a Google
    testi = set()
    for codice in pagine.values():
        for figura in re.findall(r"<figure\b[^>]*data-recensione[^>]*>(.*?)</figure\s*>", codice, re.S):
            testo = re.sub(r"<[^>]+>", " ", re.search(r"<blockquote\b.*?</blockquote\s*>", figura, re.S).group(0)) \
                if "<blockquote" in figura else ""
            if testo.strip() and "{" not in testo:
                testi.add(" ".join(testo.split()))
    if len(testi) < RECENSIONI_DELL_ADVANCED:
        mancano.append(f"nel sito ci sono {len(testi)} recensioni, l'Advanced ne ha {RECENSIONI_DELL_ADVANCED}")
    if not any('data-link="recensioni"' in codice for codice in pagine.values()):
        mancano.append("manca il link alle recensioni Google")

    # 6. pulsanti WhatsApp e chiamata, animati, in ogni pagina (WhatsApp solo se il cliente lo usa)
    whatsapp = [v for v in valoriDelFileDiConfigurazione(sito, "contatti.whatsapp") if v]
    telefono = [v for v in valoriDelFileDiConfigurazione(sito, "contatti.telefono") if v]
    for nome, codice in pagine.items():
        if telefono and not re.search(r'class="pk-tasto pk-tasto--tel"[^>]*data-link="tel"', codice):
            mancano.append(f"{nome}: manca il pulsante animato della chiamata")
        if whatsapp and not re.search(r'class="pk-tasto pk-tasto--wa"[^>]*data-link="whatsapp"', codice):
            mancano.append(f"{nome}: manca il pulsante animato di WhatsApp")
    if not telefono:
        mancano.append("manca il telefono del cliente per il pulsante della chiamata")
    if "pk-onda" not in stile:
        mancano.append("i pulsanti WhatsApp e chiamata non sono animati")

    # 7. pulsante Prenota con la finestra delle date, in ogni pagina
    for nome, codice in pagine.items():
        if "data-apri-prenota" not in codice or not re.search(r'<dialog\b[^>]*id="finestra-prenota".*?type="date".*?</dialog', codice, re.S):
            mancano.append(f"{nome}: manca il pulsante Prenota con la finestra delle date")
    if "pk-riflesso" not in stile:
        mancano.append("il pulsante Prenota non è animato")

    # 8. mappa e indicazione della sede, animata
    dove = pagine.get("dove-siamo.html", "")
    luogo = [v for v in valoriDelFileDiConfigurazione(sito, "contatti.comune") + valoriDelFileDiConfigurazione(sito, "contatti.latitudine") if v]
    if 'class="mappa"' not in dove or "mappa__spillo" not in dove:
        mancano.append("manca la mappa della sede")
    if not luogo:
        mancano.append("manca il luogo del cliente per la mappa")
    if "pk-spillo" not in stile:
        mancano.append("la mappa non è animata")

    # 9. preparazione completa per Google: titolo, descrizione, lingua della pagina, dati strutturati
    for nome, codice in pagine.items():
        if not re.search(r"<title\b[^>]*>[^<{}]+</title", codice):
            mancano.append(f"{nome}: manca il titolo per Google")
        if not re.search(r'<meta name="description" content="[^"{}]+"', codice):
            mancano.append(f"{nome}: manca la descrizione per Google")
        if not re.search(r'<html\b[^>]*\blang="it"', codice):
            mancano.append(f"{nome}: manca la lingua della pagina")
    if "application/ld+json" not in script.get("main.js", ""):
        mancano.append("mancano i dati strutturati per Google")

    # 10. galleria di foto statica: la pagina Galleria, oppure la galleria nella Home quando c'è una pagina interna
    if "galleria.html" not in pagine and 'class="galleria"' not in pagine["index.html"]:
        mancano.append("manca la galleria di foto")
    return mancano

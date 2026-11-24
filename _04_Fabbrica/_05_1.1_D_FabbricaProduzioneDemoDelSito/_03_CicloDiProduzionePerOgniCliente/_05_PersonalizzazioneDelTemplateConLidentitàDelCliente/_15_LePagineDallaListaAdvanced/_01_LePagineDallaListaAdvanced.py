"""Passo 5.15: le pagine dalla lista Advanced (Michele, 11/11/2026, task #576).

Nascono solo le pagine del pacchetto Advanced, mai a sentimento. Le pagine standard sono Home, Camere, Galleria, Recensioni,
Dove siamo e contatti. Una pagina a sé c'è solo per un servizio dentro la struttura (ristorante, centro benessere, piscina) e
solo se la sua scena ha la foto del cliente; in quel caso Galleria e Recensioni entrano nella Home (i blocchi della Home con
data-solo-con-pagine-interne) e le loro pagine non nascono. Tutto il resto sta nella Home. Al massimo 5 sezioni nel menu.

Due momenti:
1. scegliLePagine, subito dopo le aree del passo 5.7 e prima dei testi: le pagine interne con la foto, Galleria e Recensioni
   nella Home o nelle loro pagine, la Galleria solo con almeno minimoDiFotoDellaGalleria foto.
2. togliLePagineVuote, alla fine del passo 5: una pagina rimasta senza foto del cliente e senza testi non nasce
   (Michele: una pagina senza materiale non nasce). Home e Dove siamo e contatti restano sempre.
Ogni pagina che non nasce esce con le sue voci di menu, le sue schede nella Home e i link che portano a lei.
"""

import json
import re
from pathlib import Path


def chiusuraDellElemento(codice, inizio, tag):
    """La posizione dopo la chiusura dell'elemento <tag> che si apre in inizio, contando gli elementi uguali dentro."""
    apertura, chiusura = re.compile(r"<" + tag + r"\b", re.I), re.compile(r"</" + tag + r"\s*>", re.I)
    profondita, posizione = 0, inizio
    while True:
        a, c = apertura.search(codice, posizione), chiusura.search(codice, posizione)
        if not c:
            return len(codice)
        if a and a.start() < c.start():
            profondita, posizione = profondita + 1, a.end()
        else:
            profondita, posizione = profondita - 1, c.end()
            if profondita == 0:
                return c.end()


def togliGliElementi(codice, attributo):
    """Toglie ogni elemento che ha l'attributo dato (per esempio data-pagina="spa.html"), intero."""
    while True:
        trovato = re.search(r"<(\w+)\b[^>]*\s" + re.escape(attributo) + r"[\s>/]", codice)
        if not trovato:
            return codice
        codice = codice[:trovato.start()] + codice[chiusuraDellElemento(codice, trovato.start(), trovato.group(1)):]


def togliLaPagina(sito, file):
    """La pagina non nasce: esce il file, e da tutte le altre pagine le voci di menu, le schede e i link verso di lei."""
    (Path(sito) / file).unlink(missing_ok=True)
    for pagina in Path(sito).glob("*.html"):
        codice = pagina.read_text(encoding="utf-8-sig")
        nuovo = togliGliElementi(codice, f'data-voce-pagina="{file}"')
        nuovo = togliGliElementi(nuovo, f'data-pagina="{file}"')
        nuovo = re.sub(r'<a\b[^>]*href="' + re.escape(file) + r'(?:#[^"]*)?"[^>]*>.*?</a\s*>', "", nuovo, flags=re.S)
        if nuovo != codice:
            pagina.write_text(nuovo, encoding="utf-8")


def regoleDellePagine(contratto):
    pagine = json.loads(Path(contratto).read_text(encoding="utf-8-sig")).get("pagine")
    return pagine if isinstance(pagine, dict) else None


FORME_DEL_3D = ["chiave", "dado", "biglietto", "cartolina"]


def scegliLaFormaDel3D(sito, aree):
    """Michele, 11/11/2026: le forme dell'elemento 3D si alternano da un cliente all'altro (chiave della camera, dado, biglietto
    da visita, cartolina). La forma dipende dal codice del cliente, così resta la stessa a ogni giro; la cartolina solo con la sua
    foto. Le altre forme escono dalla pagina."""
    import zlib
    idCliente = Path(sito).parent.name
    forme = [f for f in FORME_DEL_3D if f != "cartolina" or aree.get("cartolina")]
    scelta = forme[zlib.crc32(idCliente.encode("utf-8")) % len(forme)]
    for pagina in Path(sito).glob("*.html"):
        codice = pagina.read_text(encoding="utf-8-sig")
        nuovo = codice
        for forma in FORME_DEL_3D:
            if forma != scelta:
                nuovo = togliGliElementi(nuovo, f'data-oggetto="{forma}"')
        if nuovo != codice:
            pagina.write_text(nuovo, encoding="utf-8")
    return scelta


def scegliLePagine(sito, contratto, aree):
    forma3D = scegliLaFormaDel3D(sito, aree)
    regole = regoleDellePagine(contratto)
    if not regole:
        return {"pagine": sorted(p.name for p in Path(sito).glob("*.html")), "tolte": []}
    tolte = []
    interne = [voce for voce in regole["interne"] if aree.get(voce["scena"])][:int(regole["massimoDiPagineInterne"])]
    for voce in regole["interne"]:
        if voce not in interne:
            tolte.append(voce["file"])
    if interne:
        tolte += regole["sostituibiliDallePagineInterne"]
    else:
        for pagina in Path(sito).glob("*.html"):
            codice = pagina.read_text(encoding="utf-8-sig")
            nuovo = togliGliElementi(codice, "data-solo-con-pagine-interne")
            if nuovo != codice:
                pagina.write_text(nuovo, encoding="utf-8")
        fotoDellaGalleria = sum(1 for scena, conFoto in aree.items() if conFoto and scena.startswith("galleria"))
        if fotoDellaGalleria < int(regole["minimoDiFotoDellaGalleria"]):
            tolte.append("galleria.html")
    for file in tolte:
        togliLaPagina(sito, file)
    return {"pagine": sorted(p.name for p in Path(sito).glob("*.html")), "tolte": tolte,
            "interne": [voce["file"] for voce in interne], "forma3D": forma3D}


SEZIONE = re.compile(r"<section\b([^>]*)>(.*?)</section\s*>", re.S | re.I)
TESTO = re.compile(r"<(p|h3|li|blockquote|dt|dd)\b[^>]*>(?:(?!</\1).)*?[^\s<](?:(?!</\1).)*?</\1\s*>", re.S | re.I)


def haMateriale(sezione, aree):
    if any(aree.get(scena) for scena in re.findall(r'data-scena="([\w-]+)"', sezione)):
        return True
    senzaLink = re.sub(r"<(a|button)\b.*?</\1\s*>", "", sezione, flags=re.S | re.I)
    return bool(TESTO.search(senzaLink))


def togliLePagineVuote(sito, contratto, aree):
    regole = regoleDellePagine(contratto)
    if not regole:
        return []
    tolte = []
    for pagina in sorted(Path(sito).glob("*.html")):
        if pagina.name in regole["sempre"]:
            continue
        principale = re.search(r"<main\b.*?</main\s*>", pagina.read_text(encoding="utf-8-sig"), re.S | re.I)
        sezioni = [s.group(0) for s in SEZIONE.finditer(principale.group(0) if principale else "")
                   if "testa-pagina" not in s.group(1) and 'id="prenota"' not in s.group(1)]
        if not any(haMateriale(sezione, aree) for sezione in sezioni):
            tolte.append(pagina.name)
    for file in tolte:
        togliLaPagina(sito, file)
    return tolte


PARAGRAFO = re.compile(r"<p\b(?![^>]*class=\"(?:pk-info|centro|recensioni__link)[^\"]*\")[^>]*>\s*[^<\s]", re.I)


def primaSezioneRicca(sito):
    """Michele, 11/11/2026 (regola del product manager: la prima sezione dopo l'apertura non è spoglia): tra le sezioni della
    Home che il product manager misura (con un titolo, senza recensioni, moduli o mappe) la prima deve avere almeno 2 frasi.
    Se non le ha, al suo posto sale la più ricca che ne ha almeno 2; se nessuna ne ha 2, la sezione povera scende in fondo,
    prima dell'invito finale. Restituisce l'id della sezione spostata, oppure ""."""
    pagina = Path(sito) / "index.html"
    codice = pagina.read_text(encoding="utf-8-sig")
    principale = re.search(r"<main\b[^>]*>(.*?)</main\s*>", codice, re.S | re.I)
    if not principale:
        return ""
    dentro = principale.group(1)
    misurate = [m for m in SEZIONE.finditer(dentro)
                if re.search(r"<h[12]\b", m.group(0), re.I) and not re.search(r"<(?:blockquote|form|iframe|h1)\b", m.group(0), re.I)
                and 'id="prenota"' not in m.group(1)]
    frasi = lambda m: len(PARAGRAFO.findall(m.group(0)))
    if not misurate or frasi(misurate[0]) >= 2:
        return ""
    prima = misurate[0]
    ricca = max(misurate[1:], key=frasi, default=None)
    identita = lambda m: (re.search(r'id="([^"]+)"', m.group(1)) or re.search(r"()", "")).group(1)
    if ricca is not None and frasi(ricca) >= 2:
        nuovo = dentro.replace(ricca.group(0), "", 1).replace(prima.group(0), ricca.group(0) + prima.group(0), 1)
        spostata = identita(ricca)
    else:
        invito = re.search(r'<section\b[^>]*id="prenota"', dentro)
        if not invito:
            return ""
        senza = dentro.replace(prima.group(0), "", 1)
        invito = re.search(r'<section\b[^>]*id="prenota"', senza)
        nuovo = senza[:invito.start()] + prima.group(0) + senza[invito.start():]
        spostata = identita(prima) + " (in fondo)"
    pagina.write_text(codice.replace(dentro, nuovo, 1), encoding="utf-8")
    return spostata

"""Passo 5.8.6: una frase non verificata si sostituisce; solo se non c'è una sostituta esce dalla pagina.

Sostituzioni (Michele, 9/11/2026): una frase senza una candidata verificata non si toglie, si sostituisce nel suo stesso
elemento (stesso tag e attributi, data-en con l'inglese della verifica o tolto), subito dopo il passo 5.8.5 e prima del
5.8.7, in quest'ordine:
1. un'altra frase approvata della stessa sezione e dello stesso gruppo, completa con i fatti veri e verificata (5.8.4);
2. una frase del sito attuale del cliente per la stessa sezione, parola per parola (solo per i testi, non titoli e voci);
3. una frase approvata della stessa sezione e dello stesso gruppo senza graffe e con [prova: dati]: non ha fatti.
Mai una frase già nella pagina, che dice le stesse cose di un'altra (giaDetta), che comincia con le stesse tre parole di
un'altra frase della sezione o che ripete il telefono o l'email della sezione. Mai testo nuovo, mai fatti inventati.
Ogni sostituzione va nel risultato (registro della fabbrica) e in frasiVerificate.json per il collaudo 7.7.
Se non c'è nessuna sostituta, la frase esce come prima.

Mai una frase generica o con le graffe al posto di un fatto che manca:
- un testo con graffe rimaste esce con il suo elemento (o solo il testo, se l'elemento continua dopo, come dopo un <br>);
- un collegamento con graffe rimaste (per esempio https://wa.me/{whatsapp} senza WhatsApp) esce con il suo pulsante;
- un meta con graffe rimaste (per esempio la descrizione per Google) esce;
- un attributo con graffe rimaste (data-en, alt, title...) si toglie;
- senza WhatsApp del cliente, anche le frasi che parlano di WhatsApp escono con il loro elemento.
- una sezione rimasta senza testo (nessun paragrafo, voce, recensione o recapito, solo titoli e pulsanti) esce intera,
  con i link del menu che portano a lei; restano sempre l'apertura (con il titolo h1), le sezioni con un modulo e quelle con le
  foto del cliente (Michele, 8/11/2026).
Restano solo i segnaposto che si completano dopo: le recensioni (passo 5.9) e il modulo WhatsApp ({arrivo}...).
Restituisce le frasi tolte, con la loro sezione.
"""

import html
import re
from pathlib import Path

RESTANO = {"recensioneInEvidenza", "testoDellaRecensione", "recensione2", "recensione3",
          "testoRecensione1", "testoRecensione2", "testoRecensione3", "testoRecensione4", "testoRecensione5", "testoRecensione6", "arrivo", "partenza", "ospiti"} | {f"stelleRecensione{n}" for n in range(1, 7)}
GRAFFA = re.compile(r"\{(\w+)\}")
rimaste = lambda testo: any(nome not in RESTANO for nome in GRAFFA.findall(testo))


def elementoOriginale(frase):
    """L'elemento della frase come era nel template; le graffe valgono qualunque fatto, perché il passo 5.8.5 completa
    già gli attributi (per esempio data-en) con i fatti che ci sono."""
    return re.compile(re.sub(r"\\\{\w+\\\}", lambda m: r'[^"<>]*', re.escape(frase["originale"])))


# siti atomici (Michele, 9/11/2026): il titolo dell'apertura e il nome nella testata non escono mai. Se la loro frase non è
# confermata, al suo posto va il nome della struttura, che è sempre vero (Golden Dreams B&B era rimasto senza titolo e senza nome).
SEMPRE_PRESENTI = re.compile(r'class="[^"]*\b(logotipo|marchio|testata__marchio|testata__logo|marchio__nome)\b|\bdata-(marchio|nome-breve)\b', re.I)


def sempreObbligatoria(frase):
    return frase["tag"].lower() == "h1" or bool(SEMPRE_PRESENTI.search(frase.get("attributi") or ""))


SEZIONE_DELLA_PAGINA = re.compile(r"<section\b[^>]*>.*?</section\s*>", re.S | re.I)
GRUPPO_DEI_TESTI = "Testi"


def sostituisciLeFrasiNonVerificate(sito, completate):
    """Michele, 9/11/2026: ogni frase senza scelta prende al suo posto, nello stesso elemento, una frase verificata della
    sua sezione, poi una del sito del cliente, poi una approvata senza fatti. Restituisce le sostituzioni fatte."""
    from .._04_CompletaLaFraseConIFattiVeriDelCliente._02_CompletaLaFraseConIFattiVeriDelCliente import regoleDelleCandidate
    from .._07_DueOTreFrasiPerOgniSezione._01_DueOTreFrasiPerOgniSezione import TESTO_NELLA_PAGINA, giaDetta, inizio
    fatti, provati, verificate = completate["fatti"], completate["provati"], completate["verificate"]
    _, verificabili = regoleDelleCandidate(fatti, provati, verificate)
    _, senzaVerifica = regoleDelleCandidate(fatti, provati, None)
    dalSito, inglese = completate.get("dalSito") or {}, completate.get("inglese") or {}
    contatti = [html.escape(str(fatti[k]), quote=True) for k in ("telefono", "email") if fatti.get(k)]
    riempi = lambda testo: GRAFFA.sub(lambda m: html.escape(str(fatti[m.group(1)]), quote=True) if m.group(1) in fatti
                                      else m.group(0), testo)
    pagine, sostituzioni = {}, []
    for frase in completate["frasi"]:
        if frase["scelta"] or not frase.get("sezione"):
            continue
        percorso = frase["pagina"]
        if percorso not in pagine:
            pagine[percorso] = Path(percorso).read_text(encoding="utf-8-sig")
        codice = pagine[percorso]
        trovato = elementoOriginale(frase).search(codice)
        if not trovato:
            continue
        senza = codice[:trovato.start()] + codice[trovato.end():]  # la pagina senza la frase da sostituire
        sezione = next((s.group(0) for s in SEZIONE_DELLA_PAGINA.finditer(codice)
                        if s.start() <= trovato.start() < s.end()), "").replace(trovato.group(0), "", 1)
        inizi = {inizio(t) for _, t in TESTO_NELLA_PAGINA.findall(sezione) if t.strip()}
        modello, prove = frase["candidate"][0], frase.get("prove", {})
        possibili = [(c, t, "verificata") for c, t in verificabili(frase) if c != modello]
        if frase.get("gruppo") == GRUPPO_DEI_TESTI:
            possibili += [(t, t, "sito") for t in dalSito.get(frase["sezione"], [])]
        possibili += [(c, t, "senza fatti") for c, t in senzaVerifica(frase)
                      if c != modello and not GRAFFA.search(c) and prove.get(c) == []]
        buona = lambda t: (t.strip() and t not in senza and inizio(t) not in inizi and not giaDetta(t, senza, [])
                           and not any(c in t and c in sezione for c in contatti)
                           and (fatti.get("whatsapp") or "whatsapp" not in t.lower()))
        scelta = next(((c, t, fonte) for c, t, fonte in possibili if buona(t)), None)
        if not scelta:
            continue
        candidata, testo, fonte = scelta
        attributi = frase["attributi"]
        if inglese.get(testo):
            attributi = re.sub(r'(\sdata-en=")[^"]*(")', lambda m: m.group(1) + inglese[testo] + m.group(2), attributi)
        else:
            attributi = re.sub(r'\sdata-en="[^"]*"', "", attributi)
        spazi = re.match(r"\s*", frase["testo"]).group(0), re.search(r"\s*$", frase["testo"]).group(0)
        nuovo = f"<{frase['tag']}{riempi(attributi)}>{spazi[0]}{testo}{spazi[1]}"
        pagine[percorso] = codice[:trovato.start()] + nuovo + codice[trovato.end():]
        frase["scelta"], frase["italiano"], frase["ingleseCompleto"] = candidata, testo, None
        if fonte == "verificata":
            frase["prova"] = {chiave: provati[chiave] for chiave in (prove.get(candidata) or [])}
            if testo in verificate:
                frase["prova"]["fraseVerificata"] = verificate[testo]
        else:
            frase["prova"] = {"fonte": "sito del cliente" if fonte == "sito" else "frase approvata senza fatti"}
        voce = {"fraseOriginale": frase["testo"].strip(), "sostituta": testo, "fonte": fonte,
                "sezione": frase["sezione"], "pagina": Path(percorso).name}
        frase["sostituzione"] = voce
        sostituzioni.append(voce)
    for percorso, codice in pagine.items():
        Path(percorso).write_text(codice, encoding="utf-8")
    return sostituzioni


def togliLeSezioniSenzaUnaFraseCompleta(sito, frasi, fatti, sceneConFoto=()):
    tolte = []
    nome = html.escape(str(fatti.get("nomestruttura") or fatti.get("nomeBreve") or ""), quote=False)
    for frase in frasi:
        if frase["scelta"]:
            continue
        pagina = Path(frase["pagina"])
        codice = pagina.read_text(encoding="utf-8-sig")
        originale = elementoOriginale(frase)
        if nome and sempreObbligatoria(frase):
            conChiusura = originale.pattern + r"</" + re.escape(frase["tag"]) + r"\s*>"
            attributi = re.sub(r'\s(?:data-en|data-t)="[^"]*"', "", frase["attributi"])
            nuovo = re.sub(conChiusura, lambda m: f"<{frase['tag']}{attributi}>{nome}</{frase['tag']}>", codice, count=1)
            if nuovo != codice:
                pagina.write_text(nuovo, encoding="utf-8")
                tolte.append({"frase": frase["testo"].strip(), "sezione": frase["sezione"], "alPostoIlNome": True})
                continue
        originale = elementoOriginale(frase)
        conChiusura = originale.pattern + r"</" + re.escape(frase["tag"]) + r"\s*>"
        if re.search(conChiusura, codice):
            nuovo = re.sub(conChiusura, "", codice, count=1)
        else:
            nuovo = originale.sub(lambda m: f"<{frase['tag']}{frase['attributi']}>", codice, count=1)
        if nuovo != codice:
            pagina.write_text(nuovo, encoding="utf-8")
            tolte.append({"frase": frase["testo"].strip(), "sezione": frase["sezione"]})
    for pagina in Path(sito).glob("*.html"):
        codice = pagina.read_text(encoding="utf-8-sig")
        nuovo = re.sub(r"<a\b[^>]*\bhref=\"[^\"]*\{\w+\}[^\"]*\"[^>]*>.*?</a\s*>",
                       lambda m: "" if rimaste(m.group(0).split(">")[0]) else m.group(0), codice, flags=re.S)
        nuovo = re.sub(r"<meta\b[^>]*>", lambda m: "" if rimaste(m.group(0)) else m.group(0), nuovo)
        nuovo = re.sub(r"\s(?!data-messaggio)[\w-]+=\"[^\"]*\{\w+\}[^\"]*\"",
                       lambda m: "" if rimaste(m.group(0)) else m.group(0), nuovo)
        if not fatti.get("whatsapp"):
            nuovo = re.sub(r"<(p|span|li|small|h[1-6])\b[^>]*>[^<]*WhatsApp[^<]*</\1\s*>", "", nuovo)
        if nuovo != codice:
            pagina.write_text(nuovo, encoding="utf-8")
    for pagina in Path(sito).glob("*.html"):
        codice = pagina.read_text(encoding="utf-8-sig")
        nuovo = codice
        for sezione in re.finditer(r"<section\b([^>]*)>(.*?)</section\s*>", codice, flags=re.S | re.I):
            dentro = re.sub(r"<(a|button)\b.*?</\1\s*>", "", sezione.group(2), flags=re.S | re.I)
            conTesto = re.search(r"<(p|li|blockquote|figcaption|address|dd)\b[^>]*>\s*[^<\s]", dentro, re.I)
            fotoDelCliente = any(scena in sceneConFoto for scena in re.findall(r'data-scena="([^"]+)"', sezione.group(0)))
            # la sezione dell'elemento 3D resta sempre: le sue informazioni cominciano con un'icona (Michele, 11/11/2026)
            if conTesto or fotoDelCliente or "data-3d" in sezione.group(0) or "data-sempre" in sezione.group(1) or re.search(r"<(h1|form|input|iframe)\b", sezione.group(0), re.I):
                continue
            nuovo = nuovo.replace(sezione.group(0), "", 1)
            identita = re.search(r'\bid="([^"]+)"', sezione.group(1))
            if identita:
                nuovo = re.sub(r"<li\b[^>]*>\s*<a\b[^>]*href=\"#" + re.escape(identita.group(1)) + r"\"[^>]*>.*?</a\s*>\s*</li\s*>", "",
                               nuovo, flags=re.S)
                nuovo = re.sub(r"<a\b[^>]*href=\"#" + re.escape(identita.group(1)) + r"\"[^>]*>.*?</a\s*>", "", nuovo, flags=re.S)
            tolte.append({"frase": "(sezione senza testo)", "sezione": identita.group(1) if identita else ""})
        # una voce rimasta con la sola icona (il suo testo non era provato) esce intera (Michele, 9/11/2026)
        nuovo = re.sub(r"<li\b[^>]*>(?:(?!</?li\b).)*?</li\s*>",
                       lambda m: "" if "<svg" in m.group(0) and not re.search(r"<a\b|<button\b", m.group(0)) and not re.sub(r"<svg\b.*?</svg\s*>|<[^>]+>", "", m.group(0), flags=re.S).strip()
                       else m.group(0), nuovo, flags=re.S | re.I)
        # un pulsante o un collegamento rimasto con la sola icona (la busta senza email, il calendario senza testo) esce intero:
        # mai un'icona da sola (Michele, 9/11/2026, demo Hotel fermate per il punto 10)
        nuovo = re.sub(r"<(a|button)\b[^>]*>(?:(?!</?\1\b).)*?</\1\s*>",
                       lambda m: "" if "<svg" in m.group(0)
                       and not re.search(r"chiud|close|menu|apri|freccia|prec|succ|prev|next|scorri|lingu", m.group(0).split(">")[0], re.I)
                       and not re.sub(r"<svg\b.*?</svg\s*>|<[^>]+>", "", m.group(0), flags=re.S).strip()
                       else m.group(0), nuovo, flags=re.S | re.I)
        nuovo = togliITitoliSoli(nuovo, tolte)
        if nuovo != codice:
            pagina.write_text(nuovo, encoding="utf-8")
    return tolte


TITOLO = re.compile(r"<(h2|h3)\b[^>]*>(.*?)</\1\s*>", re.S | re.I)
CONTENUTO = re.compile(r"<(p|li|blockquote|figcaption|address|dd|label|button|a)\b[^>]*>\s*(?:<[^>]+>\s*)*[^<\s]|<(form|input|iframe|dialog)\b", re.I)


def togliITitoliSoli(codice, tolte):
    """Mai un titolo da solo, senza niente sotto (per esempio "Spazio per tutti." sotto le foto): il titolo esce
    (Michele, 9/11/2026). Conta come contenuto tutto quello che c'è dopo il titolo fino al titolo seguente o alla fine
    della sezione: un testo, una voce, una recensione, un modulo, un pulsante o un collegamento."""
    for titolo in reversed(list(TITOLO.finditer(codice))):
        if not re.sub(r"<[^>]+>", "", titolo.group(2)).strip():
            continue
        dopo = codice[titolo.end():]
        fine = re.search(r"<(h2|h3)\b|</section\s*>|</dialog\s*>|</main\s*>|<footer\b", dopo, re.I)
        tratto = dopo[:fine.start()] if fine else dopo
        if not CONTENUTO.search(tratto):
            codice = codice[:titolo.start()] + codice[titolo.end():]
            tolte.append({"frase": re.sub(r"<[^>]+>", "", titolo.group(2)).strip(), "sezione": "(titolo senza testo)"})
    return codice

"""Passo 5.8.4: per ogni frase della pagina, la prima candidata completa con i fatti veri del cliente e verificata.

Una candidata va bene solo se ha tutti i fatti delle sue graffe, se ogni fatto della sua prova ([prova: ...] nel
copywriting) è provato dal materiale del cliente (_07_FattiProvatiDalMaterialeDelCliente.py) e se la frase completa, di
almeno quattro parole, è verificata dal materiale (_08_VerificaDelleFrasiComplete.py): le frasi del copy si usano solo
quando sono verificate (Michele, 8/11/2026). Se una candidata non va bene, si prende la successiva della stessa sezione;
se nessuna va bene, la frase resta senza scelta e il passo 5.8.6 la sostituisce (con una verificata, del sito o senza fatti) o, se non c'è una sostituta, la toglie (Michele, 9/11/2026). Una frase di riserva con le parole di un altro
tipo di struttura (_04_ParoleDiOgniTipoDiStruttura.json) non si usa, e nemmeno una frase di riserva senza graffe e senza
prova. I fatti si scrivono pronti per la pagina (& < > " protetti).
Una frase approvata già usata nella stessa pagina non si ripete: si prende la candidata successiva. Fanno eccezione i
pulsanti e le etichette del template senza graffe: restano come sono anche se ripetuti.
L'inglese (data-en) si completa solo se resta la frase del template e tutti i suoi fatti ci sono.
"""

import html
import json
import re
from pathlib import Path

GRAFFA = re.compile(r"\{(\w+)\}")
FILE_DELLE_PAROLE_DEI_TIPI = Path(__file__).absolute().parent / "_04_ParoleDiOgniTipoDiStruttura.json"
PAROLE_DI_UNA_FRASE = 4
paroleDi = lambda testo: len(re.findall(r"[a-zà-ÿ']+", html.unescape(testo).lower()))


SEZIONE_DELL_APERTURA = "_01_TitoloInApertura"
SCRIVETECI = re.compile(r"\bscriv", re.I)
ATTIVITA = re.compile(r"\b(albergo|hotel|b&b|b&amp;b|bed and breakfast|agriturismo|casa|appartament|residence|locanda)", re.I)


PAROLE_VUOTE = {"per", "con", "che", "del", "della", "dei", "delle", "nel", "nella", "una", "uno", "gli", "le", "il", "lo",
                "la", "di", "da", "in", "su", "al", "alla", "ai", "a", "e", "o", "ci", "vi", "noi", "voi", "siamo", "è"}
paroleDiContenuto = lambda testo: {p for p in re.findall(r"[a-zà-ÿ0-9]+", html.unescape(testo).lower()) if p not in PAROLE_VUOTE}


def doppiaNellaSezione(testo, giaScelte, contatti):
    """Nella stessa sezione mai due frasi con lo stesso telefono o la stessa email, né due frasi che dicono le stesse cose:
    "Per un tavolo, chiamateci" e "Per un tavolo o per sapere cosa c'è nel menù, chiamateci" (Michele, 9/11/2026)."""
    mie = paroleDiContenuto(testo)
    for altra in giaScelte:
        if any(c in testo and c in altra for c in contatti):
            return True
        sue = paroleDiContenuto(altra)
        if len(mie) >= 2 and len(sue) >= 2 and len(mie & sue) / min(len(mie), len(sue)) >= 0.8:
            return True
    return False


def parolaRipetuta(testo):
    """Una frase completata con i fatti che ripete una parola (di almeno 4 lettere) non entra: "Hotel Treviglio, a
    Treviglio" (Michele, 8/11/2026)."""
    parole = re.findall(r"[a-zà-ÿ]{4,}", html.unescape(testo).lower())
    return len(parole) != len(set(parole))


def regoleDelleCandidate(fatti, provati, verificate=None):
    """Restituisce completa(frase) e usabili(frase): le candidate che si possono usare, in ordine, come (candidata, testo)."""
    paroleDeiTipi = json.loads(FILE_DELLE_PAROLE_DEI_TIPI.read_text(encoding="utf-8-sig"))
    paroleDegliAltriTipi = [parola for tipo, parole in paroleDeiTipi.items()
                            if tipo not in ("descrizione", fatti.get("tipo")) for parola in parole]
    altroTipo = lambda frase: any(parola in frase.lower() for parola in paroleDegliAltriTipi)

    def completa(frase):
        if not all(nome in fatti for nome in GRAFFA.findall(frase)):
            return None
        return GRAFFA.sub(lambda m: html.escape(fatti[m.group(1)], quote=True), frase)

    def usabili(frase):
        modello, riserve, prove = frase["candidate"][0], frase["candidate"][1:], frase.get("prove", {})
        elenco = []
        for candidata in [modello] + [riserva for riserva in riserve if not altroTipo(riserva)
                                      and (GRAFFA.search(riserva) or prove.get(riserva) is not None)]:
            testo = completa(candidata)
            if testo is None or not all(chiave in provati for chiave in (prove.get(candidata) or [])):
                continue
            if not (fatti.get("email") or fatti.get("whatsapp")) and SCRIVETECI.search(html.unescape(testo)):
                continue  # "Scriveteci" solo se c'è un modo per scrivere: email o WhatsApp (Michele, 9/11/2026)
            if GRAFFA.search(candidata) and parolaRipetuta(testo):
                continue  # "Hotel Treviglio, a Treviglio": mai la stessa parola due volte nella frase (Michele, 8/11/2026)
            if verificate is not None and paroleDi(testo) >= PAROLE_DI_UNA_FRASE and testo not in verificate:
                continue
            elenco.append((candidata, testo))
        return elenco

    return completa, usabili


# la firma di ogni recensione si ripete sotto ognuna delle 6 recensioni (Michele, 11/11/2026, task #577)
# e il nome della struttura come marchio (testata, piede, elemento 3D) si ripete in ogni pagina
RIPETIBILI = {"Un ospite di {nomestruttura}", "{nomestruttura}"}


def completaLaFraseConIFattiVeriDelCliente(frasi, fatti, provati, verificate):
    completa, usabili = regoleDelleCandidate(fatti, provati, verificate)
    usate, giaScelte = set(), {}
    contatti = [html.escape(str(fatti[k]), quote=True) for k in ("telefono", "email") if fatti.get(k)]
    for frase in frasi:
        modello, prove = frase["candidate"][0], frase.get("prove", {})
        fissa = lambda c: c == modello and (not GRAFFA.search(modello) or c.rstrip(".") in RIPETIBILI)
        candidate = usabili(frase)
        if frase.get("sezione") == SEZIONE_DELL_APERTURA:
            # nell'apertura prima i titoli che dicono cosa fa l'attività (Michele, 9/11/2026)
            candidate.sort(key=lambda ct: not (ATTIVITA.search(html.unescape(ct[1])) or fatti.get("nomestruttura", "") in html.unescape(ct[1])))
        gia = giaScelte.setdefault((frase["pagina"], frase.get("sezione"), frase.get("gruppo")), [])  # titoli con titoli, testi con testi
        scelta, testo = next(((c, t) for c, t in candidate
                              if (fissa(c) or not frase["sezione"] or (frase["pagina"], c) not in usate)
                              and not (frase["sezione"] and not fissa(c) and doppiaNellaSezione(t, gia, contatti))), (None, None))
        if scelta and frase["sezione"]:
            usate.add((frase["pagina"], scelta))
            gia.append(testo)
        frase["scelta"] = scelta
        frase["italiano"] = testo
        frase["prova"] = {chiave: provati[chiave] for chiave in (prove.get(scelta) or [])} if scelta else {}
        if testo in verificate:
            frase["prova"]["fraseVerificata"] = verificate[testo]
        frase["ingleseCompleto"] = completa(frase["inglese"]) if scelta == modello and frase["inglese"] else None
    # implementare post template: l'inglese delle frasi approvate. Quando la frase cambia, oggi non c'è la sua versione
    # inglese approvata e la pagina in inglese mostra la frase italiana.
    return frasi

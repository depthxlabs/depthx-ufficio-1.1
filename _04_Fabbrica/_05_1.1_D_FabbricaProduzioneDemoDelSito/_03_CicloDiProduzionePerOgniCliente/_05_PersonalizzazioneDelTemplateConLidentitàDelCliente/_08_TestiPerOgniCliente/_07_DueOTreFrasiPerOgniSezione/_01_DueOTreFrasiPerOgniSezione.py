"""Passo 5.8.7: ogni sezione racconta con 2 o 3 frasi verificate (Michele, 8/11/2026).

Sostituzioni (Michele, 9/11/2026): prima di questo passo le frasi non verificate sono già sostituite nel loro elemento
(passo 5.8.6, sostituisciLeFrasiNonVerificate) e contano come frasi della sezione: restano senza scelta solo quelle
senza nessuna sostituta, quindi una sezione esce di rado.

Gira dopo il passo 5.8.5 e prima del 5.8.6, quando nella pagina ci sono ancora i paragrafi delle frasi rimaste senza una
candidata verificata: così anche una sezione che perde la sua frase si arricchisce. In ogni sezione con una frase del
copywriting del gruppo "Testi" si contano i paragrafi con un testo che resteranno (non contano quelli senza una candidata
né quelli con graffe vuote, come le schede delle camere senza i dati). Se sono meno di 3, si aggiungono altre
frasi dello stesso argomento, in quest'ordine:
- le altre frasi approvate della stessa sezione, complete con i fatti veri, provate e verificate (passo 5.8.4);
- le frasi del sito attuale del cliente scelte per quell'argomento, copiate parola per parola (passo 5.8.4).
Ogni frase nuova è un paragrafo con la stessa classe del paragrafo che c'è già, subito dopo di lui, con l'inglese scritto
nella verifica (passo 5.8.4).
Una frase già presente nella pagina non si ripete, e nemmeno una che comincia con le stesse tre parole di un'altra frase
della sezione. Una sezione che anche così resta con meno di 2 frasi esce intera, con i link del menu che portano a lei, ma solo se
non mostra nessuna foto del cliente: una sezione con le foto del cliente resta sempre (Michele, 8/11/2026).
Non si toccano l'apertura (con il titolo h1), le sezioni con un modulo e quelle delle recensioni.
Restituisce le frasi aggiunte e le sezioni tolte.
"""

import html
import re
from pathlib import Path

from .._04_CompletaLaFraseConIFattiVeriDelCliente._02_CompletaLaFraseConIFattiVeriDelCliente import regoleDelleCandidate
from .._06_TogliLeSezioniSenzaUnaFraseCompleta._01_TogliLeSezioniSenzaUnaFraseCompleta import elementoOriginale

FRASI_MINIME, FRASI_MASSIME = 2, 3
GRUPPO_DEI_TESTI = "Testi"
NON_SI_TOCCA = re.compile(r"<(h1|form)\b|\{(?:recensione\w*|testoDellaRecensione|testoRecensione\d)\}", re.I)
SEZIONE = re.compile(r"<section\b([^>]*)>(.*?)</section\s*>", re.S | re.I)
PARAGRAFO_CON_TESTO = re.compile(r"<p\b[^>]*>(.*?)</p\s*>", re.S | re.I)
GRAFFA = re.compile(r"\{\w+\}")
SEZIONI_SENZA_LA_REGOLA_DELLE_FOTO = {"_03_ChiSiamo"}
# i dati di chi è e dove sta la struttura si possono ripetere: nome, luogo e contatti
FATTI_DELL_IDENTITA = {"nomestruttura", "nomeBreve", "tipo", "comune", "via", "cap", "provincia", "regione", "telefono",
                       "telefonoLink", "email", "whatsapp", "facebook", "instagram", "linkRecensioni", "linkIndicazioni",
                       "annoCorrente"}
inizio = lambda testo: " ".join(re.findall(r"[a-zà-ÿ0-9']+", html.unescape(re.sub(r"<[^>]+>", "", testo)).lower())[:3])


PAROLE_VUOTE = {"per", "con", "che", "del", "della", "dei", "delle", "nel", "nella", "una", "uno", "gli", "le", "il", "lo",
                "la", "di", "da", "in", "su", "al", "alla", "ai", "a", "e", "o", "ci", "vi", "noi", "voi", "siamo", "è"}
TESTO_NELLA_PAGINA = re.compile(r"<(p|li|h[1-6]|dd|span|a)\b[^>]*>([^<]+)<", re.I)
STESSE_COSE = 0.8  # parte delle parole di una frase già presenti in un'altra frase della pagina


def paroleDiContenuto(testo):
    return {p for p in re.findall(r"[a-zà-ÿ0-9]+", html.unescape(testo).lower()) if p not in PAROLE_VUOTE}


def giaDetta(testo, codice, nuove):
    """Una frase che dice le stesse cose di un'altra già nella pagina, in qualsiasi sezione, non entra: per esempio "Siamo
    in Frazione Canova, a Colli Verdi" dopo "Siamo a Colli Verdi, in Frazione Canova" (Michele, 8/11/2026)."""
    mie = paroleDiContenuto(testo)
    if len(mie) < 2:
        return False
    for altra in [t for _, t in TESTO_NELLA_PAGINA.findall(codice)] + list(nuove):
        sue = paroleDiContenuto(altra)
        if len(sue) >= 2 and len(mie & sue) / min(len(mie), len(sue)) >= STESSE_COSE:
            return True
    return False


def paragrafo(testo):
    return re.compile(r"<p\b([^>]*)>\s*" + re.escape(testo) + r"\s*</p\s*>")


def togliLaSezione(codice, sezione):
    codice = codice.replace(sezione.group(0), "", 1)
    identita = re.search(r'\bid="([^"]+)"', sezione.group(1))
    if identita:
        ancora = re.escape(identita.group(1))
        codice = re.sub(r"<li\b[^>]*>\s*<a\b[^>]*href=\"#" + ancora + r"\"[^>]*>.*?</a\s*>\s*</li\s*>", "", codice, flags=re.S)
        codice = re.sub(r"<a\b[^>]*href=\"#" + ancora + r"\"[^>]*>.*?</a\s*>", "", codice, flags=re.S)
    return codice, identita.group(1) if identita else ""


def conLeFotoDelCliente(sezione, sceneConFoto):
    """La sezione mostra almeno una foto del cliente: non esce mai dalla pagina (Michele, 8/11/2026)."""
    return any(scena in sceneConFoto for scena in re.findall(r'data-scena="([^"]+)"', sezione))


def dueOTreFrasiPerOgniSezione(sito, completate, sceneConFoto=()):
    _, usabili = regoleDelleCandidate(completate["fatti"], completate["provati"], completate["verificate"])
    dalSito = completate.get("dalSito") or {}
    testi = [frase for frase in completate["frasi"] if frase.get("gruppo") == GRUPPO_DEI_TESTI and frase["tag"].lower() == "p"]
    aggiunte, tolte = [], []
    contatti = [html.escape(str(completate["fatti"][k]), quote=True) for k in ("telefono", "email") if completate["fatti"].get(k)]
    fattiDescrittivi = [html.escape(valore, quote=True) for chiave, valore in completate["fatti"].items()
                        if chiave not in FATTI_DELL_IDENTITA and len(str(valore)) >= 12]
    for pagina in sorted(Path(sito).glob("*.html")):
        codice = pagina.read_text(encoding="utf-8-sig")
        prima = codice
        for sezione in list(SEZIONE.finditer(prima)):
            if NON_SI_TOCCA.search(sezione.group(0)):
                continue
            dentro = sezione.group(0)
            trovate, daTogliere = [], set()
            for frase in testi:
                if frase["pagina"] != str(pagina):
                    continue
                if frase["scelta"]:
                    trovato = paragrafo(frase["italiano"]).search(dentro)
                else:
                    trovato = re.compile(elementoOriginale(frase).pattern + r"</p\s*>").search(dentro)
                    if trovato:
                        daTogliere.add(trovato.group(0))
                if trovato:
                    trovate.append((frase, trovato))
            if not trovate:
                continue
            # contano solo i paragrafi che resteranno: non quelli senza una candidata e non quelli con graffe vuote
            # (le schede delle camere senza i dati), che il passo 5.8.6 toglie
            restano = [p.group(1) for p in PARAGRAFO_CON_TESTO.finditer(dentro)
                       if re.sub(r"<[^>]+>", "", p.group(1)).strip() and not GRAFFA.search(p.group(1))
                       and p.group(0) not in daTogliere]
            presenti = len(restano)
            inizi = {inizio(testo) for testo in restano}
            altre = []
            for frase, _ in trovate:
                altre += [testo for _, testo in usabili(frase)]
            for frase, _ in trovate:
                altre += dalSito.get(frase["sezione"], [])
            nuove = []
            # un fatto descrittivo (dotazioni, vista...) già scritto nella sezione non si ripete in un'altra frase
            ripete = lambda testo: any(valore in testo and (valore in dentro or any(valore in n for n in nuove))
                                       for valore in fattiDescrittivi)
            for testo in altre:
                if presenti + len(nuove) >= FRASI_MASSIME:
                    break
                # mai lo stesso telefono o la stessa email in due frasi della stessa sezione (Michele, 9/11/2026)
                contattoDoppio = any(c in testo and (c in dentro or any(c in n for n in nuove)) for c in contatti)
                if (testo not in codice and testo not in nuove and inizio(testo) not in inizi and not ripete(testo)
                        and not giaDetta(testo, codice, nuove) and not contattoDoppio):
                    nuove.append(testo)
                    inizi.add(inizio(testo))
            # Chi siamo parla solo dell'attività: la foto della facciata non basta a tenerla (Michele, 8/11/2026)
            protetta = conLeFotoDelCliente(dentro, sceneConFoto) and not any(f["sezione"] in SEZIONI_SENZA_LA_REGOLA_DELLE_FOTO for f, _ in trovate)
            # Michele, 11/11/2026: le camere ci sono sempre (sezioni con data-sempre)
            if presenti + len(nuove) < FRASI_MINIME and not protetta and "data-sempre" not in dentro[:400]:
                codice, identita = togliLaSezione(codice, sezione)
                tolte.append({"sezione": identita, "frasi": presenti + len(nuove)})
                continue
            if not nuove:
                continue
            ultimo = max((trovato for _, trovato in trovate), key=lambda trovato: trovato.end())
            attributi = re.search(r"<p\b([^>]*)>", ultimo.group(0)).group(1)
            attributi = re.sub(r'\s(?:data-en|data-t|id)="[^"]*"', "", attributi)
            rientro = re.search(r"[ \t]*$", dentro[:ultimo.start()]).group(0)
            inglese = completate.get("inglese") or {}
            conInglese = lambda testo: f' data-en="{inglese[testo]}"' if inglese.get(testo) else ""
            aggiunta = "".join(f"\n{rientro}<p{attributi}{conInglese(testo)}>{testo}</p>" for testo in nuove)
            arricchita = dentro[:ultimo.end()] + aggiunta + dentro[ultimo.end():]
            codice = codice.replace(dentro, arricchita, 1)
            aggiunte += [{"pagina": pagina.name, "sezione": trovate[0][0]["sezione"], "frase": testo} for testo in nuove]
        if codice != prima:
            pagina.write_text(codice, encoding="utf-8")
    return {"aggiunte": aggiunte, "sezioniTolte": tolte}

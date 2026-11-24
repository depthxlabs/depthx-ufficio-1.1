"""Passo 5.8.4: la verifica di ogni frase completa, prima che vada nella pagina.

Le frasi del copy si usano solo quando sono verificate (Michele, 8/11/2026): una frase con il fatto provato può comunque
essere smentita dal materiale ("Il caffè lo prepariamo al momento" dove la colazione è a buffet). Ogni candidata che si
può usare, completata con i fatti veri e senza prezzi, va a Claude sul server con il materiale del cliente e i
suoi dati, in una sola chiamata (_05_RegoleDeiFattiProvati.json, istruzioni _09_IstruzioniPerLaVerificaDelleFrasi.md).
Claude dice quali sono verificate, con la citazione, e per ogni argomento del sito sceglie fino a 5 frasi del sito attuale
del cliente, copiate parola per parola: servono quando una sezione non ha 2 o 3 frasi approvate e verificate (passo
5.8.7). Una frase del sito vale solo se è davvero nel testo del sito, senza parole vietate, senza io e senza tu, senza prezzi.
Se Claude non risponde il cliente si ferma: senza verifica nessuna frase entra nella pagina.
Nella stessa chiamata Claude traduce in inglese ogni frase verificata e ogni frase del sito (Michele, 8/11/2026): così una
frase cambiata o aggiunta ha il suo inglese e la pagina inglese non resta mista.
Restituisce {"verificate": frase -> {citazione, fonte}, "dalSito": argomento -> [frasi], "inglese": frase -> inglese}.
"""

import html
import json
import re
from pathlib import Path

from ...._07_CollaudoBasicoDellaDemo._08_ControlloCheLaStrutturaParliConIlNoiEChiamiLOspiteConIlVoi._01_FrasiInPrimaPersonaSingolareOConIlTu import \
    PAROLE_DELL_IO_E_DEL_TU
from ._02_CompletaLaFraseConIFattiVeriDelCliente import paroleDi, regoleDelleCandidate
from ._07_FattiProvatiDalMaterialeDelCliente import chiediAClaude, materialePerClaude

CARTELLA = Path(__file__).absolute().parent
FILE_DELLE_REGOLE = CARTELLA / "_05_RegoleDeiFattiProvati.json"
FILE_DELLE_ISTRUZIONI = CARTELLA / "_09_IstruzioniPerLaVerificaDelleFrasi.md"
CARTELLA_DEL_COPYWRITING = CARTELLA.parent / "_02_CopywritingDellOspitalità"
FILE_DELLE_PAROLE_VIETATE = (CARTELLA.parents[2] / "_07_CollaudoBasicoDellaDemo" / "_02_ControlloCheNonCiSiaNessunaParolaVietata"
                             / "_01_ParoleVietateNeiTestiDelleDemo.json")
PAROLE_MINIME_DAL_SITO, PAROLE_MASSIME_DAL_SITO = 5, 45
FRASI_DAL_SITO_PER_ARGOMENTO = 5  # candidate: nella pagina ne vanno al massimo 3 per sezione (passo 5.8.7)
NON_DAL_SITO = re.compile(r"€|\beuro\b|%|prezz|scont|offert|promozion|\bvoto\b|recension", re.I)
PREZZO = re.compile(r"€|\beuro\b", re.I)  # i prezzi cambiano: una frase completata con un prezzo non entra
normale = lambda testo: " ".join(html.unescape(testo).lower().replace("’", "'").split())


def titoloDellArgomento(sezione):
    file = CARTELLA_DEL_COPYWRITING / f"{sezione}.md" if sezione else None
    return file.read_text(encoding="utf-8-sig").splitlines()[0].lstrip("# ").strip() if file and file.is_file() else ""


def argomentiDelSito(frasi):
    argomenti = {}
    for frase in frasi:
        if frase.get("sezione") and frase.get("gruppo") == "Testi":
            file = CARTELLA_DEL_COPYWRITING / f"{frase['sezione']}.md"
            titolo = file.read_text(encoding="utf-8-sig").splitlines()[0].lstrip("# ").strip() if file.is_file() else ""
            argomenti[frase["sezione"]] = titolo or frase["sezione"]
    return argomenti


def fraseBuonaDalSito(frase, sitoAttuale, parole):
    testo = " ".join(str(frase).split())
    minuscolo = normale(testo)
    if not (PAROLE_MINIME_DAL_SITO <= paroleDi(testo) <= PAROLE_MASSIME_DAL_SITO) or minuscolo not in sitoAttuale:
        return False
    if NON_DAL_SITO.search(testo) or PAROLE_DELL_IO_E_DEL_TU.search(testo):
        return False
    return not any(re.search(r"(?<![\wà-ÿ])" + re.escape(parola.lower()) + r"(?![\wà-ÿ])", minuscolo) for parola in parole)


def verificaDelleFrasiComplete(frasi, fatti, provati, datiUnici, recensioni):
    _, usabili = regoleDelleCandidate(fatti, provati)
    daVerificare, argomentoDi = [], {}
    for frase in frasi:
        for _, testo in usabili(frase):
            argomentoDi.setdefault(testo, titoloDellArgomento(frase.get("sezione")))
            # anche le frasi corte (i titoli) vanno a Claude, per avere il loro inglese
            if testo not in daVerificare and not PREZZO.search(html.unescape(testo)):
                daVerificare.append(testo)
    argomenti = argomentiDelSito(frasi)
    if not daVerificare and not argomenti:
        return {"verificate": {}, "dalSito": {}, "inglese": {}}
    regole = json.loads(FILE_DELLE_REGOLE.read_text(encoding="utf-8-sig"))
    dati = {chiave: " ".join(str(valore).split())[:200] for chiave, valore in fatti.items() if str(valore).strip()}
    istruzioni = (FILE_DELLE_ISTRUZIONI.read_text(encoding="utf-8-sig")
                  .replace("{materiale}", json.dumps(materialePerClaude(datiUnici, recensioni, regole), ensure_ascii=False, indent=1))
                  .replace("{dati}", json.dumps(dati, ensure_ascii=False, indent=1))
                  .replace("{frasi}", "\n".join(f"{numero}. [{argomentoDi.get(testo) or 'testo della pagina'}] {html.unescape(testo)}"
                                                for numero, testo in enumerate(daVerificare, 1)) or "nessuna")
                  .replace("{paroleVietate}", ", ".join(json.loads(FILE_DELLE_PAROLE_VIETATE.read_text(encoding="utf-8-sig"))["parole"]))
                  .replace("{argomenti}", "\n".join(f"{chiave}: {titolo}" for chiave, titolo in argomenti.items()) or "nessuno"))
    risposta = chiediAClaude(istruzioni, regole)
    if risposta is None:
        raise RuntimeError("la verifica delle frasi non ha risposto: senza verifica nessuna frase entra nella pagina")
    verificate, inglese = {}, {}
    perAttributo = lambda testo: html.escape(" ".join(str(testo).split()), quote=True)
    for numero, voce in (risposta.get("verificate") or {}).items():
        if str(numero).isdigit() and 1 <= int(numero) <= len(daVerificare) and isinstance(voce, dict):
            testo = daVerificare[int(numero) - 1]
            verificate[testo] = {"citazione": str(voce.get("citazione", ""))[:300], "fonte": str(voce.get("fonte", ""))[:80]}
            if str(voce.get("inglese") or "").strip():
                inglese[testo] = perAttributo(voce["inglese"])
    sitoAttuale = normale(datiUnici.get("sitoAttuale") or "")
    parole = json.loads(FILE_DELLE_PAROLE_VIETATE.read_text(encoding="utf-8-sig"))["parole"]
    traduzioni = {" ".join(str(it).split()): en for it, en in (risposta.get("ingleseDalSito") or {}).items()
                  if str(en or "").strip()}
    dalSito = {}
    for argomento, elenco in (risposta.get("dalSito") or {}).items():
        if argomento in argomenti and isinstance(elenco, list):
            buone = [" ".join(str(frase).split()) for frase in elenco if fraseBuonaDalSito(frase, sitoAttuale, parole)]
            if buone:
                dalSito[argomento] = [html.escape(frase, quote=False) for frase in buone[:FRASI_DAL_SITO_PER_ARGOMENTO]]
                inglese.update({html.escape(frase, quote=False): perAttributo(traduzioni[frase])
                                for frase in buone[:FRASI_DAL_SITO_PER_ARGOMENTO] if frase in traduzioni})
    return {"verificate": verificate, "dalSito": dalSito, "inglese": inglese}

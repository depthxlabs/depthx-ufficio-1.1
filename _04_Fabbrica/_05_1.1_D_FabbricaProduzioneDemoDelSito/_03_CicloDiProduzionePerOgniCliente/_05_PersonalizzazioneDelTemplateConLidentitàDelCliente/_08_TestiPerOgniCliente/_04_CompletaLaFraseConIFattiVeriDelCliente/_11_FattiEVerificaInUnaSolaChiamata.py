"""Passo 5.8.4: i fatti provati e la verifica delle frasi insieme, in parti piccole che partono tutte nello stesso momento.

La chiamata dei fatti è divisa in una parte per ogni gruppo di materiale del cliente: il sito attuale, la scheda Google, il
rapporto di unicità e le recensioni (GRUPPI_DI_MATERIALE). Ogni parte ha le istruzioni di
_12_IstruzioniPerFattiEVerificaInUnaSolaChiamata.md con il suo solo gruppo di materiale: i fatti provati con la citazione, i
valori delle graffe, la verifica delle frasi che hanno ancora una graffa da trovare e il loro inglese; le frasi del sito per
argomento (quarto compito) le sceglie solo la parte del sito. Nello stesso momento partono chiamateDiVerificaInsieme chiamate
(_05_RegoleDeiFattiProvati.json) che verificano e traducono le altre frasi candidate, a gruppi, con tutto il materiale e le
istruzioni di _09. Ogni parte risponde in meno tempo; il tempo del passo è quello della parte più lunga.

Le risposte delle parti si uniscono: un fatto è provato se una parte lo prova (vale la citazione del primo gruppo, nell'ordine
di GRUPPI_DI_MATERIALE), una graffa ha il valore del primo gruppo che lo trova, e una frase con la graffa è verificata se l'ha
verificata una parte che ha trovato per le sue graffe gli stessi valori che la pagina userà. Nessun fatto provato da una parte
si perde. Dopo l'unione la fabbrica rifà da sola gli stessi controlli di prima: una frase entra solo se i fatti della sua
prova sono provati, se tutte le sue graffe hanno un valore e se un modello l'ha verificata. Le parole vietate, il noi e il voi,
i prezzi e le frasi del sito si controllano come prima (_08: fraseBuonaDalSito).
Ogni chiamata va ai modelli gratuiti di FreeLLMAPI con le ripetizioni (_07: chiediAFreeLLM); se dopo tutte le ripetizioni
nessun modello risponde, NOTGO di sistema: il passo si rifà al giro dopo, mai una demo con meno fatti.
Restituisce {"provati", "dati", "verificate", "dalSito", "inglese"}.
"""

import contextvars
import html
import json
import re
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from ._02_CompletaLaFraseConIFattiVeriDelCliente import regoleDelleCandidate
from ._07_FattiProvatiDalMaterialeDelCliente import (FILE_DEI_FATTI_DA_PROVARE, GRAFFA, GRAFFA_DI_PROVA, GRAFFE_DELLA_FABBRICA,
                                                     chiediAFreeLLM, materialePerIModelli)
from ._08_VerificaDelleFrasiComplete import (FILE_DELLE_PAROLE_VIETATE, FRASI_DAL_SITO_PER_ARGOMENTO, PREZZO, argomentiDelSito,
                                             fraseBuonaDalSito, normale, titoloDellArgomento)

CARTELLA = Path(__file__).absolute().parent
FILE_DELLE_REGOLE = CARTELLA / "_05_RegoleDeiFattiProvati.json"
FILE_DELLE_ISTRUZIONI = CARTELLA / "_12_IstruzioniPerFattiEVerificaInUnaSolaChiamata.md"
FILE_DELLE_ISTRUZIONI_DELLA_VERIFICA = CARTELLA / "_09_IstruzioniPerLaVerificaDelleFrasi.md"
FRASE_DEL_MATERIALE = ("Questo è il materiale del cliente: il testo del suo sito attuale, il rapporto di unicità (ogni settore ha "
                       "una frase e la citazione da cui viene), la scheda Google e alcune recensioni degli ospiti.")
# i gruppi di materiale, uno per parte, nell'ordine in cui valgono le citazioni: prima il cliente stesso, poi le recensioni
GRUPPI_DI_MATERIALE = (("sitoDelCliente", "il testo del suo sito attuale"),
                       ("schedaGoogle", "la scheda Google"),
                       ("rapportoDiUnicita", "il rapporto di unicità (ogni settore ha una frase e la citazione da cui viene)"),
                       ("recensioni", "alcune recensioni degli ospiti"))


class TuttoProvato(dict):
    """Per scegliere le candidate prima di sapere quali fatti sono provati: ogni fatto vale come provato."""

    def __contains__(self, chiave):
        return True


def gruppoPieno(valore):
    if isinstance(valore, dict):
        return any(gruppoPieno(voce) for voce in valore.values())
    if isinstance(valore, list):
        return any(gruppoPieno(voce) for voce in valore)
    return valore is not None and bool(str(valore).strip())


def rispostaDiUnaParte(risposta):
    """Una parte risponde bene se ha almeno una delle sue voci e ogni voce che ha è un oggetto."""
    voci = [risposta.get(chiave) for chiave in ("provati", "dati", "verificate", "dalSito") if chiave in risposta]
    return bool(voci) and all(isinstance(voce, dict) for voce in voci)


def fattiEVerificaInUnaSolaChiamata(frasi, datiUnici, recensioni, fatti):
    daProvare = sorted({chiave for frase in frasi for prove in frase.get("prove", {}).values() for chiave in (prove or [])}
                       | {"usaWhatsapp"})
    esempi = {}
    for frase in frasi:
        for candidata in frase.get("candidate") or []:
            for graffa in GRAFFA.findall(candidata):
                if graffa not in fatti and graffa not in GRAFFE_DELLA_FABBRICA:
                    esempi.setdefault(graffa, GRAFFA_DI_PROVA.sub("", candidata).strip())
    # le candidate che potrebbero servire: le graffe ancora da trovare restano tra graffe. Dentro la fabbrica il segnaposto è
    # senza lettere ({#1}), così il controllo della parola ripetuta (_02) non lo scambia per una parola; al modello va {graffa}
    segnaposto = {graffa: "{#" + str(numero) + "}" for numero, graffa in enumerate(sorted(esempi), 1)}
    perIlModello = lambda testo: re.sub(r"\{#(\d+)\}", lambda m: "{" + sorted(esempi)[int(m.group(1)) - 1] + "}", testo)
    conLeGraffe = {**fatti, **segnaposto}
    _, usabili = regoleDelleCandidate(conLeGraffe, TuttoProvato())
    candidate, argomentoDi = [], {}
    for frase in frasi:
        for candidata, testo in usabili(frase):
            if (candidata, testo) not in candidate and not PREZZO.search(html.unescape(testo)):
                candidate.append((candidata, testo))
                argomentoDi.setdefault(testo, titoloDellArgomento(frase.get("sezione")))
    argomenti = argomentiDelSito(frasi) if (datiUnici.get("sitoAttuale") or "").strip() else {}
    regole = json.loads(FILE_DELLE_REGOLE.read_text(encoding="utf-8-sig"))
    descrizioni = json.loads(FILE_DEI_FATTI_DA_PROVARE.read_text(encoding="utf-8-sig")).get("fatti", {})
    paroleVietate = json.loads(FILE_DELLE_PAROLE_VIETATE.read_text(encoding="utf-8-sig"))["parole"]
    dati = {chiave: " ".join(str(valore).split())[:200] for chiave, valore in fatti.items() if str(valore).strip()}
    testi = []  # un numero per ogni testo diverso: lo stesso testo da due candidate si verifica una volta
    for _, testo in candidate:
        if testo not in testi:
            testi.append(testo)
    tuttoIlMateriale = materialePerIModelli(datiUnici, recensioni, regole)
    materiale = json.dumps(tuttoIlMateriale, ensure_ascii=False, indent=1)
    elenco = lambda numeri: "\n".join(f"{numero}. [{argomentoDi.get(testi[numero - 1]) or 'testo della pagina'}] "
                                      f"{perIlModello(html.unescape(testi[numero - 1]))}" for numero in numeri) or "nessuna"
    conGraffa = [numero for numero, testo in enumerate(testi, 1) if "{#" in testo]
    senza = [numero for numero, testo in enumerate(testi, 1) if "{#" not in testo]
    gruppi = max(1, int(regole.get("chiamateDiVerificaInsieme", 3)))
    gruppi = [senza[i::gruppi] for i in range(gruppi) if senza[i::gruppi]]
    # una parte per ogni gruppo di materiale che il cliente ha; senza nessun gruppo, una parte con il materiale vuoto
    parti = [(chiave, descrizione) for chiave, descrizione in GRUPPI_DI_MATERIALE if gruppoPieno(tuttoIlMateriale.get(chiave))]
    istruzioniDellaParte = FILE_DELLE_ISTRUZIONI.read_text(encoding="utf-8-sig")
    if FRASE_DEL_MATERIALE not in istruzioniDellaParte:
        raise RuntimeError("le istruzioni dei fatti (_12) non hanno più la frase del materiale: le parti non si possono dividere")
    comune = (istruzioniDellaParte.replace("{dati}", json.dumps(dati, ensure_ascii=False, indent=1))
              .replace("{fatti}", "\n".join(f"{chiave}: {descrizioni.get(chiave, chiave)}" for chiave in daProvare) or "nessuno")
              .replace("{graffe}", "\n".join(f"{{{graffa}}}: {esempio}" for graffa, esempio in sorted(esempi.items())) or "nessuna")
              .replace("{frasi}", elenco(conGraffa))
              .replace("{paroleVietate}", ", ".join(paroleVietate)))
    elencoDegliArgomenti = "\n".join(f"{chiave}: {titolo}" for chiave, titolo in argomenti.items()) or "nessuno"
    istruzioniDellePartiDiMateriale = []
    for chiave, descrizione in parti or [(None, "")]:
        if chiave is None:
            testo = comune.replace("{materiale}", materiale)
        else:
            testo = (comune.replace(FRASE_DEL_MATERIALE, f"Questa è una parte del materiale del cliente: {descrizione}. Le altre parti "
                                                         "le leggono altre chiamate: rispondi solo con quello che dice questa parte.")
                     .replace("{materiale}", json.dumps({chiave: tuttoIlMateriale[chiave]}, ensure_ascii=False, indent=1)))
        delSito = chiave in (None, "sitoDelCliente")
        istruzioniDellePartiDiMateriale.append((delSito, testo.replace("{argomenti}", elencoDegliArgomenti if delSito else "nessuno")))
    istruzioniDellaVerifica = FILE_DELLE_ISTRUZIONI_DELLA_VERIFICA.read_text(encoding="utf-8-sig")
    altreIstruzioni = [istruzioniDellaVerifica.replace("{materiale}", materiale).replace("{dati}", json.dumps(dati, ensure_ascii=False, indent=1))
                       .replace("{frasi}", elenco(gruppo)).replace("{argomenti}", "nessuno")
                       .replace("{paroleVietate}", ", ".join(paroleVietate)) for gruppo in gruppi]
    verificaValida = lambda r: isinstance(r.get("verificate"), dict)
    with ThreadPoolExecutor(max_workers=len(istruzioniDellePartiDiMateriale) + len(altreIstruzioni)) as insieme:
        partiInCorso = [insieme.submit(contextvars.copy_context().run, chiediAFreeLLM, testo, (), 330, rispostaDiUnaParte, numero)
                        for numero, (_, testo) in enumerate(istruzioniDellePartiDiMateriale)]
        altre = [insieme.submit(contextvars.copy_context().run, chiediAFreeLLM, istruzione, (), 330, verificaValida,
                                len(partiInCorso) + numero) for numero, istruzione in enumerate(altreIstruzioni)]
        # una parte senza risposta dopo tutte le ripetizioni alza NessunModelloRisponde: NOTGO di sistema del passo
        risposteDellePartiDiMateriale = [futuro.result() for futuro in partiInCorso]
        altreRisposte = [futuro.result() for futuro in altre]
    # l'unione delle parti di materiale: fatti, graffe e frasi con la graffa
    provati, trovati, valoriDellaParte = {}, {}, []
    for risposta in risposteDellePartiDiMateriale:
        for chiave, voce in (risposta.get("provati") or {}).items():
            if chiave in daProvare and chiave not in provati and isinstance(voce, dict) and voce.get("citazione"):
                provati[chiave] = {"citazione": str(voce.get("citazione", ""))[:300], "fonte": str(voce.get("fonte", ""))[:80]}
        valori = {}
        for graffa, voce in (risposta.get("dati") or {}).items():
            graffa = graffa.strip("{}")
            if graffa in esempi and isinstance(voce, dict) and voce.get("valore") and voce.get("citazione"):
                valori[graffa] = {"valore": " ".join(str(voce.get("valore", "")).split())[:120],
                                  "citazione": str(voce.get("citazione", ""))[:300], "fonte": str(voce.get("fonte", ""))[:80]}
        valoriDellaParte.append(valori)
        for graffa, voce in valori.items():
            trovati.setdefault(graffa, voce)
    verificateDalModello = {}
    for risposta, valori in zip(risposteDellePartiDiMateriale, valoriDellaParte):
        for numero, voce in (risposta.get("verificate") or {}).items():
            if not (str(numero).isdigit() and int(numero) in conGraffa and isinstance(voce, dict)):
                continue
            graffe = [sorted(esempi)[int(n) - 1] for n in re.findall(r"\{#(\d+)\}", testi[int(numero) - 1])]
            # la parte ha verificato la frase con i suoi valori: vale solo se sono quelli che la pagina userà
            if all(graffa in valori and trovati[graffa]["valore"] == valori[graffa]["valore"] for graffa in graffe):
                verificateDalModello.setdefault(str(int(numero)), voce)
    for gruppo, r in zip(gruppi, altreRisposte):
        verificateDalModello.update({str(int(n)): v for n, v in r["verificate"].items() if str(n).isdigit() and int(n) in gruppo})
    # le frasi verificate, scritte con i valori trovati: il testo è quello che la pagina userà (_02)
    completi = {**{graffa: voce["valore"] for graffa, voce in trovati.items()}, **fatti}  # come il manager: i dati del CRM restano
    completa, _ = regoleDelleCandidate(completi, provati)
    perAttributo = lambda testo: html.escape(" ".join(str(testo).split()), quote=True)
    verificate, inglese = {}, {}
    for numero, voce in verificateDalModello.items():
        if not (1 <= int(numero) <= len(testi) and isinstance(voce, dict)):
            continue
        conGraffe = testi[int(numero) - 1]
        for candidata, testo in candidate:
            if testo != conGraffe:
                continue
            completata = completa(candidata)
            if completata is None or PREZZO.search(html.unescape(completata)):
                continue
            verificate[completata] = {"citazione": str(voce.get("citazione", ""))[:300], "fonte": str(voce.get("fonte", ""))[:80]}
            if str(voce.get("inglese") or "").strip() and not GRAFFA.search(str(voce["inglese"])):
                inglese[completata] = perAttributo(voce["inglese"])
    # le frasi del sito, dalla parte del sito, con gli stessi controlli di _08
    sitoAttuale = normale(datiUnici.get("sitoAttuale") or "")
    dalSito = {}
    for (delSito, _), risposta in zip(istruzioniDellePartiDiMateriale, risposteDellePartiDiMateriale):
        if not delSito:
            continue
        traduzioni = {" ".join(str(it).split()): en for it, en in (risposta.get("ingleseDalSito") or {}).items() if str(en or "").strip()}
        for argomento, elencoDelSito in (risposta.get("dalSito") or {}).items():
            if argomento in argomenti and argomento not in dalSito and isinstance(elencoDelSito, list):
                buone = [" ".join(str(frase).split()) for frase in elencoDelSito if fraseBuonaDalSito(frase, sitoAttuale, paroleVietate)]
                if buone:
                    dalSito[argomento] = [html.escape(frase, quote=False) for frase in buone[:FRASI_DAL_SITO_PER_ARGOMENTO]]
                    inglese.update({html.escape(frase, quote=False): perAttributo(traduzioni[frase])
                                    for frase in buone[:FRASI_DAL_SITO_PER_ARGOMENTO] if frase in traduzioni})
    return {"provati": provati, "dati": trovati, "verificate": verificate, "dalSito": dalSito, "inglese": inglese}

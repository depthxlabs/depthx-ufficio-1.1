"""Passo 5.8.4, pitstop 7 (Michele, 12/11/2026, task #612): i fatti provati e la verifica delle frasi insieme, senza attese.

Prima erano due chiamate a Claude una dopo l'altra (_07 i fatti provati, _08 la verifica delle frasi), ognuna con tutto il
materiale del cliente: 22,5 + 45,5 secondi in media. Ora nessuna chiamata aspetta l'altra: una chiamata fa i fatti provati
con la citazione, i valori delle graffe dal materiale, la verifica delle frasi che hanno ancora una graffa da trovare, fino a
5 frasi del sito attuale per argomento e il loro inglese (_12_IstruzioniPerFattiEVerificaInUnaSolaChiamata.md, che unisce
_06 e _09 con le stesse regole, parola per parola); nello stesso momento partono chiamateDiVerificaInsieme chiamate
(_05_RegoleDeiFattiProvati.json) che verificano e traducono le altre frasi candidate, a gruppi, con le istruzioni di prima
(_09). Il tempo del passo è quello della chiamata più lunga (prova sul banco di S1_BEB_CAL_009: una chiamata sola con tutto
63,4 secondi contro 72,8 delle due in fila: troppo poco, per questo le frasi si dividono).

Le frasi candidate sono tutte quelle che potrebbero servire: completate con i dati del CRM, con le graffe ancora da trovare
lasciate tra graffe (Claude le legge con il valore che trova nello stesso giro). Dopo la risposta la fabbrica rifà da sola
gli stessi controlli di prima: una frase entra solo se i fatti della sua prova sono provati, se tutte le sue graffe hanno un
valore e se Claude l'ha verificata. Le parole vietate, il noi e il voi, i prezzi e le frasi del sito si controllano come
prima (_08: fraseBuonaDalSito). Se Claude non risponde, la fabbrica torna alle due chiamate di prima (_07 e _08), così una
frase senza verifica non entra mai nella pagina.
Restituisce {"provati", "dati", "verificate", "dalSito", "inglese"} come _07 e _08 insieme, oppure None.
"""

import contextvars
import html
import json
import re
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from ._02_CompletaLaFraseConIFattiVeriDelCliente import regoleDelleCandidate
from ._07_FattiProvatiDalMaterialeDelCliente import (FILE_DEI_FATTI_DA_PROVARE, GRAFFA, GRAFFA_DI_PROVA, GRAFFE_DELLA_FABBRICA,
                                                     chiediAClaude, materialePerClaude)
from ._08_VerificaDelleFrasiComplete import (FILE_DELLE_PAROLE_VIETATE, FRASI_DAL_SITO_PER_ARGOMENTO, PREZZO, argomentiDelSito,
                                             fraseBuonaDalSito, normale, titoloDellArgomento)

CARTELLA = Path(__file__).absolute().parent
FILE_DELLE_REGOLE = CARTELLA / "_05_RegoleDeiFattiProvati.json"
FILE_DELLE_ISTRUZIONI = CARTELLA / "_12_IstruzioniPerFattiEVerificaInUnaSolaChiamata.md"
FILE_DELLE_ISTRUZIONI_DELLA_VERIFICA = CARTELLA / "_09_IstruzioniPerLaVerificaDelleFrasi.md"


class TuttoProvato(dict):
    """Per scegliere le candidate prima di sapere quali fatti sono provati: ogni fatto vale come provato."""

    def __contains__(self, chiave):
        return True


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
    # senza lettere ({#1}), così il controllo della parola ripetuta (_02) non lo scambia per una parola; a Claude va {graffa}
    segnaposto = {graffa: "{#" + str(numero) + "}" for numero, graffa in enumerate(sorted(esempi), 1)}
    perClaude = lambda testo: re.sub(r"\{#(\d+)\}", lambda m: "{" + sorted(esempi)[int(m.group(1)) - 1] + "}", testo)
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
    # le parti indipendenti in parallelo (Michele, 12/11/2026): la chiamata dei fatti verifica anche le frasi con le graffe da
    # trovare (dipendono dai valori che trova lei); le altre frasi non dipendono dai fatti e si verificano a gruppi, in
    # chiamate che partono insieme, con le istruzioni della verifica di prima (_09). Il tempo è quello della chiamata più lunga.
    materiale = json.dumps(materialePerClaude(datiUnici, recensioni, regole), ensure_ascii=False, indent=1)
    elenco = lambda numeri: "\n".join(f"{numero}. [{argomentoDi.get(testi[numero - 1]) or 'testo della pagina'}] "
                                      f"{perClaude(html.unescape(testi[numero - 1]))}" for numero in numeri) or "nessuna"
    conGraffa = [numero for numero, testo in enumerate(testi, 1) if "{#" in testo]
    senza = [numero for numero, testo in enumerate(testi, 1) if "{#" not in testo]
    gruppi = max(1, int(regole.get("chiamateDiVerificaInsieme", 3)))
    gruppi = [senza[i::gruppi] for i in range(gruppi) if senza[i::gruppi]]
    primaIstruzione = (FILE_DELLE_ISTRUZIONI.read_text(encoding="utf-8-sig")
                       .replace("{materiale}", materiale).replace("{dati}", json.dumps(dati, ensure_ascii=False, indent=1))
                       .replace("{fatti}", "\n".join(f"{chiave}: {descrizioni.get(chiave, chiave)}" for chiave in daProvare) or "nessuno")
                       .replace("{graffe}", "\n".join(f"{{{graffa}}}: {esempio}" for graffa, esempio in sorted(esempi.items())) or "nessuna")
                       .replace("{frasi}", elenco(conGraffa))
                       .replace("{argomenti}", "\n".join(f"{chiave}: {titolo}" for chiave, titolo in argomenti.items()) or "nessuno")
                       .replace("{paroleVietate}", ", ".join(paroleVietate)))
    istruzioniDellaVerifica = FILE_DELLE_ISTRUZIONI_DELLA_VERIFICA.read_text(encoding="utf-8-sig")
    altreIstruzioni = [istruzioniDellaVerifica.replace("{materiale}", materiale).replace("{dati}", json.dumps(dati, ensure_ascii=False, indent=1))
                       .replace("{frasi}", elenco(gruppo)).replace("{argomenti}", "nessuno")
                       .replace("{paroleVietate}", ", ".join(paroleVietate)) for gruppo in gruppi]
    with ThreadPoolExecutor(max_workers=1 + len(altreIstruzioni)) as insieme:
        prima = insieme.submit(contextvars.copy_context().run, chiediAClaude, primaIstruzione, regole)
        altre = [insieme.submit(contextvars.copy_context().run, chiediAClaude, istruzione, regole) for istruzione in altreIstruzioni]
        risposta, altreRisposte = prima.result(), [futuro.result() for futuro in altre]
    if risposta is None or not isinstance(risposta.get("verificate"), dict) or any(
            r is None or not isinstance(r.get("verificate"), dict) for r in altreRisposte):
        return None
    # le verifiche di ogni gruppo valgono solo per i numeri del suo gruppo
    risposta["verificate"] = {str(n): v for n, v in risposta["verificate"].items() if str(n).isdigit() and int(n) in conGraffa}
    for gruppo, r in zip(gruppi, altreRisposte):
        risposta["verificate"].update({str(n): v for n, v in r["verificate"].items() if str(n).isdigit() and int(n) in gruppo})
    # i fatti provati e le graffe, con gli stessi controlli di _07
    provati = {chiave: {"citazione": str(voce.get("citazione", ""))[:300], "fonte": str(voce.get("fonte", ""))[:80]}
               for chiave, voce in (risposta.get("provati") or {}).items()
               if chiave in daProvare and isinstance(voce, dict) and voce.get("citazione")}
    trovati = {graffa.strip("{}"): {"valore": " ".join(str(voce.get("valore", "")).split())[:120],
                                    "citazione": str(voce.get("citazione", ""))[:300], "fonte": str(voce.get("fonte", ""))[:80]}
               for graffa, voce in (risposta.get("dati") or {}).items()
               if graffa.strip("{}") in esempi and isinstance(voce, dict) and voce.get("valore") and voce.get("citazione")}
    # le frasi verificate, scritte con i valori trovati: il testo è quello che la pagina userà (_02)
    completi = {**{graffa: voce["valore"] for graffa, voce in trovati.items()}, **fatti}  # come il manager: i dati del CRM restano
    completa, _ = regoleDelleCandidate(completi, provati)
    perAttributo = lambda testo: html.escape(" ".join(str(testo).split()), quote=True)
    verificate, inglese = {}, {}
    for numero, voce in risposta["verificate"].items():
        if not (str(numero).isdigit() and 1 <= int(numero) <= len(testi) and isinstance(voce, dict)):
            continue
        conGraffe = testi[int(numero) - 1]
        for candidata, testo in candidate:
            if testo != conGraffe:
                continue
            finale = completa(candidata)
            if finale is None or PREZZO.search(html.unescape(finale)):
                continue
            verificate[finale] = {"citazione": str(voce.get("citazione", ""))[:300], "fonte": str(voce.get("fonte", ""))[:80]}
            if str(voce.get("inglese") or "").strip() and not GRAFFA.search(str(voce["inglese"])):
                inglese[finale] = perAttributo(voce["inglese"])
    # le frasi del sito, con gli stessi controlli di _08
    sitoAttuale = normale(datiUnici.get("sitoAttuale") or "")
    traduzioni = {" ".join(str(it).split()): en for it, en in (risposta.get("ingleseDalSito") or {}).items() if str(en or "").strip()}
    dalSito = {}
    for argomento, elenco in (risposta.get("dalSito") or {}).items():
        if argomento in argomenti and isinstance(elenco, list):
            buone = [" ".join(str(frase).split()) for frase in elenco if fraseBuonaDalSito(frase, sitoAttuale, paroleVietate)]
            if buone:
                dalSito[argomento] = [html.escape(frase, quote=False) for frase in buone[:FRASI_DAL_SITO_PER_ARGOMENTO]]
                inglese.update({html.escape(frase, quote=False): perAttributo(traduzioni[frase])
                                for frase in buone[:FRASI_DAL_SITO_PER_ARGOMENTO] if frase in traduzioni})
    return {"provati": provati, "dati": trovati, "verificate": verificate, "dalSito": dalSito, "inglese": inglese}

"""Passo 5.8.4: i fatti che le frasi approvate affermano, provati dal materiale del cliente.

I fatti da verificare sono quelli che le frasi della pagina chiedono ([prova: ...] nel copywriting, descritti in
_02_CopywritingDellOspitalità/_00_FattiDaProvare.json). Una chiamata ai modelli gratuiti di FreeLLMAPI (_05_RegoleDeiFattiProvati.json)
legge il testo del sito attuale del cliente, il rapporto di unicità del motore, la scheda Google e alcune recensioni, e
restituisce solo i fatti provati, ognuno con la citazione e la fonte (_06_IstruzioniPerIFattiProvati.md). Nella stessa
chiamata ricava dal materiale i valori delle graffe che le frasi candidate chiedono e che i dati del CRM non hanno (per
esempio {camere}, {distanza}, {luogo}), sempre con la citazione. Senza niente da chiedere non si chiama nessuno.
Se nessun modello risponde dopo le ripetizioni, NOTGO di sistema (NessunModelloRisponde): il passo si rifà al giro dopo,
mai una demo con meno fatti.
Restituisce {"provati": chiave -> {citazione, fonte}, "dati": graffa -> {valore, citazione, fonte}}.
"""

import sys
import json
import re
from pathlib import Path

CARTELLA = Path(__file__).absolute().parent
FILE_DELLE_REGOLE = CARTELLA / "_05_RegoleDeiFattiProvati.json"
FILE_DELLE_ISTRUZIONI = CARTELLA / "_06_IstruzioniPerIFattiProvati.md"
FILE_DEI_FATTI_DA_PROVARE = CARTELLA.parent / "_02_CopywritingDellOspitalità" / "_00_FattiDaProvare.json"
GRAFFA = re.compile(r"\{(\w+)\}")
GRAFFA_DI_PROVA = re.compile(r"\s*\[prova:[^\]]*\]")
# graffe che riempie la fabbrica da sola (recensioni, nome, contatti): non si chiedono al materiale
GRAFFE_DELLA_FABBRICA = {"nomestruttura", "nomeBreve", "telefono", "telefonoLink", "email", "whatsapp", "annoCorrente",
                         "recensioneInEvidenza", "testoDellaRecensione", "recensione2", "recensione3",
                         "testoRecensione1", "testoRecensione2", "testoRecensione3", "testoRecensione4", "testoRecensione5", "testoRecensione6", "voto"} | {f"stelleRecensione{n}" for n in range(1, 7)}


def materialePerIModelli(datiUnici, recensioni, regole):
    unicita = datiUnici.get("unicita") or {}
    scheda = datiUnici.get("schedaGoogle") or {}
    return {"sitoDelCliente": datiUnici.get("sitoAttuale") or "",
            "rapportoDiUnicita": {"sintesi": unicita.get("sintesi"), "settori": unicita.get("settori")},
            "schedaGoogle": {chiave: valore for chiave, valore in scheda.items()
                             if chiave not in ("id", "addressComponents", "googleMapsUri", "photos")},
            "recensioni": [voce.get("testo") for voce in recensioni[:int(regole["recensioniMassime"])] if voce.get("testo")]}


CHIAVE_FREE_LLM = Path(r"C:\_02_DepthXSoftware\_01_CentroGestioneDepthX\V1.0(161126_1124)\_01_StrumentiDiLavoroPerIlServer\_01_ChiaviAccessiServiziTerzeParti\_11_FreeLLMAPI\_01_ChiaveUnica.txt")
INDIRIZZO_FREE_LLM = "http://127.0.0.1:3001/v1/chat/completions"
# i modelli attivi in FreeLLMAPI (fornitori kilo e ovh del suo database), dal più capace e veloce; "auto" sceglie tra tutti gli altri
MODELLI_DI_TESTO = ("nemotron-3.5-super-vl", "nemotron-3-ultra-550b", "gpt-oss-120b", "qwen3.5-397b", "kilo-auto", "auto")
# solo i modelli che nel database leggono le immagini
MODELLI_CON_IMMAGINI = ("nemotron-3-nano-omni-reasoning", "qwen2.5-vl-72b", "free-router", "auto")
RIPETIZIONI = 4  # giri completi su tutti i modelli; tra un giro e l'altro l'attesa raddoppia
SECONDI_DELLA_PRIMA_ATTESA = 15
SECONDI_MASSIMI_DI_UNA_DOMANDA = 1500  # oltre, NOTGO di sistema: il passo si rifà al giro dopo
MODELLI_DI_PARTENZA = 3  # le chiamate che partono insieme cominciano da modelli diversi, così nessun fornitore si intasa


class NessunModelloRisponde(RuntimeError):
    """NOTGO di sistema: nessun modello gratuito ha dato una risposta valida dopo tutte le ripetizioni. Non è mai
    un'esclusione del cliente: il passo si rifà al giro dopo."""


def _unaChiamata(chiave, modello, contenuto, secondi):
    import urllib.request
    corpo = json.dumps({"model": modello, "temperature": 0.2, "messages": [
        {"role": "system", "content": "Rispondi solo con un oggetto JSON valido, in italiano, senza altro testo."},
        {"role": "user", "content": contenuto}]}).encode("utf-8")
    richiesta = urllib.request.Request(INDIRIZZO_FREE_LLM, data=corpo, method="POST",
                                       headers={"Authorization": "Bearer " + chiave, "Content-Type": "application/json"})
    with urllib.request.urlopen(richiesta, timeout=secondi) as risposta:
        testo = json.loads(risposta.read().decode("utf-8"))["choices"][0]["message"]["content"] or ""
    testo = re.sub(r"<think>.*?</think>", "", testo, flags=re.S)
    return json.loads(re.search(r"\{.*\}", testo, re.S).group(0))


def _registroDelModello(modello, inizio, esito):
    """Una riga per ogni chiamata a un modello: nome, secondi ed esito, senza dati del cliente (la legge la prova della fabbrica)."""
    import time
    print(f"[modello] {modello} {round(time.monotonic() - inizio)}s {esito}", file=sys.stderr, flush=True)


def chiediAFreeLLM(istruzioni, immagini=(), secondi=330, valida=None, partenza=0):
    """I modelli gratuiti di FreeLLMAPI, con le ripetizioni. immagini: percorsi JPG da mandare insieme alle istruzioni,
    nell'ordine in cui le istruzioni le nominano. valida: controllo della risposta; una risposta che non lo passa vale come
    nessuna risposta e si passa al modello dopo. partenza: da quale dei primi modelli comincia la chiamata.
    Ogni giro prova tutti i modelli, uno dopo l'altro; dopo un giro senza risposta valida si aspetta (15, 30, 60 secondi) e si
    ricomincia. Restituisce l'oggetto JSON della risposta; se nessun modello risponde, NessunModelloRisponde.
    La usano anche le categorie delle foto (4.1), il product manager (8.2) e la correzione (8.4)."""
    import base64
    import time
    try:
        chiave = CHIAVE_FREE_LLM.read_text(encoding="utf-8").strip()
    except OSError as errore:
        raise NessunModelloRisponde(f"NOTGO di sistema: la chiave di FreeLLMAPI non si legge ({type(errore).__name__})")
    contenuto = istruzioni
    if immagini:
        contenuto = [{"type": "text", "text": istruzioni}]
        for percorso in immagini:
            dati = base64.b64encode(Path(percorso).read_bytes()).decode()
            contenuto.append({"type": "image_url", "image_url": {"url": "data:image/jpeg;base64," + dati}})
    modelli = list(MODELLI_CON_IMMAGINI if immagini else MODELLI_DI_TESTO)
    primo = partenza % min(MODELLI_DI_PARTENZA, len(modelli))
    modelli = modelli[primo:primo + 1] + modelli[:primo] + modelli[primo + 1:]
    scadenza = time.monotonic() + SECONDI_MASSIMI_DI_UNA_DOMANDA
    errori = []
    for giro in range(RIPETIZIONI):
        for modello in modelli:
            rimasti = scadenza - time.monotonic()
            if rimasti < 20:
                break
            inizio = time.monotonic()
            try:
                risposta = _unaChiamata(chiave, modello, contenuto, min(secondi, rimasti))
            except Exception as errore:  # noqa: BLE001
                errori.append(f"{modello}: {type(errore).__name__} {str(errore)[:80]}")
                _registroDelModello(modello, inizio, "NOTGO " + type(errore).__name__)
                continue
            if isinstance(risposta, dict) and (valida is None or valida(risposta)):
                _registroDelModello(modello, inizio, "GO")
                return risposta
            errori.append(f"{modello}: risposta non valida")
            _registroDelModello(modello, inizio, "risposta non valida")
        attesa = SECONDI_DELLA_PRIMA_ATTESA * 2 ** giro
        if giro == RIPETIZIONI - 1 or scadenza - time.monotonic() < attesa + 20:
            break
        time.sleep(attesa)
    raise NessunModelloRisponde("NOTGO di sistema: nessun modello gratuito ha risposto dopo le ripetizioni, il passo si rifà al giro dopo ("
                                + "; ".join(errori[-3:]) + ")")


def fattiProvatiDalMaterialeDelCliente(frasi, datiUnici, recensioni, fatti=None):
    fatti = fatti or {}
    # usaWhatsapp si chiede sempre: senza di lui la demo non mostra né pulsanti né frasi WhatsApp (Michele, 8/11/2026)
    daProvare = sorted({chiave for frase in frasi for prove in frase.get("prove", {}).values() for chiave in (prove or [])}
                       | {"usaWhatsapp"})
    esempi = {}
    for frase in frasi:
        for candidata in frase.get("candidate") or []:
            for graffa in GRAFFA.findall(candidata):
                if graffa not in fatti and graffa not in GRAFFE_DELLA_FABBRICA:
                    esempi.setdefault(graffa, GRAFFA_DI_PROVA.sub("", candidata).strip())
    if not daProvare and not esempi:
        return {"provati": {}, "dati": {}}
    regole = json.loads(FILE_DELLE_REGOLE.read_text(encoding="utf-8-sig"))
    descrizioni = json.loads(FILE_DEI_FATTI_DA_PROVARE.read_text(encoding="utf-8-sig")).get("fatti", {})
    materiale = materialePerIModelli(datiUnici, recensioni, regole)
    istruzioni = (FILE_DELLE_ISTRUZIONI.read_text(encoding="utf-8-sig")
                  .replace("{materiale}", json.dumps(materiale, ensure_ascii=False, indent=1))
                  .replace("{fatti}", "\n".join(f"{chiave}: {descrizioni.get(chiave, chiave)}" for chiave in daProvare) or "nessuno")
                  .replace("{graffe}", "\n".join(f"{{{graffa}}}: {esempio}" for graffa, esempio in sorted(esempi.items())) or "nessuna"))
    trovati = chiediAFreeLLM(istruzioni)
    provati = {chiave: {"citazione": str(voce.get("citazione", ""))[:300], "fonte": str(voce.get("fonte", ""))[:80]}
               for chiave, voce in (trovati.get("provati") or {}).items()
               if chiave in daProvare and isinstance(voce, dict) and voce.get("citazione")}
    dati = {graffa: {"valore": " ".join(str(voce.get("valore", "")).split())[:120],
                     "citazione": str(voce.get("citazione", ""))[:300], "fonte": str(voce.get("fonte", ""))[:80]}
            for graffa, voce in (trovati.get("dati") or {}).items()
            if graffa.strip("{}") in esempi and isinstance(voce, dict) and voce.get("valore") and voce.get("citazione")}
    return {"provati": provati, "dati": {graffa.strip("{}"): voce for graffa, voce in dati.items()}}

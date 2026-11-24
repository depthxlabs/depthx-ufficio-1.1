"""Passo 5.8.4: i fatti che le frasi approvate affermano, provati dal materiale del cliente.

I fatti da verificare sono quelli che le frasi della pagina chiedono ([prova: ...] nel copywriting, descritti in
_02_CopywritingDellOspitalità/_00_FattiDaProvare.json). Una sola chiamata a Claude sul server (_05_RegoleDeiFattiProvati.json)
legge il testo del sito attuale del cliente, il rapporto di unicità del motore, la scheda Google e alcune recensioni, e
restituisce solo i fatti provati, ognuno con la citazione e la fonte (_06_IstruzioniPerIFattiProvati.md). Nella stessa
chiamata ricava dal materiale i valori delle graffe che le frasi candidate chiedono e che i dati del CRM non hanno (per
esempio {camere}, {distanza}, {luogo}), sempre con la citazione (8/11/2026). Senza niente da chiedere non si chiama nessuno.
Se Claude non risponde, nessun fatto è provato: le frasi che ne hanno bisogno non si usano.
Restituisce {"provati": chiave -> {citazione, fonte}, "dati": graffa -> {valore, citazione, fonte}}.
"""

import json
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

CARTELLA = Path(__file__).absolute().parent
FILE_DELLE_REGOLE = CARTELLA / "_05_RegoleDeiFattiProvati.json"
FILE_DELLE_ISTRUZIONI = CARTELLA / "_06_IstruzioniPerIFattiProvati.md"
FILE_DEI_FATTI_DA_PROVARE = CARTELLA.parent / "_02_CopywritingDellOspitalità" / "_00_FattiDaProvare.json"
PROGRAMMA_DI_CLAUDE = Path.home() / ".local" / "bin" / "claude.exe"
GRAFFA = re.compile(r"\{(\w+)\}")
GRAFFA_DI_PROVA = re.compile(r"\s*\[prova:[^\]]*\]")
# graffe che riempie la fabbrica da sola (recensioni, nome, contatti): non si chiedono al materiale
GRAFFE_DELLA_FABBRICA = {"nomestruttura", "nomeBreve", "telefono", "telefonoLink", "email", "whatsapp", "annoCorrente",
                         "recensioneInEvidenza", "testoDellaRecensione", "recensione2", "recensione3",
                         "testoRecensione1", "testoRecensione2", "testoRecensione3", "testoRecensione4", "testoRecensione5", "testoRecensione6", "voto"} | {f"stelleRecensione{n}" for n in range(1, 7)}


def materialePerClaude(datiUnici, recensioni, regole):
    unicita = datiUnici.get("unicita") or {}
    scheda = datiUnici.get("schedaGoogle") or {}
    return {"sitoDelCliente": datiUnici.get("sitoAttuale") or "",
            "rapportoDiUnicita": {"sintesi": unicita.get("sintesi"), "settori": unicita.get("settori")},
            "schedaGoogle": {chiave: valore for chiave, valore in scheda.items()
                             if chiave not in ("id", "addressComponents", "googleMapsUri", "photos")},
            "recensioni": [voce.get("testo") for voce in recensioni[:int(regole["recensioniMassime"])] if voce.get("testo")]}


CHIAVE_FREE_LLM = Path(r"C:\_02_DepthXSoftware\_01_CentroGestioneDepthX\V1.0(161126_1124)\_01_StrumentiDiLavoroPerIlServer\_01_ChiaviAccessiServiziTerzeParti\_11_FreeLLMAPI\_01_ChiaveUnica.txt")
MODELLI_GRATUITI = ("nemotron-3.5-super-vl", "auto")


def chiediAFreeLLM(istruzioni, immagini=(), secondi=90):
    """I modelli gratuiti di FreeLLMAPI sul server, in ordine. immagini: percorsi JPG da mandare insieme alle istruzioni,
    nell'ordine in cui le istruzioni le nominano. Restituisce l'oggetto JSON della risposta, o None.
    Lo usano anche le categorie delle foto (4.1), il product manager (8.2) e la correzione (8.4)."""
    import base64
    import urllib.request
    try:
        chiave = CHIAVE_FREE_LLM.read_text(encoding="utf-8").strip()
    except OSError:
        return None
    contenuto = istruzioni
    if immagini:
        contenuto = [{"type": "text", "text": istruzioni}]
        for percorso in immagini:
            dati = base64.b64encode(Path(percorso).read_bytes()).decode()
            contenuto.append({"type": "image_url", "image_url": {"url": "data:image/jpeg;base64," + dati}})
    for modello in MODELLI_GRATUITI:
        corpo = json.dumps({"model": modello, "temperature": 0.2, "messages": [
            {"role": "system", "content": "Rispondi solo con un oggetto JSON valido, in italiano, senza altro testo."},
            {"role": "user", "content": contenuto}]}).encode("utf-8")
        richiesta = urllib.request.Request("http://127.0.0.1:3001/v1/chat/completions", data=corpo, method="POST",
                                           headers={"Authorization": "Bearer " + chiave, "Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(richiesta, timeout=secondi) as risposta:
                testo = json.loads(risposta.read().decode("utf-8"))["choices"][0]["message"]["content"]
            return json.loads(re.search(r"\{.*\}", testo, re.S).group(0))
        except Exception:
            continue
    return None


def chiediAClaude(istruzioni, regole):
    """Una sola chiamata, senza strumenti: prima FreeLLMAPI, poi Claude sul server. Restituisce l'oggetto JSON della risposta, o None."""
    gratuito = chiediAFreeLLM(istruzioni)
    if isinstance(gratuito, dict):
        return gratuito
    programma = shutil.which("claude") or (str(PROGRAMMA_DI_CLAUDE) if PROGRAMMA_DI_CLAUDE.is_file() else "")
    if not programma:
        raise RuntimeError("Claude non è installato sul server")
    with tempfile.TemporaryDirectory(prefix="dxfatti_", ignore_cleanup_errors=True) as corta:
        try:
            esito = subprocess.run([programma, "-p", "--model", regole["modello"], "--max-turns", "1",
                                    "--output-format", "json"], input=istruzioni, capture_output=True, text=True,
                                   encoding="utf-8", errors="ignore", cwd=corta, timeout=int(regole["secondiMassimi"]),
                                   creationflags=subprocess.CREATE_NO_WINDOW)
        except subprocess.TimeoutExpired:
            return None
    try:
        risposta = json.loads(esito.stdout).get("result", "")
        return json.loads(re.search(r"\{.*\}", risposta, re.S).group(0))
    except (ValueError, AttributeError):
        return None


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
    materiale = materialePerClaude(datiUnici, recensioni, regole)
    istruzioni = (FILE_DELLE_ISTRUZIONI.read_text(encoding="utf-8-sig")
                  .replace("{materiale}", json.dumps(materiale, ensure_ascii=False, indent=1))
                  .replace("{fatti}", "\n".join(f"{chiave}: {descrizioni.get(chiave, chiave)}" for chiave in daProvare) or "nessuno")
                  .replace("{graffe}", "\n".join(f"{{{graffa}}}: {esempio}" for graffa, esempio in sorted(esempi.items())) or "nessuna"))
    trovati = chiediAClaude(istruzioni, regole)
    if trovati is None:
        return {"provati": {}, "dati": {}}
    provati = {chiave: {"citazione": str(voce.get("citazione", ""))[:300], "fonte": str(voce.get("fonte", ""))[:80]}
               for chiave, voce in (trovati.get("provati") or {}).items()
               if chiave in daProvare and isinstance(voce, dict) and voce.get("citazione")}
    dati = {graffa: {"valore": " ".join(str(voce.get("valore", "")).split())[:120],
                     "citazione": str(voce.get("citazione", ""))[:300], "fonte": str(voce.get("fonte", ""))[:80]}
            for graffa, voce in (trovati.get("dati") or {}).items()
            if graffa.strip("{}") in esempi and isinstance(voce, dict) and voce.get("valore") and voce.get("citazione")}
    return {"provati": provati, "dati": {graffa.strip("{}"): voce for graffa, voce in dati.items()}}

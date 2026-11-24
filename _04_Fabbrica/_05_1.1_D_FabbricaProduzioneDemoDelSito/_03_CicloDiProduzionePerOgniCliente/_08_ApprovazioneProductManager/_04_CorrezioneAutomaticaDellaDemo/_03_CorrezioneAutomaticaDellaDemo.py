"""Passo 8.4: la correzione del product manager, sulla demo che non è passata al collaudo (passo 7) o al product manager (passo 8).

Nessun cliente resta fermo con un NOTGO (Michele, 8/11/2026). I problemi del collaudo e i punti della checklist che il product
manager non ha fatto passare vanno ai modelli gratuiti di FreeLLMAPI, con le ripetizioni, con le istruzioni di
_02_IstruzioniPerLaCorrezione.md. La correzione lavora in una cartella dal percorso corto, con le pagine, gli
stili e gli script della demo, le sole frasi verificate del cliente (passo 5.8.4) e le parole vietate. I file cambiati tornano nel sito; il coordinatore poi ripubblica e ricontrolla la demo.
Restituisce i problemi, cosa è stato corretto, cosa no e i file cambiati. Se nessun modello risponde dopo le ripetizioni,
NOTGO di sistema: il passo si rifà al giro dopo.
"""

import json
import re
import shutil
import tempfile
from pathlib import Path

CARTELLA = Path(__file__).absolute().parent
FILE_DELLE_REGOLE = CARTELLA / "_01_RegoleDellaCorrezione.json"
FILE_DELLE_ISTRUZIONI = CARTELLA / "_02_IstruzioniPerLaCorrezione.md"
CICLO = CARTELLA.parents[1]
PAROLE_VIETATE = (CICLO / "_07_CollaudoBasicoDellaDemo" / "_02_ControlloCheNonCiSiaNessunaParolaVietata"
                  / "_01_ParoleVietateNeiTestiDelleDemo.json")
DA_CORREGGERE = ("*.html", "assets/css/*.css", "assets/js/*.js")
# la correzione non toglie mai niente (Michele, 9/11/2026): sezioni, foto con il loro file, voci del menu e paragrafi si contano prima e dopo
CONTEGGI = {"sezioni": r"<section\b", "foto": r"\bdata-scena=\"[^\"]+\"","voci del menu": r"<a\b[^>]*href=\"#[^\"]+\"",
            "paragrafi": r"<p\b"}


def conteggiDellaPagina(cartella):
    testo = "".join(file.read_text(encoding="utf-8", errors="ignore") for file in Path(cartella).glob("*.html"))
    return {nome: len(re.findall(modello, testo, re.I)) for nome, modello in CONTEGGI.items()}


def problemiDaCorreggere(collaudo, approvazione):
    problemi = []
    for controllo, voci in ((collaudo or {}).get("controlli") or {}).items():
        problemi += [f"collaudo, {controllo}: {voce}" for voce in voci or []]
    for cosa, voci in ((approvazione or {}).get("note") or {}).items():
        problemi += [f"product manager, {cosa}: {voce}" for voce in voci or []]
    return problemi


CARATTERI_MASSIMI_PER_FILE = 40000


def correzioneDaiModelliGratuiti(istruzioni, problemi, cartellaSito):
    """La correzione da FreeLLMAPI. Il modello riceve le pagine nominate nei problemi (o la home), il primo foglio di stile,
    le frasi verificate e le parole vietate, e restituisce le modifiche esatte {file, cerca, sostituisci}. Ogni modifica si
    applica solo se il testo cercato compare una sola volta nel file. Il resoconto {corretti, nonCorretti}."""
    from _03_CicloDiProduzionePerOgniCliente._05_PersonalizzazioneDelTemplateConLidentitàDelCliente._08_TestiPerOgniCliente._04_CompletaLaFraseConIFattiVeriDelCliente._07_FattiProvatiDalMaterialeDelCliente import chiediAFreeLLM
    cartellaSito = Path(cartellaSito)
    pagine = sorted({nome for problema in problemi for nome in re.findall(r"[\w-]+\.html", problema)
                     if (cartellaSito / nome).is_file()}) or ["index.html"]
    stili = sorted(str(file.relative_to(cartellaSito)).replace("\\", "/") for file in cartellaSito.glob("assets/css/*.css"))[:1]
    file = [nome for nome in pagine + stili if (cartellaSito / nome).is_file()]
    allegati = "\n\n".join(f"=== FILE {nome} ===\n" + (cartellaSito / nome).read_text(encoding="utf-8", errors="ignore")[:CARATTERI_MASSIMI_PER_FILE]
                           for nome in file)
    extra = (cartellaSito.parent / "frasiVerificate.json").read_text(encoding="utf-8", errors="ignore")[:12000]
    vietate = (cartellaSito.parent / "paroleVietate.json").read_text(encoding="utf-8", errors="ignore")[:4000]
    testo = (istruzioni.replace("Lavora con gli strumenti Read, Glob, Grep ed Edit.", "Non hai strumenti: i file sono qui sotto.")
             + "\n\nfrasiVerificate.json:\n" + extra + "\n\nparoleVietate.json:\n" + vietate + "\n\nI file della demo:\n" + allegati
             + "\n\nRispondi con un solo oggetto JSON: {\"modifiche\": [{\"file\": \"nome del file\", \"cerca\": \"testo copiato esattamente dal file, "
               "che compare una sola volta\", \"sostituisci\": \"testo nuovo\"}], \"corretti\": [...], \"nonCorretti\": [...]}.")
    risposta = chiediAFreeLLM(testo, (), 330, valida=lambda r: isinstance(r.get("modifiche"), list))
    applicate, scartate = 0, []
    for modifica in risposta["modifiche"]:
        if not isinstance(modifica, dict):
            continue
        nome, cerca, nuovo = str(modifica.get("file") or ""), str(modifica.get("cerca") or ""), str(modifica.get("sostituisci") or "")
        bersaglio = cartellaSito / nome
        if nome not in file or not cerca or not bersaglio.is_file():
            scartate.append(f"modifica su {nome or 'un file'} non applicata: file non valido")
            continue
        contenuto = bersaglio.read_text(encoding="utf-8", errors="ignore")
        if contenuto.count(cerca) != 1:
            scartate.append(f"modifica su {nome} non applicata: il testo cercato non compare una sola volta")
            continue
        bersaglio.write_text(contenuto.replace(cerca, nuovo, 1), encoding="utf-8")
        applicate += 1
    corretti = [str(voce) for voce in risposta.get("corretti") or []] if applicate else []
    return {"corretti": corretti, "nonCorretti": [str(voce) for voce in risposta.get("nonCorretti") or []] + scartate}


def correzioneAutomaticaDellaDemo(sito, collaudo, approvazione, testi, giriPrecedenti=()):
    regole = json.loads(FILE_DELLE_REGOLE.read_text(encoding="utf-8-sig"))
    problemi = problemiDaCorreggere(collaudo, approvazione)
    if not problemi:
        return {"problemi": [], "corretti": [], "nonCorretti": [], "fileCambiati": []}
    sito = Path(sito)
    cambiati = []
    with tempfile.TemporaryDirectory(prefix="dxcorr_", ignore_cleanup_errors=True) as corta:
        corta = Path(corta)
        copiati = {}
        for modello in DA_CORREGGERE:
            for file in sito.glob(modello):
                copia = corta / "sito" / file.relative_to(sito)
                copia.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(file, copia)
                copiati[file] = (copia, file.read_bytes())
        shutil.copy2(PAROLE_VIETATE, corta / "paroleVietate.json")
        (corta / "frasiVerificate.json").write_text(json.dumps(testi.get("verificate") or [], ensure_ascii=False, indent=1),
                                                    encoding="utf-8")
        istruzioni = FILE_DELLE_ISTRUZIONI.read_text(encoding="utf-8-sig").replace(
            "{problemi}", "\n".join(f"- {problema}" for problema in problemi)).replace(
            "{giriPrecedenti}", "\n".join(
                f"- giro {numero}: problemi: {' | '.join(giro.get('problemi') or [])}; corretto: {' | '.join(giro.get('corretti') or [])}"
                for numero, giro in enumerate(giriPrecedenti, 1)) or "- nessuno")
        # i modelli gratuiti di FreeLLMAPI restituiscono le modifiche esatte, applicate qui sulle copie con gli stessi controlli
        resoconto = correzioneDaiModelliGratuiti(istruzioni, problemi, corta / "sito")
        prima, dopo = conteggiDellaPagina(sito), conteggiDellaPagina(corta / "sito")
        tolti = [f"{nome} da {prima[nome]} a {dopo[nome]}" for nome in CONTEGGI if dopo[nome] < prima[nome]]
        if not tolti:
            for file, (copia, primaDelFile) in copiati.items():
                if copia.is_file() and copia.read_bytes() != primaDelFile:
                    shutil.copy2(copia, file)
                    cambiati.append(str(file.relative_to(sito)))
    if tolti:
        # la demo resta com'era: la correzione toglieva contenuti, e questo non si fa mai
        resoconto = {"corretti": [], "nonCorretti": ["correzione respinta perché toglieva contenuti dalla pagina (" + ", ".join(tolti) + ")"]
                     + [str(voce) for voce in resoconto.get("nonCorretti") or []]}
    return {"problemi": problemi, "corretti": [str(voce) for voce in resoconto.get("corretti") or []],
            "nonCorretti": [str(voce) for voce in resoconto.get("nonCorretti") or []], "fileCambiati": cambiati}

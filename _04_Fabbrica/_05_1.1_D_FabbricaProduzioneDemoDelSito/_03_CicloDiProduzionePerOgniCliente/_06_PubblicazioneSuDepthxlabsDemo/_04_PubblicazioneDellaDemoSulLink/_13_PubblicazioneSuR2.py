"""R2 (12/11/2026): la demo pubblicata caricando solo i suoi file nel bucket R2 "depthx-demo", senza ripubblicare il Worker.

Le risorse statiche del Worker delle demo avevano raggiunto il limite di file del piano gratuito di Cloudflare (errore 10304):
ora il Worker (_01_PercorsoDelleDemoSuCloudflare/worker.js, binding DEMO) legge i file da R2.
1. i file della demo vanno in R2 con lo stesso percorso: "<nome>/<file>";
2. per ultimo l'elenco della demo ".manifesti/<nome>.json" ({"file": {"/index.html": [impronta, tipo], ...}}): appena c'è,
   il Worker serve la demo nuova. L'impronta è quella di wrangler (_10_ImprontaDeiFile.js), così gli ETag non cambiano;
3. i file di una versione vecchia della stessa demo che non ci sono più escono da R2.
Una demo scaduta esce da R2 con togliLaDemoDaR2 (prima l'elenco, poi i file).
Se R2 non risponde, il passo dà NOTGO con il motivo: niente ritorno a wrangler deploy, che riempirebbe di nuovo le risorse.
Spesa: piano gratuito R2 (10 GB, 1 milione di scritture al mese): ogni demo costa un caricamento per file più l'elenco.
"""

import hashlib
import json
import urllib.parse
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from .._02_CopiaNellaCartellaDiPubblicazione._01_CopiaNellaCartellaDiPubblicazione import CARTELLA_DI_PUBBLICAZIONE
import time

from ._09_ApiDiCloudflare import ACCOUNT, ErroreDiCloudflare, chiamata
from ._11_PubblicazioneDirettaDelWorker import MASSIMO_PER_FILE, TIPI, calcolaLeImpronte

BUCKET = "depthx-demo"
CARTELLA_DEI_MANIFESTI = ".manifesti/"
CONTEMPORANEI = 4


def tipoDelFileSuR2(percorso):
    """Il Content-Type che dava il server delle risorse del Worker (senza charset)."""
    ultimo = percorso.rsplit("/", 1)[-1]
    return TIPI.get(ultimo.rsplit(".", 1)[-1].lower() if "." in ultimo else "") or "application/octet-stream"


def indirizzoDellOggetto(chiave):
    return f"/accounts/{ACCOUNT}/r2/buckets/{BUCKET}/objects/" + urllib.parse.quote(chiave, safe="/")


def chiamataPaziente(*argomenti, **opzioni):
    """Le API di Cloudflare ammettono 1.200 chiamate ogni 5 minuti per tutto l'account: se il limite è pieno (429),
    si aspetta un minuto e si riprova, fino a 3 volte, prima di dare NOTGO."""
    for volta in range(4):
        try:
            return chiamata(*argomenti, **opzioni)
        except ErroreDiCloudflare as errore:
            if errore.stato != 429 or volta == 3:
                raise
            time.sleep(60)


def caricaSuR2(chiave, contenuto, tipo):
    stato, risposta = chiamataPaziente("PUT", indirizzoDellOggetto(chiave), contenuto, tipo, attesa=300)
    if stato != 200 or not (risposta or {}).get("success"):
        raise RuntimeError(f"R2 ha risposto {stato} per {chiave}")
    if ((risposta.get("result") or {}).get("etag") or "").strip('"') != hashlib.md5(contenuto).hexdigest():
        raise RuntimeError(f"R2 ha ricevuto {chiave} diverso dal file della demo")


def cancellaDaR2(chiave):
    chiamataPaziente("DELETE", indirizzoDellOggetto(chiave))


def oggettiSuR2(prefisso):
    """Le chiavi in R2 che cominciano con il prefisso."""
    chiavi, cursore = [], ""
    while True:
        domanda = urllib.parse.urlencode({"prefix": prefisso, "per_page": 1000, **({"cursor": cursore} if cursore else {})})
        _, dati = chiamataPaziente("GET", f"/accounts/{ACCOUNT}/r2/buckets/{BUCKET}/objects?{domanda}")
        chiavi += [voce["key"] for voce in (dati or {}).get("result") or []]
        cursore = ((dati or {}).get("result_info") or {}).get("cursor") or ""
        if not cursore or not ((dati or {}).get("result_info") or {}).get("is_truncated", True):
            return chiavi


def fileDellaDemo(cartella):
    """[(percorso nella demo "/x/y", percorso sul disco)] di tutti i file della demo."""
    file = []
    for voce in sorted(Path(cartella).rglob("*")):
        if voce.is_file() and not voce.is_symlink():
            if voce.stat().st_size > MASSIMO_PER_FILE:
                raise RuntimeError(f"file troppo grande per la demo (max 25 MB): {voce}")
            file.append(("/" + voce.relative_to(cartella).as_posix(), str(voce)))
    return file


def pubblicazioneDellaDemoSuR2(nome, cartella=CARTELLA_DI_PUBBLICAZIONE, impronte=None):
    """Carica la demo <nome> su R2. impronte: {percorso nella demo: impronta} già calcolate (facoltativo).
    Restituisce {"versione", "fileCaricati", "fileTolti"}."""
    demo = Path(cartella) / nome
    file = fileDellaDemo(demo)
    if not any(percorso == "/index.html" for percorso, _ in file):
        raise RuntimeError(f"la demo {nome} non ha la home index.html nella cartella di pubblicazione")
    impronte = dict(impronte or {})
    mancanti = [(percorso, assoluto) for percorso, assoluto in file if not impronte.get(percorso)]
    for (percorso, _), impronta in zip(mancanti, calcolaLeImpronte([assoluto for _, assoluto in mancanti])):
        impronte[percorso] = impronta
    manifesto = {"file": {percorso: [impronte[percorso], tipoDelFileSuR2(percorso)] for percorso, _ in file}}
    try:
        with ThreadPoolExecutor(CONTEMPORANEI) as squadra:
            list(squadra.map(lambda voce: caricaSuR2(nome + voce[0], Path(voce[1]).read_bytes(), tipoDelFileSuR2(voce[0])), file))
        caricaSuR2(CARTELLA_DEI_MANIFESTI + nome + ".json", json.dumps(manifesto, separators=(",", ":")).encode("utf-8"),
                   "application/json")
    except Exception as errore:
        raise RuntimeError(f"R2 di Cloudflare non risponde, la demo {nome} non è stata caricata: {errore}"[:600]) from errore
    tolti = []
    try:  # i file della versione di prima che non ci sono più (non blocca la demo nuova, già online)
        validi = {nome + percorso for percorso, _ in file}
        tolti = [chiave for chiave in oggettiSuR2(nome + "/") if chiave not in validi]
        with ThreadPoolExecutor(CONTEMPORANEI) as squadra:
            list(squadra.map(cancellaDaR2, tolti))
    except Exception as errore:
        print(f"file vecchi della demo {nome} non tolti da R2: {errore}"[:400])
    return {"versione": f"R2 {BUCKET}: {len(file)} file", "fileCaricati": len(file), "fileTolti": len(tolti)}


def togliLaDemoDaR2(nome):
    """La demo scaduta esce da R2: prima l'elenco (il Worker smette di servirla), poi i file."""
    try:
        cancellaDaR2(CARTELLA_DEI_MANIFESTI + nome + ".json")
        chiavi = oggettiSuR2(nome + "/")
        with ThreadPoolExecutor(CONTEMPORANEI) as squadra:
            list(squadra.map(cancellaDaR2, chiavi))
    except Exception as errore:
        raise RuntimeError(f"R2 di Cloudflare non risponde, la demo scaduta {nome} non è stata tolta: {errore}"[:600]) from errore
    return len(chiavi)

"""Pitstop 4 (task #609, 12/11/2026): il Worker delle demo pubblicato con le chiamate dirette alle API di Cloudflare.

Fa le stesse cose di "wrangler deploy", ma in pochi secondi:
1. l'elenco di tutti i file della cartella di pubblicazione con la loro impronta (calcolata come wrangler); le impronte si tengono
   in _12_ImpronteDeiFile.json, così si calcolano solo per i file nuovi o cambiati;
2. Cloudflare riceve l'elenco e chiede solo i file che non ha già: si caricano solo quelli (in pratica la demo nuova);
3. il Worker (lo stesso worker.js, le stesse impostazioni di wrangler.toml, lo stesso _headers) si pubblica con le risorse nuove.
Le demo già online restano identiche: stessi file, stesse impronte, stesso Worker. Restituisce la versione pubblicata.
"""

import base64
import json
import os
import re
import subprocess
import tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from .._02_CopiaNellaCartellaDiPubblicazione._01_CopiaNellaCartellaDiPubblicazione import CARTELLA_DI_PUBBLICAZIONE
from ._02_ProgrammaWrangler import CARTELLA_DEL_WORKER
from ._09_ApiDiCloudflare import ACCOUNT, ErroreDiCloudflare, chiamata, moduloMultipart

QUI = Path(__file__).absolute().parent
PROGRAMMA_DELLE_IMPRONTE = QUI / "_10_ImprontaDeiFile.js"
FILE_DELLE_IMPRONTE = QUI / "_12_ImpronteDeiFile.json"
BLAKE3 = Path(os.environ.get("APPDATA", "")) / "npm" / "node_modules" / "wrangler" / "node_modules" / "blake3-wasm"
FILE_SPECIALI = {"/_headers", "/_redirects", "/.assetsignore"}  # wrangler non li carica come risorse
MASSIMO_PER_FILE = 25 * 1024 * 1024
# i tipi che wrangler 4 dà ai file (pacchetto mime), con "; charset=utf-8" per i testi
TIPI = {"html": "text/html", "htm": "text/html", "css": "text/css", "js": "text/javascript", "mjs": "text/javascript",
        "txt": "text/plain", "xml": "text/xml", "csv": "text/csv", "json": "application/json", "svg": "image/svg+xml",
        "jpg": "image/jpeg", "jpeg": "image/jpeg", "png": "image/png", "webp": "image/webp", "gif": "image/gif",
        "avif": "image/avif", "ico": "image/vnd.microsoft.icon", "woff2": "font/woff2", "woff": "font/woff", "ttf": "font/ttf",
        "otf": "font/otf", "mp4": "video/mp4", "webm": "video/webm", "pdf": "application/pdf", "webmanifest": "application/manifest+json"}


def tipoDelFile(percorso):
    tipo = TIPI.get(percorso.rsplit(".", 1)[-1].lower() if "." in percorso.rsplit("/", 1)[-1] else "")
    return (tipo + "; charset=utf-8" if tipo and tipo.startswith("text/") else tipo) or "application/null"


def leggiLeImpronte():
    try:
        return json.loads(FILE_DELLE_IMPRONTE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def salvaLeImpronte(impronte):
    descrittore, provvisorio = tempfile.mkstemp(dir=QUI, suffix=".tmp")
    with os.fdopen(descrittore, "w", encoding="utf-8") as uscita:
        json.dump(impronte, uscita, separators=(",", ":"))
    os.replace(provvisorio, FILE_DELLE_IMPRONTE)


def calcolaLeImpronte(file):
    if not file:
        return []
    esito = subprocess.run(["node", str(PROGRAMMA_DELLE_IMPRONTE), str(BLAKE3)], input=json.dumps(file), capture_output=True,
                           text=True, encoding="utf-8", timeout=900, creationflags=subprocess.CREATE_NO_WINDOW)
    if esito.returncode != 0:
        raise RuntimeError("impronte dei file non calcolate: " + esito.stderr.strip()[-300:])
    return json.loads(esito.stdout)


def elencoDelleRisorse(cartella):
    """{"/nome/file": {"hash", "size"}} di tutta la cartella, come lo costruisce wrangler."""
    vecchie, nuove, daCalcolare = leggiLeImpronte(), {}, []
    cartelle = [(str(cartella), "")]
    while cartelle:
        radice, prefisso = cartelle.pop()
        with os.scandir(radice) as voci:
            for voce in voci:
                percorso = prefisso + "/" + voce.name
                if voce.is_dir(follow_symlinks=False):
                    cartelle.append((voce.path, percorso))
                    continue
                if voce.is_symlink() or percorso in FILE_SPECIALI:
                    continue
                stato = voce.stat()
                if stato.st_size > MASSIMO_PER_FILE:
                    raise RuntimeError(f"file troppo grande per Cloudflare (max 25 MB): {percorso}")
                segno = [stato.st_size, stato.st_mtime_ns]
                vecchia = vecchie.get(percorso)
                if vecchia and vecchia[:2] == segno:
                    nuove[percorso] = vecchia
                else:
                    nuove[percorso] = segno + [None]
                    daCalcolare.append((percorso, voce.path))
    for (percorso, _), impronta in zip(daCalcolare, calcolaLeImpronte([assoluto for _, assoluto in daCalcolare])):
        nuove[percorso][2] = impronta
    salvaLeImpronte(nuove)
    return {percorso: {"hash": voce[2], "size": voce[0]} for percorso, voce in nuove.items()}


def datiDelGettone(gettone):
    try:
        parte = gettone.split(".")[1]
        return json.loads(base64.urlsafe_b64decode(parte + "=" * (-len(parte) % 4)))
    except (IndexError, ValueError):
        return {}


def caricaLeRisorseNuove(cartella, elenco, sessione):
    """Carica i file che Cloudflare non ha ancora; restituisce (gettone finale, file caricati)."""
    gettone, gruppi = sessione["jwt"], [gruppo for gruppo in sessione.get("buckets") or [] if gruppo]
    if not gruppi:
        return gettone, 0
    perImpronta = {voce["hash"]: percorso for percorso, voce in elenco.items()}
    assoluto = lambda impronta: os.path.join(cartella, *perImpronta[impronta].lstrip("/").split("/"))
    intestazioni = {"Authorization": "Bearer " + gettone}
    if datiDelGettone(gettone).get("wrangler_single_asset_uploads") is True:
        carica = lambda lavoro: chiamata("POST", f"/accounts/{ACCOUNT}/workers/assets/upload/{lavoro[0]}",
                                         Path(assoluto(lavoro[0])).read_bytes(), tipoDelFile(perImpronta[lavoro[0]]),
                                         intestazioni, chiave=gettone)[1]
        lavori, contemporanei = [[impronta] for gruppo in gruppi for impronta in gruppo], 20
    else:
        def carica(gruppo):
            corpo, tipo = moduloMultipart([(impronta, base64.b64encode(Path(assoluto(impronta)).read_bytes()), impronta,
                                            tipoDelFile(perImpronta[impronta])) for impronta in gruppo])
            return chiamata("POST", f"/accounts/{ACCOUNT}/workers/assets/upload?base64=true", corpo, tipo, intestazioni,
                            chiave=gettone, attesa=300)[1]
        lavori, contemporanei = gruppi, 3
    finale = ""
    with ThreadPoolExecutor(contemporanei) as squadra:
        for risposta in squadra.map(carica, lavori):
            finale = ((risposta or {}).get("result") or {}).get("jwt") or finale
    if not finale:
        raise RuntimeError("Cloudflare non ha confermato il caricamento dei file delle demo")
    return finale, sum(len(gruppo) for gruppo in gruppi)


def impostazioniDelWorker():
    """Nome, data di compatibilità, binding del KV e run_worker_first da wrangler.toml."""
    testo = (CARTELLA_DEL_WORKER / "wrangler.toml").read_text(encoding="utf-8-sig")
    valore = lambda chiave: re.search(rf'^{chiave} = "([^"]*)"', testo, re.M).group(1)
    kv = re.search(r'\[\[kv_namespaces\]\]\s*binding = "([^"]+)"\s*id = "([^"]+)"', testo)
    return {"nome": valore("name"), "data": valore("compatibility_date"), "risorse": valore("binding"),
            "kv": (kv.group(1), kv.group(2)), "primaIlWorker": re.search(r"^run_worker_first = true", testo, re.M) is not None}


def pubblicazioneDirettaDelWorker(cartella=CARTELLA_DI_PUBBLICAZIONE):
    """Restituisce {"versione", "fileCaricati", "fileTotali"}."""
    impostazioni = impostazioniDelWorker()
    elenco = elencoDelleRisorse(cartella)
    _, sessione = chiamata("POST", f"/accounts/{ACCOUNT}/workers/scripts/{impostazioni['nome']}/assets-upload-session",
                           {"manifest": elenco}, attesa=300)
    gettone, caricati = caricaLeRisorseNuove(cartella, elenco, sessione["result"])
    intestazioni = Path(cartella) / "_headers"
    configurazione = {"run_worker_first": impostazioni["primaIlWorker"],
                      **({"_headers": intestazioni.read_text(encoding="utf-8")} if intestazioni.is_file() else {})}
    regole = Path(cartella) / "_redirects"
    if regole.is_file():
        configurazione["_redirects"] = regole.read_text(encoding="utf-8")
    dati = {"main_module": "worker.js", "compatibility_date": impostazioni["data"],
            "bindings": [{"type": "assets", "name": impostazioni["risorse"]},
                         {"type": "kv_namespace", "name": impostazioni["kv"][0], "namespace_id": impostazioni["kv"][1]}],
            "assets": {"jwt": gettone, "config": configurazione}}
    corpo, tipo = moduloMultipart([("metadata", json.dumps(dati).encode("utf-8"), None, None),
                                   ("worker.js", (CARTELLA_DEL_WORKER / "worker.js").read_bytes(), "worker.js",
                                    "application/javascript+module")])
    try:
        _, risposta = chiamata("PUT", f"/accounts/{ACCOUNT}/workers/scripts/{impostazioni['nome']}", corpo, tipo, attesa=300)
    except ErroreDiCloudflare as errore:
        raise RuntimeError(f"pubblicazione del Worker non riuscita: {errore}")
    risultato = risposta.get("result") or {}
    versione = risultato.get("deployment_id") or (risultato.get("version") or {}).get("id") or risultato.get("etag") or ""
    if re.fullmatch(r"[0-9a-f]{32}", versione):  # come la scriveva wrangler: 8-4-4-4-12
        versione = "-".join((versione[:8], versione[8:12], versione[12:16], versione[16:20], versione[20:]))
    return {"versione": versione, "fileCaricati": caricati, "fileTotali": len(elenco)}

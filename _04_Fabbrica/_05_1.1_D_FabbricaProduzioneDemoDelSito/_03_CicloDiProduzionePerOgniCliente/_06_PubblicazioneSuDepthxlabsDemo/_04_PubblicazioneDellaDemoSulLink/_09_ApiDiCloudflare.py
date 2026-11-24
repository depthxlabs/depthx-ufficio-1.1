"""Pitstop 4 (task #609, 12/11/2026): le chiamate dirette alle API di Cloudflare, senza avviare wrangler ogni volta.

L'accesso è quello di wrangler sul server (il file default.toml del login di wrangler): se sta per scadere, si lancia una volta
"wrangler whoami", che lo rinnova e lo riscrive, poi si rilegge. Così wrangler e queste chiamate usano sempre lo stesso accesso.
Un errore momentaneo (rete, 429, 5xx) si riprova fino a 5 volte in tutto, con un'attesa che cresce (Michele, 8/11/2026).
"""

import datetime
import json
import os
import re
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
from pathlib import Path

from ._02_ProgrammaWrangler import programmaWrangler

ACCOUNT = "2a0fa6b4d9517975f6c76b95a5d87a47"
REGISTRO_DELLE_DEMO = "d020f4c03f0b4b1dbf63fbe5ec6f1433"  # il KV TRACCIAMENTO di wrangler.toml
INDIRIZZO = "https://api.cloudflare.com/client/v4"
FILE_DELL_ACCESSO = Path(os.environ.get("APPDATA", "")) / "xdg.config" / ".wrangler" / "config" / "default.toml"
TENTATIVI = 5


class ErroreDiCloudflare(RuntimeError):
    def __init__(self, stato, testo):
        super().__init__(f"Cloudflare {stato}: {testo[-300:]}")
        self.stato = stato


def accessoDiWrangler():
    testo = FILE_DELL_ACCESSO.read_text(encoding="utf-8")
    chiave = re.search(r'^oauth_token = "([^"]+)"', testo, re.M)
    scadenza = re.search(r'^expiration_time = "([^"]+)"', testo, re.M)
    if not chiave:
        raise RuntimeError("accesso di wrangler a Cloudflare non trovato sul server")
    fine = datetime.datetime.fromisoformat(scadenza.group(1).replace("Z", "+00:00")) if scadenza else None
    return chiave.group(1), fine


# Sulle macchine di GitHub la fabbrica usa il token API di Cloudflare (segreto CLOUDFLARE_API_TOKEN): più macchine insieme
# rinnoverebbero a turno l'accesso di wrangler e si annullerebbero a vicenda.
TOKEN_API = os.environ.get("CLOUDFLARE_API_TOKEN", "").strip()
SU_GITHUB = os.environ.get("GITHUB_ACTIONS") == "true"


def chiaveDiAccesso(rinnova=False):
    if TOKEN_API:
        return TOKEN_API
    chiave, fine = accessoDiWrangler()
    quasiScaduta = fine is not None and fine <= datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(minutes=3)
    if rinnova or quasiScaduta:
        programmaWrangler("whoami", attesa=120)  # wrangler rinnova l'accesso e lo riscrive in default.toml
        chiave, _ = accessoDiWrangler()
    return chiave


def chiamata(metodo, percorso, corpo=None, tipo="application/json", intestazioni=None, chiave=None, grezza=False, attesa=120):
    """Una chiamata alle API di Cloudflare. Restituisce (stato, risposta); 404 non è un errore, il resto sì."""
    if isinstance(corpo, (dict, list)):
        corpo = json.dumps(corpo).encode("utf-8")
    rinnovata = chiave is not None
    for volta in range(TENTATIVI):
        segreto = chiave or chiaveDiAccesso()
        richiesta = urllib.request.Request(INDIRIZZO + percorso, data=corpo, method=metodo,
                                           headers={"Authorization": "Bearer " + segreto, **({"Content-Type": tipo} if corpo is not None else {}),
                                                    **(intestazioni or {})})
        try:
            with urllib.request.urlopen(richiesta, timeout=attesa) as risposta:
                dati = risposta.read()
                return risposta.status, (dati if grezza else json.loads(dati or b"null"))
        except urllib.error.HTTPError as errore:
            dati = errore.read()
            if errore.code == 404:
                return 404, None
            if errore.code in (401, 403) and not rinnovata:
                chiaveDiAccesso(rinnova=True)
                rinnovata = True
                continue
            if errore.code != 429 and errore.code < 500 or volta == TENTATIVI - 1:
                raise ErroreDiCloudflare(errore.code, dati.decode("utf-8", "ignore"))
        except (urllib.error.URLError, TimeoutError, OSError) as errore:
            if volta == TENTATIVI - 1:
                raise ErroreDiCloudflare(0, str(errore))
        time.sleep(3 * (volta + 1))


def moduloMultipart(parti):
    """parti: lista di (nome, contenuto in byte, nome del file o None, tipo o None). Restituisce (corpo, tipo)."""
    confine = "dx" + uuid.uuid4().hex
    corpo = bytearray()
    for nome, contenuto, nomeDelFile, tipo in parti:
        corpo += f"--{confine}\r\nContent-Disposition: form-data; name=\"{nome}\"".encode()
        if nomeDelFile:
            corpo += f"; filename=\"{nomeDelFile}\"".encode()
        corpo += b"\r\n"
        if tipo:
            corpo += f"Content-Type: {tipo}\r\n".encode()
        corpo += b"\r\n" + contenuto + b"\r\n"
    corpo += f"--{confine}--\r\n".encode()
    return bytes(corpo), f"multipart/form-data; boundary={confine}"


# Il registro delle demo (schede demo:<nome> con cliente, pubblicazione, scadenza, invio) sta in un file dedicato sul server,
# _05_RegistroDelleDemoPubblicate\_01_RegistroDelleDemo.json: letture e elenchi senza limiti. Ogni scheda scritta si copia anche su R2 (.registro/<chiave>.json),
# dove la legge il Worker delle demo. Il vecchio registro KV di Cloudflare accetta 1.000 scritture al giorno nel piano gratuito:
# resta solo come riserva in lettura, per le schede non ancora nel file.
CARTELLA_DEL_REGISTRO = Path(r"C:\_01_DepthX\_01_Linea1_ProductionDepartement\_01_Linea_1.1_OUTBOUND_WEBSITES\_05_1.1_D_FabbricaProduzioneDemoDelSito\_05_RegistroDelleDemoPubblicate")
FILE_DEL_REGISTRO = CARTELLA_DEL_REGISTRO / "_01_RegistroDelleDemo.json"
BLOCCO_DEL_REGISTRO = CARTELLA_DEL_REGISTRO / "_02_RegistroDelleDemoInScrittura.blocco"
BUCKET_DELLE_DEMO = "depthx-demo"


def chiaveDelRegistro(chiave):
    return f"/accounts/{ACCOUNT}/storage/kv/namespaces/{REGISTRO_DELLE_DEMO}/values/" + urllib.parse.quote(chiave, safe="")


def oggettoDelRegistroSuR2(chiave):
    return f"/accounts/{ACCOUNT}/r2/buckets/{BUCKET_DELLE_DEMO}/objects/" + urllib.parse.quote(f".registro/{chiave}.json", safe="/")


class _BloccoDelRegistro:
    """Un solo programma alla volta scrive il file del registro (le fabbriche e il pannello lavorano insieme)."""
    def __enter__(self):
        for _ in range(600):
            try:
                self.numero = os.open(BLOCCO_DEL_REGISTRO, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
                return self
            except FileExistsError:
                try:
                    if time.time() - BLOCCO_DEL_REGISTRO.stat().st_mtime > 120:
                        BLOCCO_DEL_REGISTRO.unlink()   # un blocco rimasto da un programma fermato
                except OSError:
                    pass
                time.sleep(0.1)
        raise RuntimeError("registro delle demo occupato da oltre 60 secondi")

    def __exit__(self, *errore):
        os.close(self.numero)
        try:
            BLOCCO_DEL_REGISTRO.unlink()
        except OSError:
            pass


def _leggiIlFile():
    for _ in range(20):
        try:
            return json.loads(FILE_DEL_REGISTRO.read_text(encoding="utf-8")) if FILE_DEL_REGISTRO.exists() else {}
        except (OSError, ValueError):
            time.sleep(0.1)
    return {}


def _scriviIlFile(dati):
    provvisorio = FILE_DEL_REGISTRO.with_name(f"{FILE_DEL_REGISTRO.name}.{os.getpid()}.tmp")
    provvisorio.write_text(json.dumps(dati, ensure_ascii=False), encoding="utf-8")
    os.replace(provvisorio, FILE_DEL_REGISTRO)


def _copiaSuR2(chiave, voce):
    chiamata("PUT", oggettoDelRegistroSuR2(chiave), json.dumps(voce, ensure_ascii=False).encode("utf-8"), "application/json")


def leggiDalRegistro(chiave):
    """Il valore JSON della chiave nel registro delle demo, o None se non c'è."""
    voce = _leggiIlFile().get(chiave)
    if voce is not None:
        return voce.get("valore")
    if SU_GITHUB:
        # su GitHub il file del registro non c'è: la scheda si legge dalla sua copia su R2, la stessa che legge il Worker
        stato, dati = chiamata("GET", oggettoDelRegistroSuR2(chiave), grezza=True)
        return None if stato == 404 else (json.loads(dati) or {}).get("valore")
    # riserva: una scheda scritta prima del file si legge una volta dal vecchio registro e da quel momento sta nel file e su R2
    try:
        stato, dati = chiamata("GET", chiaveDelRegistro(chiave), grezza=True)
    except Exception:
        return None
    if stato == 404:
        return None
    valore = json.loads(dati)
    with _BloccoDelRegistro():
        tutti = _leggiIlFile()
        tutti.setdefault(chiave, {"valore": valore, "metadata": None})
        _scriviIlFile(tutti)
    try:
        _copiaSuR2(chiave, tutti[chiave])
    except Exception:
        pass
    return valore


def scriviNelRegistro(chiave, valore, etichetta=None):
    with _BloccoDelRegistro():
        tutti = _leggiIlFile()
        tutti[chiave] = {"valore": valore, "metadata": etichetta}
        _scriviIlFile(tutti)
    _copiaSuR2(chiave, tutti[chiave])


def chiaviDelRegistro(prefisso):
    """Tutte le chiavi del registro con quel prefisso: [{"name": ..., "metadata": ...}]."""
    if SU_GITHUB:
        # su GitHub le chiavi si elencano dalle copie su R2 (.registro/<chiave>.json), senza le etichette
        from ._13_PubblicazioneSuR2 import oggettiSuR2
        return [{"name": nome[len(".registro/"):-len(".json")], "metadata": None} for nome in oggettiSuR2(".registro/" + prefisso)
                if nome.endswith(".json")]
    # l'etichetta è la scadenza: per le schede venute dal vecchio registro si prende dalla scheda stessa
    return [{"name": chiave, "metadata": voce.get("metadata") or {"scadenza": (voce.get("valore") or {}).get("scadenza", "")}}
            for chiave, voce in sorted(_leggiIlFile().items()) if chiave.startswith(prefisso)]

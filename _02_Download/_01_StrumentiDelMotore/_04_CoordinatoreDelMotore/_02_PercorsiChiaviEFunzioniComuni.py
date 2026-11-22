"""Parti comuni del motore unico di download del materiale clienti della Linea 1.2.

Percorsi, configurazione, chiavi (lette solo al momento dell'uso, mai mostrate),
rete con ripresa, verifica di ogni file e cartella temporanea dedicata.
"""

import sys

sys.dont_write_bytecode = True  # nessuna cartella __pycache__

import os

os.environ["PYTHONDONTWRITEBYTECODE"] = "1"


def percorsiBreviPerWindows():
    """Windows non carica le librerie compilate con percorsi oltre 260 caratteri: le cartelle di sys.path diventano nomi brevi 8.3."""
    if os.name != "nt":
        return
    import ctypes

    nomeBreve = ctypes.windll.kernel32.GetShortPathNameW
    for numero, voce in enumerate(list(sys.path)):
        if voce and len(voce) > 60 and os.path.isdir(voce):
            memoria = ctypes.create_unicode_buffer(2048)
            if nomeBreve(voce, memoria, 2048) and memoria.value:
                sys.path[numero] = memoria.value


percorsiBreviPerWindows()

import datetime
import hashlib
import json
import mimetypes
import re
import shutil
import socket
import subprocess
import time
import unicodedata
import urllib.parse

# Percorsi del motore, ricavati dalla posizione di questo file (struttura dei 6 passi decisa da Michele il 4/11/2026).
CARTELLA_DEL_COORDINATORE = os.path.dirname(os.path.abspath(__file__))
STRUMENTI_DEL_MOTORE = os.path.dirname(CARTELLA_DEL_COORDINATORE)  # _01_StrumentiDelMotore
RADICE_DEL_MOTORE = os.path.dirname(STRUMENTI_DEL_MOTORE)  # _04_1.1_C_DownloadMaterialeClienti
# il CRM su disco: sezioni, tipi e un file xlsx per blocco (S2_HOT_LOM), dove scrive anche la ricerca clienti su GitHub
CRM_SU_DISCO = os.path.join(os.path.dirname(RADICE_DEL_MOTORE), "_03_1.1_C_CRM_Clienti")
# sezioni che il motore scarica: S1, S2 e S3; S4 si lavora più avanti
SEZIONI_DA_SCARICARE = ("[01]", "[02]", "[03]")
# il nome della cartella di sezione su Drive, nell'Area 1B: una cartella per sezione, con il nome completo
SEZIONE_SU_DRIVE = {"[01] S1_ClientiSenzaSito": "[01] CRM_Section_1_ClientiSenzaSito",
                    "[02] S2_ClientiConSitoDebole": "[02] CRM_Section_2_ClientiConSitoEsistenteDebole",
                    "[03] S3_ClientiConSitoDatato": "[03] CRM_Section_3_ClientiConSitoEsistenteDatato",
                    "[04] S4_ClientiConSitoDiQualita": "[04] CRM_Section_4_ClientiConSitoEsistenteDiAltaQualità"}
LETTURA_DAL_CRM = os.path.join(RADICE_DEL_MOTORE, "_02_LetturaDalCRM")
DOWNLOAD_DALLE_FONTI = os.path.join(RADICE_DEL_MOTORE, "_03_DownloadDalleFonti")
CARICAMENTO_SU_DRIVE = os.path.join(RADICE_DEL_MOTORE, "_06_CaricamentoSuDrive")

PYTHON_DEL_MOTORE = os.path.join(STRUMENTI_DEL_MOTORE, "_01_AmbientePythonDelMotore", "Scripts", "python.exe")
CARTELLA_DELLE_CHIAVI = os.path.join(STRUMENTI_DEL_MOTORE, "_02_ChiaviDiAccessoAServiziDiTerzeParti")
FILE_DELLE_REGOLE = os.path.join(STRUMENTI_DEL_MOTORE, "_03_RegoleDelMotore", "_01_RegoleNumericheDelMotore.json")
CARTELLA_DEL_REGISTRO = os.path.join(STRUMENTI_DEL_MOTORE, "_05_RegistroEStatoDelMotore")
CARTELLA_TEMPORANEA = os.path.join(STRUMENTI_DEL_MOTORE, "_06_FileTemporaneiDelMotore")
CARTELLA_DEL_PROFILO_CHROME = os.path.join(STRUMENTI_DEL_MOTORE, "_07_ProfiloChromeDellAccountDelMotore")

SCRIPT_DI_LETTURA_DEI_FOGLI = os.path.join(LETTURA_DAL_CRM, "_01_LetturaDeiFogliDaGoogleSheets.js")
FILE_DELLE_IMPOSTAZIONI_DEL_CRM = os.path.join(LETTURA_DAL_CRM, "_03_ColonneEImpostazioniDelCrm.json")
# dal 9/11/2026 (Michele) i blocchi del CRM: sezione / tipo / blocco, letti da Drive attraverso il Centro Gestione a ogni avvio
FILE_DEI_FOGLI_DEL_CRM = os.path.join(LETTURA_DAL_CRM, "_04_ElencoDeiBlocchiDelCrm.json")
URL_DEI_BLOCCHI_DEL_CRM = "http://127.0.0.1:8787/api/crm11"
FILE_DEL_BLOCCO_DI_DOWNLOAD = os.path.join(LETTURA_DAL_CRM, "_05_BloccoDiDownloadInCorso.json")
SCRIPT_YTDLP = os.path.join(DOWNLOAD_DALLE_FONTI, "_05_VideoConYtDlp", "_02_AvvioDiYtDlpConIPercorsiBrevi.py")
FILE_DELLE_CARTELLE_DEI_CLIENTI = os.path.join(CARICAMENTO_SU_DRIVE, "_02_CartelleDeiClientiSuDrive.json")

# ogni passo ha il suo codice nella sua cartella: Python li trova tutti, in ordine
CARTELLE_DEL_CODICE = [CARTELLA_DEL_COORDINATORE, LETTURA_DAL_CRM] + [
    os.path.join(DOWNLOAD_DALLE_FONTI, nome) for nome in sorted(os.listdir(DOWNLOAD_DALLE_FONTI)) if os.path.isdir(os.path.join(DOWNLOAD_DALLE_FONTI, nome))
] + [os.path.join(RADICE_DEL_MOTORE, "_04_RiconoscimentoDelleFoto"), os.path.join(RADICE_DEL_MOTORE, "_05_RapportoDiUnicita"), CARICAMENTO_SU_DRIVE]
for cartella in CARTELLE_DEL_CODICE:
    if cartella not in sys.path:
        sys.path.append(cartella)
percorsiBreviPerWindows()

FILE_DELLE_CHIAVI = {
    "mappe": "_01_ChiaveGoogleMapsApi.md",
    "youtube": "_02_ChiaveAPIYoutube.md",
    "fogli": "_03_ChiaveGoogleSheet.json",
    "meta": "_04_TokenAccessoMetaDevelopers.md",
    "clienteDrive": "_05_AccessoGoogleDriveOAuth.json",
    "tokenDrive": "_06_TokenGoogleDrive.json",
}

AGENTE_DEL_BROWSER = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36"
CODICI_DA_RIPETERE = (408, 425, 429, 500, 502, 503, 504)
PRIORITA_BASSA = getattr(subprocess, "BELOW_NORMAL_PRIORITY_CLASS", 0)
SENZA_FINESTRA = getattr(subprocess, "CREATE_NO_WINDOW", 0)


class ChiaveMancante(Exception):
    """Una chiave manca o non è più valida: il motore si ferma e lo scrive nel registro."""


class ConsensoDriveMancante(Exception):
    """Il token di Google Drive non è valido: serve il consenso di Michele con _08_ComandiDelMotore/_02_ConsensoGoogleDriveDelMotore.cmd."""


class ElementoNonScaricabile(Exception):
    """Un elemento non si scarica con questo metodo; il messaggio dice il motivo preciso.

    definitivo: la risposta non cambia ripetendo (per esempio 404), si passa subito al metodo seguente.
    """

    def __init__(self, messaggio, definitivo=False):
        super().__init__(messaggio)
        self.definitivo = definitivo


CODICI_DEFINITIVI = (400, 401, 403, 404, 410, 451)


def leggiJson(percorso, predefinito=None):
    try:
        with open(percorso, "r", encoding="utf-8") as file:
            return json.load(file)
    except (OSError, ValueError):
        return predefinito


def scriviJsonSulDisco(percorso, oggetto):
    """Scrive un JSON in modo sicuro: prima un .tmp, poi la sostituzione."""
    os.makedirs(os.path.dirname(percorso), exist_ok=True)
    provvisorio = percorso + ".tmp"
    with open(provvisorio, "w", encoding="utf-8") as file:
        json.dump(oggetto, file, ensure_ascii=False, indent=1)
    for giro in range(20):
        try:
            os.replace(provvisorio, percorso)
            return
        except PermissionError:
            time.sleep(0.2)
    os.replace(provvisorio, percorso)


REGOLE = leggiJson(FILE_DELLE_REGOLE, {})

# Dal 2 novembre 2026 il motore legge i CRM nuovi (cartella Drive "_01_CRM Linea 1.2"): il vecchio CRM a 20 industrie
# (_01_Industrie.json) non conta più. Ogni foglio dei CRM nuovi (tipo, categoria, regione) è una "industria" del motore:
# numero a tre cifre stabile (posizione nell'elenco ordinato dei fogli), nome = percorso del foglio nella cartella dei CRM.
CRM_NUOVI = leggiJson(FILE_DELLE_IMPOSTAZIONI_DEL_CRM, {}) or {}


def _fogliDeiCrmNuovi():
    """Dal 9/11/2026 (Michele) ogni blocco del CRM è una "industria" del motore: "[01] S1_ClientiSenzaSito/[01] HOTEL (HOT)/[01] S1_HOT_LOM".
    Numero a tre cifre = posizione nell'elenco ordinato dei blocchi; nome = nome del blocco (S1_HOT_LOM); nell'Area 1B le cartelle
    dei clienti stanno sotto sezione / tipo / blocco, con gli stessi nomi del CRM."""
    elenco = leggiJson(FILE_DEI_FOGLI_DEL_CRM, []) or []
    fogli = sorted((voce for voce in elenco if voce.get("percorso")), key=lambda voce: voce["percorso"])
    tipiPerSigla = {valore.get("sigla"): valore for valore in (CRM_NUOVI.get("tipi") or {}).values()}
    voci = []
    for numero, voce in enumerate(fogli, start=1):
        parti = [parte for parte in voce["percorso"].split("/") if parte]
        blocco = re.sub(r"^\[\d+\]\s*", "", parti[-1])
        _, sigla, regione = (blocco.split("_") + ["", "", ""])[:3]
        tipo = tipiPerSigla.get(sigla, {})
        voci.append({
            "numero": f"{numero:03d}",
            "nome": blocco,
            "blocco": blocco,
            "cartellaDrive": "/".join(parti),  # nome dell'industria nel registro: sezione/tipo/blocco
            "percorsoDrive": [SEZIONE_SU_DRIVE.get(parti[0], parti[0])] + parti[1:],  # cartelle annidate nell'Area 1B: sezione con il nome completo, poi tipo e blocco
            "sezione": parti[0],
            "idCrm": voce["id"],
            "idCartellaDrive": "",
            "tipoDiCrm": parti[1] if len(parti) > 1 else "",
            "regione": regione,
            "sigla": sigla,
            "tipoDiAttivita": tipo.get("tipoDiAttivita", ""),
            "descrizioneDeiProdotti": tipo.get("descrizioneDeiProdotti", ""),
            "campiGoogleDellIndustria": list(tipo.get("campiGoogleDellIndustria", [])),
        })
    return voci


def aggiornaIBlocchiDelCrm():
    """All'avvio del coordinatore: i blocchi del CRM su disco (un file xlsx per blocco) nel file dell'elenco, solo le sezioni da scaricare.
    Restituisce il numero dei blocchi."""
    global TUTTI_I_FOGLI, INDUSTRIE
    nuovi = []
    for sezione in sorted(os.listdir(CRM_SU_DISCO)) if os.path.isdir(CRM_SU_DISCO) else []:
        if not sezione.startswith(SEZIONI_DA_SCARICARE):
            continue
        for tipo in sorted(os.listdir(os.path.join(CRM_SU_DISCO, sezione))):
            cartella = os.path.join(CRM_SU_DISCO, sezione, tipo)
            for file in sorted(os.listdir(cartella)) if os.path.isdir(cartella) else []:
                if file.endswith(".xlsx") and not file.startswith("~$"):
                    nome = file[:-5]
                    nuovi.append({"id": "disco:" + "/".join([sezione, tipo, file]), "nome": nome, "percorso": "/" + "/".join([sezione, tipo, nome])})
    if nuovi:
        scriviJsonSulDisco(FILE_DEI_FOGLI_DEL_CRM, nuovi)
    TUTTI_I_FOGLI = _fogliDeiCrmNuovi()
    INDUSTRIE = [voce for voce in TUTTI_I_FOGLI if not REGIONI or voce["regione"].lower() in REGIONI]
    return len(INDUSTRIE)


TUTTI_I_FOGLI = _fogliDeiCrmNuovi()
REGIONI = [regione.lower() for regione in CRM_NUOVI.get("regioni", [])]
INDUSTRIE = [voce for voce in TUTTI_I_FOGLI if not REGIONI or voce["regione"].lower() in REGIONI]  # solo le regioni scelte


def regola(nome):
    """Valore di una regola numerica: se manca, il motore si ferma e dice quale."""
    if nome not in REGOLE:
        raise ChiaveMancante(f"Nel file _01_StrumentiDelMotore/_03_RegoleDelMotore/_01_RegoleNumericheDelMotore.json manca la regola '{nome}'.")
    return REGOLE[nome]


# Giro del lavoratore: 1 = primo giro con i tetti di primoGiro (prima si chiudono i clienti piccoli), 2 = completamento dei PARZIALE.
GIRO = 2


def tettoDelPrimoGiro(nome):
    """Dal 9/11/2026 (Michele) un solo giro, con i tetti fissi delle regole: nessun tetto del primo giro (None)."""
    return None


def scadenzaDellaFonte(nome):
    """Ora (time.time) in cui la fonte deve fermarsi e tenere quello che è arrivato (regola minutiMassimiPerFonte), o None."""
    minuti = (regola("minutiMassimiPerFonte") or {}).get(nome)
    return time.time() + float(minuti) * 60 if minuti else None


def scaduta(scadenza):
    return bool(scadenza) and time.time() > scadenza


def sostituisciFile(origine, destinazione, tentativi=10):
    """os.replace che riprova quando Windows tiene il file ancora aperto (WinError 32, antivirus o indicizzazione): dal 9/11/2026."""
    for tentativo in range(tentativi):
        try:
            return os.replace(origine, destinazione)
        except PermissionError:
            if tentativo == tentativi - 1:
                raise
            time.sleep(0.5 * (tentativo + 1))


def industria(numero):
    """Foglio dei CRM nuovi con il numero indicato (anche fuori dalle regioni scelte, per il collaudo)."""
    for voce in TUTTI_I_FOGLI:
        if int(voce["numero"]) == int(numero):
            return voce
    raise ChiaveMancante(f"Il blocco {numero} non è nel file _02_LetturaDalCRM/_04_ElencoDeiBlocchiDelCrm.json.")


def adesso():
    return datetime.datetime.now().astimezone().isoformat(timespec="seconds")


# Chiavi: lette dal codice al momento dell'uso, mai stampate.

_segreti = []


def percorsoChiave(nome):
    return os.path.join(CARTELLA_DELLE_CHIAVI, FILE_DELLE_CHIAVI[nome])


def leggiChiaveTesto(nome, modello):
    percorso = percorsoChiave(nome)
    if not os.path.isfile(percorso):
        raise ChiaveMancante(f"Manca la chiave {FILE_DELLE_CHIAVI[nome]} in _02_ChiaviDiAccessoAServiziDiTerzeParti.")
    with open(percorso, "r", encoding="utf-8-sig", errors="ignore") as file:
        trovato = re.search(modello, file.read())
    if not trovato:
        raise ChiaveMancante(f"La chiave {FILE_DELLE_CHIAVI[nome]} è vuota o non leggibile.")
    _segreti.append(trovato.group(0))
    return trovato.group(0)


def messaggioSicuro(testo):
    """Toglie da ogni messaggio chiavi e token."""
    testo = str(testo or "")
    for segreto in _segreti:
        if segreto:
            testo = testo.replace(segreto, "***")
    testo = re.sub(r"(key|access_token|token|signature|sig)=[^&\s\"']+", r"\1=***", testo, flags=re.I)
    testo = re.sub(r"EA[A-Za-z0-9]{40,}|AIza[0-9A-Za-z_\-]{30,}|ya29\.[0-9A-Za-z_\-.]+", "***", testo)
    return testo[:600]


# Nomi.


def nomeSenzaSpazi(testo):
    semplice = unicodedata.normalize("NFKD", str(testo or "")).encode("ascii", "ignore").decode("ascii")
    parole = [parola for parola in re.split(r"[^A-Za-z0-9]+", semplice) if parola]
    return "".join(parola[0].upper() + parola[1:] for parola in parole) or "Cliente"


def nomeDiFilePulito(testo, lunghezza=60):
    semplice = unicodedata.normalize("NFKD", str(testo or "")).encode("ascii", "ignore").decode("ascii")
    semplice = re.sub(r"[^A-Za-z0-9._-]+", "_", semplice).strip("._")
    return semplice[:lunghezza] or "file"


def estensioneDalTipo(tipoMime, predefinita=".bin"):
    tipo = (tipoMime or "").split(";")[0].strip().lower()
    noti = {"image/jpeg": ".jpg", "image/jpg": ".jpg", "image/png": ".png", "image/webp": ".webp", "image/gif": ".gif",
            "image/svg+xml": ".svg", "image/avif": ".avif", "image/x-icon": ".ico", "image/vnd.microsoft.icon": ".ico",
            "image/heic": ".heic", "video/mp4": ".mp4", "video/webm": ".webm", "application/pdf": ".pdf", "text/html": ".html"}
    return noti.get(tipo) or mimetypes.guess_extension(tipo) or predefinita


# Rete.

_sessione = None


def sessioneWeb():
    global _sessione
    if _sessione is None:
        import requests

        _sessione = requests.Session()
        _sessione.headers.update({"User-Agent": AGENTE_DEL_BROWSER, "Accept-Language": "it-IT,it;q=0.9,en;q=0.6"})
    return _sessione


def dominioBloccatoDalDns(nome):
    """Vero se il DNS di questo PC risponde 0.0.0.0 o 127.x per il dominio (blocco del filtro DNS)."""
    try:
        ipTrovati = {voce[4][0] for voce in socket.getaddrinfo(nome, 443, proto=socket.IPPROTO_TCP)}
    except socket.gaierror:
        return True
    return all(ip in ("0.0.0.0", "::") or ip.startswith("127.") for ip in ipTrovati)


def scaricaInFile(url, destinazione, intestazioni=None, byteMassimi=None):
    """Scarica un collegamento in un file temporaneo, con ripresa (Range) e controllo della lunghezza dichiarata.

    Restituisce il tipo MIME. Solleva ElementoNonScaricabile con il motivo preciso.
    """
    import requests

    scritti = 0
    totale = None
    tipo = ""
    ultimoErrore = ""
    for giro in range(2):
        richiesta = {"Accept-Encoding": "identity"}
        richiesta.update(intestazioni or {})
        if scritti:
            richiesta["Range"] = f"bytes={scritti}-"
        try:
            with sessioneWeb().get(url, headers=richiesta, stream=True, timeout=(15, 60), allow_redirects=True) as risposta:
                codice = risposta.status_code
                if codice == 416 and scritti:
                    return tipo
                if codice in CODICI_DA_RIPETERE:
                    raise requests.ConnectionError(f"risposta {codice}")
                if codice not in (200, 206):
                    raise ElementoNonScaricabile(f"il server risponde {codice}", definitivo=codice in CODICI_DEFINITIVI)
                modo = "ab"
                if codice == 200:
                    scritti, modo = 0, "wb"
                tipo = risposta.headers.get("Content-Type", tipo)
                if totale is None:
                    if codice == 206 and "/" in risposta.headers.get("Content-Range", ""):
                        fine = risposta.headers["Content-Range"].split("/")[-1]
                        totale = int(fine) if fine.isdigit() else None
                    elif risposta.headers.get("Content-Length", "").isdigit():
                        totale = int(risposta.headers["Content-Length"])
                with open(destinazione, modo) as file:
                    for pezzo in risposta.iter_content(chunk_size=512 * 1024):
                        file.write(pezzo)
                        scritti += len(pezzo)
                        if byteMassimi and scritti > byteMassimi:
                            raise ElementoNonScaricabile(f"file oltre {byteMassimi} byte")
            if totale is None or scritti >= totale:
                if scritti == 0:
                    raise ElementoNonScaricabile("il server restituisce un file vuoto")
                return tipo
        except (requests.ConnectionError, requests.Timeout, requests.exceptions.ChunkedEncodingError) as errore:
            ultimoErrore = type(errore).__name__
            testo = str(errore)
            if isinstance(errore, requests.ConnectionError) and any(segno in testo for segno in ("NameResolution", "getaddrinfo", "Name or service", "refused", "10061")):
                raise ElementoNonScaricabile(f"server non raggiungibile ({ultimoErrore}: nome inesistente o connessione rifiutata)", definitivo=True) from None
        time.sleep(3 * (giro + 1))
    raise ElementoNonScaricabile(f"scaricamento incompleto: {scritti} byte su {totale if totale is not None else 'sconosciuti'} ({ultimoErrore or 'lunghezza diversa da quella dichiarata'})")


# Verifica dei file: dimensione, apertura, formato.


def percorsoFfprobe():
    return shutil.which("ffprobe") or ""


def verificaFile(percorso, genere):
    """Controlla un file scaricato. Restituisce un dizionario di misure; solleva ElementoNonScaricabile se il file non è valido.

    genere: immagine, video, pdf, html, json, testo, qualsiasi.
    """
    if not os.path.isfile(percorso):
        raise ElementoNonScaricabile("file assente dopo lo scaricamento")
    byte = os.path.getsize(percorso)
    if byte < max(1, int(REGOLE.get("byteMinimiDiUnFile", 1))):
        raise ElementoNonScaricabile("file vuoto")
    misure = {"byte": byte}
    with open(percorso, "rb") as file:
        inizio = file.read(4096)
    if genere == "immagine":
        if inizio.lstrip()[:15].lower().startswith((b"<!doctype html", b"<html")):
            # il collegamento porta a una pagina, non a un'immagine: ripetere dà sempre la stessa pagina
            raise ElementoNonScaricabile("il server restituisce una pagina HTML, non un'immagine", definitivo=True)
        if inizio.lstrip()[:5].lower() in (b"<?xml", b"<svg ") or b"<svg" in inizio[:400].lower():
            try:
                from xml.etree import ElementTree

                ElementTree.parse(percorso)
            except Exception:
                raise ElementoNonScaricabile("SVG non leggibile") from None
            misure.update({"formato": "SVG"})
            return misure
        from PIL import Image

        try:
            import pillow_heif

            pillow_heif.register_heif_opener()
        except Exception:
            pass
        try:
            with Image.open(percorso) as immagine:
                immagine.verify()
            with Image.open(percorso) as immagine:
                immagine.load()
                misure.update({"formato": immagine.format, "larghezza": immagine.width, "altezza": immagine.height})
        except Exception as errore:
            # un file che non è un'immagine resta tale ripetendo; un file troncato invece si ripete
            raise ElementoNonScaricabile(f"immagine non apribile ({type(errore).__name__})", definitivo=type(errore).__name__ == "UnidentifiedImageError") from None
        return misure
    if genere == "video":
        sonda = percorsoFfprobe()
        if not sonda:
            raise ChiaveMancante("Manca ffprobe sul PC: senza non si verificano i video.")
        risultato = subprocess.run([sonda, "-v", "error", "-show_entries", "format=duration:stream=codec_type", "-of", "json", percorso],
                                   capture_output=True, text=True, timeout=120, creationflags=SENZA_FINESTRA)
        try:
            dati = json.loads(risultato.stdout or "{}")
        except ValueError:
            dati = {}
        flussi = [voce.get("codec_type") for voce in dati.get("streams", [])]
        secondi = float((dati.get("format") or {}).get("duration") or 0)
        if risultato.returncode != 0 or "video" not in flussi or secondi <= 0:
            raise ElementoNonScaricabile("video non apribile o senza immagini")
        misure.update({"secondi": round(secondi, 2), "audio": "audio" in flussi})
        return misure
    if genere == "pdf":
        with open(percorso, "rb") as file:
            file.seek(max(0, byte - 2048))
            coda = file.read()
        if not inizio.startswith(b"%PDF") or b"%%EOF" not in coda:
            raise ElementoNonScaricabile("PDF non completo")
        return misure
    if genere in ("html", "testo"):
        testo = open(percorso, "rb").read().decode("utf-8", "ignore")
        if not testo.strip():
            raise ElementoNonScaricabile("testo vuoto")
        if genere == "html" and "<" not in testo:
            raise ElementoNonScaricabile("HTML non valido")
        return misure
    if genere == "json":
        try:
            json.load(open(percorso, "r", encoding="utf-8"))
        except ValueError:
            raise ElementoNonScaricabile("JSON non valido") from None
        return misure
    return misure


def impronta(percorso):
    calcolo = hashlib.md5()
    with open(percorso, "rb") as file:
        for pezzo in iter(lambda: file.read(1024 * 1024), b""):
            calcolo.update(pezzo)
    return calcolo.hexdigest()


# yt-dlp in un processo a parte, con il motore JavaScript node per YouTube.


def eseguiYtDlp(argomenti, secondiMassimi=3600):
    """Avvia yt-dlp con i parametri indicati, a priorità bassa. Restituisce (codice, uscita, errori)."""
    comando = [PYTHON_DEL_MOTORE, "-B", SCRIPT_YTDLP, "--no-warnings", "--js-runtimes", "node"] + argomenti
    risultato = subprocess.run(comando, capture_output=True, text=True, encoding="utf-8", errors="ignore", timeout=secondiMassimi,
                               creationflags=PRIORITA_BASSA | SENZA_FINESTRA, stdin=subprocess.DEVNULL)
    return risultato.returncode, risultato.stdout, risultato.stderr


def ultimoErrore(testo):
    righe = [riga.strip() for riga in (testo or "").splitlines() if "ERROR" in riga or "Error" in riga]
    return messaggioSicuro(righe[-1] if righe else (testo or "").strip()[-300:])


# Battito del lavoratore: il coordinatore lo guarda e riavvia il lavoratore fermo da troppe ore.

FILE_DEL_BATTITO = ""  # impostato dal lavoratore: _03_Registro/battiti/industria_NN.battito


def percorsoDelBattito(numero):
    return os.path.join(CARTELLA_DEL_REGISTRO, "battiti", f"industria_{numero}.battito")


def battito():
    """Segna che il lavoratore sta andando avanti (data di modifica del file del battito)."""
    if not FILE_DEL_BATTITO:
        return
    try:
        os.makedirs(os.path.dirname(FILE_DEL_BATTITO), exist_ok=True)
        with open(FILE_DEL_BATTITO, "w", encoding="utf-8") as file:
            file.write(adesso())
    except OSError:
        pass


def cartellaTemporaneaDelCliente(idCliente):
    percorso = os.path.join(CARTELLA_TEMPORANEA, nomeDiFilePulito(idCliente))
    os.makedirs(percorso, exist_ok=True)
    return percorso


def svuotaCartella(percorso):
    """Rimuove una cartella temporanea del motore (solo dentro _04_FileTemporanei)."""
    pieno = os.path.abspath(percorso)
    if not pieno.startswith(os.path.abspath(CARTELLA_TEMPORANEA)):
        return
    shutil.rmtree(pieno, ignore_errors=True)


def collegamentoAssoluto(base, valore):
    try:
        return urllib.parse.urljoin(base, valore)
    except ValueError:
        return ""


# Un solo Chrome nascosto per i siti di tutti i lavoratori (Michele, 9/11/2026): ogni cliente apre la sua scheda,
# Chrome gira con pochi processi, senza scheda grafica e con memoria ridotta per pagina; il coordinatore lo chiude.
PORTA_DEL_CHROME_DEI_SITI = 9333
FILE_DEL_CHROME_DEI_SITI = os.path.join(CARTELLA_DEL_REGISTRO, "chromeDeiSiti.json")
PROFILO_DEL_CHROME_DEI_SITI = os.path.join(CARTELLA_TEMPORANEA, "_ChromeDeiSiti")
ESEGUIBILE_DI_CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
OPZIONI_DEL_CHROME_DEI_SITI = ["--headless=new", "--disable-gpu", "--renderer-process-limit=3", "--js-flags=--max-old-space-size=512",
                               "--disable-extensions", "--mute-audio", "--no-first-run", "--no-default-browser-check",
                               "--disable-background-networking", "--disable-component-update", "--disable-sync"]


def _chromeDeiSitiRisponde():
    try:
        with socket.create_connection(("127.0.0.1", PORTA_DEL_CHROME_DEI_SITI), timeout=1):
            return True
    except OSError:
        return False


def chromeDeiSiti(programma):
    """Il Chrome condiviso dei siti (lo accende il primo lavoratore che ne ha bisogno). Restituisce il browser collegato."""
    bloccoFile = FILE_DEL_CHROME_DEI_SITI + ".lock"
    for _ in range(60):
        if _chromeDeiSitiRisponde():
            break
        try:
            descrittore = os.open(bloccoFile, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        except FileExistsError:
            if time.time() - os.path.getmtime(bloccoFile) > 60:
                try:
                    os.remove(bloccoFile)
                except OSError:
                    pass
            time.sleep(1)
            continue
        try:
            os.close(descrittore)
            if not _chromeDeiSitiRisponde():
                os.makedirs(PROFILO_DEL_CHROME_DEI_SITI, exist_ok=True)
                processo = subprocess.Popen([ESEGUIBILE_DI_CHROME, f"--remote-debugging-port={PORTA_DEL_CHROME_DEI_SITI}",
                                             f"--user-data-dir={PROFILO_DEL_CHROME_DEI_SITI}", *OPZIONI_DEL_CHROME_DEI_SITI, "about:blank"],
                                            creationflags=SENZA_FINESTRA, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                scriviJsonSulDisco(FILE_DEL_CHROME_DEI_SITI, {"pid": processo.pid, "acceso": adesso()})
                for _ in range(30):
                    if _chromeDeiSitiRisponde():
                        break
                    time.sleep(0.5)
        finally:
            try:
                os.remove(bloccoFile)
            except OSError:
                pass
    return programma.chromium.connect_over_cdp(f"http://127.0.0.1:{PORTA_DEL_CHROME_DEI_SITI}")


def chiudiChromeDeiSiti():
    """Chiude il Chrome condiviso dei siti (all'accensione e allo spegnimento del motore)."""
    voce = leggiJson(FILE_DEL_CHROME_DEI_SITI, {}) or {}
    if voce.get("pid"):
        subprocess.run(["taskkill", "/PID", str(voce["pid"]), "/T", "/F"], creationflags=SENZA_FINESTRA,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        os.remove(FILE_DEL_CHROME_DEI_SITI)
    except OSError:
        pass

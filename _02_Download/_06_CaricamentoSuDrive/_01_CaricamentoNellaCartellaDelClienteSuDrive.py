"""Dove va il materiale: Google Drive dell'account depthxlabs@gmail.com, Area 1B.

Ogni file caricato si verifica: impronta MD5 e dimensione su Drive uguali a quelle del file temporaneo.
La destinazione di collaudo (DestinazioneDiCollaudo) scrive in una cartella del disco e serve
soltanto al collaudo quando Drive non è disponibile; la cartella si rimuove a collaudo finito.
"""

import sys

sys.dont_write_bytecode = True

import io
import json
import mimetypes
import os
import shutil
import threading
import time

import _02_PercorsiChiaviEFunzioniComuni as comune

AMBITI_DRIVE = ["https://www.googleapis.com/auth/drive"]
ACCOUNT_DRIVE = "depthxlabs@gmail.com"
TIPO_CARTELLA = "application/vnd.google-apps.folder"
ID_CARTELLA_1B = "1Lf_1OndQT_30Doj3HE8XMfaMKauQfXHZ"  # _03_1.1_C_DownloadMaterialeClienti su Drive, accanto a _02_1.1_B_CRM_Clienti
NOME_CARTELLA_1B = "_03_1.1_C_DownloadMaterialeClienti"
PEZZO = 8 * 1024 * 1024


# L'accesso a Drive è quello di rclone: su GitHub la configurazione arriva dal segreto, sul server è il file di rclone in scrittura
CONFIGURAZIONE_RCLONE = os.environ.get("MOTORE_RCLONE_CONF") or r"C:\_02_DepthXSoftware\_02_RCloneDepthX\rclone_scrittura.conf"
PROGRAMMA_RCLONE = os.environ.get("MOTORE_RCLONE") or r"C:\_02_DepthXSoftware\_02_RCloneDepthX\rclone.exe"


def accessoDaRclone(richiesta=None, scopes=None):
    """Rinnova l'accesso con rclone e lo legge dalla sua configurazione: (accesso, scadenza). Non si stampa mai."""
    import datetime
    import json
    import re
    import subprocess

    subprocess.run([PROGRAMMA_RCLONE, "about", "gdrivescrittura:", "--config", CONFIGURAZIONE_RCLONE], capture_output=True, timeout=120)
    with open(CONFIGURAZIONE_RCLONE, encoding="utf-8") as file:
        sezione = file.read().split("[gdrivescrittura]", 1)[1].split("\n[", 1)[0]
    gettone = json.loads(re.search(r"^token\s*=\s*(\{.*\})\s*$", sezione, re.M).group(1))
    scadenza = datetime.datetime.fromisoformat(re.sub(r"(\.\d{6})\d+", r"\1", gettone["expiry"]).replace("Z", "+00:00"))
    return gettone["access_token"], scadenza.astimezone(datetime.timezone.utc).replace(tzinfo=None)


# Al massimo 60 richieste a Drive in 60 secondi, contate su tutti i fili del lavoratore; con più macchine insieme la quota si divide
RICHIESTE_AL_MINUTO = max(1, int(os.environ.get("MOTORE_RICHIESTE_AL_MINUTO") or 60))
_richiesteFatte = []
_bloccoDelleRichieste = __import__("threading").Lock()


def aspettaIlTurno():
    while True:
        with _bloccoDelleRichieste:
            adesso = time.monotonic()
            while _richiesteFatte and adesso - _richiesteFatte[0] >= 60:
                _richiesteFatte.pop(0)
            if len(_richiesteFatte) < RICHIESTE_AL_MINUTO:
                _richiesteFatte.append(adesso)
                return
            attesa = 60 - (adesso - _richiesteFatte[0])
        time.sleep(max(0.2, attesa))


def credenzialiDrive(conConsenso=False):
    """Credenziali di Drive dal token nella cartella delle chiavi (il file resta dov'è).

    Senza consenso valido solleva ConsensoDriveMancante; con conConsenso=True apre il browser per il consenso di Michele.
    """
    comune.percorsiBreviPerWindows()
    from google.oauth2.credentials import Credentials

    if not os.path.isfile(CONFIGURAZIONE_RCLONE):
        raise ConsensoMancante()
    accesso, scadenza = accessoDaRclone()
    return Credentials(token=accesso, expiry=scadenza, refresh_handler=accessoDaRclone)


def scriviToken(fileDelToken, credenziali):
    """Scrive il token nel suo file di sempre: prima un file provvisorio accanto, poi la sostituzione."""
    provvisorio = f"{fileDelToken}.{os.getpid()}.tmp"
    with open(provvisorio, "w", encoding="utf-8") as file:
        file.write(credenziali.to_json())
    for giro in range(20):
        try:
            os.replace(provvisorio, fileDelToken)
            return
        except PermissionError:
            time.sleep(0.2)
    os.replace(provvisorio, fileDelToken)


def ConsensoMancante():
    return comune.ConsensoDriveMancante("Il token di Google Drive è scaduto o revocato (invalid_grant): serve il consenso con _08_ComandiDelMotore/_02_ConsensoGoogleDriveDelMotore.cmd.")


class DestinazioneDrive:
    """Cartelle e file su Google Drive, con ripetizioni per rete e limiti.

    Più file salgono insieme (caricamentiInParalleloSuDrive): ogni filo di caricamento ha la sua connessione a Drive,
    perché una connessione non si divide tra fili; gli elenchi delle cartelle si leggono uno alla volta.
    """

    def __init__(self):
        self.credenziali = credenzialiDrive()
        self.connessioni = threading.local()
        self.bloccoDegliElenchi = threading.Lock()
        self.elenchi = {}

    @property
    def servizio(self):
        if not hasattr(self.connessioni, "servizio"):
            from googleapiclient.discovery import build

            self.connessioni.servizio = build("drive", "v3", credentials=self.credenziali, cache_discovery=False)
        return self.connessioni.servizio

    def collegamento(self, idCartella):
        return f"https://drive.google.com/drive/folders/{idCartella}"

    def esegui(self, richiesta):
        from googleapiclient.errors import HttpError

        for giro in range(10):
            try:
                aspettaIlTurno()
                return richiesta.execute()
            except HttpError as errore:
                codice = errore.resp.status if errore.resp is not None else 0
                if codice == 401:
                    raise ConsensoMancante() from None
                limite = codice in (403, 429) and any(p in str(errore).lower() for p in ("quota", "ratelimit", "rate limit"))
                if codice not in comune.CODICI_DA_RIPETERE and not limite:
                    raise
                if giro == 9:
                    raise
            except OSError:
                if giro == 9:
                    raise
            time.sleep(min(2 ** (giro + 2), 65))

    @staticmethod
    def _testo(nome):
        return nome.replace("\\", "\\\\").replace("'", "\\'")

    def cercaCartella(self, nome, idMadre):
        domanda = f"name = '{self._testo(nome)}' and '{idMadre}' in parents and mimeType = '{TIPO_CARTELLA}' and trashed = false"
        file = self.esegui(self.servizio.files().list(q=domanda, fields="files(id,name)", pageSize=10, spaces="drive")).get("files", [])
        return file[0]["id"] if file else ""

    def cartella(self, nome, idMadre):
        trovata = self.cercaCartella(nome, idMadre)
        if trovata:
            return trovata
        corpo = {"name": nome, "mimeType": TIPO_CARTELLA, "parents": [idMadre]}
        return self.esegui(self.servizio.files().create(body=corpo, fields="id"))["id"]

    def cartellaValida(self, idCartella):
        from googleapiclient.errors import HttpError

        if not idCartella:
            return False
        try:
            dati = self.esegui(self.servizio.files().get(fileId=idCartella, fields="id,mimeType,trashed"))
        except HttpError:
            return False
        return bool(dati) and dati.get("mimeType") == TIPO_CARTELLA and not dati.get("trashed")

    def cartellaDellIndustria(self, voceIndustria):
        """CRM nuovi: Area 1B / [NN] CRM Tipo / [NN] Categoria / [NN] Regione, come nella cartella dei CRM (una volta per processo)."""
        if self.cartellaValida(voceIndustria.get("idCartellaDrive")):
            return voceIndustria["idCartellaDrive"]
        if not self.cartellaValida(ID_CARTELLA_1B):
            raise comune.ChiaveMancante(f"Su Google Drive non trovo la cartella {NOME_CARTELLA_1B} (ID {ID_CARTELLA_1B}): il motore non la crea.")
        idMadre = ID_CARTELLA_1B
        for nome in voceIndustria.get("percorsoDrive") or [voceIndustria["cartellaDrive"]]:
            idMadre = self.cartella(nome, idMadre)
        voceIndustria["idCartellaDrive"] = idMadre
        return idMadre

    def elenco(self, idCartella, rileggi=False):
        """nome -> {id, md5, byte} dei file nella cartella."""
        with self.bloccoDegliElenchi:
            return self._elenco(idCartella, rileggi)

    def _elenco(self, idCartella, rileggi):
        if rileggi or idCartella not in self.elenchi:
            presenti, pagina = {}, None
            while True:
                risposta = self.esegui(self.servizio.files().list(q=f"'{idCartella}' in parents and trashed = false",
                                                                   fields="nextPageToken, files(id,name,md5Checksum,size,mimeType)",
                                                                   pageSize=1000, pageToken=pagina))
                for file in risposta.get("files", []):
                    presenti[file["name"]] = {"id": file["id"], "md5": file.get("md5Checksum"), "byte": int(file.get("size") or 0)}
                pagina = risposta.get("nextPageToken")
                if not pagina:
                    break
            self.elenchi[idCartella] = presenti
        return self.elenchi[idCartella]

    def caricaFile(self, idCartella, percorso, nome, md5, tipoMime=None):
        """Carica il file e verifica MD5 e dimensione su Drive. Se c'è già lo stesso file (stesso nome e MD5) lo tiene."""
        from googleapiclient.http import MediaFileUpload

        byte = os.path.getsize(percorso)
        presenti = self.elenco(idCartella)
        if nome in presenti and presenti[nome]["md5"] == md5 and presenti[nome]["byte"] == byte:
            return presenti[nome]["id"]
        tipoMime = tipoMime or mimetypes.guess_type(nome)[0] or "application/octet-stream"
        for giro in range(4):
            contenuto = MediaFileUpload(percorso, mimetype=tipoMime, chunksize=PEZZO, resumable=True)
            if nome in presenti:
                richiesta = self.servizio.files().update(fileId=presenti[nome]["id"], media_body=contenuto, fields="id,md5Checksum,size")
            else:
                richiesta = self.servizio.files().create(body={"name": nome, "parents": [idCartella]}, media_body=contenuto, fields="id,md5Checksum,size")
            try:
                risultato = self._aPezzi(richiesta)
            finally:
                contenuto.stream().close()
            if risultato.get("md5Checksum") == md5 and int(risultato.get("size") or -1) == byte:
                presenti[nome] = {"id": risultato["id"], "md5": md5, "byte": byte}
                return risultato["id"]
            presenti[nome] = {"id": risultato["id"], "md5": risultato.get("md5Checksum"), "byte": int(risultato.get("size") or 0)}
            time.sleep(5 * (giro + 1))
        raise comune.ElementoNonScaricabile(f"su Drive il file {nome} non corrisponde (MD5 o dimensione) dopo 4 caricamenti")

    def _aPezzi(self, richiesta):
        from googleapiclient.errors import HttpError

        risposta, errori = None, 0
        while risposta is None:
            try:
                aspettaIlTurno()
                _, risposta = richiesta.next_chunk()
                errori = 0
            except HttpError as errore:
                codice = errore.resp.status if errore.resp is not None else 0
                errori += 1
                if codice == 401:
                    raise ConsensoMancante() from None
                limite = codice in (403, 429) and any(p in str(errore).lower() for p in ("quota", "ratelimit", "rate limit"))
                if (codice not in comune.CODICI_DA_RIPETERE and not limite) or errori > 9:
                    raise
                time.sleep(min(2 ** (errori + 1), 65))
            except OSError:
                errori += 1
                if errori > 6:
                    raise
                time.sleep(2 ** errori)
        return risposta

    def scriviJson(self, idCartella, nome, oggetto, cartellaTemporanea):
        percorso = os.path.join(cartellaTemporanea, "_json_" + nome)
        with open(percorso, "w", encoding="utf-8") as file:
            json.dump(oggetto, file, ensure_ascii=False, indent=1)
        try:
            return self.caricaFile(idCartella, percorso, nome, comune.impronta(percorso), "application/json")
        finally:
            os.remove(percorso)

    def scaricaFile(self, idFile, percorso):
        from googleapiclient.http import MediaIoBaseDownload

        with open(percorso, "wb") as file:
            scaricamento = MediaIoBaseDownload(file, self.servizio.files().get_media(fileId=idFile), chunksize=PEZZO)
            fatto = False
            while not fatto:
                _, fatto = scaricamento.next_chunk()
        return percorso

    def leggiJson(self, idCartella, nome):
        from googleapiclient.http import MediaIoBaseDownload

        presenti = self.elenco(idCartella)
        if nome not in presenti:
            return None
        memoria = io.BytesIO()
        scaricamento = MediaIoBaseDownload(memoria, self.servizio.files().get_media(fileId=presenti[nome]["id"]))
        fatto = False
        while not fatto:
            _, fatto = scaricamento.next_chunk()
        try:
            return json.loads(memoria.getvalue().decode("utf-8"))
        except ValueError:
            return None


class DestinazioneDiCollaudo:
    """Stessa interfaccia di DestinazioneDrive, su una cartella del disco: solo per il collaudo senza Drive."""

    def __init__(self, radice):
        self.radice = os.path.abspath(radice)
        os.makedirs(self.radice, exist_ok=True)

    def collegamento(self, idCartella):
        return idCartella

    def cartella(self, nome, idMadre):
        percorso = os.path.join(idMadre, nome)
        os.makedirs(percorso, exist_ok=True)
        return percorso

    def cartellaDellIndustria(self, voceIndustria):
        percorso = self.radice
        for nome in voceIndustria.get("percorsoDrive") or [voceIndustria["cartellaDrive"]]:
            percorso = self.cartella(nome, percorso)
        return percorso

    def elenco(self, idCartella, rileggi=False):
        presenti = {}
        for nome in os.listdir(idCartella):
            percorso = os.path.join(idCartella, nome)
            if os.path.isfile(percorso):
                presenti[nome] = {"id": percorso, "md5": comune.impronta(percorso), "byte": os.path.getsize(percorso)}
        return presenti

    def caricaFile(self, idCartella, percorso, nome, md5, tipoMime=None):
        arrivo = os.path.join(idCartella, nome)
        shutil.copyfile(percorso, arrivo)
        if comune.impronta(arrivo) != md5 or os.path.getsize(arrivo) != os.path.getsize(percorso):
            raise comune.ElementoNonScaricabile(f"copia di collaudo di {nome} non corrisponde")
        return arrivo

    def scriviJson(self, idCartella, nome, oggetto, cartellaTemporanea):
        arrivo = os.path.join(idCartella, nome)
        with open(arrivo, "w", encoding="utf-8") as file:
            json.dump(oggetto, file, ensure_ascii=False, indent=1)
        return arrivo

    def scaricaFile(self, idFile, percorso):
        shutil.copyfile(idFile, percorso)
        return percorso

    def leggiJson(self, idCartella, nome):
        return comune.leggiJson(os.path.join(idCartella, nome), None)


# Consenso a Drive da Mac o telefono, come per Gmail nel centro gestione (posta.js):
# il motore dà un link; Michele lo apre sul suo dispositivo; il browser finisce su una pagina 127.0.0.1 che non si apre;
# Michele copia tutto il link dalla barra e lo incolla; il motore scambia il code con il token.
# Code e token non si stampano e non vanno mai nel registro.

RITORNO_DEL_CONSENSO = "http://127.0.0.1:8765/consensoDrive"  # client Desktop: Google accetta ogni porta di 127.0.0.1
FILE_DEL_CONSENSO_IN_ATTESA = os.path.join(comune.CARTELLA_DEL_REGISTRO, "consensoDriveInAttesa.json")
MINUTI_DI_VALIDITA_DEL_LINK = 30


def _clienteOAuth():
    dati = comune.leggiJson(comune.percorsoChiave("clienteDrive"), {}) or {}
    voce = dati.get("installed") or dati.get("web")
    if not voce or not voce.get("client_id"):
        raise comune.ChiaveMancante("Il file _05_AccessoGoogleDriveOAuth.json non contiene un client OAuth valido.")
    return voce


def linkDiConsenso():
    import secrets
    import urllib.parse

    stato = secrets.token_hex(16)
    comune.scriviJsonSulDisco(FILE_DEL_CONSENSO_IN_ATTESA, {"stato": stato, "creato": time.time()})
    parametri = {"client_id": _clienteOAuth()["client_id"], "redirect_uri": RITORNO_DEL_CONSENSO, "response_type": "code",
                 "scope": " ".join(AMBITI_DRIVE), "access_type": "offline", "prompt": "consent", "login_hint": ACCOUNT_DRIVE, "state": stato}
    return "https://accounts.google.com/o/oauth2/v2/auth?" + urllib.parse.urlencode(parametri)


def incollaConsenso(incollato):
    """Riceve il link copiato dalla barra del browser e salva il token nel suo file di sempre. Restituisce l'account."""
    import urllib.parse

    from google.oauth2.credentials import Credentials

    parti = urllib.parse.urlsplit(str(incollato or "").strip())
    domande = urllib.parse.parse_qs(parti.query)
    if domande.get("error"):
        raise comune.ChiaveMancante("Google ha risposto: " + domande["error"][0])
    codice, stato = (domande.get("code") or [""])[0], (domande.get("state") or [""])[0]
    if not codice or not stato:
        raise comune.ChiaveMancante("Nel link incollato mancano code o state: si copia tutta la barra del browser.")
    attesa = comune.leggiJson(FILE_DEL_CONSENSO_IN_ATTESA, {}) or {}
    if attesa.get("stato") != stato or time.time() - float(attesa.get("creato") or 0) > MINUTI_DI_VALIDITA_DEL_LINK * 60:
        raise comune.ChiaveMancante("Link di consenso scaduto o diverso dall'ultimo creato: si riparte con un link nuovo.")
    cliente = _clienteOAuth()
    risposta = comune.sessioneWeb().post("https://oauth2.googleapis.com/token", timeout=(20, 60), data={
        "code": codice, "client_id": cliente["client_id"], "client_secret": cliente.get("client_secret", ""),
        "redirect_uri": RITORNO_DEL_CONSENSO, "grant_type": "authorization_code"})
    dati = risposta.json() if risposta.content else {}
    if not dati.get("refresh_token"):
        raise comune.ChiaveMancante("Google non ha dato l'accesso permanente (" + str(dati.get("error", risposta.status_code)) + "): si ripete il consenso.")
    credenziali = Credentials(token=dati.get("access_token"), refresh_token=dati["refresh_token"], token_uri="https://oauth2.googleapis.com/token",
                              client_id=cliente["client_id"], client_secret=cliente.get("client_secret", ""), scopes=AMBITI_DRIVE)
    from googleapiclient.discovery import build

    account = build("drive", "v3", credentials=credenziali, cache_discovery=False).about().get(fields="user(emailAddress)").execute()["user"]["emailAddress"]
    if account != ACCOUNT_DRIVE:
        raise comune.ChiaveMancante(f"Account scelto sbagliato ({account}): serve {ACCOUNT_DRIVE}.")
    scriviToken(comune.percorsoChiave("tokenDrive"), credenziali)
    os.remove(FILE_DEL_CONSENSO_IN_ATTESA)
    return account

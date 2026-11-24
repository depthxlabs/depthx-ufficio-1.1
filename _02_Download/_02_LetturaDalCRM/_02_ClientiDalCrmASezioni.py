"""Lettura dei CRM nuovi della Linea 1.2 (cartella Drive "_01_CRM Linea 1.2"), in SOLA LETTURA.

Un foglio per tipo, categoria e regione; scheda "Lista"; riga 1 con i gruppi, riga 2 con le intestazioni, dati dalla riga 3.
Le colonne si leggono per nome di intestazione, mai per lettera. La lettura passa da _01_LetturaDeiFogliDaGoogleSheets.js (Node), che prende
il token dal Centro Gestione e non lo restituisce mai: qui arrivano solo le righe.
Al massimo una lettura al secondo tra tutti i processi del motore (blocco su _03_Registro/letturaCrm.lock).
"""

import sys

sys.dont_write_bytecode = True

import json
import msvcrt
import os
import re
import subprocess
import time

import _02_PercorsiChiaviEFunzioniComuni as comune

SCRIPT_DI_LETTURA = comune.SCRIPT_DI_LETTURA_DEI_FOGLI
FILE_DEL_BLOCCO = os.path.join(comune.CARTELLA_DEL_REGISTRO, "letturaCrm.lock")
SECONDI_TRA_LE_LETTURE = 1.1

# Intestazione del CRM nuovo -> campo del motore (le fonti usano questi nomi).
CAMPI_DEL_CRM = {
    "ID cliente": "idCliente",
    "Nome commerciale": "nome",
    "Ragione sociale": "ragioneSociale",
    "Forma giuridica": "formaGiuridica",
    "Sottosettore": "sottosettore",
    "Partita IVA": "partitaIva",
    "Titolare o referente": "referente",
    "Ruolo del referente": "ruoloDelReferente",
    "Via e numero civico": "via",
    "CAP": "cap",
    "Comune": "comune",
    "Provincia": "provincia",
    "Sede unica": "sedeUnica",
    "Numero di sedi": "numeroDiSedi",
    "Orari": "orari",
    "Codice CIN": "codiceCin",
    "Numero di camere": "numeroDiCamere",
    "Motore di prenotazione attuale": "motoreDiPrenotazione",
    "Telefono fisso": "telefono",
    "Cellulare": "cellulare",
    "Tutti i contatti Email": "email",
    "Ha Instagram?": "instagram",
    "Ha Facebook?": "facebook",
    "Ha gia un sito?": "sito",
    "Ha un Canale YouTube?": "youtube",
    "Ha TikTok?": "tiktok",
    "Pagina LinkedIn aziendale": "linkedin",
    "Piattaforma del sito": "piattaformaDelSito",
    "Agenzia o crediti": "agenzia",
    "Numero di pagine del sito attuale": "pagineDelSito",
    "Google Maps": "googleMaps",
    "Voto Google": "votoGoogle",
    "Recensioni Google": "recensioniGoogle",
    "Foto Google": "fotoGoogle",
    "Verifica sito": "verificaSito",
    "Verifica Registro Imprese": "verificaRegistroImprese",
    "Link demo": "linkDemo",
    "Stato dell'ondata": "statoDellOndata",
}

# valori che nel CRM vogliono dire assente ("no" vale per "Ha gia un sito?" dei clienti senza sito ufficiale)
VALORI_VUOTI = {"", "non trovato", "non esiste", "nessuno", "nessuna", "no", "n/d", "nd", "-", "non presente"}


class ErroreDelCrm(Exception):
    """Lettura del CRM nuovo non riuscita, con il motivo."""


class _Blocco:
    """Una lettura alla volta tra i processi del motore, con almeno SECONDI_TRA_LE_LETTURE tra una e l'altra."""

    def __enter__(self):
        os.makedirs(comune.CARTELLA_DEL_REGISTRO, exist_ok=True)
        self.file = open(FILE_DEL_BLOCCO, "a+b")
        for giro in range(6000):
            try:
                self.file.seek(0)
                msvcrt.locking(self.file.fileno(), msvcrt.LK_NBLCK, 1)
                break
            except OSError:
                time.sleep(0.1)
        else:
            raise ErroreDelCrm("lettura del CRM occupata da oltre 10 minuti")
        try:
            attesa = SECONDI_TRA_LE_LETTURE - (time.time() - os.path.getmtime(FILE_DEL_BLOCCO + ".ora"))
            if attesa > 0:
                time.sleep(attesa)
        except OSError:
            pass
        return self

    def __exit__(self, *dettagli):
        try:
            with open(FILE_DEL_BLOCCO + ".ora", "w", encoding="utf-8") as file:
                file.write(comune.adesso())
        except OSError:
            pass
        try:
            self.file.seek(0)
            msvcrt.locking(self.file.fileno(), msvcrt.LK_UNLCK, 1)
        finally:
            self.file.close()


def righeDelFoglioSuDrive(idFoglio):
    """Righe del Foglio Google del CRM su Drive ("sheets:<id del foglio>"), in sola lettura, come testo."""
    sys.path.insert(0, comune.CARTELLA_DEL_CRM_SU_DRIVE)
    import _00_CrmSuGoogleSheets as crmSuDrive
    try:
        return crmSuDrive.leggi(idFoglio[7:])
    except Exception as errore:
        raise ErroreDelCrm(f"foglio del CRM su Drive non leggibile: {idFoglio}: {str(errore)[:200]}")


def righeDelFoglio(idFoglio):
    """Righe della scheda Lista del foglio (una lettura, in sola lettura). I fogli "sheets:" si leggono dal CRM su Drive.
    Su GitHub (variabile MOTORE_CODA) le righe arrivano dal file della coda preparato dal server."""
    if os.environ.get("MOTORE_CODA"):
        with open(os.environ["MOTORE_CODA"], encoding="utf-8") as file:
            return json.load(file)["fogli"][idFoglio]
    if str(idFoglio).startswith("sheets:"):
        return righeDelFoglioSuDrive(idFoglio)
    with _Blocco():
        risultato = subprocess.run(["node", SCRIPT_DI_LETTURA, idFoglio], capture_output=True, text=True, encoding="utf-8", errors="ignore",
                                   timeout=900, creationflags=comune.SENZA_FINESTRA, stdin=subprocess.DEVNULL)
    try:
        voce = json.loads(risultato.stdout or "{}").get(idFoglio) or {}
    except ValueError:
        voce = {}
    if "righe" not in voce:
        raise ErroreDelCrm(comune.messaggioSicuro(voce.get("errore") or risultato.stderr[-300:] or "lettura del CRM non riuscita"))
    return voce["righe"]


# dal 4/11/2026 una cella senza dato dice il motivo ("no: nessun sito proprio; controllati...", "Nessuna email aziendale pubblicata: ..."):
# per il motore è vuota; i collegamenti valgono solo se sono indirizzi web, le email solo se sono indirizzi
CAMPI_COLLEGAMENTO = {"instagram", "facebook", "sito", "youtube", "tiktok", "linkedin", "googleMaps", "linkDemo"}
MOTIVO_SENZA_DATO = re.compile(r"^(no:|nessun|struttura senza|la scheda google|numero di|orari non|cin non|partita iva|ragione sociale non|forma giuridica non|"
                               r"titolare:|ruolo:|sede unica:|numero di sedi:|piattaforma non|indirizzo non|cap non|comune non|la sola partita)", re.I)


def pulisciValore(valore, campo=""):
    testo = str(valore or "").strip()
    if testo.lower() in VALORI_VUOTI or MOTIVO_SENZA_DATO.match(testo):
        return ""
    if campo in CAMPI_COLLEGAMENTO and not re.match(r"^https?://", testo, re.I):
        return ""
    if campo == "email":
        return "; ".join(re.findall(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+", testo))
    return testo


_indiceDelleSchede = None


def placeIdDalRiempimento(collegamento):
    """Place id della scheda Google già trovato da chi ha riempito il CRM (stesso cid), così il motore non ripete la ricerca."""
    global _indiceDelleSchede
    trovato = re.search(r"[?&]cid=(\d{5,})", str(collegamento or ""))
    if not trovato:
        return ""
    if _indiceDelleSchede is None:
        _indiceDelleSchede = {}
        stato = comune.leggiJson(comune.CRM_NUOVI.get("statoDelRiempimentoDeiCrm", ""), {}) or {}
        for candidato in (stato.get("candidati") or {}).values():
            scheda = candidato.get("place") or {}
            cid = re.search(r"[?&]cid=(\d{5,})", str(scheda.get("googleMapsUri") or ""))
            if cid and str(scheda.get("id") or "").startswith("ChIJ"):
                _indiceDelleSchede[cid.group(1)] = scheda["id"]
    return _indiceDelleSchede.get(trovato.group(1), "")


CODICE_CLIENTE = re.compile(r"^(S\d_[A-Z]{3}_[A-Z]{3}_\d{3,}|C_S_[A-Z]{3}_\d{4})$")


def leggiClientiDelFoglio(voceFoglio):
    """Clienti del foglio, un dizionario per cliente con i campi del motore e in "campi" tutte le colonne del CRM."""
    righe = righeDelFoglio(voceFoglio["idCrm"])
    if len(righe) < 2:
        return []
    intestazioni = [str(nome).strip() for nome in righe[1]]
    posizioni = {}
    for numero, nome in enumerate(intestazioni):
        if nome and nome not in posizioni:
            posizioni[nome] = numero
    if "ID cliente" not in posizioni:
        raise ErroreDelCrm(f"Nel foglio {voceFoglio['nome']} manca l'intestazione 'ID cliente' nella riga 2.")
    clienti, visti = [], set()
    for riga in righe[2:]:
        campi = {nome: (riga[numero] if numero < len(riga) else "") for nome, numero in posizioni.items()}
        idCliente = str(campi.get("ID cliente", "")).strip()
        # dal 9/11/2026 (Michele) il codice è quello del blocco: S1_BEB_PIE_007 (i vecchi C_S_ restano validi)
        if not CODICE_CLIENTE.match(idCliente.upper()) or idCliente.upper() in visti:
            continue
        visti.add(idCliente.upper())
        cliente = {campo: pulisciValore(campi.get(intestazione, ""), campo) for intestazione, campo in CAMPI_DEL_CRM.items()}
        cliente["idCliente"] = idCliente
        cliente["foglioCrm"] = {"id": voceFoglio["idCrm"], "nome": voceFoglio["nome"], "percorso": voceFoglio["cartellaDrive"]}
        cliente["campi"] = {nome: str(valore).strip() for nome, valore in campi.items()}
        cliente["googleMapsDelCrm"] = cliente.get("googleMaps", "")
        placeId = placeIdDalRiempimento(cliente.get("googleMaps"))
        if placeId:
            cliente["googleMaps"] = placeId  # la fonte Google Maps legge il place id senza ricerca
        clienti.append(cliente)
    return clienti


def trovaFoglioDelCliente(idCliente):
    """Numero del foglio che contiene il cliente (cerca prima nelle regioni scelte, solo nei fogli del suo tipo), oppure ''."""
    cercato = str(idCliente).strip().upper()
    # codice nuovo: il blocco è nel codice stesso (S1_BEB_PIE_007 sta nel blocco S1_BEB_PIE)
    if re.match(r"^S\d_[A-Z]{3}_[A-Z]{3}_\d+$", cercato):
        blocco = "_".join(cercato.split("_")[:3])
        return next((voce["numero"] for voce in comune.TUTTI_I_FOGLI if voce.get("blocco") == blocco), "")
    sigla = cercato.split("_")[2] if cercato.count("_") >= 3 else ""
    candidati = [voce for voce in comune.INDUSTRIE if not sigla or voce["sigla"] == sigla]
    for voce in candidati:
        try:
            righe = righeDelFoglio(voce["idCrm"])
        except ErroreDelCrm:
            continue
        if any(riga and str(riga[0]).strip().upper() == cercato for riga in righe[2:]):
            return voce["numero"]
    return ""

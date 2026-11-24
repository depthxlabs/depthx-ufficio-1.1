"""La bolla del cliente (Michele, 11/11/2026, task #570, #571, #572).

La bolla è il file _00_Bolla.json nella cartella del cliente su Drive (percorso in _03_RegoleDelCoordinatore.json). Nasce
all'inizio con il passo 0 e ogni passo la aggiorna: passo, esito, motivo, ora e file prodotti. Formato approvato da Michele:
idCliente, NomeAziendaCliente, tipoCliente, PacchettoSitoInBaseAlMaterialeEsistenteDelCliente, versione, passo, esito, motivo,
ora, materiale, home, fileProdotti.

Il passo dopo parte solo se la bolla è GO e se i file che elenca esistono nel banco di lavoro del cliente
(_02_SitoDelClienteInCorso/<idCliente>). Il risultato di ogni passo GO si salva nel banco in _passi/<numero>.json: alla
riaccensione la fabbrica riparte dal primo passo senza risultato GO, non più dal passo 1.
"""

import datetime
import json
import subprocess
from pathlib import Path

REGOLE = Path(__file__).absolute().parent / "_03_RegoleDelCoordinatore.json"
CARTELLA_DEI_PASSI = "_passi"


class BollaNonValida(Exception):
    pass


def regole():
    return json.loads(REGOLE.read_text(encoding="utf-8-sig"))


def rclone(r, scrittura, idDrive, *argomenti, ingresso=None):
    remoto = r["remotoDiScrittura"] if scrittura else r["remotoDiLettura"]
    configurazione = r["configurazioneDiScrittura"] if scrittura else r["configurazioneDiLettura"]
    return subprocess.run([r["rclone"], *argomenti[:-1], f"{remoto}:{argomenti[-1]}", "--drive-root-folder-id", idDrive,
                           "--config", configurazione], input=ingresso, capture_output=True, encoding="utf-8", errors="ignore",
                          timeout=int(r["secondiMassimiDiRclone"]), creationflags=subprocess.CREATE_NO_WINDOW)


def leggiLaBolla(idCliente, idDrive):
    r = regole()
    esito = rclone(r, False, idDrive, "cat", r["percorsoDellaBollaSuDrive"])
    if esito.returncode != 0 or not esito.stdout.strip():
        raise BollaNonValida(f"{idCliente}: bolla assente su Drive ({r['percorsoDellaBollaSuDrive']})")
    bolla = json.loads(esito.stdout)
    if bolla.get("idCliente") != idCliente:
        raise BollaNonValida(f"{idCliente}: la bolla su Drive è di un altro cliente ({bolla.get('idCliente')})")
    return bolla


def bollaDavveroAssente(idDrive):
    """True solo se Drive risponde e il file della bolla non c'è: un errore di rete non vale come bolla assente."""
    r = regole()
    cartella, _, nome = r["percorsoDellaBollaSuDrive"].rpartition("/")
    esito = rclone(r, False, idDrive, "lsf", cartella)
    # la cartella della bolla che non esiste ancora è una bolla assente, non un errore di rete (rclone: "directory not found")
    if esito.returncode != 0 and "directory not found" in (esito.stderr or "").lower():
        return True
    return esito.returncode == 0 and nome not in [riga.strip() for riga in esito.stdout.splitlines()]


def creaLaBollaIniziale(idCliente, idDrive, nome="", tipo=""):
    """Michele, 13/11/2026: un cliente scaricato dopo la creazione delle bolle non ha la bolla. La fabbrica la crea al passo 0
    (GO, nessun file prodotto) e il cliente parte, invece di fermarsi. Si crea solo se il file manca davvero su Drive."""
    if not bollaDavveroAssente(idDrive):
        raise BollaNonValida(f"{idCliente}: bolla non letta da Drive, ma il file potrebbe esistere: nessuna bolla nuova scritta")
    bolla = {"idCliente": idCliente, "NomeAziendaCliente": nome, "tipoCliente": tipo, "PacchettoSitoInBaseAlMaterialeEsistenteDelCliente": "",
             "versione": 1, "passo": 0, "esito": "GO", "motivo": "bolla creata dalla fabbrica: mancava su Drive",
             "ora": datetime.datetime.now().astimezone().isoformat(timespec="seconds"), "materiale": {}, "home": "", "fileProdotti": []}
    return scriviLaBolla(bolla, idDrive)


def scriviLaBolla(bolla, idDrive):
    r = regole()
    testo = json.dumps(bolla, ensure_ascii=False, indent=2)
    esito = rclone(r, True, idDrive, "rcat", r["percorsoDellaBollaSuDrive"], ingresso=testo)
    if esito.returncode != 0:
        raise BollaNonValida(f"{bolla['idCliente']}: bolla non scritta su Drive: " + (esito.stderr or esito.stdout).strip()[-300:])
    riletta = leggiLaBolla(bolla["idCliente"], idDrive)
    if riletta != bolla:
        raise BollaNonValida(f"{bolla['idCliente']}: la bolla riletta da Drive è diversa da quella scritta")
    return bolla


def controllaLaBolla(bolla, banco):
    """Prima di ogni passo: la bolla è GO e i file che elenca esistono nel banco di lavoro."""
    if bolla.get("esito") != "GO":
        raise BollaNonValida(f"{bolla['idCliente']}: la bolla non è GO (passo {bolla.get('passo')}: {bolla.get('motivo')})")
    mancano = [f for f in bolla.get("fileProdotti") or [] if not (Path(banco) / f).is_file()]
    if mancano:
        raise BollaNonValida(f"{bolla['idCliente']}: mancano nel banco di lavoro i file della bolla: " + ", ".join(mancano))


def aggiornaLaBolla(bolla, idDrive, passo, esito, motivo="", fileProdotto=None):
    bolla = {**bolla, "passo": passo, "esito": esito, "motivo": str(motivo)[:900],
             "ora": datetime.datetime.now().astimezone().isoformat(timespec="seconds")}
    if fileProdotto and fileProdotto not in bolla.get("fileProdotti", []):
        bolla["fileProdotti"] = [*bolla.get("fileProdotti", []), fileProdotto]
    spedisciLaBolla(bolla, idDrive)  # Pitstop 1 (task #605): la fabbrica non aspetta Drive
    return bolla


# Il pitstop (Michele, 11/11/2026): ogni scrittura della bolla su Drive costava 8 secondi e fermava la fabbrica a ogni passo.
# Ora la bolla si spedisce a Drive in un filo a parte: la fabbrica va avanti subito, il filo scrive sempre l'ultima versione
# (se nel frattempo ne arriva una più nuova, quella vecchia non si scrive più). attendiLaBolla() aspetta che l'ultima sia su
# Drive e la rilegge per controllo: il coordinatore la chiama alla fine di ogni cliente e prima di ogni stop.
import threading

_daSpedire = {}           # idDrive -> ultima bolla da scrivere
_errori = {}              # idDrive -> errore dell'ultima scrittura
_condizione = threading.Condition()
_filo = None


def _spedizioniere():
    while True:
        with _condizione:
            while not _daSpedire:
                _condizione.wait()
            idDrive, bolla = next(iter(_daSpedire.items()))
        try:
            r = regole()
            esito = rclone(r, True, idDrive, "rcat", r["percorsoDellaBollaSuDrive"], ingresso=json.dumps(bolla, ensure_ascii=False, indent=2))
            errore = None if esito.returncode == 0 else (esito.stderr or esito.stdout).strip()[-300:]
        except Exception as eccezione:  # noqa: BLE001
            errore = str(eccezione)
        with _condizione:
            if _daSpedire.get(idDrive) is bolla:
                del _daSpedire[idDrive]
            if errore:
                _errori[idDrive] = errore
            else:
                _errori.pop(idDrive, None)
            _condizione.notify_all()


def spedisciLaBolla(bolla, idDrive):
    global _filo
    with _condizione:
        _daSpedire[idDrive] = bolla
        if _filo is None or not _filo.is_alive():
            _filo = threading.Thread(target=_spedizioniere, name="bollaSuDrive", daemon=True)
            _filo.start()
        _condizione.notify_all()


def attendiLaBolla(bolla, idDrive):
    """Aspetta che l'ultima bolla sia scritta su Drive e la rilegge: deve essere uguale a quella del coordinatore."""
    with _condizione:
        while idDrive in _daSpedire:
            _condizione.wait(timeout=5)
        errore = _errori.pop(idDrive, None)
    if errore:
        scriviLaBolla(bolla, idDrive)  # un'ultima volta, aspettando, con la rilettura
        return bolla
    if leggiLaBolla(bolla["idCliente"], idDrive) != bolla:
        scriviLaBolla(bolla, idDrive)
    return bolla


def salvaIlPasso(banco, numero, risultato):
    """Il risultato GO di un passo nel banco di lavoro, per la ripresa. Restituisce il percorso relativo al banco."""
    relativo = f"{CARTELLA_DEI_PASSI}/{numero}.json"
    file = Path(banco) / relativo
    file.parent.mkdir(parents=True, exist_ok=True)
    file.write_text(json.dumps(risultato, ensure_ascii=False, indent=1), encoding="utf-8")
    return relativo


def passoSalvato(banco, numero):
    file = Path(banco) / CARTELLA_DEI_PASSI / f"{numero}.json"
    return json.loads(file.read_text(encoding="utf-8")) if file.is_file() else None

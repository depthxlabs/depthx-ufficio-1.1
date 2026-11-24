"""Il tracciamento di ogni azione della fabbrica (Michele, 11/11/2026): quando inizia, quando finisce, quanto dura, con che
esito, e dentro quale azione sta (gli step intermedi).

Ogni sezione della fabbrica ha il suo registro in _04_LogDiOgniSezione/<sezione>/<anno>/<mese>/<giorno>/_01_AzioniDelGiorno.sqlite:
un database SQLite per giorno, veloce da scrivere e da interrogare. La sezione si riconosce dalla cartella del passo in cui sta
la funzione (_01_LetturaDellaSezione... -> _02_LogLetturaDellaSezione..., e così via); il coordinatore e il passo 2 (scelta del
template, che non ha una cartella sua) scrivono in _01_LogCoordinatore.

Come funziona: strumenta() avvolge, una volta sola all'avvio, ogni funzione dei passi della fabbrica e le funzioni del
coordinatore. Nessun file dei passi va toccato: ogni chiamata diventa una riga con inizio, fine, millisecondi, esito, errore,
cliente, fabbrica (pid) e azione padre. Le chiamate ripetute molte volte sotto la stessa azione (per esempio una funzione per
ogni frase) dopo le prime RIGHE_PER_AZIONE_RIPETUTA si sommano in una riga sola con il conteggio, così il registro resta
leggero. Le righe si scrivono in un filo a parte, a gruppi, per non rallentare la fabbrica; alla chiusura del processo il filo
scrive quello che resta.
"""

import atexit
import contextvars
import datetime
import functools
import inspect
import os
import queue
import sqlite3
import sys
import threading
import time
import traceback
import uuid
from pathlib import Path

FABBRICA = Path(__file__).absolute().parents[2]
CARTELLA_DEI_LOG = FABBRICA / "_04_LogDiOgniSezione"
SEZIONE_DEL_COORDINATORE = "_01_LogCoordinatore"
SEZIONI = {
    "_01_LetturaDellaSezioneDelTipoDiClienteDalCRM": "_02_LogLetturaDellaSezioneDelTipoDiClienteDalCRM",
    "_03_DownloadDelMaterialeDelClienteDaDrive": "_03_LogDownloadDelMaterialeDelClienteDaDrive",
    "_04_MiglioramentoDelleFotoEsistentiDelCliente": "_04_LogMiglioramentoDelleFotoEsistentiDelCliente",
    "_05_PersonalizzazioneDelTemplateConLidentitàDelCliente": "_05_LogPersonalizzazioneDelTemplateConLidentitàDelCliente",
    "_06_PubblicazioneSuDepthxlabsDemo": "_06_LogPubblicazioneSuDepthxlabsDemo",
    "_07_CollaudoBasicoDellaDemo": "_07_LogCollaudoBasicoDellaDemo",
    "_08_ApprovazioneProductManager": "_08_LogApprovazioneProductManager",
    "_09_EsportazioneSuDrive": "_09_LogEsportazioneSuDrive",
}
PACCHETTO_DEI_PASSI = "_03_CicloDiProduzionePerOgniCliente"
RIGHE_PER_AZIONE_RIPETUTA = 30
TABELLA = """CREATE TABLE IF NOT EXISTS azioni (
    idAzione TEXT PRIMARY KEY, padre TEXT, profondita INTEGER, idCliente TEXT, fabbrica INTEGER, sezione TEXT,
    azione TEXT, modulo TEXT, inizio TEXT, fine TEXT, millisecondi REAL, esito TEXT, errore TEXT, ripetizioni INTEGER)"""
INDICI = ("CREATE INDEX IF NOT EXISTS azioniPerCliente ON azioni(idCliente, inizio)",
          "CREATE INDEX IF NOT EXISTS azioniPerPadre ON azioni(padre)")

azioneInCorso = contextvars.ContextVar("azioneInCorso", default=None)  # (idAzione, profondita, conteggi delle ripetute)
clienteInCorso = contextvars.ContextVar("clienteInCorso", default="")
coda = queue.Queue()
avvolte = {}  # funzione originale -> funzione avvolta


def adesso():
    return datetime.datetime.now().astimezone().isoformat(timespec="milliseconds")


def sezioneDelModulo(nomeDelModulo):
    for parte in nomeDelModulo.split("."):
        if parte in SEZIONI:
            return SEZIONI[parte]
    return SEZIONE_DEL_COORDINATORE


def fileDelGiorno(sezione):
    oggi = datetime.date.today()
    cartella = CARTELLA_DEI_LOG / sezione / f"{oggi:%Y}" / f"{oggi:%m}" / f"{oggi:%d}"
    cartella.mkdir(parents=True, exist_ok=True)
    return cartella / "_01_AzioniDelGiorno.sqlite"


# ------------------------------------------------------------------------------------------ lo scrittore, in un filo a parte

def scrittore():
    connessioni = {}
    while True:
        voci = [coda.get()]
        try:
            while len(voci) < 500:
                voci.append(coda.get(timeout=0.3))
        except queue.Empty:
            pass
        fine = any(voce is None for voce in voci)
        perFile = {}
        for voce in voci:
            if voce is not None:
                perFile.setdefault(fileDelGiorno(voce[1]), []).append(voce)
        for file, righe in perFile.items():
            try:
                db = connessioni.get(file)
                if db is None:
                    db = connessioni[file] = sqlite3.connect(file, timeout=30, check_same_thread=False)
                    db.execute("PRAGMA journal_mode=WAL")
                    db.execute("PRAGMA synchronous=NORMAL")
                    db.execute(TABELLA)
                    for indice in INDICI:
                        db.execute(indice)
                with db:
                    for tipo, _, dati in righe:
                        if tipo == "inizio":
                            db.execute("INSERT OR REPLACE INTO azioni (idAzione, padre, profondita, idCliente, fabbrica, sezione, azione, modulo,"
                                       " inizio, esito, ripetizioni) VALUES (?,?,?,?,?,?,?,?,?, 'in corso', 1)", dati)
                        elif tipo == "fine":
                            db.execute("UPDATE azioni SET fine=?, millisecondi=?, esito=?, errore=? WHERE idAzione=?", dati)
                        else:  # le ripetute sommate in una riga sola
                            db.execute("INSERT OR REPLACE INTO azioni (idAzione, padre, profondita, idCliente, fabbrica, sezione, azione, modulo,"
                                       " inizio, fine, millisecondi, esito, errore, ripetizioni) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)", dati)
            except sqlite3.Error:
                pass  # il registro non ferma mai la fabbrica
        for _ in voci:
            coda.task_done()
        if fine:
            return


filo = threading.Thread(target=scrittore, name="tracciamentoDelleAzioni", daemon=True)


def chiudi():
    if filo.is_alive():
        coda.put(None)
        filo.join(timeout=10)


# ------------------------------------------------------------------------------------------ l'azione tracciata

class azione:
    """Un'azione tracciata, da usare anche a mano: with azione("download delle foto", modulo=__name__): ..."""

    def __init__(self, nome, modulo="", idCliente=None):
        self.nome, self.modulo, self.idCliente = nome, modulo, idCliente

    def __enter__(self):
        if not filo.is_alive():
            try:
                filo.start()
            except RuntimeError:
                pass
        if self.idCliente:
            self.gettoneCliente = clienteInCorso.set(self.idCliente)
        padre = azioneInCorso.get()
        self.sezione = sezioneDelModulo(self.modulo)
        self.idAzione, self.profondita = uuid.uuid4().hex, (padre[1] + 1 if padre else 0)
        self.inizio, self.partenza = adesso(), time.perf_counter()
        # le ripetute: dopo RIGHE_PER_AZIONE_RIPETUTA chiamate uguali sotto lo stesso padre si sommano
        self.sommata = None
        if padre is not None:
            conteggi = padre[2]
            chiave = (self.nome, self.modulo)
            conteggi[chiave] = conteggi.get(chiave, 0) + 1
            if conteggi[chiave] > RIGHE_PER_AZIONE_RIPETUTA:
                self.sommata = (padre, chiave)
        if self.sommata is None:
            coda.put(("inizio", self.sezione, (self.idAzione, padre[0] if padre else None, self.profondita, clienteInCorso.get(),
                                                os.getpid(), self.sezione, self.nome, self.modulo, self.inizio)))
        self.gettone = azioneInCorso.set((self.idAzione, self.profondita, {}))
        return self

    def __exit__(self, tipo, errore, traccia):
        millisecondi = (time.perf_counter() - self.partenza) * 1000
        azioneInCorso.reset(self.gettone)
        esito = "OK" if tipo is None else ("FERMATO" if tipo.__name__ in ("ClienteFermato", "BollaNonValida") else "ERRORE")
        testoDellErrore = "" if tipo is None else (f"{tipo.__name__}: {errore}"[:1500])
        if self.sommata is None:
            coda.put(("fine", self.sezione, (adesso(), round(millisecondi, 2), esito, testoDellErrore, self.idAzione)))
        else:
            padre, chiave = self.sommata
            somme = padre[2].setdefault(("somma",) + chiave, {"id": uuid.uuid4().hex, "inizio": self.inizio, "ms": 0.0, "n": 0, "errori": 0})
            somme["ms"] += millisecondi
            somme["n"] += 1
            somme["errori"] += tipo is not None
            coda.put(("somma", self.sezione, (somme["id"], padre[0], self.profondita, clienteInCorso.get(), os.getpid(), self.sezione,
                                              f"{self.nome} (dopo le prime {RIGHE_PER_AZIONE_RIPETUTA}, sommate)", self.modulo,
                                              somme["inizio"], adesso(), round(somme["ms"], 2),
                                              "OK" if not somme["errori"] else f"ERRORI: {somme['errori']}", "", somme["n"])))
        if self.idCliente:
            clienteInCorso.reset(self.gettoneCliente)
        return False


# ------------------------------------------------------------------------------------------ l'avvolgimento delle funzioni

def avvolgi(funzione):
    if funzione in avvolte or getattr(funzione, "_tracciata", False):
        return avvolte.get(funzione, funzione)
    try:
        firma = inspect.signature(funzione)
        conCliente = "idCliente" in firma.parameters
    except (TypeError, ValueError):
        firma, conCliente = None, False

    @functools.wraps(funzione)
    def tracciata(*argomenti, **chiavi):
        idCliente = None
        if conCliente:
            try:
                idCliente = firma.bind_partial(*argomenti, **chiavi).arguments.get("idCliente")
            except TypeError:
                pass
        with azione(funzione.__name__, funzione.__module__, idCliente if isinstance(idCliente, str) else None):
            return funzione(*argomenti, **chiavi)

    tracciata._tracciata = True
    avvolte[funzione] = tracciata
    return tracciata


def daTracciare(modulo, nomeDelModulo):
    return nomeDelModulo.startswith(PACCHETTO_DEI_PASSI) or nomeDelModulo in ("_01_CoordinatoreDellaFabbrica", "__main__", "_04_BollaDelCliente")


def strumenta():
    """Avvolge ogni funzione dei passi della fabbrica e del coordinatore, e ogni riferimento a quelle funzioni negli altri
    moduli (gli import "from ... import funzione"). Si chiama una volta, dopo gli import del coordinatore."""
    moduli = [(nome, modulo) for nome, modulo in list(sys.modules.items()) if modulo is not None and daTracciare(modulo, nome)]
    for nome, modulo in moduli:
        for attributo, valore in list(vars(modulo).items()):
            if (inspect.isfunction(valore) and valore.__module__ == nome and valore.__name__ != "<lambda>"
                    and not attributo.startswith("__") and valore.__name__ not in ("registraEvento", "registraErrore")):
                setattr(modulo, attributo, avvolgi(valore))
    for nome, modulo in moduli:
        for attributo, valore in list(vars(modulo).items()):
            if inspect.isfunction(valore) and valore in avvolte:
                setattr(modulo, attributo, avvolte[valore])
    if not filo.is_alive():
        filo.start()
    atexit.register(chiudi)
    return len(avvolte)

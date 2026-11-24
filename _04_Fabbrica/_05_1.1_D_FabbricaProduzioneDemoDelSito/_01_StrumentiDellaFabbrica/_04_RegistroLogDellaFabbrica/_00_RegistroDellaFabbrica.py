"""Il registro della fabbrica, letto dal Centro Gestione: un file per giorno in _02_RegistroProduzione.

- _01_EventiDellaProduzione/AAAA/MM/GG/_01_EventiDelGiorno.jsonl: un evento per riga (inizio_cliente, passo, fine_cliente,
  fabbrica), con ora, pid e versione 2 (il ciclo per ogni cliente del 7/11/2026);
- _02_StatoDelleDemo/AAAA/MM/GG/_01_StatoDelleDemoDelGiorno.json: per ogni cliente del giorno i passi con esito e dettagli;
- _03_MessaggiDellaProduzione/AAAA/MM/GG/_01_MessaggiDelGiorno.txt: una riga leggibile per ogni evento;
- _04_ErroriDellaProduzione/AAAA/MM/GG/_01_ErroriDelGiorno.txt: gli errori con il loro dettaglio.
"""

import contextlib
import ctypes
import datetime
import json
import os
import re
import time
from pathlib import Path

REGISTRO = Path(__file__).absolute().parent / "_02_RegistroProduzione"


@contextlib.contextmanager
def unaScritturaAllaVolta():
    """Il blocco di Windows del registro: aspetta che nessun'altra fabbrica stia scrivendo. Windows lo libera da solo se il
    processo finisce."""
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.CreateMutexW.restype = ctypes.c_void_p
    kernel.CreateMutexW.argtypes = (ctypes.c_void_p, ctypes.c_bool, ctypes.c_wchar_p)
    kernel.WaitForSingleObject.argtypes = (ctypes.c_void_p, ctypes.c_uint32)
    kernel.ReleaseMutex.argtypes = (ctypes.c_void_p,)
    kernel.CloseHandle.argtypes = (ctypes.c_void_p,)
    blocco = kernel.CreateMutexW(None, False, "Global\\DepthXFabbricaRegistro")
    kernel.WaitForSingleObject(blocco, 60000)
    try:
        yield
    finally:
        kernel.ReleaseMutex(blocco)
        kernel.CloseHandle(blocco)
VERSIONE = 6  # 11/11/2026 sera: una foto per area su computer e telefono, 3D più ricco con foto e scritte che non escono mai; tutte le demo si rifanno (Michele)


# Codici vecchi e nuovi dei clienti (Michele, 9/11/2026): il motore scrive per ogni cliente il codice nuovo (S1_HOT_LOM_001) e il
# vecchio (C_S_HOT_0001) nel campo codiceVecchio del suo stato. La fabbrica riconosce lo stesso cliente con tutti e due.
STATO_DEL_MOTORE = (Path(__file__).absolute().parents[3] / "_01_1.1_A_MotoreGestioneAcquisizioneMaterialeClienti" / "_01_StrumentiDelMotore"
                    / "_05_RegistroEStatoDelMotore" / "stato.json")
_codici = {"letto": 0, "nuovo": {}}


def codiceNuovo(idCliente):
    """Il codice nuovo del cliente (lo stesso, se è già nuovo o non ha un codice nuovo)."""
    if os.path.exists(STATO_DEL_MOTORE) and os.path.getmtime(STATO_DEL_MOTORE) != _codici["letto"]:
        try:
            clienti = json.loads(STATO_DEL_MOTORE.read_text(encoding="utf-8-sig")).get("clienti", {})
            _codici["nuovo"] = {voce["codiceVecchio"]: nuovo for nuovo, voce in clienti.items() if voce.get("codiceVecchio")}
            _codici["letto"] = os.path.getmtime(STATO_DEL_MOTORE)
        except (OSError, ValueError):
            pass
    return _codici["nuovo"].get(idCliente, idCliente)


def stessoCliente(primo, secondo):
    return bool(primo) and bool(secondo) and codiceNuovo(primo) == codiceNuovo(secondo)


def ora():
    return datetime.datetime.now().astimezone().isoformat(timespec="seconds")


def fileDelGiorno(cartella, nome):
    oggi = datetime.date.today()
    file = REGISTRO / cartella / f"{oggi:%Y}" / f"{oggi:%m}" / f"{oggi:%d}" / nome
    file.parent.mkdir(parents=True, exist_ok=True)
    return file


def scriviMessaggio(testo):
    with fileDelGiorno("_03_MessaggiDellaProduzione", "_01_MessaggiDelGiorno.txt").open("a", encoding="utf-8") as file:
        file.write(f"{ora()} {testo}\n")


def compatto(valore, livello=0):
    """I dettagli di un passo in breve: testi di al massimo 300 caratteri, elenchi di al massimo 20 voci, tre livelli."""
    if isinstance(valore, dict):
        if livello >= 3:
            return f"{len(valore)} voci"
        return {str(chiave): compatto(voce, livello + 1) for chiave, voce in list(valore.items())[:40]}
    if isinstance(valore, (list, tuple, set)):
        valore = list(valore)
        if livello >= 3:
            return f"{len(valore)} voci"
        return [compatto(voce, livello + 1) for voce in valore[:20]] + ([f"e altre {len(valore) - 20}"] if len(valore) > 20 else [])
    if isinstance(valore, str):
        return valore[:300]
    if valore is None or isinstance(valore, (int, float, bool)):
        return valore
    return str(valore)[:300]


def registraEvento(tipo, **dati):
    if "dettagli" in dati:
        dati["dettagli"] = compatto(dati["dettagli"])
    # con più fabbriche accese (task #582) il registro si scrive una fabbrica alla volta: lo stato del giorno si legge e si
    # riscrive intero, e due scritture insieme lo rompevano (11/11/2026)
    with unaScritturaAllaVolta():
        _registraEvento(tipo, dati)


def _registraEvento(tipo, dati):
    evento = {"ora": ora(), "tipo": tipo, "pid": os.getpid(), "versione": VERSIONE, **dati}
    with fileDelGiorno("_01_EventiDellaProduzione", "_01_EventiDelGiorno.jsonl").open("a", encoding="utf-8") as file:
        file.write(json.dumps(evento, ensure_ascii=False, default=str) + "\n")
    if tipo == "passo":
        statoDelGiorno = fileDelGiorno("_02_StatoDelleDemo", "_01_StatoDelleDemoDelGiorno.json")
        stato = json.loads(statoDelGiorno.read_text(encoding="utf-8-sig")) if statoDelGiorno.is_file() else {"clienti": {}}
        cliente = stato["clienti"].setdefault(dati.get("idCliente", ""), {"passi": {}})
        cliente["passi"][dati.get("passo", "")] = {"esito": dati.get("esito", ""), "motivo": dati.get("motivo", ""),
                                                     "dettagli": dati.get("dettagli"), "ora": evento["ora"]}
        temporaneo = statoDelGiorno.with_suffix(f".{os.getpid()}.tmp")
        temporaneo.write_text(json.dumps(stato, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
        # Windows rifiuta la sostituzione se un altro programma tiene aperto il file in quel momento: la fabbrica si
        # chiudeva senza scrivere l'errore (12/11/2026). Si riprova fino a 5 secondi; se non riesce lo stato del giorno
        # resta quello di prima, l'evento è già nel registro e la fabbrica continua.
        for volta in range(20):
            try:
                os.replace(temporaneo, statoDelGiorno)
                break
            except PermissionError as errore:
                if volta == 19:
                    scriviMessaggio(f"stato del giorno non aggiornato, file occupato: {errore}")
                    with contextlib.suppress(OSError):
                        temporaneo.unlink()
                else:
                    time.sleep(0.25)
    scriviMessaggio(f"{tipo} {dati.get('idCliente', '')} {dati.get('passo', '')} {dati.get('esito', '')} {dati.get('motivo', '')}".strip())


def registraErrore(idCliente, passo, dettaglio):
    with fileDelGiorno("_04_ErroriDellaProduzione", "_01_ErroriDelGiorno.txt").open("a", encoding="utf-8") as file:
        file.write(f"{ora()} {idCliente} {passo}\n{dettaglio}\n")


def famigliaDelMotivo(motivo):
    """Il motivo di un NOTGO senza numeri, nomi tra virgolette e codici: due NOTGO con la stessa famiglia sono lo stesso problema."""
    testo = re.sub(r"\"[^\"]*\"|“[^”]*”|S\d_[A-Z]{3}_[A-Z]{3}_\d+|\d+", "", str(motivo or ""))
    return " ".join(testo.split())[:160]


def clientiFermiPerLoStessoMotivo():
    """Un cliente NOTGO si rifà una sola volta: con 2 NOTGO per lo stesso motivo resta fermo, con il motivo,
    finché quel motivo non viene corretto. {idCliente: motivo}"""
    conteggio, motivi = {}, {}
    try:
        corretti = json.loads((Path(__file__).absolute().parents[2] / "_02_CoordinatoreDiLavoroDellaFabbrica" / "_03_RegoleDelCoordinatore.json")
                              .read_text(encoding="utf-8-sig")).get("motiviCorretti") or []
    except (OSError, ValueError):
        corretti = []
    for file in (REGISTRO / "_01_EventiDellaProduzione").rglob("_01_EventiDelGiorno.jsonl"):
        for riga in file.read_text(encoding="utf-8-sig", errors="ignore").splitlines():
            try:
                evento = json.loads(riga)
            except ValueError:
                continue
            if (evento.get("tipo") == "fine_cliente" and evento.get("versione") == VERSIONE and evento.get("esito") == "NOTGO"
                    and not any(m.lower() in str(evento.get("motivo") or "").lower() for m in corretti)):
                chiave = (codiceNuovo(evento.get("idCliente")), famigliaDelMotivo(evento.get("motivo")))
                conteggio[chiave] = conteggio.get(chiave, 0) + 1
                motivi[chiave[0]] = str(evento.get("motivo") or "")[:300]
    return {idCliente: motivi[idCliente] for (idCliente, _), volte in conteggio.items() if volte >= 2}


def clientiGiaLavorati():
    """I clienti con la demo pronta per l'invio, quelli senza materiale minimo e quelli fermi per lo stesso NOTGO due volte."""
    lavorati = set(clientiFermiPerLoStessoMotivo())
    for file in (REGISTRO / "_01_EventiDellaProduzione").rglob("_01_EventiDelGiorno.jsonl"):
        for riga in file.read_text(encoding="utf-8-sig", errors="ignore").splitlines():
            try:
                evento = json.loads(riga)
            except ValueError:
                continue
            # un cliente senza il materiale minimo non si riprova a ogni giro (Michele, 9/11/2026): resta tra le fermate
            if (evento.get("tipo") == "fine_cliente" and evento.get("versione") == VERSIONE
                    and (evento.get("esito") == "PRONTA PER L'INVIO" or "materiale insufficiente" in str(evento.get("motivo")))):
                lavorati.add(codiceNuovo(evento.get("idCliente")))
    return lavorati

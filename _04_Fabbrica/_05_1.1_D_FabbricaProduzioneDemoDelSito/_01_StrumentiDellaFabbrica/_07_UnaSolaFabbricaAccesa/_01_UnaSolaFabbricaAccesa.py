"""Le fabbriche accese insieme (Michele, 7/11/2026; più fabbriche insieme dall'11/11/2026, task #582).

Più fabbriche servono solamente per produrre più demo Advanced contemporaneamente. Quante possono essere accese insieme lo
dice fabbricheInsieme in _02_CoordinatoreDiLavoroDellaFabbrica/_03_RegoleDelCoordinatore.json (1 = una sola fabbrica,
come prima). Si può perché ogni cliente ha il suo banco di lavoro e la sua bolla, e riparte dall'ultimo passo GO.
Tre blocchi di Windows, con un nome unico:
- un posto per ogni fabbrica accesa: il coordinatore, appena parte, prende il primo posto libero; se i posti sono tutti
  presi esce subito;
- un blocco per ogni cliente: due fabbriche non lavorano mai lo stesso cliente;
- il blocco della pubblicazione: il Worker delle demo si pubblica una fabbrica alla volta.
Windows libera ogni blocco da solo quando il processo finisce, anche con lo stop forzato del Centro Gestione: non resta mai
un blocco dimenticato.
"""

import contextlib
import ctypes
import json
from pathlib import Path

NOME_DEL_BLOCCO = "Global\\DepthXFabbricaDeiSitiDemo"
NOME_DEL_CLIENTE = "Global\\DepthXFabbricaCliente_"
NOME_DELLA_PUBBLICAZIONE = "Global\\DepthXFabbricaPubblicazione"
REGOLE = Path(__file__).absolute().parents[2] / "_02_CoordinatoreDiLavoroDellaFabbrica" / "_03_RegoleDelCoordinatore.json"
GIA_PRESO = 183
ATTESA_INFINITA = 0xFFFFFFFF
bloccoTenuto = None
kernel = ctypes.WinDLL("kernel32", use_last_error=True)
kernel.CreateMutexW.restype = ctypes.c_void_p
kernel.CreateMutexW.argtypes = (ctypes.c_void_p, ctypes.c_bool, ctypes.c_wchar_p)
kernel.WaitForSingleObject.argtypes = (ctypes.c_void_p, ctypes.c_uint32)
kernel.ReleaseMutex.argtypes = (ctypes.c_void_p,)
kernel.CloseHandle.argtypes = (ctypes.c_void_p,)


def fabbricheInsieme():
    try:
        return max(1, int(json.loads(REGOLE.read_text(encoding="utf-8-sig")).get("fabbricheInsieme", 1)))
    except (OSError, ValueError):
        return 1


def prendiIlBlocco(nome):
    """Il blocco con questo nome, se nessun altro processo lo tiene; altrimenti None."""
    blocco = kernel.CreateMutexW(None, False, nome)
    if not blocco:
        return None
    if ctypes.get_last_error() == GIA_PRESO:
        kernel.CloseHandle(blocco)
        return None
    return blocco


def unaSolaFabbricaAccesa():
    """Vero se questa fabbrica ha preso un posto libero, entro fabbricheInsieme (il nome di prima resta per il primo posto)."""
    global bloccoTenuto
    for posto in range(1, fabbricheInsieme() + 1):
        blocco = prendiIlBlocco(NOME_DEL_BLOCCO if posto == 1 else f"{NOME_DEL_BLOCCO}_{posto}")
        if blocco:
            bloccoTenuto = blocco
            return True
    return False


@contextlib.contextmanager
def clienteLibero(idCliente):
    """Il cliente si lavora solo se nessun'altra fabbrica lo sta lavorando: dentro il blocco vale True, altrimenti False."""
    blocco = prendiIlBlocco(NOME_DEL_CLIENTE + "".join(c if c.isalnum() or c == "_" else "_" for c in str(idCliente)))
    try:
        yield bool(blocco)
    finally:
        if blocco:
            kernel.CloseHandle(blocco)


@contextlib.contextmanager
def unaPubblicazioneAllaVolta():
    """Aspetta che nessun'altra fabbrica stia pubblicando il Worker delle demo, poi pubblica."""
    blocco = kernel.CreateMutexW(None, False, NOME_DELLA_PUBBLICAZIONE)
    kernel.WaitForSingleObject(blocco, ATTESA_INFINITA)
    try:
        yield
    finally:
        kernel.ReleaseMutex(blocco)
        kernel.CloseHandle(blocco)

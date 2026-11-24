r"""IL CRM SU GOOGLE SHEETS, Linea 1.1 Outbound Websites: il modulo comune di chi legge e scrive il CRM.

Il CRM sta soltanto su Drive, nella cartella "_01_CRM Linea 1.1": un Foglio Google per sezione, tipo e regione.
L'accesso è quello di rclone in scrittura (rclone_scrittura.conf): rclone rinnova l'accesso, il modulo lo legge e non lo stampa mai.

  fogli()                          i fogli del CRM: id, percorso ("[02] S2_.../[02] BED.../[06] S2_BEB_LOM"), nome, cartella
  leggi(idFoglio)                  le righe del primo foglio, come liste di testi
  scriviCelle(idFoglio, celle)     celle = {"B5": "valore", ...}
  scriviRighe(idFoglio, riga, righe)   righe dalla riga indicata in giù
  cancellaRighe(idFoglio, numeri)  le righe indicate (numeri da 1)
  nuovoFoglio(modello, cartella, nome) la copia di un foglio, senza i clienti dalla riga 3
  firma()                          cambia quando un foglio del CRM cambia
"""
import json
import urllib.error
import re
import subprocess
import time
import urllib.parse
import urllib.request

CARTELLA_DEL_CRM = "1Mqc9nDqLQpPIk21agOP87Hr9WipKphva"
RCLONE = r"C:\_02_DepthXSoftware\_02_RCloneDepthX\rclone.exe"
CONFIGURAZIONE = r"C:\_02_DepthXSoftware\_02_RCloneDepthX\rclone_scrittura.conf"
FOGLIO_GOOGLE = "application/vnd.google-apps.spreadsheet"
CARTELLA_GOOGLE = "application/vnd.google-apps.folder"
PRIMA_RIGA_CLIENTI = 3
_ACCESSO = {"valore": "", "fino": 0}


def accesso():
    """L'accesso a Google di rclone in scrittura, rinnovato da rclone quando scade."""
    if _ACCESSO["valore"] and time.time() < _ACCESSO["fino"]:
        return _ACCESSO["valore"]
    subprocess.run([RCLONE, "lsf", "gdrivescrittura:", "--max-depth", "1", "--drive-root-folder-id", CARTELLA_DEL_CRM,
                    "--config", CONFIGURAZIONE], capture_output=True, timeout=120, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    testo = open(CONFIGURAZIONE, encoding="utf-8").read()
    sezione = testo.split("[gdrivescrittura]", 1)[1].split("\n[", 1)[0]
    gettone = json.loads(re.search(r"^token\s*=\s*(\{.*\})\s*$", sezione, re.M).group(1))
    _ACCESSO["valore"], _ACCESSO["fino"] = gettone["access_token"], time.time() + 1800
    return _ACCESSO["valore"]


def _chiama(metodo, indirizzo, corpo=None, tentativi=5):
    for tentativo in range(tentativi):
        richiesta = urllib.request.Request(indirizzo, method=metodo, data=None if corpo is None else json.dumps(corpo).encode("utf-8"),
                                           headers={"Authorization": "Bearer " + accesso(), "Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(richiesta, timeout=120) as risposta:
                dati = risposta.read()
                return json.loads(dati) if dati else {}
        except urllib.error.HTTPError as errore:
            if errore.code in (429, 500, 502, 503) and tentativo < tentativi - 1:
                time.sleep(20 * (tentativo + 1))
                continue
            if errore.code == 401 and tentativo < tentativi - 1:
                _ACCESSO["fino"] = 0
                continue
            raise RuntimeError(f"Google {errore.code}: {errore.read()[:300]!r}")


def _figli(cartella):
    trovati, pagina = [], ""
    while True:
        q = urllib.parse.quote(f"'{cartella}' in parents and trashed = false")
        d = _chiama("GET", f"https://www.googleapis.com/drive/v3/files?q={q}&pageSize=1000&fields=nextPageToken,files(id,name,mimeType,modifiedTime)"
                           + (f"&pageToken={pagina}" if pagina else ""))
        trovati += d.get("files", [])
        pagina = d.get("nextPageToken", "")
        if not pagina:
            return trovati


def fogli(tipo=FOGLIO_GOOGLE):
    """Tutti i fogli del CRM (o tutti i file del tipo indicato), con il percorso delle cartelle."""
    risultato, coda = [], [(CARTELLA_DEL_CRM, "")]
    while coda:
        cartella, percorso = coda.pop(0)
        for f in sorted(_figli(cartella), key=lambda x: x["name"]):
            dentro = f"{percorso}/{f['name']}" if percorso else f["name"]
            if f["mimeType"] == CARTELLA_GOOGLE:
                coda.append((f["id"], dentro))
            elif f["mimeType"] == tipo:
                risultato.append({"id": f["id"], "nome": f["name"], "percorso": dentro, "cartella": cartella, "modificato": f["modifiedTime"]})
    return sorted(risultato, key=lambda x: x["percorso"])


_PAGINE = {}


def _primaPagina(idFoglio):
    if idFoglio not in _PAGINE:
        d = _chiama("GET", f"https://sheets.googleapis.com/v4/spreadsheets/{idFoglio}?fields=sheets.properties")
        _PAGINE[idFoglio] = d["sheets"][0]["properties"]
    return _PAGINE[idFoglio]


def leggi(idFoglio, tentativi=5):
    """Le righe del primo foglio, come liste di testi (le celle vuote in fondo alla riga non ci sono).
    La lettura passa dall'esportazione di Drive in CSV: una chiamata per foglio, con i limiti di Drive e non quelli di Google Sheets
    (60 letture al minuto, troppo poche per i 117 fogli del CRM)."""
    import csv
    import io
    for tentativo in range(tentativi):
        richiesta = urllib.request.Request(f"https://www.googleapis.com/drive/v3/files/{idFoglio}/export?mimeType=text/csv",
                                           headers={"Authorization": "Bearer " + accesso()})
        try:
            with urllib.request.urlopen(richiesta, timeout=120) as risposta:
                testo = risposta.read().decode("utf-8-sig")
            break
        except urllib.error.HTTPError as errore:
            if errore.code in (401, 429, 500, 502, 503) and tentativo < tentativi - 1:
                _ACCESSO["fino"] = 0 if errore.code == 401 else _ACCESSO["fino"]
                time.sleep(5 * (tentativo + 1))
                continue
            raise RuntimeError(f"Google {errore.code}: {errore.read()[:300]!r}")
    righe = []
    for riga in csv.reader(io.StringIO(testo)):
        while riga and not riga[-1]:
            riga.pop()
        righe.append(riga)
    while righe and not righe[-1]:
        righe.pop()
    return righe


def colonna(numero):
    """1 -> A, 27 -> AA."""
    lettere = ""
    while numero:
        numero, resto = divmod(numero - 1, 26)
        lettere = chr(65 + resto) + lettere
    return lettere


def scriviCelle(idFoglio, celle):
    if not celle:
        return 0
    nome = _primaPagina(idFoglio)["title"]
    dati = [{"range": f"'{nome}'!{cella}", "values": [[valore]]} for cella, valore in celle.items()]
    for inizio in range(0, len(dati), 500):
        _chiama("POST", f"https://sheets.googleapis.com/v4/spreadsheets/{idFoglio}/values:batchUpdate",
                {"valueInputOption": "RAW", "data": dati[inizio:inizio + 500]})
    return len(dati)


def scriviRighe(idFoglio, riga, righe):
    if not righe:
        return 0
    nome = _primaPagina(idFoglio)["title"]
    _chiama("POST", f"https://sheets.googleapis.com/v4/spreadsheets/{idFoglio}/values:batchUpdate",
            {"valueInputOption": "RAW", "data": [{"range": f"'{nome}'!A{riga}", "values": righe}]})
    return len(righe)


def cancellaRighe(idFoglio, numeri):
    if not numeri:
        return 0
    pagina = _primaPagina(idFoglio)["sheetId"]
    richieste = [{"deleteDimension": {"range": {"sheetId": pagina, "dimension": "ROWS", "startIndex": n - 1, "endIndex": n}}}
                 for n in sorted(set(numeri), reverse=True)]
    _chiama("POST", f"https://sheets.googleapis.com/v4/spreadsheets/{idFoglio}:batchUpdate", {"requests": richieste})
    return len(richieste)


def nuovoFoglio(modello, cartella, nome):
    """La copia del foglio modello nella cartella indicata, senza i clienti dalla riga 3 in giù."""
    nuovo = _chiama("POST", f"https://www.googleapis.com/drive/v3/files/{modello}/copy", {"name": nome, "parents": [cartella]})["id"]
    proprieta = _primaPagina(nuovo)
    if proprieta.get("gridProperties", {}).get("rowCount", 0) >= PRIMA_RIGA_CLIENTI:
        _chiama("POST", f"https://sheets.googleapis.com/v4/spreadsheets/{nuovo}/values:batchClear",
                {"ranges": [f"'{proprieta['title']}'!A{PRIMA_RIGA_CLIENTI}:ZZ"]})
    return nuovo


def firma():
    """Cambia quando un foglio del CRM cambia: i nomi e le ore di modifica di tutti i fogli."""
    return "|".join(f["id"] + f["modificato"] for f in fogli())

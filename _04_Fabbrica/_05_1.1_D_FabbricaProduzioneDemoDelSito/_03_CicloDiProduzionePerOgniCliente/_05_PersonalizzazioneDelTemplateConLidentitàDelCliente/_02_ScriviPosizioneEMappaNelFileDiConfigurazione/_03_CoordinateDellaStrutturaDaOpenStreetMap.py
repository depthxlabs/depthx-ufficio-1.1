"""Le coordinate della struttura per la mappa di OpenStreetMap (Michele, 11/11/2026).

La mappa della pagina Dove siamo e contatti è quella di OpenStreetMap e si attiva con un clic. La scheda Google scaricata dal
motore non ha le coordinate: si ricavano dall'indirizzo pubblico della struttura con Nominatim, il servizio di OpenStreetMap,
prima con via, CAP e comune, poi con il solo comune. Le regole del servizio chiedono al massimo una richiesta al secondo e un
nome dell'applicazione: si rispettano, e ogni indirizzo già cercato si legge da _04_CoordinateGiaTrovate.json senza
richiederlo. Restituisce (latitudine, longitudine) come testi, oppure ("", "") se l'indirizzo non si trova.
"""

import json
import threading
import time
import urllib.parse
import urllib.request
from pathlib import Path

FILE_DELLE_COORDINATE = Path(__file__).absolute().parent / "_04_CoordinateGiaTrovate.json"
INDIRIZZO_DEL_SERVIZIO = "https://nominatim.openstreetmap.org/search?format=json&limit=1&countrycodes=it&q="
NOME_DELL_APPLICAZIONE = "DepthX-Fabbrica/1.0"
_blocco = threading.Lock()
_ultima = [0.0]


def coordinateGiaTrovate():
    try:
        return json.loads(FILE_DELLE_COORDINATE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def cerca(testo):
    with _blocco:
        attesa = 1.1 - (time.time() - _ultima[0])
        if attesa > 0:
            time.sleep(attesa)
        richiesta = urllib.request.Request(INDIRIZZO_DEL_SERVIZIO + urllib.parse.quote(testo), headers={"User-Agent": NOME_DELL_APPLICAZIONE})
        try:
            with urllib.request.urlopen(richiesta, timeout=15) as risposta:
                trovati = json.loads(risposta.read().decode("utf-8"))
        except (OSError, ValueError):
            trovati = []
        finally:
            _ultima[0] = time.time()
    return (str(trovati[0]["lat"]), str(trovati[0]["lon"])) if trovati else None


def coordinateDellaStrutturaDaOpenStreetMap(via, cap, comune, provincia):
    ricerche = [", ".join(v for v in (via, cap, comune, provincia, "Italia") if v), ", ".join(v for v in (comune, provincia, "Italia") if v)]
    gia = coordinateGiaTrovate()
    for testo in ricerche:
        if not testo or testo == "Italia":
            continue
        if testo in gia:
            return tuple(gia[testo])
        trovate = cerca(testo)
        if trovate:
            gia = coordinateGiaTrovate()
            gia[testo] = list(trovate)
            FILE_DELLE_COORDINATE.write_text(json.dumps(gia, ensure_ascii=False, indent=1), encoding="utf-8")
            return trovate
    return ("", "")

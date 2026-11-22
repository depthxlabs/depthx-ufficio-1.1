"""Fonte Google Maps con Google Places API (New): scheda verificata, foto e recensioni in pochi secondi.

Scrive gli stessi file della fonte con il Chrome (_01_DownloadDiSchedaFotoERecensioniDaGoogleMaps), così la fabbrica li legge come prima:
_01_VerificaDellaScheda.json, _02_SchedaGoogle.json, _01_RecensioniGoogle.json e le foto googleMaps_NNN.
- La scheda si trova e si verifica con le stesse regole di sempre (_02_VerificaDellaSchedaConIDatiDelCrm, almeno due dati uguali al CRM).
- Foto: quelle che Places dà, al massimo 10, alla grandezza più alta.
- Recensioni: Places ne dà 5 per lingua; si chiedono in 5 lingue e si tiene il testo originale scritto dall'ospite.
- Se le recensioni diverse sono meno di RECENSIONI_MINIME e la scheda ne ha di più, solo le recensioni si leggono con il Chrome del motore.
Se anche così restano meno di RECENSIONI_MINIME, il cliente è ESCLUSO per materiale insufficiente (Michele, 22/11/2026).
La chiave è quella di Places della Linea 1.1 (variabile CHIAVE_GOOGLE_MAPS su GitHub, file della chiave sul server). Non si stampa mai.
"""

import sys

sys.dont_write_bytecode = True

import datetime
import json
import os
import re
import urllib.request

import _02_PercorsiChiaviEFunzioniComuni as comune
import _02_VerificaDellaSchedaConIDatiDelCrm as regole
from _04_ContestoDelClienteEConteggioDeiPassi import Passo

FILE_DELLA_CHIAVE = r"C:\_02_DepthXSoftware\_01_CentroGestioneDepthX\V1.0(161126_1124)\_01_StrumentiDiLavoroPerIlServer\_01_ChiaviAccessiServiziTerzeParti\_02_Google\_03_ChiavePlacesUfficio1.1.txt"
URL = "https://places.googleapis.com/v1/"
CAMPI_DELLA_RICERCA = ",".join("places." + campo for campo in (
    "id", "displayName", "formattedAddress", "addressComponents", "nationalPhoneNumber", "internationalPhoneNumber", "websiteUri",
    "googleMapsUri", "location", "rating", "userRatingCount", "types", "primaryType", "regularOpeningHours", "editorialSummary", "businessStatus"))
LINGUE_DELLE_RECENSIONI = ("it", "en", "de", "fr", "es")
FOTO_MASSIME = 10           # Places non ne dà di più
LARGHEZZA_DELLE_FOTO = 4800  # la più alta che Places concede
RECENSIONI_MINIME = 6        # il pacchetto Advanced ne mostra 6: sotto si leggono con il Chrome del motore


def chiave():
    testo = os.environ.get("CHIAVE_GOOGLE_MAPS") or open(FILE_DELLA_CHIAVE, encoding="utf-8-sig").read()
    trovata = re.findall(r"AIza[0-9A-Za-z_\-]{35}", testo)
    if not trovata:
        raise comune.ChiaveMancante("Chiave di Google Places della Linea 1.1 non trovata.")
    return trovata[0]


def chiama(url, corpo=None, campi=""):
    richiesta = urllib.request.Request(url, data=json.dumps(corpo).encode() if corpo is not None else None,
                                       headers={"X-Goog-Api-Key": chiave(), "X-Goog-FieldMask": campi, "Content-Type": "application/json"})
    with urllib.request.urlopen(richiesta, timeout=40) as risposta:
        return json.load(risposta)


def cerca(testo, _=None):
    return chiama(URL + "places:searchText", {"textQuery": testo, "languageCode": "it", "regionCode": "IT", "pageSize": 10},
                  CAMPI_DELLA_RICERCA).get("places", [])


MESI = ("", "gennaio", "febbraio", "marzo", "aprile", "maggio", "giugno", "luglio", "agosto", "settembre", "ottobre", "novembre", "dicembre")


def dataDellaRecensione(iso):
    """La data come la scriveva Maps: "3 mesi fa", "un anno fa"."""
    try:
        giorni = (datetime.datetime.now(datetime.timezone.utc) - datetime.datetime.fromisoformat(iso.replace("Z", "+00:00"))).days
    except (ValueError, AttributeError):
        return ""
    for unita, singolare, plurale in ((365, "un anno", "anni"), (30, "un mese", "mesi"), (7, "una settimana", "settimane"), (1, "un giorno", "giorni")):
        if giorni >= unita:
            n = giorni // unita
            return (singolare if n == 1 else f"{n} {plurale}") + " fa"
    return "oggi"


def recensioniInCinqueLingue(idScheda):
    """Le recensioni diverse della scheda, chieste in 5 lingue, con il testo originale. Restituisce (recensioni, foto della scheda)."""
    recensioni, viste, foto = [], set(), []
    for lingua in LINGUE_DELLE_RECENSIONI:
        dati = chiama(f"{URL}places/{idScheda}?languageCode={lingua}", None, "reviews,photos" if lingua == "it" else "reviews")
        if lingua == "it":
            foto = dati.get("photos", [])[:FOTO_MASSIME]
        for voce in dati.get("reviews", []):
            if voce.get("name") in viste:
                continue
            viste.add(voce.get("name"))
            originale = (voce.get("originalText") or voce.get("text") or {})
            recensioni.append({"autore": (voce.get("authorAttribution") or {}).get("displayName", ""), "voto": voce.get("rating"),
                               "testo": originale.get("text", "").strip(), "testoOriginale": originale.get("text", "").strip(),
                               "lingua": originale.get("languageCode", ""), "data": dataDellaRecensione(voce.get("publishTime", "")), "fonte": "Google"})
    recensioni.sort(key=lambda voce: (-(voce.get("voto") or 0), -len(voce.get("testo") or "")))
    return recensioni, foto


def recensioniDalChrome(cliente):
    """Solo per le schede con poche recensioni da Places: le recensioni lette con il Chrome del motore, come prima."""
    import _01_DownloadDiSchedaFotoERecensioniDaGoogleMaps as maps
    from playwright.sync_api import sync_playwright
    with maps.FilaDelChrome(), sync_playwright() as programma:
        sessione = programma.chromium.launch_persistent_context(maps.PROFILO, headless=False, channel="chrome", args=["--window-position=-32000,-32000"],
                                                                locale="it-IT", viewport={"width": 1400, "height": 900})
        try:
            pagina = sessione.pages[0] if sessione.pages else sessione.new_page()
            scheda, _, _ = maps.trovaLaScheda(pagina, cliente)
            if scheda is None:
                return []
            recensioni, _ = maps.recensioniDellaPagina(pagina, int(comune.regola("recensioniGoogleDaScaricare")), None)
            return recensioni
        finally:
            sessione.close()


def esegui(contesto):
    """Scheda, foto e recensioni con Places. Restituisce (passi, numero di foto o None se la scheda non è verificata)."""
    cliente = contesto.cliente
    passoFoto, passoRecensioni = Passo("Google Maps foto"), Passo("Google Maps recensioni")
    scheda, come, esame = regole.ricercaVerificata(cliente, cerca)
    verifica = {"ricerca": regole.testoDellaRicerca(cliente), "collegamentoDelCrm": cliente.get("googleMaps", ""), "risultati": esame, "metodo": "Google Places API"}
    if scheda is None:
        contesto.scriviJson("scheda", "_01_VerificaDellaScheda.json", {**verifica, "esito": regole.MOTIVO_NON_VERIFICATA})
        passoFoto.limite = passoRecensioni.limite = f"{regole.MOTIVO_NON_VERIFICATA}: {len(esame)} risultati esaminati, nessuno ha almeno due dati uguali al CRM"
        return [passoFoto, passoRecensioni], None
    contesto.scriviJson("scheda", "_01_VerificaDellaScheda.json", {**verifica, "esito": come})
    contesto.scriviJson("scheda", "_02_SchedaGoogle.json", scheda)
    totali, voto = scheda.get("userRatingCount") or 0, scheda.get("rating")
    contesto.stato["schedaGoogle"] = {"id": scheda["id"], "link": scheda.get("googleMapsUri", ""), "recensioniTotali": totali, "voto": voto}

    recensioni, foto = recensioniInCinqueLingue(scheda["id"])
    metodo = "Google Places API, 5 lingue"
    if len(recensioni) < RECENSIONI_MINIME and totali > len(recensioni):
        dalChrome = recensioniDalChrome(cliente)
        if len(dalChrome) > len(recensioni):
            recensioni, metodo = dalChrome, "Chrome del motore (Places ne dava " + str(len(recensioni)) + ")"

    # Foto: quelle di Places, alla grandezza più alta.
    from concurrent.futures import ThreadPoolExecutor
    passoFoto.attesi = len(foto)

    def unaFoto(numero, voce):
        def originale(percorso, nome=voce["name"]):
            return comune.scaricaInFile(f"{URL}{nome}/media?maxWidthPx={LARGHEZZA_DELLE_FOTO}&key={chiave()}", percorso)
        contesto.scaricaElemento(passoFoto, "fotoMaps", "places:" + voce["name"].rsplit("/", 1)[-1][-60:], f"googleMaps_{numero:03d}", "immagine",
                                 [("Google Places API", originale)], foto=True, descrizione={"larghezza": voce.get("widthPx"), "altezza": voce.get("heightPx")})

    with ThreadPoolExecutor(max_workers=int(comune.regola("fotoMapsInParallelo")), thread_name_prefix="fotoPlaces") as fili:
        for futuro in [fili.submit(unaFoto, numero, voce) for numero, voce in enumerate(foto, start=1)]:
            futuro.result()
    contesto.giroDiRecupero(passoFoto)
    passoFoto.dettagli = {"fotoDellaScheda": len(foto), "metodo": "Google Places API"}

    contesto.scriviJson("recensioni", "_01_RecensioniGoogle.json", {"voto": voto, "numeroDiRecensioni": totali, "ordine": "voto più alto, poi testo più lungo",
                                                                   "recensioni": recensioni})
    passoRecensioni.attesi = passoRecensioni.scaricati = len(recensioni)
    passoRecensioni.dettagli = {"recensioniTotaliDellaScheda": totali, "recensioniLette": len(recensioni), "metodo": metodo}
    if not totali:
        passoRecensioni.piattaforma = "la scheda Google non ha recensioni"
    if len(recensioni) < RECENSIONI_MINIME:
        # meno recensioni di quelle che servono al pacchetto: il cliente è ESCLUSO per materiale insufficiente, non è un errore
        contesto.stato["materialeInsufficiente"] = f"materiale insufficiente: {len(recensioni)} recensioni, ne servono almeno {RECENSIONI_MINIME}"
    contesto.stato["recensioniConTesto"] = len([voce for voce in recensioni if voce["testo"]])
    return [passoFoto, passoRecensioni], len(foto)

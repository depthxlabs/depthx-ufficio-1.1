"""Fonte Google Maps dal browser: scheda verificata, galleria completa e recensioni, senza Places API.

Deciso da Michele il 4/11/2026: il motore legge Google Maps come in chat, con un Chrome vero collegato
all'account Google dedicato al motore (profilo _01_StrumentiDelMotore/_07_ProfiloChromeDellAccountDelMotore, accesso fatto da Michele).
Senza account Google Maps mostra solo una vista limitata; in modalità headless Google la mostra lo stesso,
per questo il Chrome è vero ma con la finestra fuori dallo schermo.
Un solo Chrome alla volta usa il profilo (i lavoratori si mettono in fila) e tra un cliente e l'altro c'è una pausa,
così l'account non lavora a ritmo da robot. I controlli anti robot non si aggirano mai: il passo si ferma con il motivo.
La scheda si verifica con le stesse regole della fonte con la Places API (_02_VerificaDellaSchedaConIDatiDelCrm).
Su GitHub (variabile MAPS_WORKER) il Chrome non si apre: la lettura la fa il servizio Maps del server (maps-download.depthxlabs.com),
nell'unico Chrome con l'account del motore, un cliente alla volta; la sessione Google non esce dal server.
La chiave è nella variabile MAPS_CHIAVE_DEL_WORKER. Sul server la variabile non c'è.
"""

import sys

sys.dont_write_bytecode = True

import msvcrt
import os
import random
import re
import time
import urllib.parse

import json
import urllib.request

import _02_PercorsiChiaviEFunzioniComuni as comune
import _02_VerificaDellaSchedaConIDatiDelCrm as regole
from _04_ContestoDelClienteEConteggioDeiPassi import Passo

PROFILO = comune.CARTELLA_DEL_PROFILO_CHROME  # profilo Chrome con l'account del motore
FILE_DELLA_FILA = os.path.join(comune.CARTELLA_TEMPORANEA, "_FilaDelChromeDiMaps")  # un file per scheda del Chrome condiviso
SCHEDE_INSIEME = int(comune.regola("schedeDiMapsInsieme") or 4)  # schede aperte insieme nel Chrome di Maps
SECONDI_TRA_UN_CLIENTE_E_ALTRO = tuple(comune.regola("secondiTraUnClienteEAltroDiMaps") or (6, 12))  # pausa di ogni scheda tra due clienti
GIRI_MASSIMI_DELLA_GALLERIA = 80  # scorrimenti della galleria; si ferma prima se non compaiono foto nuove o alle foto massime
FOTO_MASSIME_DELLA_GALLERIA = int(comune.regola("fotoMapsMassime") or 40)  # il riconoscimento ne sceglie 15 che coprano le categorie
GIRI_MASSIMI_DELLE_RECENSIONI = 3000  # si ferma all'obiettivo, quando non ne compaiono di nuove o al tempo massimo
MINUTI_MASSIMI_DELLE_RECENSIONI = float(comune.regola("minutiMassimiDelleRecensioni") or 2)
RECENSIONI_MINIME = 6  # il pacchetto Advanced ne mostra 6: sotto, il cliente è escluso per materiale insufficiente
RISULTATI_DELLA_RICERCA = 10  # schede della ricerca esaminate una per una
FOTO_DELLA_SCHEDA = re.compile(r"https://lh\d\.googleusercontent\.com/(?:p|gps-cs-s|gps-proxy)/[A-Za-z0-9_\-]+")  # foto della scheda, non avatar né Street View
MOTIVO_ANTI_ROBOT = "Google ha chiesto la verifica anti robot: non si aggira, il cliente si riprende nel giro successivo"
WORKER_DI_MAPS = os.environ.get("MAPS_WORKER", "").strip().rstrip("/")  # su GitHub: il servizio Maps del server
MOTIVO_SENZA_ACCESSO = "il Chrome del motore non ha l'accesso all'account Google dedicato: Maps mostra la vista limitata (va rifatto l'accesso, task 485)"


class FermoDiMaps(Exception):
    """Maps non si può leggere ora (anti robot o accesso mancante): il motivo va nei passi."""


# Fila delle schede: il Chrome di Maps è uno solo, con al massimo SCHEDE_INSIEME schede aperte dai lavoratori.


class FilaDelChrome:
    def __enter__(self):
        os.makedirs(os.path.dirname(FILE_DELLA_FILA), exist_ok=True)
        while True:
            for numero in range(1, SCHEDE_INSIEME + 1):
                self.percorso = f"{FILE_DELLA_FILA}_{numero:02d}.lock"
                self.file = open(self.percorso, "a+")
                try:
                    self.file.seek(0)
                    msvcrt.locking(self.file.fileno(), msvcrt.LK_NBLCK, 1)
                    break
                except OSError:
                    self.file.close()
                    self.file = None
            if self.file:
                break
            time.sleep(3)
        attesa = random.uniform(*SECONDI_TRA_UN_CLIENTE_E_ALTRO) - (time.time() - self.ultimoUso())
        if attesa > 0:
            time.sleep(attesa)
        return self

    def ultimoUso(self):
        percorso = self.percorso + ".ultimo"
        try:
            with open(percorso, encoding="utf-8") as file:
                return float(file.read().strip() or 0)
        except (OSError, ValueError):
            return 0.0

    def __exit__(self, *errore):
        with open(self.percorso + ".ultimo", "w", encoding="utf-8") as file:
            file.write(str(time.time()))
        self.file.seek(0)
        msvcrt.locking(self.file.fileno(), msvcrt.LK_UNLCK, 1)
        self.file.close()


# Lettura della pagina.


def pausa(pagina, minimo=1.2, massimo=2.8):
    pagina.wait_for_timeout(int(random.uniform(minimo, massimo) * 1000))


def controllaPagina(pagina):
    """Ferma la fonte se Google chiede la verifica anti robot o se il profilo non ha l'accesso."""
    if "/sorry/" in pagina.url or "recaptcha" in pagina.content()[:200000].lower():
        raise FermoDiMaps(MOTIVO_ANTI_ROBOT)
    if "insieme limitato di dati" in pagina.inner_text("body"):
        raise FermoDiMaps(MOTIVO_SENZA_ACCESSO)


def apri(pagina, url):
    pagina.goto(url, wait_until="domcontentloaded", timeout=60000)
    pausa(pagina, 3.5, 5.5)
    for testo in ("Rifiuta tutto", "Reject all"):
        bottone = pagina.get_by_role("button", name=testo)
        if bottone.count():
            bottone.first.click()
            pausa(pagina, 3, 4)
            break
    controllaPagina(pagina)


def schedaDallaPagina(pagina):
    """Dati della scheda aperta, nella forma della Places API, per usare le stesse regole di verifica."""
    # il nome è il titolo del pannello principale della scheda; i titoli degli annunci ("Sponsorizzato") non contano
    principale = pagina.eval_on_selector_all("div[role='main'][aria-label]", "e => e.map(x => x.getAttribute('aria-label').trim()).filter(Boolean)")
    titoli = [t for t in pagina.eval_on_selector_all("h1", "e => e.map(x => x.innerText.trim()).filter(Boolean)")
              if not re.search(r"sponsorizzat|sponsored|annuncio", t, re.I)]
    nome = next((t for t in titoli if t in principale), (titoli or [""])[0])
    voci = pagina.eval_on_selector_all("[data-item-id]", "e => e.map(x => [x.getAttribute('data-item-id'), x.getAttribute('aria-label') || '', x.href || ''])")
    indirizzo = telefono = sito = ""
    for chiave, etichetta, collegamento in voci:
        if chiave == "address":
            indirizzo = etichetta.split(":", 1)[-1].strip()
        elif chiave.startswith("phone:tel:") and not telefono:
            telefono = chiave.removeprefix("phone:tel:")
        elif chiave == "authority" and not sito:
            sito = collegamento
    componenti = []
    trovato = re.search(r"\b(\d{5})\s+([^,\d]+?)(?:\s+[A-Z]{2})?(?:,|$)", indirizzo)
    if trovato:
        componenti = [{"types": ["postal_code"], "longText": trovato.group(1)}, {"types": ["locality"], "longText": trovato.group(2).strip()}]
    return {"id": pagina.url.split("?")[0], "displayName": {"text": nome}, "formattedAddress": indirizzo, "addressComponents": componenti,
            "nationalPhoneNumber": telefono, "websiteUri": sito, "googleMapsUri": pagina.url}


def collegamentiDeiRisultati(pagina):
    return pagina.eval_on_selector_all("a[href*='/maps/place/']", "e => [...new Set(e.map(x => x.href))]")[:RISULTATI_DELLA_RICERCA]


def trovaLaScheda(pagina, cliente):
    """Apre la scheda giusta: il collegamento del CRM, altrimenti la ricerca verificata. Restituisce (scheda, come, esame)."""
    valore = str(cliente.get("googleMapsDelCrm") or cliente.get("googleMaps") or "").strip()
    idScheda = regole.idDellaSchedaDalCrm(str(cliente.get("googleMaps") or ""))
    if idScheda and not regole.collegamentoMappeDelCrm(valore):
        valore = "https://www.google.com/maps/place/?q=place_id:" + idScheda
    if regole.collegamentoMappeDelCrm(valore):
        apri(pagina, valore)
        if "/maps/place/" in pagina.url or pagina.locator("h1").count():
            scheda = schedaDallaPagina(pagina)
            if scheda["displayName"]["text"]:
                return scheda, "collegamento del CRM: " + ", ".join(regole.proveDellaScheda(cliente, scheda)), []
    esame, viste = [], set()
    migliore, proveMigliori, urlMigliore = None, [], ""
    testi = []
    for testo in (regole.testoDellaRicerca(cliente), regole.testoBreveDellaRicerca(cliente), str(cliente.get("nome") or "").strip()):
        if testo and testo not in testi:
            testi.append(testo)
    for testo in testi:
        apri(pagina, "https://www.google.com/maps/search/" + urllib.parse.quote(testo))
        candidati = [pagina.url] if "/maps/place/" in pagina.url else collegamentiDeiRisultati(pagina)
        for collegamento in candidati:
            if collegamento != pagina.url:
                apri(pagina, collegamento)
            scheda = schedaDallaPagina(pagina)
            chiave = scheda["displayName"]["text"] + "|" + scheda["formattedAddress"]
            if chiave in viste:
                continue
            viste.add(chiave)
            prove = regole.proveDellaScheda(cliente, scheda)
            voce = regole.voceDiEsame(scheda, prove)
            voce["verificata"] = regole.schedaVerificata(prove)
            esame.append(voce)
            if voce["verificata"] and len(prove) > len(proveMigliori):
                migliore, proveMigliori, urlMigliore = scheda, prove, pagina.url
        if migliore:
            break
    if not migliore:
        return None, "", esame
    if pagina.url != urlMigliore:
        apri(pagina, urlMigliore)
    return migliore, "ricerca verificata: " + ", ".join(proveMigliori), esame


def fotoDellaGalleria(pagina, nome):
    """Collegamenti di tutte le foto della galleria (Tutte), scorrendo finché ne compaiono di nuove."""
    # il nome si confronta come testo e non dentro il selettore: apostrofi e virgolette del nome (per esempio L'Angolo) non lo rompono
    bottone = pagina.get_by_role("button", name="Foto di " + nome, exact=True).first if nome else pagina.locator("button[aria-label^='Foto di']").first
    if not bottone.count():
        bottone = pagina.locator("button[aria-label^='Foto di']").first
    if not bottone.count():
        return []
    bottone.click()
    pausa(pagina, 4, 5.5)
    controllaPagina(pagina)
    trovate, fermo = [], 0
    for _ in range(GIRI_MASSIMI_DELLA_GALLERIA):
        prima = len(trovate)
        for collegamento in FOTO_DELLA_SCHEDA.findall(pagina.content()):
            if collegamento not in trovate:
                trovate.append(collegamento)
        fermo = fermo + 1 if len(trovate) == prima else 0
        if fermo >= 4 or len(trovate) >= FOTO_MASSIME_DELLA_GALLERIA:
            break
        pagina.mouse.move(300, 500)
        pagina.mouse.wheel(0, 3000)
        pausa(pagina)
    pagina.go_back()
    pausa(pagina, 3, 4.5)
    return trovate[:FOTO_MASSIME_DELLA_GALLERIA]


def votoDellaScheda(pagina):
    """Voto medio e numero di recensioni scritti nella testata della scheda aperta (Michele, 10/11/2026). (None, 0) se non si leggono."""
    try:
        dati = pagina.evaluate("""() => {
            const zona = document.querySelector('div[role=main]') || document.body;
            const riga = zona.querySelector('div.F7nice');
            const stelle = [...zona.querySelectorAll('[role=img][aria-label]')].map(x => x.getAttribute('aria-label')).find(t => /stell|star/i.test(t)) || '';
            return {riga: riga ? riga.innerText : '', stelle};
        }""")
    except Exception:
        return None, 0
    import re as _re
    voto = _re.search(r"([1-5][,.]\d)", dati.get("riga") or "") or _re.search(r"([1-5][,.]\d)", dati.get("stelle") or "")
    numero = _re.search(r"\(([\d.,]+)\)", dati.get("riga") or "")
    return (float(voto.group(1).replace(",", ".")) if voto else None,
            int(_re.sub(r"[.,]", "", numero.group(1))) if numero else 0)


LETTURA = {"senzaRecensioni": False}  # la scheda Google non ha nessuna recensione (11/11/2026)
UNITA_INGLESI = {"minute": ("un minuto", "minuti"), "hour": ("un'ora", "ore"), "day": ("un giorno", "giorni"), "week": ("una settimana", "settimane"),
                 "month": ("un mese", "mesi"), "year": ("un anno", "anni")}


def dataInItaliano(testo):
    """'11 months ago' diventa '11 mesi fa', come la scrive Maps in italiano."""
    trovato = re.search(r"\b(a|an|\d+)\s+(minute|hour|day|week|month|year)s?\s+ago\b", testo or "", re.I)
    if not trovato:
        return testo
    unita = UNITA_INGLESI[trovato.group(2).lower()]
    return (unita[0] if trovato.group(1).lower() in ("a", "an") else f"{trovato.group(1)} {unita[1]}") + " fa"


def recensioniDellaPagina(pagina, obiettivo, scadenza=None, inInglese=False):
    """Recensioni della scheda con il testo completo, scorrendo fino all'obiettivo. Restituisce (recensioni, totali)."""
    LETTURA["senzaRecensioni"] = False
    # ogni strada per aprire le recensioni (Michele, 9/11/2026: La Portesina ne aveva 34 e il motore ne ha lette 0 perché la scheda
    # "Recensioni" non era ancora caricata): si aspetta la scheda, poi il pulsante "N recensioni" o "Altre recensioni", poi si ricarica
    def apriLeRecensioni():
        # dall'11/11/2026 la scheda si chiama anche "Recensioni su <nome>"
        nomi = re.compile(r"^(Recensioni|Reviews|Rezensionen|Avis)(\s+(su|for|about)\b.*)?$", re.I)
        for _ in range(30):
            scheda = pagina.get_by_role("tab", name=nomi)
            if scheda.count():
                scheda.first.click()
                return True
            pagina.wait_for_timeout(500)
        for modello in (r"^\s*[\d.]+\s+(recensioni|reviews)\s*$", r"Altre recensioni|More reviews"):
            pulsante = pagina.locator("button").filter(has_text=re.compile(modello, re.I))
            if pulsante.count():
                pulsante.first.click()
                return True
        return False

    if not apriLeRecensioni():
        pagina.reload(wait_until="domcontentloaded")
        pausa(pagina, 4, 6)
        if not apriLeRecensioni():
            # nessuna scheda Recensioni e nessun "N recensioni" sulla scheda caricata: su Google non ce ne sono (11/11/2026)
            corpo = pagina.inner_text("body")
            LETTURA["senzaRecensioni"] = bool(pagina.locator("h1").count()) and not re.search(r"\d\s+(recensioni|recensione|reviews?)\b", corpo, re.I)
            if LETTURA["senzaRecensioni"] or inInglese:
                return [], 0
            # la scheda ha recensioni ma la scheda Recensioni non si è aperta (Chrome appena acceso, 24/11/2026: 1165 recensioni, 0 lette):
            # si legge la stessa scheda in inglese, con il testo originale
            apri(pagina, pagina.url.split("?")[0] + "?hl=en")
            return recensioniDellaPagina(pagina, obiettivo, max(scadenza or 0, time.time() + 120), inInglese=True)
    pausa(pagina, 3.5, 5)
    # le recensioni arrivano qualche secondo dopo il clic: si aspetta la prima, fino a 30 secondi
    try:
        pagina.locator("div[data-review-id][aria-label]").first.wait_for(timeout=30000)
    except Exception:
        pass
    testo = pagina.inner_text("body")
    numero = re.search(r"([\d.,]+)\s+(?:recensioni|reviews)", testo, re.I)
    totali = int(re.sub(r"[.,]", "", numero.group(1))) if numero else 0
    fermo, prima = 0, 0
    for _ in range(GIRI_MASSIMI_DELLE_RECENSIONI):
        presenti = pagina.locator("div[data-review-id][aria-label]").count()
        if presenti >= obiettivo or presenti >= totali or comune.scaduta(scadenza):
            break
        fermo = fermo + 1 if presenti == prima else 0
        if fermo >= 4:
            break
        prima = presenti
        if presenti:
            pagina.locator("div[data-review-id][aria-label]").last.scroll_into_view_if_needed()
        pausa(pagina)
    pagina.evaluate("() => document.querySelectorAll(\"button.w8nwRe, button[aria-label='Visualizza altro'], button[aria-label='See more']\").forEach(b => b.click())")
    pausa(pagina)
    if inInglese:
        # Maps in inglese traduce: si torna al testo originale di ogni recensione ("See original")
        pagina.evaluate("() => document.querySelectorAll('div[data-review-id] button').forEach(b => { if (/See original/i.test(b.innerText)) b.click(); })")
        pausa(pagina, 3, 4)
        pagina.evaluate("() => document.querySelectorAll(\"button.w8nwRe, button[aria-label='See more']\").forEach(b => b.click())")
        pausa(pagina)
    righe = pagina.eval_on_selector_all("div[data-review-id][aria-label]", """e => e.map(x => ({
        id: x.getAttribute('data-review-id'), autore: x.getAttribute('aria-label') || '',
        voto: ((x.querySelector('[role=img][aria-label*=stell], [role=img][aria-label*=star]') || {}).ariaLabel || ''),
        testo: ((x.querySelector('.wiI7pd') || {}).innerText || ''), data: ((x.querySelector('.rsqaWe') || x.querySelector('.xRkPPb') || {}).innerText || ''),
        tutto: x.innerText || ''}))""")
    recensioni, viste = [], set()
    for riga in righe:
        if riga["id"] in viste:
            continue
        viste.add(riga["id"])
        # strutture ricettive: il voto è scritto "4/5" e Maps mostra anche recensioni di altri siti
        # strutture ricettive (11/11/2026): la data è scritta "2 anni fa su Google", si tiene solo "2 anni fa"
        riga["data"] = re.split(r"\s+(?:su|on)\s", riga["data"].replace("\n", " ") + " ", maxsplit=1)[0].strip()
        riga["data"] = re.sub(r"^(Ultima modifica|Modificata|Edited)\s*:?\s*", "", riga["data"], flags=re.I)
        voto = re.search(r"\d", riga["voto"]) or re.search(r"\b([1-5])/5\b", riga["tutto"])
        fonte = re.search(r"\b(Tripadvisor|Booking\.com|Expedia|Hotels\.com|Trip\.com|Priceline|Agoda|Holidaycheck)\b", riga["tutto"], re.I)
        recensioni.append({"autore": riga["autore"], "voto": int(voto.group(voto.lastindex or 0)) if voto else None, "testo": riga["testo"].strip(),
                           "testoOriginale": "", "lingua": "", "data": dataInItaliano(riga["data"]) if inInglese else riga["data"],
                           "fonte": fonte.group(1) if fonte else "Google"})
    recensioni.sort(key=lambda voce: (-(voce.get("voto") or 0), -len(voce.get("testo") or "")))
    if not recensioni and totali and not inInglese:
        # 11/11/2026: su alcune schede Maps in italiano va in errore e l'elenco non si carica (Il Feudo, 38 recensioni, 0 lette);
        # la stessa scheda in inglese si carica, e con "See original" il testo resta quello scritto dall'ospite
        apri(pagina, pagina.url.split("?")[0] + "?hl=en")
        recensioni, _ = recensioniDellaPagina(pagina, obiettivo, max(scadenza or 0, time.time() + 300), inInglese=True)
    return recensioni, totali


# Lettura dal servizio Maps del server (solo con la variabile MAPS_WORKER).


def letturaDalWorker(cliente, obiettivo, secondiDelleRecensioni, veloci):
    """Chiede la scheda al servizio Maps del server. Restituisce (scheda, come, esame, voto, numero della testata, foto, recensioni, totali)."""
    campi = ("nome", "via", "cap", "comune", "provincia", "telefono", "cellulare", "sito", "googleMaps", "googleMapsDelCrm")
    corpo = {"cliente": {campo: cliente.get(campo) for campo in campi if cliente.get(campo)}, "obiettivo": obiettivo,
             "fotoMassime": FOTO_MASSIME_DELLA_GALLERIA, "secondiDelleRecensioni": max(30, int(secondiDelleRecensioni)),
             "senzaFoto": veloci, "senzaImmagini": bool(comune.regola("mapsSenzaImmagini"))}
    richiesta = urllib.request.Request(WORKER_DI_MAPS + "/Scheda", data=json.dumps(corpo).encode("utf-8"), method="POST",
                                       headers={"content-type": "application/json", "user-agent": "DepthX-Download/1.1",
                                                "x-chiave": os.environ.get("MAPS_CHIAVE_DEL_WORKER", "").strip()})
    dati, motivo = None, ""
    for volta in range(3):
        try:
            # la richiesta aspetta in fila gli altri clienti: il servizio manda uno spazio ogni 20 secondi, il collegamento resta vivo
            with urllib.request.urlopen(richiesta, timeout=120) as risposta:
                dati = json.loads(risposta.read().decode("utf-8"))
            break
        except Exception as errore:
            motivo = f"servizio Maps del server non raggiungibile: {type(errore).__name__}"
            time.sleep(20 * (volta + 1))
    if dati is None:
        raise FermoDiMaps(motivo)
    if dati.get("errore"):
        raise FermoDiMaps(str(dati["errore"]))
    if dati.get("fermo"):
        raise FermoDiMaps(str(dati["fermo"]))
    totali = int(dati.get("totali") or 0) or int(dati.get("numeroDellaTestata") or 0)
    if dati.get("scheda") and not dati.get("recensioni") and totali and not (dati.get("lettura") or {}).get("senzaRecensioni"):
        # la scheda ha recensioni e il servizio ne ha lette 0: si chiedono di nuovo soltanto le recensioni, le foto restano quelle lette
        corpo["senzaFoto"] = True
        richiesta.data = json.dumps(corpo).encode("utf-8")
        try:
            with urllib.request.urlopen(richiesta, timeout=120) as risposta:
                seconda = json.loads(risposta.read().decode("utf-8"))
            if seconda.get("recensioni"):
                dati["recensioni"], dati["totali"] = seconda["recensioni"], seconda.get("totali") or dati.get("totali")
        except Exception:
            pass
    LETTURA["senzaRecensioni"] = bool((dati.get("lettura") or {}).get("senzaRecensioni"))
    return (dati.get("scheda"), dati.get("come") or "", dati.get("esame") or [], dati.get("voto"), int(dati.get("numeroDellaTestata") or 0),
            dati.get("foto") or [], dati.get("recensioni") or [], int(dati.get("totali") or 0))


# Passo della fonte.


def esegui(contesto):
    """Scheda, foto e recensioni dal browser. Restituisce (passi, numero di foto della galleria o None se non verificata)."""
    from playwright.sync_api import sync_playwright

    cliente = contesto.cliente
    passoFoto, passoRecensioni = Passo("Google Maps foto"), Passo("Google Maps recensioni")
    obiettivo = int(comune.regola("recensioniGoogleDaScaricare"))
    scadenza = getattr(contesto.filo, "scadenza", None)
    # recensioni veloci (Michele, 10/11/2026): sui clienti che hanno già la galleria si leggono solo le recensioni, al massimo 100 in 3 minuti
    veloci = os.environ.get("MOTORE_RECENSIONI_VELOCI") == "1"
    if veloci:
        obiettivo = min(obiettivo, 100)
    scadenzaRecensioni = min(scadenza or float("inf"), time.time() + 60 * (3 if veloci else MINUTI_MASSIMI_DELLE_RECENSIONI))
    try:
        if WORKER_DI_MAPS:
            rimasto = (scadenza - time.time()) if scadenza else None
            scheda, come, esame, voto, numeroDellaTestata, foto, recensioni, totali = letturaDalWorker(
                cliente, obiettivo, scadenzaRecensioni - time.time(), veloci)
            totali = totali or numeroDellaTestata
            if scadenza:
                # il tempo passato in fila al servizio Maps non toglie tempo alle foto: dopo la risposta le foto hanno il tempo che la fonte aveva
                scadenza = max(scadenza, time.time() + rimasto)
            if scheda is None:
                contesto.scriviJson("scheda", "_01_VerificaDellaScheda.json", {"ricerca": regole.testoDellaRicerca(cliente), "collegamentoDelCrm": cliente.get("googleMaps", ""),
                                                                              "esito": regole.MOTIVO_NON_VERIFICATA, "risultati": esame, "metodo": "servizio Maps del server"})
                passoFoto.limite = passoRecensioni.limite = f"{regole.MOTIVO_NON_VERIFICATA}: {len(esame)} risultati esaminati, nessuno ha almeno due dati uguali al CRM"
                return [passoFoto, passoRecensioni], None
        else:
            with FilaDelChrome(), sync_playwright() as programma:
                browser = comune.chromeDiMaps(programma)  # il Chrome condiviso con l'account: qui si apre solo una scheda
                sessione = browser.contexts[0].new_page()
                try:
                    pagina = sessione
                    pagina.set_viewport_size({"width": 1400, "height": 900})
                    # la scheda non disegna immagini, mappa e caratteri: le foto si leggono come indirizzi e si scaricano a parte (regola mapsSenzaImmagini)
                    if comune.regola("mapsSenzaImmagini"):
                        pagina.route("**/*", lambda percorso, richiesta: percorso.abort() if richiesta.resource_type in ("image", "media", "font")
                                     else percorso.continue_())
                    scheda, come, esame = trovaLaScheda(pagina, cliente)
                    if scheda is None:
                        contesto.scriviJson("scheda", "_01_VerificaDellaScheda.json", {"ricerca": regole.testoDellaRicerca(cliente), "collegamentoDelCrm": cliente.get("googleMaps", ""),
                                                                                      "esito": regole.MOTIVO_NON_VERIFICATA, "risultati": esame, "metodo": "Chrome del motore"})
                        passoFoto.limite = passoRecensioni.limite = f"{regole.MOTIVO_NON_VERIFICATA}: {len(esame)} risultati esaminati, nessuno ha almeno due dati uguali al CRM"
                        return [passoFoto, passoRecensioni], None
                    voto, numeroDellaTestata = votoDellaScheda(pagina)
                    foto = [] if veloci else fotoDellaGalleria(pagina, scheda["displayName"]["text"])
                    recensioni, totali = recensioniDellaPagina(pagina, obiettivo, scadenzaRecensioni)
                    totali = totali or numeroDellaTestata
                finally:
                    sessione.close()
    except FermoDiMaps as fermo:
        passoFoto.limite = passoRecensioni.limite = str(fermo)
        return [passoFoto, passoRecensioni], None

    scheda["userRatingCount"] = totali
    scheda["rating"] = voto
    contesto.scriviJson("scheda", "_01_VerificaDellaScheda.json", {"ricerca": regole.testoDellaRicerca(cliente), "collegamentoDelCrm": cliente.get("googleMaps", ""),
                                                                  "esito": come, "risultati": esame, "metodo": "servizio Maps del server" if WORKER_DI_MAPS else "Chrome del motore"})
    contesto.scriviJson("scheda", "_02_SchedaGoogle.json", scheda)
    contesto.stato["schedaGoogle"] = {"id": scheda["id"], "link": scheda["googleMapsUri"], "recensioniTotali": totali, "voto": voto}

    # Foto: tutta la galleria, alla grandezza originale.
    # dal 9/11/2026 (Michele): più foto alla volta (regola fotoMapsInParallelo), entro il tempo massimo di Google Maps
    from concurrent.futures import ThreadPoolExecutor

    passoFoto.attesi = len(foto)
    passoFoto.scadenza = scadenza

    def unaFoto(numero, collegamento):
        def originale(percorso, collegamento=collegamento):
            return comune.scaricaInFile(collegamento + "=s0", percorso)

        contesto.scaricaElemento(passoFoto, "fotoMaps", "mapsweb:" + collegamento.rsplit("/", 1)[-1][-60:], f"googleMaps_{numero:03d}", "immagine",
                                 [("Google Maps originale", originale)], foto=True, descrizione={"collegamento": collegamento})

    with ThreadPoolExecutor(max_workers=int(comune.regola("fotoMapsInParallelo")), thread_name_prefix="fotoMaps") as fili:
        for futuro in [fili.submit(unaFoto, numero, collegamento) for numero, collegamento in enumerate(foto, start=1)]:
            futuro.result()
    contesto.giroDiRecupero(passoFoto)
    passoFoto.dettagli = {"fotoDellaGalleria": len(foto), "metodo": "servizio Maps del server" if WORKER_DI_MAPS else "Chrome del motore"}

    # Recensioni: le migliori, fino all'obiettivo delle regole.
    obiettivo = min(obiettivo, totali or len(recensioni))
    contesto.scriviJson("recensioni", "_01_RecensioniGoogle.json", {"voto": voto, "numeroDiRecensioni": totali, "ordine": "voto più alto, poi testo più lungo", "recensioni": recensioni})
    passoRecensioni.attesi = obiettivo
    passoRecensioni.scaricati = min(len(recensioni), obiettivo)
    passoRecensioni.dettagli = {"recensioniTotaliDellaScheda": totali, "recensioniLette": len(recensioni), "metodo": "servizio Maps del server" if WORKER_DI_MAPS else "Chrome del motore"}
    if obiettivo > len(recensioni):
        passoRecensioni.scaricati = passoRecensioni.attesi = len(recensioni)  # tutte quelle che Maps ha mostrato: GO (Michele, 9/11/2026)
        passoRecensioni.piattaforma = f"la scheda ha {totali} recensioni e Maps ne ha caricate {len(recensioni)} scorrendo l'elenco"
    if not recensioni and LETTURA["senzaRecensioni"] and not totali:
        # 11/11/2026: la scheda Google non ha nessuna recensione, non manca niente
        passoRecensioni.attesi = passoRecensioni.scaricati = 0
        passoRecensioni.piattaforma = "la scheda Google non ha recensioni"
    elif not recensioni:
        # nessuna recensione letta non è un GO (Michele, 9/11/2026, La Portesina: 34 su Google, 0 lette): il passo resta da rifare
        passoRecensioni.attesi, passoRecensioni.scaricati = max(1, totali), 0
        # dal 10/11/2026 (Michele) è un NOTGO: con "piattaforma" il passo risultava GO e 130 clienti sono rimasti senza recensioni
        passoRecensioni.piattaforma = ""
        passoRecensioni.limite = (f"la scheda ha {totali} recensioni e il motore ne ha lette 0: da rifare" if totali
                                  else "nessuna recensione letta e numero delle recensioni non trovato sulla scheda: da rifare")
    contesto.stato["recensioniConTesto"] = len([voce for voce in recensioni if voce["testo"]])
    if contesto.stato["recensioniConTesto"] < RECENSIONI_MINIME and not veloci:
        contesto.stato["materialeInsufficiente"] = (f"materiale insufficiente: {contesto.stato['recensioniConTesto']} recensioni con il testo, "
                                                    f"ne servono almeno {RECENSIONI_MINIME}")
    if veloci:
        return [passoRecensioni], None
    return [passoFoto, passoRecensioni], len(foto)

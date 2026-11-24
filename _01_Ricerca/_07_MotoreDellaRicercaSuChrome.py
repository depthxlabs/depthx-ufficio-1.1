"""MOTORE DELLA RICERCA SU CHROME, Linea 1.1 Outbound Websites, Ricerca clienti.

La ricerca sul server, con il Chrome dell'account Google (profilo _02_ProfiloChromeDellaRicerca, porta 9335), al posto di Google Places API.
1. Legge la ricerca attiva e il piano dei giri dall'archivio dei dati (_06_DatiDellaRicerca, copia di depthx-dati-1.1).
2. Per ogni coppia tipo e comune cerca su Google Maps le parole del tipo, scorre l'elenco e apre le schede 3 alla volta:
   nome, sito, telefono, indirizzo, categoria, voto e recensioni.
3. Il resto è il motore di sempre (_04_MotoreDellaRicercaSuMaps): stessi filtri, stesso controllo del sito, stessi file nell'archivio.
4. Lavora COPPIE_INSIEME coppie insieme; a giro finito parte il giro successivo, finché la ricerca è attiva e l'obiettivo non è raggiunto.
Immagini, video e caratteri delle pagine di Maps non si scaricano: il processore del server resta libero per download e fabbrica.

Uso:  python -B -I _07_MotoreDellaRicercaSuChrome.py
      python -B -I _07_MotoreDellaRicercaSuChrome.py --prova "AGR|Gorle|BG"   (una coppia sola, senza salvare)
"""
import argparse, datetime, json, os, re, socket, subprocess, sys, threading, time, urllib.parse

CARTELLA = os.path.dirname(os.path.abspath(__file__))
os.environ.setdefault("DATI_RICERCA", os.path.join(CARTELLA, "_06_DatiDellaRicerca"))
os.environ.setdefault("TOKEN_GITHUB", r"C:\_02_DepthXSoftware\_01_CentroGestioneDepthX\V1.0(161126_1124)\_01_StrumentiDiLavoroPerIlServer"
                                      r"\_01_ChiaviAccessiServiziTerzeParti\_10_GitHub\_01_TokenGitHub.txt")
sys.path.insert(0, CARTELLA)
sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)
import importlib
D = importlib.import_module("_01_DatiSuGitHub")
M = importlib.import_module("_04_MotoreDellaRicercaSuMaps")
P = importlib.import_module("_05_PianoDeiGiriDellaRicerca")
from playwright.sync_api import sync_playwright

PROFILO = os.path.join(os.path.dirname(CARTELLA), "_02_ProfiloChromeDellaRicerca")
PORTA = 9335
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
COPPIE_INSIEME = 3        # coppie tipo e comune lavorate insieme, ognuna con il suo collegamento a Chrome
SCHEDE_PER_COPPIA = 3     # schede delle strutture aperte insieme da ogni coppia
MINUTI_DI_ATTESA_SENZA_LAVORO = 1
REGISTRO = os.path.join(CARTELLA, "_09_RegistroDelMotore.log")
# lo stato dal vivo per il Centro Gestione: le coppie al lavoro adesso e l'ultimo segno del motore
STATO = os.path.join(CARTELLA, "_10_StatoDelMotore.json")
AL_LAVORO, BLOCCO_DELLO_STATO = {}, threading.Lock()
BLOCCO_DEI_DATI = threading.Lock()
SENZA_RISORSE = re.compile(r"\.(png|jpe?g|gif|webp|svg|woff2?|ttf|mp4|webm)(\?|$)", re.I)


def scrivi_lo_stato():
    with BLOCCO_DELLO_STATO:
        dati = {"aggiornato": datetime.datetime.now().isoformat(timespec="seconds"), "pid": os.getpid(), "lavori": list(AL_LAVORO.values())}
        with open(STATO + ".tmp", "w", encoding="utf-8") as f:
            json.dump(dati, f, ensure_ascii=False)
        os.replace(STATO + ".tmp", STATO)


def scrivi_nel_registro(testo):
    riga = f"{datetime.datetime.now().isoformat(timespec='seconds')} {testo}"
    print(riga)
    with open(REGISTRO, "a", encoding="utf-8") as f:
        f.write(riga + "\n")


# ---- Il Chrome della ricerca: acceso una volta, fuori dallo schermo, senza rallentare le schede in secondo piano ----
def chrome_risponde():
    try:
        with socket.create_connection(("127.0.0.1", PORTA), timeout=1):
            return True
    except OSError:
        return False


def accendi_chrome():
    if chrome_risponde():
        return
    subprocess.Popen([CHROME, f"--remote-debugging-port={PORTA}", f"--user-data-dir={PROFILO}", "--window-position=-32000,-32000",
                      "--window-size=1400,900", "--no-first-run", "--lang=it-IT", "--disable-background-timer-throttling",
                      "--disable-backgrounding-occluded-windows", "--disable-renderer-backgrounding", "about:blank"],
                     creationflags=0x08000000 | 0x00004000)   # senza finestra della console, priorità sotto la normale
    for _ in range(60):
        if chrome_risponde():
            return
        time.sleep(0.5)
    raise RuntimeError("Il Chrome della ricerca non si accende")


def senza_immagini(pagina):
    pagina.route("**/*", lambda percorso, richiesta: percorso.abort() if richiesta.resource_type in ("image", "media", "font")
                 or SENZA_RISORSE.search(richiesta.url) else percorso.continue_())


# ---- La ricerca su Maps: l'elenco dei risultati, poi le schede delle strutture ----
LEGGI_ELENCO = """() => [...document.querySelectorAll('div[role=feed] a.hfpxzc')].map(a => {
  const scheda = a.closest('div[jsaction]') || a.parentElement;
  return { nome: a.getAttribute('aria-label') || '', link: a.href,
           voto: (scheda.querySelector('.MW4etd') || {}).innerText || '', recensioni: (scheda.querySelector('.UY7F9') || {}).innerText || '' };
})"""
LEGGI_SCHEDA = """() => {
  const q = s => document.querySelector(s);
  const sito = q('a[data-item-id="authority"]'), tel = q('button[data-item-id^="phone:tel:"]'), ind = q('button[data-item-id="address"]');
  const cat = q('button.DkEaL') || q('span.DkEaL');
  return { nome: (q('h1') || {}).innerText || '', sito: sito ? sito.href : '',
           telefono: tel ? tel.getAttribute('data-item-id').replace('phone:tel:', '') : '',
           indirizzo: ind ? (ind.getAttribute('aria-label') || ind.innerText || '').replace(/^Indirizzo:\\s*/, '').trim() : '',
           categoria: cat ? cat.innerText : '', chiusa: /Chiuso definitivamente/.test(document.body.innerText) };
}"""


def elenco_di_maps(pagina, testo):
    pagina.goto("https://www.google.com/maps/search/" + urllib.parse.quote(testo) + "?hl=it", wait_until="domcontentloaded", timeout=60000)
    for _ in range(20):
        if pagina.locator("div[role=feed], h1").count():
            break
        pagina.wait_for_timeout(500)
    for nome in ("Rifiuta tutto", "Reject all"):
        b = pagina.get_by_role("button", name=nome)
        if b.count():
            b.first.click(); pagina.wait_for_timeout(2000)
    if not pagina.locator("div[role=feed]").count():
        # un solo risultato: Maps apre direttamente la scheda
        return [{"nome": "", "link": pagina.url, "voto": "", "recensioni": ""}] if pagina.locator("h1").count() else []
    prima, fermo = 0, 0
    for _ in range(30):
        n = pagina.locator("div[role=feed] a.hfpxzc").count()
        if "Hai raggiunto la fine dell'elenco" in pagina.inner_text("div[role=feed]"):
            break
        fermo = fermo + 1 if n == prima else 0
        if fermo >= 4:
            break
        prima = n
        pagina.locator("div[role=feed]").first.evaluate("e => e.scrollBy(0, 5000)")
        pagina.wait_for_timeout(1200)
    return pagina.evaluate(LEGGI_ELENCO)


def leggi_le_schede(pagine, voci):
    """Le schede 3 alla volta: le navigazioni partono insieme, poi si leggono una per una."""
    lette = []
    for k in range(0, len(voci), len(pagine)):
        gruppo = list(zip(pagine, voci[k:k + len(pagine)]))
        for pagina, voce in gruppo:
            try:
                pagina.goto(voce["link"], wait_until="commit", timeout=45000)
            except Exception:
                pass
        for pagina, voce in gruppo:
            try:
                pagina.wait_for_selector("h1", timeout=25000)
                pagina.wait_for_timeout(900)
                lette.append({**voce, **pagina.evaluate(LEGGI_SCHEDA)})
            except Exception:
                pass
    return lette


# la categoria di Maps (in italiano) e il nome diventano il tipo principale di Google che il motore di sempre sa leggere
TIPO_DAL_TESTO = [(r"agriturismo|agrituristic|fattoria|masseria|cascina", "farmstay"), (r"bed\s*(and|&)\s*breakfast|\bb\s*&\s*b\b|\bbnb\b", "bed_and_breakfast"),
                  (r"affittacamere|guest\s*house|pensione", "guest_house"), (r"ostello|hostel", "hostel"), (r"campeggio|camping", "campground"),
                  (r"casa (vacanze|per ferie)|appartament|residence|villa|chalet|baita|alloggio|casa\b", "vacation_rental"),
                  (r"hotel|albergo|resort|motel|locanda|relais|\binn\b", "hotel")]


def tipo_principale(nome, categoria):
    for testo in (nome, categoria):
        for modello, tipo in TIPO_DAL_TESTO:
            if re.search(modello, testo or "", re.I):
                return tipo
    return ("altro_" + re.sub(r"\W+", "_", categoria.lower()).strip("_")) if categoria else None


def come_places(s):
    """Una struttura letta da Maps nella forma dei risultati di Google Places, per il motore di sempre."""
    via, numero, cap, comune, prov = "", "", "", "", ""
    m = re.match(r"^(.*?),\s*(?:(\d+[\w/]*)\s*,\s*)?(\d{5})\s+(.+?)\s+([A-Z]{2})(?:,\s*Italia)?$", s.get("indirizzo") or "")
    if m:
        via, numero, cap, comune, prov = m.groups()
    componenti = [{"types": [t], "longText": v, "shortText": v} for t, v in
                  (("route", via), ("street_number", numero or ""), ("postal_code", cap), ("locality", comune), ("administrative_area_level_2", prov)) if v]
    voto = (s.get("voto") or "").replace(",", ".")
    recensioni = re.sub(r"\D", "", s.get("recensioni") or "")
    identita = (re.search(r"!19s([^?&!]+)", s.get("link") or "") or re.search(r"!1s([^!]+)", s.get("link") or "") or [None, s.get("link")])[1]
    sito = re.sub(r"[?&]utm_[^&]*", "", s.get("sito") or "").rstrip("?&")
    return {"id": identita, "displayName": {"text": s.get("nome", "")}, "websiteUri": sito, "internationalPhoneNumber": (s.get("telefono") or "").replace(" ", ""),
            "addressComponents": componenti, "googleMapsUri": (s.get("link") or "").split("?")[0], "rating": float(voto) if voto else "",
            "userRatingCount": int(recensioni) if recensioni else "", "photos": [], "primaryType": tipo_principale(s.get("nome"), s.get("categoria") or ""),
            "businessStatus": "CLOSED_PERMANENTLY" if s.get("chiusa") else "OPERATIONAL"}


def cerca_con_chrome(contesto, pagine):
    def cerca(parole, comune, provincia):
        visti, risultati = set(), []
        for parola in parole:
            for voce in elenco_di_maps(pagine[0], f"{parola} {comune} {provincia}"):
                chiave = voce["link"].split("?")[0]
                if chiave not in visti:
                    visti.add(chiave); risultati.append(voce)
        contesto["risultati"] = len(risultati)
        return [come_places(s) for s in leggi_le_schede(pagine, risultati) if s.get("nome")]
    return cerca


# ---- I giri della ricerca ----
def salva_uno_alla_volta(originale):
    def salva(scrivi, messaggio):
        with BLOCCO_DEI_DATI:
            return originale(scrivi, messaggio)
    return salva


def ricerca_attiva():
    with BLOCCO_DEI_DATI:
        D.git("fetch", "-q", "origin", "main"); D.git("reset", "-q", "--hard", "origin/main")
    return next((r for r in D.leggi_tabella("_01_Ricerche/Ricerche.csv") if r.get("Stato") == "attivo"), None)


def coppie_del_giro(codice):
    uscite = {}
    originale = P.uscita
    P.uscita = lambda nome, valore: uscite.__setitem__(nome, valore)
    try:
        P.piano(codice)
    finally:
        P.uscita = originale
    gruppi = json.loads(uscite.get("lavori", "[]") or "[]")
    return [c.split("|") for g in gruppi for c in g.split(";") if c.count("|") == 2]


def lavora_le_coppie(codice, coppie):
    coda, blocco = list(coppie), threading.Lock()

    def lavoratore():
        with sync_playwright() as p:
            browser = p.chromium.connect_over_cdp(f"http://127.0.0.1:{PORTA}", timeout=60000)
            pagine = [browser.contexts[0].new_page() for _ in range(SCHEDE_PER_COPPIA)]
            for pagina in pagine:
                senza_immagini(pagina)
            try:
                while True:
                    with blocco:
                        if not coda:
                            return
                        tipo, comune, provincia = coda.pop(0)
                    inizio, contesto = time.time(), {}
                    chiave = f"{tipo}|{comune}|{provincia}"
                    AL_LAVORO[chiave] = {"nome": chiave, "ricerca": codice, "dal": datetime.datetime.now().isoformat(timespec="seconds")}
                    scrivi_lo_stato()
                    try:
                        esito = M.main(["--codice", codice, "--tipo", tipo, "--comune", comune, "--provincia", provincia], cerca_con_chrome(contesto, pagine))
                        scrivi_nel_registro(f"{codice} {tipo} {comune}: {contesto.get('risultati', 0)} su Maps, {esito['contatti']} contatti, "
                                            f"{round(time.time() - inizio)} s")
                    except Exception as e:
                        scrivi_nel_registro(f"{codice} {tipo} {comune}: NOTGO {type(e).__name__}: {str(e)[:160]}")
                    finally:
                        AL_LAVORO.pop(chiave, None)
                        scrivi_lo_stato()
            finally:
                for pagina in pagine:
                    try:
                        pagina.close()
                    except Exception:
                        pass

    lavoratori = [threading.Thread(target=lavoratore, daemon=True) for _ in range(min(COPPIE_INSIEME, len(coppie)))]
    for t in lavoratori:
        t.start()
    for t in lavoratori:
        t.join()


def giri():
    D.salva = salva_uno_alla_volta(D.salva)
    scrivi_nel_registro("Motore della ricerca su Chrome acceso")
    while True:
        try:
            accendi_chrome()
            r = ricerca_attiva()
            coppie = coppie_del_giro(r["Codice"]) if r else []
            scrivi_lo_stato()
            if not coppie:
                time.sleep(MINUTI_DI_ATTESA_SENZA_LAVORO * 60)
                continue
            scrivi_nel_registro(f"{r['Codice']}: giro con {len(coppie)} coppie tipo e comune")
            lavora_le_coppie(r["Codice"], coppie)
            P.continua(r["Codice"])
        except Exception as e:
            scrivi_nel_registro(f"NOTGO del giro: {type(e).__name__}: {str(e)[:200]}")
            time.sleep(60)


def prova(coppia):
    tipo, comune, provincia = coppia.split("|")
    accendi_chrome()
    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp(f"http://127.0.0.1:{PORTA}", timeout=60000)
        pagine = [browser.contexts[0].new_page() for _ in range(SCHEDE_PER_COPPIA)]
        for pagina in pagine:
            senza_immagini(pagina)
        inizio, contesto = time.time(), {}
        trovati = cerca_con_chrome(contesto, pagine)(M.T.TIPI[tipo]["parole"], comune, provincia)
        for pagina in pagine:
            pagina.close()
    print(json.dumps({"risultatiMaps": contesto.get("risultati"), "schedeLette": len(trovati), "conSito": sum(1 for x in trovati if x["websiteUri"]),
                      "secondi": round(time.time() - inizio), "esempi": trovati[:3]}, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    a = argparse.ArgumentParser()
    a.add_argument("--prova")
    argomenti = a.parse_args()
    prova(argomenti.prova) if argomenti.prova else giri()

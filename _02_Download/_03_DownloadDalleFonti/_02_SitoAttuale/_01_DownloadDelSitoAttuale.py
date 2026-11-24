"""Fonte Sito attuale: tutte le pagine e tutte le immagini del sito scritto nel CRM.

Chrome installato, senza account e senza finestra (Playwright). Pagina per pagina: rifiuta i cookie
facoltativi, apre menu a fisarmonica e schede, scorre fino in fondo, salva la pagina come HTML e raccoglie
collegamenti, immagini, sfondi, icone, documenti PDF e video. Le pagine arrivano anche dalla sitemap.
Attesi: pagine dello stesso dominio che rispondono, immagini distinte, file (PDF e video) distinti.
I collegamenti che rispondono 404 o 410 non sono pagine esistenti: si elencano a parte.
"""

import sys

sys.dont_write_bytecode = True

import collections
import re
import time
import urllib.parse

from bs4 import BeautifulSoup

import _02_PercorsiChiaviEFunzioniComuni as comune
from _04_ContestoDelClienteEConteggioDeiPassi import Passo
from _01_ScaricamentoDiUnVideoConYtDlp import scaricaConYtDlp

MILLISECONDI_DI_CARICAMENTO = 45000
MILLISECONDI_PER_CLIC = 1500
MASSIMI_CLIC_PER_PAGINA = 40
ESTENSIONI_DA_NON_VISITARE = (".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg", ".avif", ".pdf", ".zip", ".rar", ".mp4", ".mov", ".webm", ".mp3", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx", ".ico", ".css", ".js", ".xml", ".json", ".txt")
DOMINI_DEI_VIDEO = re.compile(r"youtube\.com/embed|youtube-nocookie\.com/embed|player\.vimeo\.com")

PULSANTI_DEI_COOKIE = [  # pulsanti noti per rifiutare i cookie facoltativi
    "#CybotCookiebotDialogBodyButtonDecline", ".iubenda-cs-reject-btn", "#onetrust-reject-all-handler",
    ".cmplz-btn.cmplz-deny", ".cky-btn-reject", "#cookie_action_close_header_reject", ".cc-deny",
    "button[data-cookiefirst-action='reject']", ".moove-gdpr-infobar-reject-btn", "#wt-cli-reject-btn",
]
TESTI_DI_RIFIUTO = re.compile(r"rifiut|nega|necessari|continua senza|reject|decline|deny", re.I)  # testi dei pulsanti di rifiuto
ELEMENTI_DA_APRIRE = [  # elementi che mostrano contenuti nascosti
    "details:not([open]) > summary", "[aria-expanded='false']", "[role='tab'][aria-selected='false']",
    ".accordion-button.collapsed", "[data-toggle='collapse']", "[data-bs-toggle='collapse']",
    "[data-toggle='tab']", "[data-bs-toggle='tab']", ".elementor-tab-title", ".elementor-toggle-title",
    ".e-n-accordion-item-title", ".et_pb_toggle_title", ".vc_tta-tab > a", ".wp-block-details summary",
    "button[aria-controls]",
]

RACCOLTA_DELLA_PAGINA = r"""
() => {
  const assoluto = (valore) => { try { return new URL(valore, document.baseURI).href; } catch (e) { return null; } };
  const migliorDaInsieme = (insieme) => {
    // lettura come la fa il browser: l'indirizzo arriva fino allo spazio, perché può contenere virgole (Wix: w_147,h_98,q_90)
    let scelta = null, larghezza = -1, posizione = 0;
    const testo = insieme || '';
    while (posizione < testo.length) {
      while (posizione < testo.length && /[\s,]/.test(testo[posizione])) posizione++;
      let fine = posizione;
      while (fine < testo.length && !/\s/.test(testo[fine])) fine++;
      let indirizzo = testo.slice(posizione, fine), descrittore = '';
      posizione = fine;
      if (/,$/.test(indirizzo)) {
        indirizzo = indirizzo.replace(/,+$/, '');
      } else {
        let virgola = testo.indexOf(',', posizione);
        if (virgola < 0) virgola = testo.length;
        descrittore = testo.slice(posizione, virgola).trim();
        posizione = virgola + 1;
      }
      if (!indirizzo) continue;
      const misura = parseFloat(descrittore) || 0;
      if (misura >= larghezza) { larghezza = misura; scelta = indirizzo; }
    }
    return scelta;
  };
  const risultato = { immagini: [], sfondi: [], video: [], incorporati: [], collegamenti: [], colori: {}, sfondiColore: {}, caratteri: {}, icone: [] };
  for (const img of document.querySelectorAll('img')) {
    let sorgente = migliorDaInsieme(img.getAttribute('srcset') || img.getAttribute('data-srcset')) || img.currentSrc || img.src;
    const pigra = img.getAttribute('data-src') || img.getAttribute('data-lazy-src') || img.getAttribute('data-original');
    if (pigra && (!sorgente || sorgente.startsWith('data:'))) sorgente = pigra;
    const testo = [img.alt, img.className, img.id, sorgente].join(' ').toLowerCase();
    const contenitore = img.closest('[class*="logo"],[id*="logo"],.navbar-brand,.site-branding,.custom-logo-link');
    risultato.immagini.push({ url: assoluto(sorgente), alt: img.alt || '', logo: testo.includes('logo') || !!contenitore, larghezza: img.naturalWidth || 0, altezza: img.naturalHeight || 0 });
  }
  for (const fonte of document.querySelectorAll('picture source[srcset]')) {
    const scelta = migliorDaInsieme(fonte.getAttribute('srcset'));
    if (scelta) risultato.immagini.push({ url: assoluto(scelta), alt: '', logo: false, larghezza: 0, altezza: 0 });
  }
  const elementi = Array.from(document.querySelectorAll('body *')).slice(0, 5000);
  for (const elemento of elementi) {
    const stile = getComputedStyle(elemento);
    const sfondo = stile.backgroundImage || '';
    for (const pezzo of sfondo.matchAll(/url\(["']?([^"')]+)["']?\)/g)) risultato.sfondi.push(assoluto(pezzo[1]));
    if (elemento.childNodes.length && elemento.innerText && elemento.innerText.trim()) {
      risultato.colori[stile.color] = (risultato.colori[stile.color] || 0) + 1;
      const famiglia = stile.fontFamily.split(',')[0].replace(/["']/g, '').trim();
      risultato.caratteri[famiglia] = (risultato.caratteri[famiglia] || 0) + 1;
    }
    if (stile.backgroundColor && stile.backgroundColor !== 'rgba(0, 0, 0, 0)' && stile.backgroundColor !== 'transparent') {
      risultato.sfondiColore[stile.backgroundColor] = (risultato.sfondiColore[stile.backgroundColor] || 0) + 1;
    }
  }
  for (const video of document.querySelectorAll('video')) {
    const sorgente = video.currentSrc || video.src || (video.querySelector('source') || {}).src;
    if (sorgente) risultato.video.push(assoluto(sorgente));
    if (video.poster) risultato.immagini.push({ url: assoluto(video.poster), alt: 'copertina del video', logo: false, larghezza: 0, altezza: 0 });
  }
  for (const cornice of document.querySelectorAll('iframe[src], iframe[data-src]')) {
    risultato.incorporati.push(assoluto(cornice.getAttribute('src') || cornice.getAttribute('data-src')));
  }
  for (const collegamento of document.querySelectorAll('a[href]')) {
    risultato.collegamenti.push({ url: assoluto(collegamento.getAttribute('href')), testo: (collegamento.innerText || '').trim().slice(0, 120) });
  }
  for (const icona of document.querySelectorAll('link[rel*="icon"], meta[property="og:image"], meta[name="twitter:image"]')) {
    const valore = icona.getAttribute('href') || icona.getAttribute('content');
    if (valore) risultato.icone.push({ url: assoluto(valore), tipo: icona.getAttribute('rel') || icona.getAttribute('property') || icona.getAttribute('name') });
  }
  risultato.fontEsterni = Array.from(document.querySelectorAll('link[href*="fonts.googleapis"], link[href*="use.typekit"], link[href*="fonts.bunny"]')).map((voce) => voce.href);
  return risultato;
}
"""  # raccolta fatta dentro la pagina


def dominio(url):
    """Dominio senza www, per riconoscere le pagine dello stesso sito."""
    return (urllib.parse.urlsplit(url).hostname or "").lower().removeprefix("www.")


def normalizza(url):
    """Collegamento senza frammento e senza barra in coda, per non leggere due volte la stessa pagina."""
    parti = urllib.parse.urlsplit(url)
    return urllib.parse.urlunsplit((parti.scheme, parti.netloc.lower(), parti.path.rstrip("/") or "/", parti.query, ""))


def stessaPagina(valore, questaPagina):
    """Vero se il collegamento è la pagina stessa (insieme di indirizzi normalizzati)."""
    if not valore:
        return False
    try:
        return normalizza(valore) in questaPagina
    except ValueError:
        return False


INDIRIZZO_DENTRO = re.compile(r"^https?://[^/]+/.*?/(https?):/+([^/].*)$", re.I)


def indirizzoVeroShortPixel(valore, sitoDelCliente):
    """ShortPixel scrive le immagini come 'w_1080/https://sito/foto.jpg': letto come relativo diventa
    'https://sito/pagina/w_1080/https:/sito/foto.jpg' (404). Restituisce la foto vera, altrimenti stringa vuota."""
    trovato = INDIRIZZO_DENTRO.match(valore or "")
    if not trovato or dominio(valore) != sitoDelCliente:
        return ""
    vero = f"{trovato.group(1).lower()}://{trovato.group(2)}"
    return vero if dominio(vero) == sitoDelCliente else ""


def urlDelSito(cliente):
    """Collegamento del sito scritto nel CRM, oppure stringa vuota.

    Vale il CRM e basta: mai il sito indicato dalla scheda Google, mai un sito cercato.
    """
    valore = str(cliente.get("sito") or "").strip()
    if not valore or " " in valore:
        return ""
    if not valore.lower().startswith("http"):
        valore = "https://" + valore
    if "." in dominio(valore) and not any(social in valore.lower() for social in ("facebook.com", "instagram.com", "tiktok.com", "youtube.com", "youtu.be")):
        return valore
    return ""


def dominioDiverso(urlDelCrm, urlRaggiunto):
    """Dominio raggiunto se è diverso da quello del sito del CRM, altrimenti stringa vuota (www, http e https non contano)."""
    raggiunto, delCrm = dominio(urlRaggiunto), dominio(urlDelCrm)
    if not raggiunto or raggiunto == delCrm or raggiunto.endswith("." + delCrm) or delCrm.endswith("." + raggiunto):
        return ""
    return raggiunto


def esitoAltroDominio(dominioDelCrm, altroDominio):
    """Risultato del passo quando il sito del CRM porta a un altro dominio: segnalazione e nessuna raccolta."""
    messaggio = f"Il sito del CRM ({dominioDelCrm}) porta a un dominio diverso ({altroDominio}): nulla raccolto, va controllato il CRM."
    return {"valori": {"Sito attuale": f"Porta ad altro dominio: {altroDominio}"}, "esito": "AVVISO", "messaggio": messaggio}


def rifiutaCookie(pagina):
    """Prova i pulsanti noti di rifiuto dei cookie facoltativi, poi i pulsanti con testo di rifiuto."""
    for selettore in PULSANTI_DEI_COOKIE:
        try:
            elemento = pagina.locator(selettore).first
            if elemento.count() and elemento.is_visible():
                elemento.click(timeout=MILLISECONDI_PER_CLIC)
                return True
        except Exception:
            continue
    try:
        pulsanti = pagina.get_by_role("button", name=TESTI_DI_RIFIUTO)
        for numero in range(min(pulsanti.count(), 3)):
            elemento = pulsanti.nth(numero)
            if elemento.is_visible():
                elemento.click(timeout=MILLISECONDI_PER_CLIC)
                return True
    except Exception:
        pass
    return False


def apriContenutiNascosti(pagina):
    """Clicca menu a fisarmonica, schede e pulsanti che aprono contenuti, senza lasciare la pagina."""
    paginaDiPartenza = pagina.url
    cliccati = 0
    for selettore in ELEMENTI_DA_APRIRE:
        try:
            elementi = pagina.locator(selettore)
            quanti = elementi.count()
        except Exception:
            continue
        for numero in range(quanti):
            if cliccati >= MASSIMI_CLIC_PER_PAGINA:
                return cliccati
            try:
                elemento = elementi.nth(numero)
                if not elemento.is_visible():
                    continue
                destinazione = elemento.get_attribute("href") or ""
                if destinazione and not destinazione.startswith("#") and not destinazione.startswith("javascript"):
                    continue
                elemento.click(timeout=MILLISECONDI_PER_CLIC)
                cliccati += 1
                pagina.wait_for_timeout(250)
                if normalizza(pagina.url) != normalizza(paginaDiPartenza):
                    pagina.go_back(timeout=MILLISECONDI_DI_CARICAMENTO)
            except Exception:
                continue
    return cliccati


def scorriFinoInFondo(pagina):
    """Scorre la pagina a passi, così le immagini caricate tardi compaiono."""
    try:
        for _ in range(12):
            pagina.mouse.wheel(0, 1600)
            pagina.wait_for_timeout(250)
        pagina.evaluate("() => window.scrollTo(0, 0)")
    except Exception:
        pass


def testoPulito(html):
    """Titolo, descrizione, titoli e testo pulito della pagina, con BeautifulSoup."""
    zuppa = BeautifulSoup(html, "html.parser")
    for elemento in zuppa(["script", "style", "noscript", "svg", "template", "iframe"]):
        elemento.decompose()
    descrizione = zuppa.find("meta", attrs={"name": "description"})
    titoli = [titolo.get_text(" ", strip=True) for titolo in zuppa.find_all(["h1", "h2", "h3"]) if titolo.get_text(strip=True)]
    righe = [riga.strip() for riga in zuppa.get_text("\n").splitlines()]
    testo = "\n".join(riga for riga in righe if riga)
    return {
        "titolo": zuppa.title.get_text(strip=True) if zuppa.title else "",
        "descrizione": descrizione.get("content", "") if descrizione else "",
        "titoli": titoli[:80],
        "testo": testo,
    }


def paginaDellaSitemap(base):
    """Collegamenti delle sitemap del sito (robots.txt, sitemap.xml, sitemap_index.xml), seguendo le sitemap annidate."""
    trovati, daLeggere, lette = set(), [], set()
    try:
        robots = comune.sessioneWeb().get(urllib.parse.urljoin(base, "/robots.txt"), timeout=(15, 30))
        if robots.ok:
            daLeggere += re.findall(r"(?im)^\s*sitemap:\s*(\S+)", robots.text)
    except Exception:
        pass
    daLeggere += [urllib.parse.urljoin(base, "/sitemap.xml"), urllib.parse.urljoin(base, "/sitemap_index.xml"), urllib.parse.urljoin(base, "/wp-sitemap.xml")]
    while daLeggere and len(lette) < 200:
        sitemap = daLeggere.pop(0)
        if sitemap in lette:
            continue
        lette.add(sitemap)
        try:
            risposta = comune.sessioneWeb().get(sitemap, timeout=(15, 40))
        except Exception:
            continue
        if not risposta.ok or "<loc" not in risposta.text:
            continue
        for voce in re.findall(r"<loc>\s*([^<\s]+)\s*</loc>", risposta.text):
            voce = voce.replace("&amp;", "&")
            if voce.lower().split("?")[0].endswith((".xml", ".xml.gz")):
                daLeggere.append(voce)
            else:
                trovati.add(voce)
    return trovati


def statoDelCollegamento(url):
    """Codice HTTP del collegamento (due letture uguali), 0 se non raggiungibile o diverso."""
    codici = []
    for _ in range(2):
        try:
            risposta = comune.sessioneWeb().get(url, timeout=(15, 40), allow_redirects=True, stream=True)
            codici.append(risposta.status_code)
            risposta.close()
        except Exception:
            codici.append(0)
    return codici[-1] if codici[0] == codici[-1] else 0


def migliorDaInsieme(insieme):
    """Indirizzo più grande di un srcset, letto come lo legge il browser.

    L'indirizzo arriva fino allo spazio, perché può contenere virgole (Wix: w_147,h_98,q_90): dividere sulle virgole
    crea indirizzi inesistenti. Restituisce stringa vuota se l'insieme è vuoto.
    """
    scelta, larghezza, posizione, testo = "", -1.0, 0, insieme or ""
    while posizione < len(testo):
        while posizione < len(testo) and (testo[posizione].isspace() or testo[posizione] == ","):
            posizione += 1
        fine = posizione
        while fine < len(testo) and not testo[fine].isspace():
            fine += 1
        indirizzo, descrittore, posizione = testo[posizione:fine], "", fine
        if indirizzo.endswith(","):
            indirizzo = indirizzo.rstrip(",")
        else:
            virgola = testo.find(",", posizione)
            virgola = len(testo) if virgola < 0 else virgola
            descrittore, posizione = testo[posizione:virgola].strip(), virgola + 1
        if not indirizzo:
            continue
        cifre = re.match(r"\d+(?:\.\d+)?", descrittore)
        misura = float(cifre.group(0)) if cifre else 0.0
        if misura >= larghezza:
            scelta, larghezza = indirizzo, misura
    return scelta


def raccoltaDaHtml(html, base):
    """Collegamenti e immagini da un HTML letto senza Chrome (secondo metodo)."""
    zuppa = BeautifulSoup(html, "html.parser")
    risultato = {"immagini": [], "sfondi": [], "video": [], "incorporati": [], "collegamenti": [], "colori": {}, "sfondiColore": {}, "caratteri": {}, "icone": []}
    for img in zuppa.find_all("img"):
        sorgente = img.get("data-src") or img.get("src") or ""
        insieme = img.get("srcset") or img.get("data-srcset")
        if insieme:
            sorgente = migliorDaInsieme(insieme) or sorgente
        if sorgente:
            risultato["immagini"].append({"url": urllib.parse.urljoin(base, sorgente), "alt": img.get("alt", ""), "logo": "logo" in str(img).lower()})
    for collegamento in zuppa.find_all("a", href=True):
        risultato["collegamenti"].append({"url": urllib.parse.urljoin(base, collegamento["href"]), "testo": collegamento.get_text(" ", strip=True)[:120]})
    for cornice in zuppa.find_all("iframe"):
        if cornice.get("src"):
            risultato["incorporati"].append(urllib.parse.urljoin(base, cornice["src"]))
    for video in zuppa.find_all(["video", "source"]):
        if video.get("src"):
            risultato["video"].append(urllib.parse.urljoin(base, video["src"]))
    return risultato


# pagine che non servono alla demo: archivi, etichette, autori, pagine 2-3 degli elenchi, feed, carrello, accessi, ricerca (Michele, 9/11/2026)
PAGINE_INUTILI = re.compile(r"/(tag|tags|category|categoria|categorie|author|autore|feed|rss|page|pagina|wp-json|wp-admin|wp-login\.php|cart|carrello|checkout|"
                            r"cassa|my-account|account|login|accedi|registrati|search|cerca|cookie-policy|privacy-policy|attachment)(/|$|\?)|[?&](s|replytocom|share|amp|p|page_id|attachment_id)=|/\d{4}/\d{2}/", re.I)


PAGINE_PER_SCHEDA = 20


def profondita(chiave):
    """Quante cartelle ha l'indirizzo: la home è 0, /camere è 1, /camere/doppia è 2."""
    percorso = urllib.parse.urlsplit(chiave if "//" in chiave else "//x/" + chiave).path
    return len([parte for parte in percorso.split("/") if parte])


def esegui(contesto):
    """Visita del sito: le pagine principali. Restituisce i passi: pagine, immagini, file."""
    from playwright.sync_api import sync_playwright

    passoPagine, passoImmagini, passoFile = Passo("Sito attuale pagine"), Passo("Sito attuale immagini"), Passo("Sito attuale file")
    inizio = urlDelSito(contesto.cliente)
    if not inizio:
        for passo in (passoPagine, passoImmagini, passoFile):
            passo.dettagli = {"nelCrm": False}
        return [passoPagine, passoImmagini, passoFile]
    massimoPagine = int(comune.regola("pagineMassimeDelSito"))
    scadenza = getattr(contesto.filo, "scadenza", None)
    sitoDelCliente = dominio(inizio)
    daVisitare = collections.OrderedDict()
    daVisitare[normalizza(inizio)] = inizio
    visitate, rotti, pagine = set(), [], []
    immagini, documenti, video, incorporati = {}, {}, [], []
    colori, sfondiColore, caratteri, fontEsterni, icone = collections.Counter(), collections.Counter(), collections.Counter(), set(), {}
    altroDominio = ""
    sitemapLetta = False
    correzioniShortPixel = 0
    statoCookie = {"rifiutati": False}
    with sync_playwright() as programma:
        # dal 9/11/2026 (Michele): un solo Chrome condiviso fra i lavoratori, una scheda per cliente, video e font non caricati
        # (le immagini il motore le scarica a parte), scheda rinnovata ogni PAGINE_PER_SCHEDA pagine per liberare la memoria
        browser = comune.chromeDeiSiti(programma)
        schede = {"sessione": None, "pagina": None, "pagine": 0}

        def nuovaScheda():
            if schede["sessione"] is not None:
                try:
                    schede["sessione"].close()
                except Exception:
                    pass
            schede["sessione"] = browser.new_context(locale="it-IT", viewport={"width": 1440, "height": 900}, ignore_https_errors=True)
            schede["sessione"].route("**/*", lambda percorso: percorso.abort() if percorso.request.resource_type in ("media", "font") else percorso.continue_())
            schede["pagina"] = schede["sessione"].new_page()
            schede["pagine"] = 0
            statoCookie["rifiutati"] = False

        try:
            nuovaScheda()
            while daVisitare:
                # dal 9/11/2026 (Michele): prima le pagine meno profonde, cioè le principali; le pagine inutili non si visitano
                chiave = min(daVisitare, key=profondita)
                url = daVisitare.pop(chiave)
                if chiave in visitate or (chiave != normalizza(inizio) and PAGINE_INUTILI.search(url)):
                    continue
                if comune.scaduta(scadenza):
                    passoPagine.piattaforma = f"tempo massimo del sito raggiunto: lette le {len(pagine)} pagine principali"
                    break
                comune.battito()
                visitate.add(chiave)
                if len(pagine) >= massimoPagine:
                    passoPagine.piattaforma = f"lette le {massimoPagine} pagine principali, le meno profonde (regola pagineMassimeDelSito)"
                    break
                raccolte = {}

                def conChrome(percorso, url=url, raccolte=raccolte):
                    if schede["pagine"] >= PAGINE_PER_SCHEDA:
                        nuovaScheda()
                    schede["pagine"] += 1
                    pagina = schede["pagina"]
                    risposta = pagina.goto(url, wait_until="domcontentloaded", timeout=MILLISECONDI_DI_CARICAMENTO)
                    if risposta is not None and risposta.status >= 400:
                        raise comune.ElementoNonScaricabile(f"la pagina risponde {risposta.status}")
                    try:
                        pagina.wait_for_load_state("networkidle", timeout=15000)
                    except Exception:
                        pass
                    if not statoCookie["rifiutati"]:
                        statoCookie["rifiutati"] = rifiutaCookie(pagina)
                    scorriFinoInFondo(pagina)
                    raccolte["aperti"] = apriContenutiNascosti(pagina)
                    raccolte["raccolta"] = pagina.evaluate(RACCOLTA_DELLA_PAGINA)
                    raccolte["url"] = pagina.url
                    html = pagina.content()
                    raccolte["html"] = html
                    with open(percorso, "w", encoding="utf-8") as file:
                        file.write(html)
                    return "text/html"

                def senzaChrome(percorso, url=url, raccolte=raccolte):
                    risposta = comune.sessioneWeb().get(url, timeout=(20, 60))
                    if risposta.status_code >= 400:
                        raise comune.ElementoNonScaricabile(f"la pagina risponde {risposta.status_code}")
                    raccolte["raccolta"] = raccoltaDaHtml(risposta.text, risposta.url)
                    raccolte["url"] = risposta.url
                    raccolte["html"] = risposta.text
                    with open(percorso, "w", encoding="utf-8") as file:
                        file.write(risposta.text)
                    return "text/html"

                codice = statoDelCollegamento(url)
                if codice in (404, 410):
                    rotti.append({"url": url, "codice": codice})
                    continue
                passoPagine.attesi += 1
                numero = passoPagine.attesi
                percorsoPagina = urllib.parse.urlsplit(url).path.strip("/") or "home"
                nomeBase = f"pagina_{numero:04d}_{comune.nomeDiFilePulito(percorsoPagina, 50)}"
                chiaveElemento = f"pagina:{chiave}"
                if contesto.giaCaricato(chiaveElemento):
                    # Ripresa: la pagina è già su Drive; si rilegge soltanto per i collegamenti.
                    passoPagine.scaricati += 1
                    riuscito = True
                    try:
                        conChrome(contesto.temporanea + "/_ripresa.html")
                    except Exception:
                        try:
                            senzaChrome(contesto.temporanea + "/_ripresa.html")
                        except Exception:
                            pass
                else:
                    riuscito = contesto.scaricaElemento(passoPagine, "sito", chiaveElemento, nomeBase, "html", [("Chrome", conChrome), ("richiesta diretta", senzaChrome)])
                if not riuscito or "raccolta" not in raccolte:
                    continue
                raggiunto = raccolte.get("url", url)
                if dominioDiverso(inizio, raggiunto):
                    if numero == 1:
                        altroDominio = dominioDiverso(inizio, raggiunto)
                        break
                    continue
                if numero == 1:
                    sitoDelCliente = dominio(raggiunto)
                raccolta = raccolte["raccolta"]
                # un <img> con src vuoto diventa l'indirizzo della pagina stessa: non è un'immagine
                questaPagina = {normalizza(url), normalizza(raggiunto)}
                for chiaveRaccolta in ("immagini", "icone"):
                    raccolta[chiaveRaccolta] = [voce for voce in raccolta.get(chiaveRaccolta, []) if not stessaPagina(voce.get("url"), questaPagina)]
                raccolta["sfondi"] = [sfondo for sfondo in raccolta.get("sfondi", []) if not stessaPagina(sfondo, questaPagina)]
                for voce in raccolta.get("immagini", []):
                    vero = indirizzoVeroShortPixel(voce.get("url"), sitoDelCliente)
                    if vero:
                        voce["url"] = vero
                        correzioniShortPixel += 1
                for posizione, sfondo in enumerate(raccolta.get("sfondi", [])):
                    vero = indirizzoVeroShortPixel(sfondo, sitoDelCliente)
                    if vero:
                        raccolta["sfondi"][posizione] = vero
                        correzioniShortPixel += 1
                datiDellaPagina = testoPulito(raccolte["html"])
                datiDellaPagina.update({"url": raggiunto, "file": contesto.stato["elementi"].get(chiaveElemento, {}).get("nome", ""), "contenutiAperti": raccolte.get("aperti", 0)})
                pagine.append(datiDellaPagina)
                for voce in raccolta.get("immagini", []):
                    if voce.get("url") and not voce["url"].startswith(("data:", "blob:")):
                        immagini.setdefault(voce["url"], {"alt": voce.get("alt", ""), "logo": voce.get("logo", False), "pagina": raggiunto})
                for sfondo in raccolta.get("sfondi", []):
                    if sfondo and not sfondo.startswith(("data:", "blob:")):
                        immagini.setdefault(sfondo, {"alt": "", "logo": False, "pagina": raggiunto, "sfondo": True})
                for icona in raccolta.get("icone", []):
                    if icona.get("url") and not icona["url"].startswith("data:"):
                        icone.setdefault(icona["url"], icona.get("tipo", ""))
                video.extend(sorgente for sorgente in raccolta.get("video", []) if sorgente and not sorgente.startswith("blob:") and sorgente not in video)
                incorporati.extend(sorgente for sorgente in raccolta.get("incorporati", []) if sorgente and sorgente not in incorporati)
                colori.update(raccolta.get("colori", {}))
                sfondiColore.update(raccolta.get("sfondiColore", {}))
                caratteri.update(raccolta.get("caratteri", {}))
                fontEsterni.update(raccolta.get("fontEsterni", []))
                collegamenti = [voce.get("url") or "" for voce in raccolta.get("collegamenti", [])]
                if not sitemapLetta:
                    collegamenti += sorted(paginaDellaSitemap(raggiunto))
                    sitemapLetta = True
                for destinazione in collegamenti:
                    if not destinazione.startswith("http"):
                        continue
                    percorso = urllib.parse.urlsplit(destinazione).path.lower()
                    if percorso.endswith(".pdf"):
                        documenti.setdefault(destinazione.split("#")[0], raggiunto)
                        continue
                    if dominio(destinazione) != sitoDelCliente or percorso.endswith(ESTENSIONI_DA_NON_VISITARE):
                        continue
                    chiaveNuova = normalizza(destinazione)
                    if chiaveNuova not in visitate and chiaveNuova not in daVisitare:
                        daVisitare[chiaveNuova] = destinazione
        finally:
            try:
                if schede["sessione"] is not None:
                    schede["sessione"].close()
            finally:
                browser.close()  # collegato al Chrome condiviso: si stacca soltanto, Chrome resta per gli altri lavoratori
    contesto.giroDiRecupero(passoPagine)
    if altroDominio:
        passoPagine.limite = f"il sito del CRM ({sitoDelCliente}) porta a un dominio diverso ({altroDominio}): nulla raccolto, va controllato il CRM"
        return [passoPagine, passoImmagini, passoFile]

    # Immagini e file hanno ognuno il tempo della fonte sito, dopo le pagine (24/11/2026: le pagine prendevano tutti i 5 minuti, 0 immagini su 252 scaricate);
    # le immagini si scaricano più alla volta
    from concurrent.futures import ThreadPoolExecutor

    minutiDeiFile = float((comune.regola("minutiMassimiPerFonte") or {}).get("sito") or 5)  # lo stesso tempo della fonte sito
    passoImmagini.scadenza = time.time() + minutiDeiFile * 60

    # Immagini, loghi e icone: tutte quelle trovate nelle pagine.
    tutte = list(immagini.items()) + [(url, {"alt": "", "logo": "icon" in tipo, "pagina": inizio, "icona": tipo}) for url, tipo in icone.items() if url not in immagini]
    passoImmagini.attesi = len(tutte)
    elencoDelleImmagini = []

    def unaImmagine(numero, url, dettagli):
        nomeOriginale = comune.nomeDiFilePulito(urllib.parse.unquote(urllib.parse.urlsplit(url).path.rsplit("/", 1)[-1]).rsplit(".", 1)[0], 40)
        radice = "logo" if dettagli.get("logo") else ("icona" if dettagli.get("icona") else "sito")

        def diretto(percorso, url=url, dettagli=dettagli):
            return comune.scaricaInFile(url, percorso, intestazioni={"Referer": dettagli.get("pagina", inizio)})

        def senzaRiferimento(percorso, url=url):
            return comune.scaricaInFile(url, percorso)

        contesto.scaricaElemento(passoImmagini, "sito", f"immagine:{url}", f"{radice}_{numero:04d}_{nomeOriginale}", "immagine",
                                 [("richiesta con pagina di origine", diretto), ("richiesta semplice", senzaRiferimento)],
                                 foto=not dettagli.get("logo") and not dettagli.get("icona"), descrizione={"url": url, **dettagli})

    with ThreadPoolExecutor(max_workers=int(comune.regola("fotoMapsInParallelo") or 6), thread_name_prefix="immaginiSito") as fili:
        for futuro in [fili.submit(unaImmagine, numero, url, dettagli) for numero, (url, dettagli) in enumerate(tutte, start=1)]:
            futuro.result()
    elencoDelleImmagini = [{"url": url, **dettagli} for url, dettagli in tutte]
    contesto.giroDiRecupero(passoImmagini)
    passoFile.scadenza = time.time() + minutiDeiFile * 60

    # File: PDF e video del sito.
    esterni = [url for url in incorporati if DOMINI_DEI_VIDEO.search(url)]
    passoFile.attesi = len(documenti) + len(video) + len(esterni)
    for numero, (url, origine) in enumerate(documenti.items(), start=1):
        nomeOriginale = comune.nomeDiFilePulito(urllib.parse.unquote(urllib.parse.urlsplit(url).path.rsplit("/", 1)[-1]).rsplit(".", 1)[0], 50)
        contesto.scaricaElemento(passoFile, "sito", f"pdf:{url}", f"documento_{numero:03d}_{nomeOriginale}", "pdf",
                                 [("richiesta", lambda percorso, url=url: comune.scaricaInFile(url, percorso))], descrizione={"url": url, "pagina": origine})
    for numero, url in enumerate(video, start=1):
        contesto.scaricaElemento(passoFile, "sito", f"video:{url}", f"video_sito_{numero:03d}", "video",
                                 [("richiesta", lambda percorso, url=url: (comune.scaricaInFile(url, percorso) and ".mp4")),
                                  ("yt-dlp", lambda percorso, url=url: scaricaConYtDlp(url, percorso))], descrizione={"url": url})
    for numero, url in enumerate(esterni, start=1):
        contesto.scaricaElemento(passoFile, "sito", f"incorporato:{url}", f"video_incorporato_{numero:03d}", "video",
                                 [("yt-dlp", lambda percorso, url=url: scaricaConYtDlp(url, percorso))], descrizione={"url": url})
    contesto.giroDiRecupero(passoFile)

    stile = {"coloriDelTesto": colori.most_common(12), "coloriDiSfondo": sfondiColore.most_common(12), "caratteri": caratteri.most_common(8),
             "fontEsterni": sorted(fontEsterni), "icone": icone}
    contesto.scriviJson("sito", "_01_PagineDelSito.json", {"sito": inizio, "pagine": pagine, "collegamentiRotti": rotti})
    contesto.scriviJson("sito", "_02_StileDelSito.json", stile)
    contesto.scriviJson("sito", "_03_FileDelSito.json", {"immagini": elencoDelleImmagini, "documenti": documenti, "video": video, "incorporati": incorporati})
    passoPagine.dettagli = {"collegamentiRotti": len(rotti)}
    if correzioniShortPixel:
        passoImmagini.dettagli["indirizziShortPixelCorretti"] = correzioniShortPixel  # sito con immagini ShortPixel: riconosciuto e corretto
    return [passoPagine, passoImmagini, passoFile]

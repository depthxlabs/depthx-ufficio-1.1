"""CONTROLLO DEL SITO PER LA SEZIONE, Linea 1.1 Outbound Websites, Ricerca clienti.

Legge il sito della struttura e decide la sezione del CRM con controlli rigidi, in questo ordine:
  S3 sito datato:    anno del copyright più vecchio di 3 anni, oppure sito senza https, oppure sito non adatto al telefono
  S2 sito debole:    meno di 5 pagine, oppure sito fatto con un costruttore (Wix, Jimdo, Weebly, Webnode, Site123,
                     Strikingly, GoDaddy, IONOS MyWebsite)
  S4 sito di qualità: tutti gli altri
Prende anche l'email pubblicata (mai PEC), i social, la piattaforma e il numero di pagine.
"""
import datetime, html, re, time, urllib.parse
import requests

AGENTE = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130 Safari/537.36"
PAUSA_PAGINA = 1.0   # secondi tra due pagine dello stesso sito
RE_EMAIL = re.compile(r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}")
SCARTA_EMAIL = re.compile(r"\.(png|jpe?g|gif|webp|svg|css|js)$|example\.|sentry|wixpress|domain\.|@2x|yourdomain|email\.(com|it)$|nome\.cognome|mario\.rossi|"
                          r"@([\w-]+\.)*(pec|pecaruba|arubapec|legalmail|pecimprese|postacert|sicurezzapostale|cert)\.|\.pec\.|booking\.com|airbnb|expedia|"
                          # le mail personali, sui domini di posta gratuita, non si contattano mai: restano fuori dal CRM
                          r"@([\w-]+\.)*(gmail|googlemail|libero|hotmail|yahoo|ymail|alice|virgilio|tiscali|outlook|live|msn|icloud|me|mac|aol|tin|"
                          r"inwind|iol|katamail|fastwebnet|teletu|tim|vodafone|wind|proton|protonmail|gmx|web|mail|yandex|zoho)\.[a-z.]+$|"
                          # le mail degli enti pubblici non sono della struttura
                          r"@([\w-]+\.)*(comune|regione|provincia|promoturismo|proloco|gov)\.|\.gov\.it$", re.I)
COSTRUTTORI = [("Wix", r"wix\.com|wixstatic\.com|_wixCIDX"), ("Jimdo", r"jimdo|jimcdn\.com"), ("Weebly", r"weebly\.com|editmysite\.com"),
               ("Webnode", r"webnode\."), ("Site123", r"site123\.|s123-cdn"), ("Strikingly", r"strikingly|strikinglycdn"),
               ("GoDaddy", r"img1\.wsimg\.com|godaddy.{0,40}website builder"), ("IONOS MyWebsite", r"mywebsite-editor|ionos.{0,40}mywebsite|website-editor\.net")]
PIATTAFORME = [("WordPress", r"wp-content|wp-includes"), ("Joomla", r"/media/jui/|joomla"), ("Drupal", r"drupal"),
               ("Squarespace", r"squarespace\.com|static1\.squarespace"), ("Shopify", r"cdn\.shopify\.com"), ("Webflow", r"webflow\.")]
SU_MISURA = "Piattaforma non riconoscibile dal codice del sito: sito su misura"
SOCIAL = {"instagram": r"https?://(?:www\.)?instagram\.com/[A-Za-z0-9_.]+/?", "facebook": r"https?://(?:www\.|it-it\.|m\.)?facebook\.com/[A-Za-z0-9_.\-/?=]+",
          "youtube": r"https?://(?:www\.)?youtube\.com/(?:@|channel/|c/|user/)[A-Za-z0-9_.\-]+", "tiktok": r"https?://(?:www\.)?tiktok\.com/@[A-Za-z0-9_.]+",
          "linkedin": r"https?://(?:www\.|it\.)?linkedin\.com/company/[A-Za-z0-9_.\-]+"}
SOCIAL_DA_SCARTARE = re.compile(r"/sharer|/share|/plugins|/tr\?|/dialog/|/intent/|wix|wordpress|elementor|godaddy", re.I)


def scarica(url):
    try:
        r = requests.get(url, timeout=15, headers={"User-Agent": AGENTE}, allow_redirects=True)
        if r.status_code == 200 and "html" in r.headers.get("Content-Type", ""):
            r.encoding = r.apparent_encoding if not r.encoding or r.encoding.lower() == "iso-8859-1" else r.encoding
            return r.url, r.text
    except requests.RequestException:
        pass
    return "", ""


def conta_pagine_sitemap(base):
    """Le pagine elencate nella sitemap del sito (anche sitemap divise in più file, fino a 10)."""
    for nome in ("sitemap.xml", "sitemap_index.xml", "wp-sitemap.xml"):
        try:
            r = requests.get(urllib.parse.urljoin(base, "/" + nome), timeout=12, headers={"User-Agent": AGENTE})
        except requests.RequestException:
            continue
        if r.status_code != 200 or "<loc>" not in r.text:
            continue
        if "<sitemapindex" in r.text:
            totale = 0
            for figlio in re.findall(r"<loc>\s*([^<\s]+)\s*</loc>", r.text)[:10]:
                try:
                    totale += len(re.findall(r"<url>", requests.get(figlio, timeout=12, headers={"User-Agent": AGENTE}).text))
                except requests.RequestException:
                    pass
            if totale:
                return totale
        else:
            return len(re.findall(r"<url>", r.text))
    return 0


def link_interni(testo, base, dominio):
    visti = set()
    for h in re.findall(r'href=["\']([^"\'#]+)["\']', testo, re.I):
        u = urllib.parse.urljoin(base, h.strip())
        p = urllib.parse.urlparse(u)
        if p.scheme in ("http", "https") and p.netloc.replace("www.", "") == dominio and not re.search(r"\.(jpe?g|png|gif|webp|pdf|zip|css|js|svg|mp4)$", p.path, re.I):
            visti.add(p.path.rstrip("/") or "/")
    return visti


def email_dalla_pagina(testo, dominio):
    testo = re.sub(r'placeholder\s*=\s*["\'][^"\']*["\']', "", testo, flags=re.I)
    trovate = set(urllib.parse.unquote(m) for m in re.findall(r'mailto:([^"\'?>\s]+)', testo, re.I))
    trovate |= set(RE_EMAIL.findall(html.unescape(testo)))
    trovate = {e.strip().strip(".").lower() for e in trovate if not SCARTA_EMAIL.search(e)}
    radice = dominio.split(".")[0]
    return sorted(trovate, key=lambda e: (radice not in e, len(e)))


def anno_del_copyright(testo):
    t = html.unescape(re.sub(r"<[^>]+>", " ", testo))
    anni = [int(a) for m in re.finditer(r"(?:©|\(c\)|copyright)[^0-9]{0,40}((?:19|20)\d\d)(?:\s*[-/–]\s*((?:19|20)\d\d))?", t, re.I)
            for a in m.groups() if a]
    adesso = datetime.date.today().year
    anni = [a for a in anni if 1995 <= a <= adesso]
    return max(anni) if anni else None


def testo_di_presentazione(testo):
    """Titolo, descrizione e titoli della pagina: il testo da cui si riconosce la sottocategoria."""
    pezzi = re.findall(r"<title[^>]*>(.*?)</title>", testo, re.I | re.S)
    pezzi += re.findall(r'<meta[^>]+name=["\']description["\'][^>]+content=["\']([^"\']*)', testo, re.I)
    pezzi += re.findall(r"<h[12][^>]*>(.*?)</h[12]>", testo, re.I | re.S)
    return html.unescape(re.sub(r"<[^>]+>", " ", " ".join(pezzi)))


# i crediti di chi ha fatto il sito, nel footer: "realizzato da", "web design", "powered by" con il link a un altro dominio
PAROLE_DEI_CREDITI = re.compile(r"realizzat[oa]|sviluppat[oa]|progettat[oa]|creat[oa]\s+(?:da|by)|design(?:ed)?\s+by|web\s*design|web\s*agency|"
                                r"web\s*marketing|powered\s+by|developed\s+by|made\s+by|credits|crediti|siti\s+web|sito\s+web\s+(?:a\s+cura|by|da)", re.I)
PIATTAFORME_NEI_CREDITI = re.compile(r"wordpress|blogger|blogspot|wix|jimdo|weebly|webnode|site123|strikingly|godaddy|ionos|squarespace|shopify|webflow|joomla|drupal|"
                                     r"elementor|google|facebook|instagram|booking|airbnb|tripadvisor|iubenda|cookiebot|privacy|w3\.org|schema\.org", re.I)


def crediti_di_agenzia(testo, dominio):
    """Il nome dell'agenzia se nel footer c'è un credito con il link a un altro dominio, altrimenti stringa vuota."""
    piedi = re.findall(r"<footer\b.*?</footer>", testo, re.I | re.S) or [testo[-6000:]]
    for piede in piedi:
        for m in re.finditer(r'<a\b[^>]*href=["\'](https?://[^"\']+)["\'][^>]*>(.*?)</a>', piede, re.I | re.S):
            altro = urllib.parse.urlparse(m.group(1)).netloc.replace("www.", "").lower()
            if not altro or altro == dominio or altro.endswith("." + dominio) or PIATTAFORME_NEI_CREDITI.search(altro):
                continue
            intorno = html.unescape(re.sub(r"<[^>]+>", " ", piede[max(0, m.start() - 160):m.end()]))
            if PAROLE_DEI_CREDITI.search(intorno):
                return altro
    return ""


def controlla_sito(sito):
    base = sito if sito.startswith("http") else "https://" + sito
    dominio = urllib.parse.urlparse(base).netloc.replace("www.", "").lower()
    finale, home = scarica(base)
    if not home and base.startswith("http://"):
        finale, home = scarica("https://" + base[7:])
    if not home:
        return {"letto": False}
    https = finale.startswith("https://")
    if not https:
        con_https, _ = scarica("https://" + finale.split("://", 1)[1])
        https = con_https.startswith("https://")
    dominio = urllib.parse.urlparse(finale).netloc.replace("www.", "").lower() or dominio
    testi = [home]
    contatti = [u for u in sorted(link_interni(home, finale, dominio)) if re.search(r"contatt|contact|chi-siamo|dove-siamo|about|info", u, re.I)][:2]
    for u in contatti:
        time.sleep(PAUSA_PAGINA)
        _, t = scarica(urllib.parse.urljoin(finale, u))
        if t:
            testi.append(t)
    tutto = "\n".join(testi)
    email = email_dalla_pagina(tutto, dominio)
    costruttore = next((n for n, r in COSTRUTTORI if re.search(r, home, re.I)), "")
    piattaforma = costruttore or next((n for n, r in PIATTAFORME if re.search(r, home, re.I)), SU_MISURA)
    pagine = conta_pagine_sitemap(finale) or len(link_interni(home, finale, dominio))
    anno = anno_del_copyright(tutto)
    telefono = bool(re.search(r'<meta[^>]+name=["\']viewport["\'][^>]+width\s*=\s*device-width', home, re.I) or
                    re.search(r'<meta[^>]+content=["\'][^"\']*width\s*=\s*device-width[^>]+name=["\']viewport', home, re.I))
    adesso = datetime.date.today().year
    motivi_s3 = ([f"copyright {anno}"] if anno and anno < adesso - 3 else []) + ([] if https else ["senza https"]) + ([] if telefono else ["non adatto al telefono"])
    motivi_s2 = ([f"{pagine} pagine"] if pagine < 5 else []) + ([f"costruttore {costruttore}"] if costruttore else [])
    if motivi_s3:
        sezione, motivo = "S3", "datato: " + ", ".join(motivi_s3)
    elif motivi_s2:
        sezione, motivo = "S2", "debole: " + ", ".join(motivi_s2)
    else:
        sezione, motivo = "S4", f"qualità: https, adatto al telefono, {pagine} pagine" + (f", copyright {anno}" if anno else "")
    social = {}
    for k, r in SOCIAL.items():
        trovati = [s for s in re.findall(r, tutto) if not SOCIAL_DA_SCARTARE.search(s)]
        social[k] = trovati[0] if trovati else ""
    return {"letto": True, "agenzia": crediti_di_agenzia(home, dominio), "sito": finale, "email": email, "sezione": sezione, "motivo": motivo, "piattaforma": piattaforma,
            "pagine": pagine, "social": social, "presentazione": testo_di_presentazione(home), "dominio": dominio}

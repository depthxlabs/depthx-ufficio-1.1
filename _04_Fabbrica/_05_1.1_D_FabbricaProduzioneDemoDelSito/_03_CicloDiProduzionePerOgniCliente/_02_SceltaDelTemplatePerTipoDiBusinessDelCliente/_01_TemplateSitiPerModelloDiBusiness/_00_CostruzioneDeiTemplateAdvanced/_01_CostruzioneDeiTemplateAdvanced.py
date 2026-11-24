"""La costruzione dei 4 template Advanced (Michele, 11/11/2026, task #575 e #576).

Michele: si prendono i nuovi template, uno per tipo, si mantiene il copy approvato e si aggiunge quello che il pacchetto
Advanced ha (lista della pagina Prodotti del sito): sito multipagina fino a 5 sezioni, italiano e inglese, 3 animazioni di
transizione, 1 elemento 3D di codice, 6 recensioni Google, pulsanti WhatsApp e chiamata animati, Prenota con la finestra
delle date, mappa con la sede animata, preparazione completa per Google, galleria di foto statica.
Le pagine standard sono Home, Camere, Galleria, Recensioni, Dove siamo e contatti. Una pagina a sé c'è solo per un servizio
dentro la struttura (ristorante, centro benessere, piscina): in quel caso Galleria e Recensioni entrano nella Home. Tutto il
resto (colazione, spazi, dintorni) sta nella Home. Le pagine le decide la fabbrica nel passo 5.15.

Il disegno viene dalle demo nuove del sito (Hotel Marea Alta per la struttura, i colori delle demo di ogni tipo); le frasi
sono quelle approvate dei template di prima, con le stesse chiavi. Tutti e 4 i template usano gli stessi script, lo stesso
config (window.SITO_CONFIG) e gli stessi segnaposto. Si lancia una volta: riscrive template/ e contratto.json di ogni tipo,
dopo averne tenuto la copia (template.copiaPrimaDellAdvanced, contratto.json.copiaPrimaDellAdvanced).

Pitstop 9, zero giri di correzione (Michele, 12/11/2026, task #614): le cause più frequenti dei giri del product manager si
correggono qui, nella base. Foto e sezione coincidono: sotto "La colazione" (Hotel e B&B) solo foto della colazione, mai
un piatto dei prodotti; il blocco degli spazi del B&B, che parla soprattutto di terrazza, giardino e spazi comuni, ha la sua
area "spazi" (prima terrazze e giardini, poi spazi comuni, solo alla fine la cucina) invece dell'area della cucina (sotto
"Fuori dalla porta" c'era la foto della cucina). Nel CSS comune (_02_PartiComuni/css/comune.css, in fondo) la griglia delle
camere e la galleria si ricompongono sul numero vero di foto (data-quante): mai una foto sola nell'ultima riga con lo spazio
vuoto accanto; il nome della struttura nella testata non si taglia mai con i puntini, va a capo. Copie di prima: .copiaPrimaVelocita.
"""

import json
import re
import shutil
from pathlib import Path

CARTELLA = Path(__file__).absolute().parent
MODELLI = CARTELLA.parent
COMUNI = CARTELLA / "_02_PartiComuni"
COPIA = "copiaPrimaDellAdvanced"

# --------------------------------------------------------------------------------------------- pezzi comuni delle pagine

ICONA_TEL = '<svg viewBox="0 0 24 24" aria-hidden="true" focusable="false"><path fill="currentColor" d="M6.6 10.8a15.2 15.2 0 0 0 6.6 6.6l2.2-2.2c.3-.3.7-.4 1-.2 1.1.4 2.3.6 3.6.6.6 0 1 .4 1 1V20c0 .6-.4 1-1 1A17 17 0 0 1 3 4c0-.6.4-1 1-1h3.5c.6 0 1 .4 1 1 0 1.3.2 2.5.6 3.6.1.3 0 .7-.2 1l-2.3 2.2z"/></svg>'
ICONA_WA = '<svg viewBox="0 0 24 24" aria-hidden="true" focusable="false"><path fill="currentColor" d="M12 2a10 10 0 0 0-8.6 15.1L2 22l5-1.3A10 10 0 1 0 12 2zm0 18.2a8.2 8.2 0 0 1-4.2-1.2l-.3-.2-3 .8.8-2.9-.2-.3A8.2 8.2 0 1 1 12 20.2zm4.5-6.1c-.2-.1-1.5-.7-1.7-.8-.2-.1-.4-.1-.6.1l-.8 1c-.1.2-.3.2-.5.1a6.7 6.7 0 0 1-3.3-2.9c-.3-.4.2-.4.7-1.3.1-.2 0-.3 0-.4l-.8-1.8c-.2-.5-.4-.4-.6-.4h-.5c-.2 0-.4.1-.7.3-.2.3-.9.9-.9 2.2s1 2.5 1.1 2.7c.1.2 1.9 2.9 4.6 4 1.7.7 2.4.8 3.2.7.5-.1 1.5-.6 1.8-1.2.2-.6.2-1.1.1-1.2l-.5-.3z"/></svg>'
ICONA_MAIL = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false"><rect x="3" y="5" width="18" height="14" rx="1.5"/><path d="M3.5 6l8.5 7 8.5-7"/></svg>'
ICONA_CALENDARIO = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false"><rect x="3.5" y="5" width="17" height="15.5" rx="1.5"/><path d="M3.5 10h17M8 3v4M16 3v4"/></svg>'
ICONA_MENU = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" aria-hidden="true" focusable="false"><path d="M3 8h18M3 16h18"/></svg>'

LINGUE = ('<div class="lingue" role="group" aria-label="Lingua" data-en-aria-label="Language"><button type="button" data-lingua="it" '
          'aria-pressed="true">IT</button><button type="button" data-lingua="en" aria-pressed="false">EN</button></div>')


def pic(scena, forma="16x9", sizes="100vw", alt="Una foto della struttura", altEn="A photo of the property", telefono=False, subito=False):
    """Una foto di una scena: la mette foto.js dal config (data-scena); senza foto il suo blocco esce."""
    larghezza, altezza = ("1600", "900") if forma == "16x9" else ("900", "1600")
    extra = ' data-telefono="9x16" data-media-telefono="(max-width: 760px)"' if telefono else ""
    carica = 'fetchpriority="high" decoding="async"' if subito else 'loading="lazy" decoding="async"'
    return (f'<picture data-scena="{scena}" data-forma="{forma}"{extra} data-sizes="{sizes}"><img alt="{alt}" data-en-alt="{altEn}" '
            f'width="{larghezza}" height="{altezza}" {carica}></picture>')


def foto(scena, classe="foto--larga", forma="16x9", sizes="(max-width: 900px) 100vw, 50vw", alt="Una foto della struttura",
         altEn="A photo of the property", altra=""):
    return f'<div class="foto {classe} {altra}" data-blocco-foto data-rivela>{pic(scena, forma, sizes, alt, altEn)}</div>'


def testo(tag, it, en, chiave="", classe="", extra=""):
    attributi = (f' class="{classe}"' if classe else "") + (f' data-t="{chiave}"' if chiave else "") + f' data-en="{en}"' + extra
    return f"<{tag}{attributi}>{it}</{tag}>"


def frasi(elenco):
    """elenco di (chiave, it, en): i paragrafi di un blocco."""
    return "".join(testo("p", it, en, chiave) for chiave, it, en in elenco)


def coppia(id_, scena, forma, titolo, paragrafi, inversa=False, sfondo="", dopo="", alt="Una foto della struttura", altEn="A photo of the property"):
    """Un blocco con una foto e il testo accanto. titolo = (chiave, it, en)."""
    classeFoto = "foto--alta" if forma == "9x16" else "foto--larga"
    return (f'<section class="blocco {sfondo}" id="{id_}" aria-labelledby="titolo-{id_}"><div class="contenitore">'
            f'<div class="coppia{" coppia--inversa" if inversa else ""}">'
            f'<div class="coppia__foto foto {classeFoto}" data-blocco-foto data-rivela>{pic(scena, forma, "(max-width: 900px) 100vw, 50vw", alt, altEn)}</div>'
            f'<div class="coppia__testo" data-rivela>{testo("h2", titolo[1], titolo[2], titolo[0], "titolo", f" id=\"titolo-{id_}\"")}'
            f'{frasi(paragrafi)}{dopo}</div></div></div></section>')


def bottoni(conPrenota=True):
    prenota = (f'<button class="btn btn--pieno" type="button" data-apri-prenota>{ICONA_CALENDARIO}<span data-en="Book">Prenota</span></button>'
               if conPrenota else "")
    return ('<div class="azioni">' + prenota +
            f'<a class="btn" data-link="tel" href="#">{ICONA_TEL}<span data-en="Call us">Chiamateci</span></a>'
            f'<a class="btn" data-link="whatsapp" href="#" target="_blank" rel="noopener">{ICONA_WA}<span data-en="Message us on WhatsApp">Scriveteci su WhatsApp</span></a>'
            f'<a class="btn" data-link="email" href="#">{ICONA_MAIL}<span data-en="Email us">Scriveteci una email</span></a></div>')


def moduloDate(suffisso):
    ospiti = "".join(f"<option{' selected' if n == 2 else ''}>{n}</option>" for n in range(1, 11))
    return (f'<form class="prenota" data-prenota aria-label="Verifica la disponibilità" data-en-aria-label="Check availability">'
            f'<div class="campo"><label for="arrivo-{suffisso}" data-en="Arrival">Arrivo</label><input id="arrivo-{suffisso}" name="arrivo" type="date" required></div>'
            f'<div class="campo"><label for="partenza-{suffisso}" data-en="Departure">Partenza</label><input id="partenza-{suffisso}" name="partenza" type="date" required></div>'
            f'<div class="campo"><label for="ospiti-{suffisso}" data-en="Guests">Ospiti</label><select id="ospiti-{suffisso}" name="ospiti">{ospiti}</select></div>'
            f'<button class="btn btn--pieno" type="submit"><span data-en="Book">Prenota</span></button></form>')


def recensioni(id_, sfondo="blocco--tenue", soloConPagineInterne=False, quante=6, conLink=False):
    """Le 6 recensioni Google (pacchetto Advanced): firma sempre "Un ospite di {nomestruttura}", mai nome né città; Google si
    nomina solo nel titolo (Michele, 11/11/2026, task #577). Il passo 5.9 scrive i testi; una recensione che manca esce intera."""
    voci = "".join(
        f'<figure class="recensione" data-recensione data-rivela><span class="stelle" aria-hidden="true">{{stelleRecensione{n}}}</span>'
        f'<blockquote><p data-t="rec.{n}.testo">«{{testoRecensione{n}}}»</p></blockquote>'
        f'<figcaption><span data-t="rec.firma" data-en="A guest of {{nomestruttura}}">Un ospite di {{nomestruttura}}</span></figcaption></figure>'
        for n in range(1, quante + 1))
    segno = " data-solo-con-pagine-interne" if soloConPagineInterne else (' data-pagina="recensioni.html"' if conLink else "")
    altre = ('<p class="centro" data-rivela><a class="btn" href="recensioni.html"><span data-en="All the reviews">Tutte le recensioni</span></a></p>'
             if conLink else "")
    return (f'<section class="blocco {sfondo}" id="{id_}" data-sezione-recensioni aria-labelledby="titolo-{id_}"{segno}><div class="contenitore">'
            f'<div class="testa" data-rivela>{testo("h2", "Dicono di noi su Google.", "What they say about us on Google.", "rec.titolo", "titolo", f" id=\"titolo-{id_}\"")}</div>'
            f'<div class="recensioni__elenco">{voci}</div>'
            f'<p class="recensioni__link" data-rivela><a class="link" data-link="recensioni" href="#" target="_blank" rel="noopener">'
            f'<span data-t="rec.link" data-en="Read all the reviews on Google.">Leggete tutte le recensioni su Google.</span></a></p>{altre}</div></section>')


def galleria(id_, scene, soloConPagineInterne=False, conTitolo=True):
    """La galleria di foto statica (pacchetto Advanced): foto ferme, nessuna animazione."""
    voci = "".join(f'<figure class="galleria__voce" data-blocco-foto data-rivela><div class="foto">{pic(s, "16x9", "(max-width: 900px) 50vw, 33vw")}</div></figure>'
                   for s in scene)
    segno = " data-solo-con-pagine-interne" if soloConPagineInterne else ""
    titolo = f'<div class="testa" data-rivela>{testo("h2", "Galleria", "Gallery", "", "titolo", f" id=\"titolo-{id_}\"")}</div>' if conTitolo else ""
    etichetta = f' aria-labelledby="titolo-{id_}"' if conTitolo else ' aria-label="Galleria" data-en-aria-label="Gallery"'
    return (f'<section class="blocco blocco--stretto" id="{id_}"{etichetta}{segno}><div class="contenitore">{titolo}'
            f'<div class="galleria">{voci}</div></div></section>')


def mappaEContatti(t):
    """Dove siamo e contatti: le frasi del tipo, la mappa di Google sulla sede (animata), i recapiti e i pulsanti."""
    return (f'<section class="blocco" id="dove" aria-labelledby="titolo-dove"><div class="contenitore"><div class="coppia">'
            f'<div class="coppia__testo" data-rivela>{testo("h2", t["dove"]["titolo"][1], t["dove"]["titolo"][2], t["dove"]["titolo"][0], "titolo", " id=\"titolo-dove\"")}'
            f'{frasi(t["dove"]["frasi"])}<a class="link" data-link="mappa" href="#" target="_blank" rel="noopener"><span data-en="How to get here">Come arrivare</span></a>'
            f'<ul class="recapiti"><li><a data-link="mappa" href="#" target="_blank" rel="noopener"><span data-t="posizione">{{via}}, {{cap}} {{comune}} ({{provincia}})</span></a></li>'
            f'<li><a data-link="tel" href="#"><span data-t="telefono">{{telefono}}</span></a></li>'
            f'<li><a data-link="email" href="#"><span data-t="email">{{email}}</span></a></li></ul></div>'
            f'<div class="coppia__foto foto foto--alta" data-blocco-foto data-rivela>{pic(t["dove"]["scena"], "9x16", "(max-width: 900px) 100vw, 50vw")}</div>'
            f'</div>{MAPPA}'
            f'</div></section>')


# La mappa della sede, disegnata come nella demo Advanced Hotel Marea Alta: strade di fantasia, lo spillo animato sulla sede,
# il nome e l'indirizzo veri, e il pulsante che apre Google Maps. Nessun servizio esterno nella pagina (11/11/2026).
MAPPA = ('<div class="mappa" data-mappa data-rivela>'
         '<svg class="mappa__strade" viewBox="0 0 1200 500" preserveAspectRatio="xMidYMid slice" aria-hidden="true" focusable="false">'
         '<rect width="1200" height="500" class="mappa__fondo"/>'
         '<path class="mappa__verde" d="M0 380C140 340 260 420 420 390S700 300 860 340 1080 430 1200 400V500H0Z"/>'
         '<g class="mappa__via"><path d="M0 250H1200M600 0V500M0 120C300 140 500 90 1200 160M140 0L320 500M880 0L760 500"/></g></svg>'
         '<div class="mappa__osm" data-osm aria-hidden="true"></div>'
         '<span class="mappa__alone" aria-hidden="true"></span><span class="mappa__spillo" aria-hidden="true"><svg viewBox="0 0 40 52" focusable="false">'
         '<path d="M20 51C8 35 2 27 2 19a18 18 0 0 1 36 0c0 8-6 16-18 32z"/><circle cx="20" cy="19" r="7"/></svg></span>'
         '<span class="mappa__etichetta"><span data-marchio>{nomestruttura}</span><small data-t="posizione">{via}, {cap} {comune} ({provincia})</small></span>'
         '<div class="mappa__azioni"><button class="btn btn--pieno" type="button" data-apri-mappa><span data-en="Open the map">Aprite la mappa</span></button>'
         '<a class="btn mappa__arrivare" data-link="mappa" href="#" target="_blank" rel="noopener"><span data-en="How to get here">Come arrivare</span></a></div>'
         '<small class="mappa__crediti">© OpenStreetMap</small></div>')
# Michele, 11/11/2026: la mappa è quella di OpenStreetMap; l'anteprima con le sue tessere e la sede animata, la mappa vera al clic


def invito(t):
    f = t["fine"]
    return (f'<section class="blocco blocco--scuro" id="prenota" aria-labelledby="titolo-prenota"><div class="contenitore centro stretto" data-rivela>'
            f'{testo("h2", f["titolo"][1], f["titolo"][2], f["titolo"][0], "titolo", " id=\"titolo-prenota\"")}{frasi(f["frasi"])}'
            f'<div class="invito__date">{moduloDate("invito")}</div>{bottoni(conPrenota=False)}</div></section>')


ICONA_PIN = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false"><path d="M12 21s-7-6.3-7-11.5a7 7 0 0 1 14 0C19 14.7 12 21 12 21z"/><circle cx="12" cy="9.5" r="2.5"/></svg>'


def contatto(icona, dentro):
    return f'<p class="pk-info">{icona}{dentro}</p>'


TELEFONO_3D = contatto(ICONA_TEL, '<a data-link="tel" href="#"><span data-t="telefono">{telefono}</span></a>')
EMAIL_3D = contatto(ICONA_MAIL, '<a data-link="email" href="#"><span data-t="email">{email}</span></a>')
POSIZIONE_3D = contatto(ICONA_PIN, '<span data-t="posizione">{via}, {cap} {comune} ({provincia})</span>')


def oggetto3D():
    """L'elemento 3D di codice (pacchetto Advanced, Michele 11/11/2026): bello, curato e utile, con le informazioni vere della
    struttura; gira da solo, il visitatore non deve fare niente. Quattro forme che si alternano da un cliente all'altro: la chiave
    della camera, il dado, il biglietto da visita e la cartolina. Il template le ha tutte; il passo 5.15 ne tiene una."""
    chiave = ('<div class="pk-variante" data-oggetto="chiave"><div class="pk-scena" data-3d><div class="pk-oggetto pk-chiave">'
              f'<div class="pk-faccia pk-fronte">{pic("cartolina", "16x9", "330px")}<span class="pk-chiave__foro"></span><small data-en="Room key">Chiave della camera</small>'
              '<span class="pk-nome" data-marchio>{nomestruttura}</span><span class="pk-chiave__chip"></span></div>'
              f'<div class="pk-faccia pk-retro"><div class="pk-banda"></div>{POSIZIONE_3D}{TELEFONO_3D}</div></div></div></div>')
    dado = ('<div class="pk-variante" data-oggetto="dado"><div class="pk-scena" data-3d data-asse="xy"><div class="pk-oggetto pk-dado">'
            '<div class="pk-faccia f1"><span class="pk-nome" data-marchio>{nomestruttura}</span></div>'
            f'<div class="pk-faccia f2">{TELEFONO_3D}</div><div class="pk-faccia f3">{POSIZIONE_3D}</div><div class="pk-faccia f4">{EMAIL_3D}</div>'
            f'<div class="pk-faccia f5"><button class="pk-prenota" type="button" data-apri-prenota>{ICONA_CALENDARIO}<span data-en="Book">Prenota</span></button></div>'
            f'<div class="pk-faccia f6 pk-con-foto">{pic("cartolina", "16x9", "210px")}<span class="pk-nome" data-marchio>{{nomestruttura}}</span></div></div></div></div>')
    biglietto = ('<div class="pk-variante" data-oggetto="biglietto"><div class="pk-scena" data-3d><div class="pk-oggetto pk-biglietto">'
                 '<div class="pk-faccia pk-fronte"><span class="pk-nome" data-marchio>{nomestruttura}</span><span class="pk-filetto"></span></div>'
                 f'<div class="pk-faccia pk-retro"><span class="pk-nome pk-nome--piccolo" data-marchio>{{nomestruttura}}</span>{POSIZIONE_3D}{TELEFONO_3D}{EMAIL_3D}</div></div></div></div>')
    cartolina = ('<div class="pk-variante" data-oggetto="cartolina"><div class="pk-scena" data-3d><div class="pk-oggetto pk-cartolina">'
                 f'<div class="pk-faccia pk-fronte">{pic("cartolina", "16x9", "340px")}<span class="pk-nome" data-marchio>{{nomestruttura}}</span></div>'
                 '<div class="pk-faccia pk-retro"><div class="pk-cartolina__sx"><span class="pk-nome pk-nome--piccolo" data-marchio>{nomestruttura}</span></div>'
                 f'<div class="pk-cartolina__dx"><span class="pk-francobollo"></span>{POSIZIONE_3D}{TELEFONO_3D}</div></div></div></div></div>')
    return f'<div class="pk-varianti">{chiave}{dado}{biglietto}{cartolina}</div>'


# ----------------------------------------------------------------------------------------------------- i 4 tipi

# Le scene della galleria: ognuna prende la migliore foto rimasta, prima della sua categoria e poi di tutte le altre,
# così la galleria mostra foto diverse da quelle delle sezioni (una foto non si usa mai due volte).
TUTTE = ["esterno della struttura", "esterni senza struttura", "terrazze e giardini", "camere", "bagni", "soggiorno e spazi comuni",
         "cucina", "ristorante", "colazione", "prodotti", "piscina", "spa e centro benessere"]
PRIME_DELLA_GALLERIA = ["esterni senza struttura", "camere", "terrazze e giardini", "ristorante", "soggiorno e spazi comuni", "bagni",
                        "prodotti", "piscina"]
SCENE_DELLA_GALLERIA = {f"galleria{n}": {"categorie": [prima] + [c for c in TUTTE if c != prima], "forme": ["16x9"],
                                         "dove": "galleria di foto statica"}
                        for n, prima in enumerate(PRIME_DELLA_GALLERIA, 1)}
SCENE_DELLE_PAGINE_INTERNE = {
    "piscina": {"categorie": ["piscina"], "dove": "pagina della piscina, foto grande"},
    "piscina2": {"categorie": ["piscina"], "dove": "pagina della piscina, seconda foto"},
    "spa": {"categorie": ["spa e centro benessere"], "dove": "pagina del centro benessere, foto grande"},
    "spa2": {"categorie": ["spa e centro benessere"], "dove": "pagina del centro benessere, seconda foto"},
}


def leggiLeVoci(file, attributo):
    """Le voci di un elenco del template di prima (servizi o voci della colazione): {chiave: (svg, it, en)} nell'ordine."""
    codice = Path(file).read_text(encoding="utf-8-sig")
    voci = []
    for chiave, dentro in re.findall(r'<li\b[^>]*' + attributo + r'="([\w-]+)"[^>]*>(.*?)</li>', codice, re.S):
        svg = re.search(r"<svg\b.*?</svg>", dentro, re.S)
        span = re.search(r'<span(?:\s+data-en="([^"]*)")?>([^<]*)</span>', dentro)
        voci.append((chiave, svg.group(0) if svg else "", span.group(2), span.group(1) or span.group(2)))
    return voci


def servizi(t, voci):
    elenco = "".join(f'<li class="servizio" data-servizio="{k}" data-rivela>{svg}<span data-en="{en}">{it}</span></li>' for k, svg, it, en in voci)
    s = t["servizi"]
    mosaico = ""
    if s.get("scene"):
        a, b = s["scene"]
        mosaico = (f'<div class="mosaico"><div class="foto foto--alta" data-blocco-foto data-rivela>{pic(a, "9x16", "(max-width: 900px) 100vw, 38vw")}</div>'
                   f'<div class="foto foto--larga" data-blocco-foto data-rivela>{pic(b, "16x9", "(max-width: 900px) 100vw, 56vw")}</div></div>')
    return (f'<section class="blocco blocco--tenue" id="servizi" data-servizi aria-labelledby="titolo-servizi"><div class="contenitore">'
            f'<div class="testa" data-rivela>{testo("h2", s["titolo"][1], s["titolo"][2], s["titolo"][0], "titolo", " id=\"titolo-servizi\"")}{frasi(s.get("frasi", []))}</div>'
            f'<ul class="servizi__voci">{elenco}</ul>{mosaico}</div></section>')


HOTEL = {
    "cartella": "_01_Hotel", "tipoCrm": "[01] Hotel", "tipoSchema": "Hotel", "nomeCamere": ("Le camere", "Rooms"),
    "caratteri": ("Cormorant", "cormorantGaramond400NormalLatin.woff2", "Manrope", "manrope400NormalLatin.woff2", "manrope700NormalLatin.woff2"),
    "colori": {"--scuro": "#0E1C29", "--primario": "#1B3045", "--secondario": "#2F5F73", "--chiaro": "#F5F0E7", "--tenue": "#EADFCD",
               "--accento": "#B08D57", "--accento-chiaro": "#CDB07E", "--testo": "#16222D", "--grigio": "#5E6B73", "--bianco": "#FFFFFF"},
    "home": "esterno",
    "eroe": (("hero.titolo", "Sopra {luogo}, dal {anno}.", "Above {luogo}, since {anno}."),
             ("hero.sotto", "{camere} camere, un ristorante e {luogo} a {distanza}.", "{camere} rooms, a restaurant and {luogo} {distanza} away.")),
    "chi": ("storia", "16x9", ("chi.titolo", "La nostra famiglia, dal {anno}.", "Our family, since {anno}."),
            [("chi.testo", "Conosciamo {comune} e i suoi dintorni: chiedeteci pure, vi diamo i nostri consigli.",
              "We know {comune} and the area around it: just ask us, and we will give you our advice.")]),
    "camere": {"titolo": ("camere.titolo", "Le camere.", "Rooms."),
               "frasi": [("camere.testo", "In ogni camera trovate {dotazioni}.", "In every room you will find {dotazioni}."),
                         ("camere.persone", "Diteci quante persone siete: vi proponiamo la camera giusta.", "Tell us how many you are: we will suggest the right room for you."),
                         ("camere.libere", "Per le camere libere nelle vostre date, chiamateci al {telefono}.", "For free rooms on your dates, call us on {telefono}.")],
               "scene": [("cameraComfort", "c1"), ("cameraStandard", "c2"), ("dependance", "c3")], "elenco": ["c4", "c5", "c6"]},
    "altriBlocchiDellaHome": [
        ("colazione", "colazione", "16x9", ("col.titolo", "La colazione.", "Breakfast."),
         [("col.testo", "Ogni mattina prepariamo {colazione}.", "Every morning we prepare {colazione}.")]),
    ],
    "servizi": {"titolo": ("serv.titolo", "In albergo.", "At the hotel."), "frasi": [("serv.domande", "Per ogni domanda sul soggiorno, rispondiamo noi, con piacere.", "For any question about your stay, we are happy to answer.")], "voci": ("_01_Hotel", "data-servizio"), "scene": ("giardino", "riunioni")},
    "interne": [
        {"file": "ristorante.html", "scena": "ristorante", "voce": ("Il ristorante", "The restaurant"),
         "blocchi": [("ristorante", "ristorante", "9x16", ("rist.titolo", "Il ristorante, aperto anche a chi non dorme da noi.", "The restaurant, open to non-residents too."),
                      [("rist.testo", "A pranzo e a cena trovate i piatti della tradizione di {zona}.", "At lunch and dinner you will find the traditional dishes of {zona}.")])],
         "foto": ["piatto", "sala"]},
        {"file": "spa.html", "scena": "spa", "voce": ("Il centro benessere", "Wellness"),
         "blocchi": [("spa", "spa", "16x9", ("spa.titolo", "Il centro benessere", "Wellness"),
                      [("spa.testo", "Il centro benessere ha {dotazioniSpa}.", "The wellness centre has {dotazioniSpa}.")])], "foto": ["spa2"]},
        {"file": "piscina.html", "scena": "piscina", "voce": ("La piscina", "The pool"),
         "blocchi": [("piscina", "piscina", "16x9", ("pisc.titolo", "La piscina", "The pool"),
                      [("pisc.orari", "La piscina è aperta da {mese} a {mese}, dalle {ora} alle {ora}.", "The pool is open from {mese} to {mese}, from {ora} to {ora}."),
                       ("pisc.prato", "Intorno alla piscina c'è il prato, con lettini e ombrelloni.", "Around the pool there is a lawn, with sunbeds and umbrellas.")])], "foto": ["piscina2"]},
    ],
    "dove": {"titolo": ("dove.titolo", "Dove siamo.", "Where we are."), "scena": "lago",
             "frasi": [("dove.t1", "Siamo in {via}, a {comune}.", "We are in {via}, in {comune}."),
                       ("dove.t2", "{luogo} è a {distanza}, {luogo2} a {distanza2}.", "{luogo} is {distanza} away, {luogo2} {distanza2}."),
                       ("dove.t3", "Arrivate in auto? Il parcheggio è {parcheggio}.", "Coming by car? Parking is {parcheggio}."),
                       ("dove.strada", "Per le indicazioni chiamateci al {telefono}: vi spieghiamo noi la strada.", "For directions call us on {telefono}: we will explain the way.")]},
    "fine": {"titolo": ("fine.titolo", "Vi aspettiamo a {comune}.", "We look forward to seeing you in {comune}."),
             "frasi": [("fine.testo", "Chiamateci o scriveteci: vi diciamo subito se la camera è libera.", "Call us or write to us: we will tell you straight away if the room is free.")]},
}

BEB = {
    "cartella": "_02_BeB", "tipoCrm": "[02] B&B", "tipoSchema": "BedAndBreakfast", "nomeCamere": ("Le camere", "Rooms"),
    "caratteri": ("Cormorant", "cormorant400.woff2", "DM Sans", "dmsans400.woff2", "dmsans700.woff2"),
    "colori": {"--scuro": "#2F2738", "--primario": "#6B579C", "--secondario": "#9A86C4", "--chiaro": "#F7F2E9", "--tenue": "#EFE6D6",
               "--accento": "#B4714F", "--accento-chiaro": "#E6DEF3", "--testo": "#2F2738", "--grigio": "#5A5064", "--bianco": "#FFFDF9"},
    "home": "casa",
    "eroe": (("hero.titolo", "{nomestruttura}, a {comune}.", "{nomestruttura}, in {comune}."),
             ("hero.sotto", "{camere} camere, la colazione preparata da noi e {luogo} a {distanza}.", "{camere} rooms, breakfast made by us and {luogo} {distanza} away.")),
    "chi": ("ingresso", "9x16", ("acc.titolo", "Chi vi accoglie.", "Who welcomes you."),
            [("acc.testo", "Siamo {nomiDeiPadroniDiCasa} e vi apriamo la porta di casa nostra a {comune}.", "We are {nomiDeiPadroniDiCasa}, and we open the door of our home in {comune} to you."),
             ("acc.qui", "Siamo qui ogni giorno: per qualsiasi cosa, chiedeteci.", "We are here every day: for anything at all, just ask us.")]),
    "camere": {"titolo": ("camere.titolo", "Le camere.", "The rooms."),
               "frasi": [("camere.testo", "Ogni camera ha il bagno privato, {dotazioni}.", "Every room has a private bathroom, {dotazioni}."),
                         ("camere.persone", "Diteci quante persone siete: vi proponiamo la camera giusta.", "Tell us how many you are: we will suggest the right room for you."),
                         ("camere.libere", "Per le camere libere nelle vostre date, chiamateci al {telefono}.", "For free rooms on your dates, call us on {telefono}.")],
               "scene": [("camera1", ""), ("camera2", ""), ("camera3", ""), ("bagno", "")], "elenco": []},
    "altriBlocchiDellaHome": [
        ("colazione", "colazione", "16x9", ("col.titolo", "La colazione.", "Breakfast."),
         [("col.testo", "La colazione è inclusa ed è servita {dove}.", "Breakfast is included and served {dove}."),
          ("col.torte", "Le torte sono fatte da noi.", "We bake the cakes ourselves.")]),
        ("spazi", "spazi", "16x9", ("spazi.titolo", "Gli spazi di tutti.", "The shared spaces."),
         [("spazi.cucina", "Al {piano} c'è una cucina che potete usare anche voi.", "On the {piano} there is a kitchen that you can use too."),
          ("spazi.fuori", "Fuori, {spazioEsterno} per un aperitivo o per leggere.", "Outside, {spazioEsterno} for an aperitivo or for reading.")]),
    ],
    "vociDellaColazione": ("_02_BeB", "data-voce"),
    "servizi": None,
    "interne": [
        {"file": "spa.html", "scena": "spa", "voce": ("Il centro benessere", "Wellness"),
         "blocchi": [("spa", "spa", "16x9", ("spa.titolo", "Il centro benessere", "Wellness"),
                      [("spa.testo", "Il centro benessere ha {dotazioniSpa}.", "The wellness centre has {dotazioniSpa}.")])], "foto": ["spa2"]},
        {"file": "piscina.html", "scena": "piscina", "voce": ("La piscina", "The pool"),
         "blocchi": [("piscina", "piscina", "16x9", ("pisc.titolo", "La piscina", "The pool"),
                      [("pisc.orari", "La piscina è aperta da {mese} a {mese}, dalle {ora} alle {ora}.", "The pool is open from {mese} to {mese}, from {ora} to {ora}."),
                       ("pisc.prato", "Intorno alla piscina c'è il prato, con lettini e ombrelloni.", "Around the pool there is a lawn, with sunbeds and umbrellas.")])], "foto": ["piscina2"]},
    ],
    "dove": {"titolo": ("dove.titolo", "Dove siamo.", "Where we are."), "scena": "via",
             "frasi": [("dove.t1", "Siamo in {via}: la stazione è a {distanzaStazione}, il centro a {distanzaCentro}.", "We are in {via}: the station is {distanzaStazione} away, the centre {distanzaCentro}."),
                       ("dove.t2", "Il parcheggio è {parcheggio}.", "Parking is {parcheggio}."),
                       ("dove.t3", "Arrivate in treno e non trovate la strada? Chiamateci, vi diciamo da che parte uscire.", "Arriving by train and can&#x27;t find the way? Call us, we&#x27;ll tell you which exit to take."),
                       ("dove.strada", "Per le indicazioni chiamateci al {telefono}: vi spieghiamo noi la strada.", "For directions call us on {telefono}: we will explain the way.")]},
    "fine": {"titolo": ("fine.titolo", "Scriveteci le vostre date.", "Send us your dates."),
             "frasi": [("fine.testo", "Su WhatsApp o al telefono: per prenotare in comodità.", "On WhatsApp or by phone: to book at your ease.")]},
}

AGRI = {
    "cartella": "_03_Agriturismo", "tipoCrm": "[03] Agriturismi", "tipoSchema": "LodgingBusiness", "nomeCamere": ("Le camere", "Rooms"),
    "caratteri": ("Fraunces", "fraunces400NormalLatin.woff2", "Mulish", "mulish400NormalLatin.woff2", "mulish700NormalLatin.woff2"),
    "colori": {"--scuro": "#3E1219", "--primario": "#5A1B24", "--secondario": "#58613A", "--chiaro": "#F4EEE4", "--tenue": "#E6DCCB",
               "--accento": "#A3532E", "--accento-chiaro": "#CDBB9E", "--testo": "#2A221C", "--grigio": "#4A3F35", "--bianco": "#FFFDF8"},
    "home": "casa",
    "eroe": (("hero.titolo", "Una casa di campagna a {comune}.", "A country house in {comune}."),
             ("hero.sotto", "Cucina di casa, camere e {paesaggio} intorno.", "Home cooking, rooms and {paesaggioEn} all around.")),
    "chi": ("podere", "9x16", ("podere.titolo", "Il podere.", "The farm."),
            [("podere.casa", "La casa è {tipoDiCasa}, su {piani} piani.", "The house is {tipoDiCasaEn}, on {pianiEn} floors."),
             ("podere.dintorni", "Conosciamo {comune} e i suoi dintorni: chiedeteci pure, vi diamo i nostri consigli.", "We know {comune} and the area around it: just ask, we will give you our advice."),
             ("podere.qui", "Siamo qui ogni giorno: per qualsiasi cosa, chiedeteci.", "We are here every day: for anything at all, just ask us.")]),
    "camere": {"titolo": ("camere.titolo", "Le camere.", "The rooms."),
               "frasi": [("camere.pensione", "Mezza pensione o pensione completa: scegliete voi.", "Half board or full board: you choose."),
                         ("camere.persone", "Diteci quante persone siete: vi proponiamo la camera giusta.", "Tell us how many you are: we will suggest the right room for you."),
                         ("camere.libere", "Per le camere libere nelle vostre date, chiamateci al {telefono}.", "For free rooms on your dates, call us on {telefono}.")],
               "scene": [("camera", ""), ("camera2", ""), ("camera3", "")], "elenco": []},
    "altriBlocchiDellaHome": [
        ("famiglie", "famiglie", "16x9", ("fam.titolo", "Spazio per tutti.", "Room for everyone."),
         [("fam.testo", "Intorno alla casa ci sono spazi aperti, lontani dalle auto.", "Around the house there are open spaces, away from cars.")]),
    ],
    "servizi": None,
    "interne": [
        {"file": "ristorante.html", "scena": "sala", "voce": ("La nostra cucina", "Our kitchen"),
         "blocchi": [("cucina", "sala", "16x9", ("cucina.titolo", "La nostra cucina.", "Our kitchen."),
                      [("cucina.pasta", "La pasta la facciamo noi.", "We make our own pasta.")]),
                     ("tavola", "tavola", "9x16", ("tavola.titolo", "A tavola.", "At the table."),
                      [("tavola.domenica", "Il pranzo della domenica è su prenotazione: chiamateci.", "Sunday lunch is by reservation: call us."),
                       ("tavola.piatti", "In cucina prepariamo {piatti}, con i prodotti di {zona}.", "In the kitchen we prepare {piattiEn}, with produce from {zonaEn}."),
                       ("tavola.estate", "D'estate si mangia all'aperto, sotto {copertura}.", "In summer we eat outdoors, under {coperturaEn}.")])],
         "foto": ["pasta"]},
        {"file": "spa.html", "scena": "spa", "voce": ("Il centro benessere", "Wellness"),
         "blocchi": [("spa", "spa", "16x9", ("spa.titolo", "Il centro benessere", "Wellness"),
                      [("spa.testo", "Il centro benessere ha {dotazioniSpa}.", "The wellness centre has {dotazioniSpa}.")])], "foto": ["spa2"]},
        {"file": "piscina.html", "scena": "piscina", "voce": ("La piscina", "The pool"),
         "blocchi": [("piscina", "piscina", "16x9", ("pisc.titolo", "La piscina", "The pool"),
                      [("pisc.orari", "La piscina è aperta da {mese} a {mese}, dalle {ora} alle {ora}.", "The pool is open from {mese} to {mese}, from {ora} to {ora}."),
                       ("pisc.prato", "Intorno alla piscina c'è il prato, con lettini e ombrelloni.", "Around the pool there is a lawn, with sunbeds and umbrellas.")])], "foto": ["piscina2"]},
    ],
    "dove": {"titolo": ("dove.titolo", "Come arrivare da noi.", "How to reach us."), "scena": "paesaggio",
             "frasi": [("dove.t1", "Siamo in {via}, a {distanza} da {comune}.", "We are in {via}, {distanzaEn} from {comune}."),
                       ("dove.strada", "Per le indicazioni chiamateci al {telefono}: vi spieghiamo noi la strada.", "For directions call us on {telefono}: we will explain the way.")]},
    "fine": {"titolo": ("fine.titolo", "Prenotate il vostro tavolo o la vostra camera.", "Book your table or your room."),
             "frasi": [("fine.testo", "Chiamateci o scriveteci: vi teniamo il posto.", "Call us or write to us: we will keep your place for you.")]},
}

CASA = {
    "cartella": "_04_CasaVacanza", "tipoCrm": "[04] Case Vacanze", "tipoSchema": "VacationRental", "nomeCamere": ("La casa", "The house"),
    "caratteri": ("Cormorant", "cormorantGaramond400NormalLatin.woff2", "Manrope", "manrope400NormalLatin.woff2", "manrope700NormalLatin.woff2"),
    "colori": {"--scuro": "#123441", "--primario": "#1D4B5C", "--secondario": "#8FB3BD", "--chiaro": "#FBF9F5", "--tenue": "#F3EDE3",
               "--accento": "#A8865A", "--accento-chiaro": "#CFC3B0", "--testo": "#1B2730", "--grigio": "#4A5862", "--bianco": "#FFFFFF"},
    "home": "facciata",
    "eroe": (("hero.titolo", "Nel centro di {comune}.", "In the centre of {comune}."), None),
    "chi": ("cortile", "16x9", ("fuori.titolo", "Il cortile.", "The courtyard."),
            [("fuori.testo", "Davanti alla casa c'è {spazioEsterno}, con {arredi}.", "In front of the house there is {spazioEsterno}, with {arredi}.")]),
    "camere": {"titolo": ("casa.titolo", "Una casa tutta per voi.", "A house all to yourselves."),
               "frasi": [("casa.testo", "La casa è in {via}, a {comune}: la camera da letto, la cucina, il bagno e il cortile.", "The house is in {via}, in {comune}: the bedroom, the kitchen, the bathroom and the courtyard."),
                         ("casa.cucina", "La cucina ha tutto quello che serve per preparare da mangiare.", "The kitchen has everything you need to cook."),
                         ("camere.persone", "Diteci quante persone siete: vi proponiamo la camera giusta.", "Tell us how many you are: we will suggest the right room for you."),
                         ("camere.libere", "Per le camere libere nelle vostre date, chiamateci al {telefono}.", "For free rooms on your dates, call us on {telefono}.")],
               "scene": [("camera", ""), ("cucina", ""), ("vasca", "")], "elenco": []},
    "altriBlocchiDellaHome": [
        ("arrivo", "ingresso", "9x16", ("arrivo.titolo", "Arrivo e partenza.", "Arrival and departure."),
         [("arrivo.chiavi", "Al vostro arrivo vi consegniamo le chiavi e vi mostriamo la casa.", "When you arrive we hand you the keys and show you the house.")]),
    ],
    "servizi": {"titolo": ("serv.titolo", "Nella casa.", "In the house."), "frasi": [("serv.domande", "Per ogni domanda sul soggiorno, rispondiamo noi, con piacere.", "For any question about your stay, we are happy to answer.")], "voci": ("_04_CasaVacanza", "data-servizio"), "scene": None},
    "interne": [
        {"file": "spa.html", "scena": "spa", "voce": ("Il centro benessere", "Wellness"),
         "blocchi": [("spa", "spa", "16x9", ("spa.titolo", "Il centro benessere", "Wellness"),
                      [("spa.testo", "Il centro benessere ha {dotazioniSpa}.", "The wellness centre has {dotazioniSpa}.")])], "foto": ["spa2"]},
        {"file": "piscina.html", "scena": "piscina", "voce": ("La piscina", "The pool"),
         "blocchi": [("piscina", "piscina", "16x9", ("pisc.titolo", "La piscina", "The pool"),
                      [("pisc.orari", "La piscina è aperta da {mese} a {mese}, dalle {ora} alle {ora}.", "The pool is open from {mese} to {mese}, from {ora} to {ora}."),
                       ("pisc.prato", "Intorno alla piscina c'è il prato, con lettini e ombrelloni.", "Around the pool there is a lawn, with sunbeds and umbrellas.")])], "foto": ["piscina2"]},
    ],
    "dove": {"titolo": ("dove.titolo", "Dove siamo.", "Where we are."), "scena": "esterni",
             "frasi": [("dove.t1", "Siamo in {via}, a {comune}.", "We are in {via}, in {comune}."),
                       ("dove.t2", "Ristoranti, negozi e mezzi pubblici sono vicini.", "Restaurants, shops and public transport are close by."),
                       ("dove.strada", "Per le indicazioni chiamateci al {telefono}: vi spieghiamo noi la strada.", "For directions call us on {telefono}: we will explain the way.")]},
    "fine": {"titolo": ("fine.titolo", "Diteci quando volete venire.", "Tell us when you would like to come."),
             "frasi": [("fine.testo", "Scriveteci le date e quante persone siete.", "Write us the dates and how many you are.")]},
}

# Le scene di ogni tipo: quelle del contratto di prima che il nuovo template usa, più le nuove (galleria, pagine interne,
# cartolina). Categorie dalle regole del passo 4.1 (_05_RegoleDelleCategoriePreciseDelleFoto.json).
SCENE = {
    "_01_Hotel": {
        "esterno": ["esterno della struttura"], "storia": ["esterno della struttura"], "cameraComfort": ["camere"], "cameraStandard": ["camere"],
        "dependance": ["camere"], "colazione": ["colazione"], "giardino": ["terrazze e giardini", "esterni senza struttura"],
        "riunioni": ["soggiorno e spazi comuni", "esterno della struttura"], "ristorante": ["ristorante"], "piatto": ["prodotti", "ristorante"],
        "sala": ["ristorante"], "lago": ["esterni senza struttura", "esterno della struttura"]},
    "_02_BeB": {
        "casa": ["esterno della struttura"], "ingresso": ["esterno della struttura"], "colazione": ["colazione"],
        "camera1": ["camere"], "camera2": ["camere"], "camera3": ["camere"], "bagno": ["bagni"],
        "spazi": ["terrazze e giardini", "soggiorno e spazi comuni", "cucina"],
        "via": ["esterno della struttura", "esterni senza struttura"]},
    "_03_Agriturismo": {
        "casa": ["esterno della struttura"], "podere": ["esterno della struttura"], "paesaggio": ["esterni senza struttura"],
        "camera": ["camere"], "camera2": ["camere"], "camera3": ["camere"], "famiglie": ["terrazze e giardini", "esterni senza struttura"],
        "sala": ["ristorante"], "tavola": ["ristorante"], "pasta": ["prodotti", "ristorante"]},
    "_04_CasaVacanza": {
        "facciata": ["esterno della struttura"], "cortile": ["terrazze e giardini"], "camera": ["camere"], "cucina": ["cucina"],
        "vasca": ["bagni"], "ingresso": ["esterno della struttura", "soggiorno e spazi comuni"], "esterni": ["esterni senza struttura", "esterno della struttura"],
        "cartolina": ["esterno della struttura", "esterni senza struttura"]},
}


# ------------------------------------------------------------------------------------------------ la pagina intera

def vociDelMenu(t, pagina):
    voci = [("index.html", "Home", "Home"), ("camere.html", *t["nomeCamere"])]
    voci += [(p["file"], *p["voce"]) for p in t["interne"]]
    voci += [("galleria.html", "Galleria", "Gallery"), ("recensioni.html", "Recensioni", "Reviews"),
             ("dove-siamo.html", "Dove siamo e contatti", "Location and contacts")]
    return "".join(f'<li data-voce-pagina="{f}"><a href="{f}"{" aria-current=\"page\"" if f == pagina else ""} data-en="{en}">{it}</a></li>'
                   for f, it, en in voci)


def paginaIntera(t, file, titoloIt, corpo, conEroe):
    nomeSerif, fileSerif, nomeSans, fileSans, fileSansForte = t["caratteri"]
    titolo = "{nomestruttura}, a {comune}" if file == "index.html" else f"{titoloIt} · {{nomestruttura}}"
    return f"""<!doctype html>
<html lang="it">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{titolo}</title>
<meta name="description" content="{{nomestruttura}}, a {{comune}}." data-en-content="{{nomestruttura}}, in {{comune}}.">
<meta property="og:type" content="website">
<meta property="og:title" content="{{nomestruttura}}">
<meta property="og:description" content="{{nomestruttura}}, a {{comune}}.">
<meta property="og:locale" content="it_IT">
<meta name="theme-color" content="{t["colori"]["--chiaro"]}">
<link rel="icon" href="assets/logo/icona.svg" type="image/svg+xml">
<link rel="preload" href="assets/fonts/{fileSerif}" as="font" type="font/woff2" crossorigin>
<link rel="preload" href="assets/fonts/{fileSans}" as="font" type="font/woff2" crossorigin>
<link rel="stylesheet" href="assets/css/style.css">
<script>document.documentElement.className='js';</script>
</head>
<body data-pagina="{file}">
<a class="salta" href="#contenuto" data-en="Skip to content">Vai al contenuto</a>

<header class="testata" id="testata">
  <a class="testata__marchio" href="index.html" data-marchio>{{nomestruttura}}</a>
  <nav aria-label="Menu" data-en-aria-label="Menu"><ul class="testata__voci">{vociDelMenu(t, file)}</ul></nav>
  <div class="testata__strumenti">{LINGUE}<a class="pk-tasto pk-tasto--tel testata__tasto" data-link="tel" href="#">{ICONA_TEL}<span data-en="Call us">Chiamateci</span></a><a class="pk-tasto pk-tasto--wa testata__tasto" data-link="whatsapp" href="#" target="_blank" rel="noopener">{ICONA_WA}<span>WhatsApp</span></a><button class="btn btn--pieno" type="button" data-apri-prenota><span data-en="Book">Prenota</span></button>
  <button class="testata__menu" type="button" aria-controls="menu" aria-expanded="false">{ICONA_MENU}<span data-en="Menu">Menu</span></button></div>
</header>

<nav class="menu" id="menu" aria-label="Menu" data-en-aria-label="Menu" hidden>
  <ul>{vociDelMenu(t, file)}</ul>
  <div class="menu__piede"><a data-link="tel" href="#"><span data-t="telefono">{{telefono}}</span></a>{LINGUE}</div>
</nav>

<main id="contenuto">
{corpo}
</main>

<dialog class="finestra" id="finestra-prenota" aria-labelledby="titolo-finestra">
  <div class="finestra__in">
    <button class="finestra__chiudi" type="button" data-chiudi aria-label="Chiudi" data-en-aria-label="Close">&times;</button>
    <h2 class="titolo" id="titolo-finestra"><span data-en="Book">Prenota</span></h2>
    {moduloDate("finestra")}
    <p class="finestra__nota"><a data-t="mod.voce" data-en="Would you rather talk it over? Call us on {{telefono}}." data-link="tel" href="#">Preferite parlarne a voce? Chiamateci al {{telefono}}.</a></p>
  </div>
</dialog>

<footer class="piede">
  <div class="contenitore">
    <div class="piede__colonne">
      <div><div class="piede__marchio" data-marchio>{{nomestruttura}}</div><ul><li><a data-link="mappa" href="#" target="_blank" rel="noopener"><span data-t="posizione">{{via}}, {{cap}} {{comune}} ({{provincia}})</span></a></li></ul></div>
      <ul><li><a data-link="tel" href="#"><span data-t="telefono">{{telefono}}</span></a></li><li><a data-link="email" href="#"><span data-t="email">{{email}}</span></a></li>
        <li><a data-link="whatsapp" href="#" target="_blank" rel="noopener">WhatsApp</a></li></ul>
      <ul><li><a data-link="instagram" href="#" target="_blank" rel="noopener">Instagram</a></li><li><a data-link="facebook" href="#" target="_blank" rel="noopener">Facebook</a></li>
        <li><a data-link="recensioni" href="#" target="_blank" rel="noopener"><span data-en="Google reviews">Recensioni Google</span></a></li></ul>
    </div>
    <div class="piede__fondo"><span data-t="legale" data-en="VAT {{partitaIva}} · CIN {{cin}}">P. IVA {{partitaIva}} · CIN {{cin}}</span><span data-t="copy">© {{annoCorrente}} {{nomestruttura}}</span></div>
  </div>
</footer>

<div class="pk-tasti">
  <a class="pk-tasto pk-tasto--wa" data-link="whatsapp" href="#" target="_blank" rel="noopener">{ICONA_WA}<span>WhatsApp</span></a>
  <a class="pk-tasto pk-tasto--tel" data-link="tel" href="#">{ICONA_TEL}<span data-en="Call us">Chiamateci</span></a>
</div>
<script src="assets/js/config.js"></script>
<script src="assets/js/foto.js" data-configurazione="SITO_CONFIG"></script>
<script src="assets/js/main.js" defer></script>
<script src="assets/js/pacchetto.js" defer></script>
</body>
</html>
"""


def testaDellaPagina(titoloIt, titoloEn, chiave=""):
    return (f'<section class="testa-pagina" aria-labelledby="titolo-pagina"><div class="contenitore">'
            f'{testo("h1", titoloIt, titoloEn, chiave, "", " id=\"titolo-pagina\"")}</div></section>')


def blocchi(elenco, partenza=0):
    codice = ""
    for i, (id_, scena, forma, titolo, paragrafi) in enumerate(elenco, partenza):
        codice += coppia(id_, scena, forma, titolo, paragrafi, inversa=i % 2 == 1, sfondo="blocco--tenue" if i % 2 == 1 else "")
    return codice


def pagine(t):
    # Michele, 11/11/2026: il titolo grande della Home è sempre il nome della struttura, mai una frase; la frase del tipo
    # ("Nel centro di Pescara.") scende sotto il nome, poi la riga con i fatti
    eroeTitolo, eroeSotto = t["eroe"]
    sotto = testo("p", eroeTitolo[1], eroeTitolo[2], eroeTitolo[0], "lead eroe__frase")
    sotto += testo("p", eroeSotto[1], eroeSotto[2], eroeSotto[0], "lead") if eroeSotto else ""
    eroe = (f'<section class="eroe" aria-labelledby="titolo-eroe">{pic(t["home"], "16x9", "100vw", "La struttura vista da fuori", "The property seen from outside", True, True)}'
            f'<div class="eroe__velo"></div><div class="eroe__testo contenitore"><h1 id="titolo-eroe" data-nome-eroe>{{nomestruttura}}</h1>{sotto}</div></section>'
            f'<section class="barra-prenota" aria-label="Prenota" data-en-aria-label="Book"><div class="contenitore">{moduloDate("barra")}</div></section>')
    chiScena, chiForma, chiTitolo, chiFrasi = t["chi"]
    chi = coppia("chi-siamo", chiScena, chiForma, chiTitolo, chiFrasi)
    c = t["camere"]
    primaCamera = c["scene"][0][0]
    fotoCamere = "".join(f'<div class="foto foto--alta" data-blocco-foto data-rivela>{pic(scena, "9x16", "(max-width: 900px) 50vw, 25vw")}</div>'
                         for scena, _ in c["scene"][:3])
    anteprimaCamere = (f'<section class="blocco blocco--tenue" id="camere-in-breve" data-pagina="camere.html" data-sempre aria-labelledby="titolo-camere-in-breve"><div class="contenitore">'
                       f'<div class="coppia"><div class="coppia__testo" data-rivela>{testo("h2", c["titolo"][1], c["titolo"][2], c["titolo"][0], "titolo", " id=\"titolo-camere-in-breve\"")}'
                       f'{frasi(c["frasi"][:1] + [v for v in c["frasi"] if v[0] == "camere.persone"])}<a class="btn" href="camere.html"><span data-en="{t["nomeCamere"][1]}">{t["nomeCamere"][0]}</span></a></div>'
                       f'<div class="anteprima__foto">{fotoCamere}</div></div></div></section>')
    d = t["dove"]
    elemento3D = (f'<section class="blocco" id="dove-in-breve" aria-labelledby="titolo-dove-in-breve"><div class="contenitore"><div class="pk-3d">'
                  f'<div data-rivela>{oggetto3D()}</div>'
                  f'<div data-rivela>{testo("h2", d["titolo"][1], d["titolo"][2], d["titolo"][0], "titolo", " id=\"titolo-dove-in-breve\"")}{frasi(d["frasi"][:1])}'
                  f'<a class="btn" href="dove-siamo.html"><span data-en="Location and contacts">Dove siamo e contatti</span></a></div></div></div></section>')
    anteprimaGalleria = (f'<section class="blocco blocco--stretto" id="galleria-in-breve" data-pagina="galleria.html" aria-label="Galleria" data-en-aria-label="Gallery"><div class="contenitore">'
                         f'<div class="galleria">' + "".join(f'<figure class="galleria__voce" data-blocco-foto data-rivela><div class="foto">{pic(s_, "16x9", "(max-width: 900px) 50vw, 33vw")}</div></figure>'
                                                             for s_ in list(SCENE_DELLA_GALLERIA)[:3]) +
                         f'</div><p class="centro" data-rivela><a class="btn" href="galleria.html"><span data-en="Gallery">Galleria</span></a></p></div></section>')
    altri = blocchi(t["altriBlocchiDellaHome"], 0)
    vociColazione = ""
    if t.get("vociDellaColazione"):
        voci = leggiLeVoci(MODELLI / t["vociDellaColazione"][0] / f"template.{COPIA}" / "index.html", "data-voce") or \
               [(None, "", it, en) for en, it in re.findall(r'<li><svg\b.*?</svg><span data-en="([^"]*)">([^<]*)</span></li>',
                                                          (MODELLI / t["vociDellaColazione"][0] / f"template.{COPIA}" / "index.html").read_text(encoding="utf-8-sig"), re.S)]
        vociColazione = "".join(f'<li><span data-en="{en}">{it}</span></li>' for _, _, it, en in voci)
        altri = altri.replace('</div></div></div></section>', f'<ul class="voci">{vociColazione}</ul></div></div></div></section>', 1)
    serv = ""
    if t.get("servizi"):
        sorgente = MODELLI / t["servizi"]["voci"][0] / f"template.{COPIA}" / "index.html"
        serv = servizi(t, leggiLeVoci(sorgente, "data-servizio"))
    schede = "".join(
        f'<a class="scheda" href="{p["file"]}" data-pagina="{p["file"]}" data-blocco-foto data-rivela><div class="foto foto--larga">'
        f'{pic(p["scena"], "16x9", "(max-width: 900px) 100vw, 33vw")}</div><div class="scheda__testo"><span class="scheda__nome" data-en="{p["voce"][1]}">{p["voce"][0]}</span>'
        f'<span class="link" data-en="Discover">Scoprite</span></div></a>' for p in t["interne"])
    schede = f'<section class="blocco" id="nella-struttura" aria-label="Nella struttura" data-en-aria-label="At the property"><div class="contenitore"><div class="schede">{schede}</div></div></section>'
    homeGalleria = galleria("galleria", list(SCENE_DELLA_GALLERIA), soloConPagineInterne=True)
    homeRecensioni = recensioni("recensioni", soloConPagineInterne=True)
    anteprimaRecensioni = recensioni("recensioni-in-breve", quante=3, conLink=True)
    # Michele, 11/11/2026: la Home contiene l'inizio di ogni pagina, ognuno con il suo collegamento
    home = (eroe + chi + anteprimaCamere + altri + serv + schede + anteprimaGalleria + homeGalleria + anteprimaRecensioni + homeRecensioni
            + elemento3D + invito(t))

    grigliaCamere = ""
    for scena, chiave in c["scene"]:
        nome = testo("h3", f"{{nomeCamera{chiave[1:]}}}", f"{{nomeCamera{chiave[1:]}}}", f"{chiave}.nome") if chiave else ""
        dot = testo("p", f"{{dotazioniCamera{chiave[1:]}}}", f"{{dotazioniCamera{chiave[1:]}}}", f"{chiave}.dot", "sottile") if chiave else ""
        grigliaCamere += (f'<article class="camera" data-blocco-foto data-rivela><div class="foto">{pic(scena, "16x9", "(max-width: 900px) 100vw, 33vw")}</div>'
                          f'{nome}{dot}</article>')
    elenco = ""
    if c["elenco"]:
        righe = "".join(f'<div><dt data-t="{k}.nome">{{nomeCamera{k[1:]}}}</dt><dd data-t="{k}.dot">{{dotazioniCamera{k[1:]}}}</dd></div>' for k in c["elenco"])
        elenco = f'<div class="camere__elenco" data-rivela><dl>{righe}</dl></div>'
    camere = (testaDellaPagina(c["titolo"][1], c["titolo"][2], c["titolo"][0]) +
              f'<section class="blocco blocco--stretto" id="camere" data-sempre aria-label="{t["nomeCamere"][0]}" data-en-aria-label="{t["nomeCamere"][1]}"><div class="contenitore">'
              f'<div class="testa" data-rivela>{frasi(c["frasi"])}</div><div class="camere__griglia">{grigliaCamere}</div>{elenco}'
              f'<div class="invito__date">{moduloDate("camere")}</div></div></section>')
    risultato = {
        "index.html": ("Home", home, True),
        "camere.html": (t["nomeCamere"][0], camere, False),
        "galleria.html": ("Galleria", testaDellaPagina("Galleria", "Gallery") + galleria("foto", list(SCENE_DELLA_GALLERIA), conTitolo=False), False),
        "recensioni.html": ("Recensioni", testaDellaPagina("Recensioni", "Reviews") + recensioni("recensioni", sfondo=""), False),
        "dove-siamo.html": ("Dove siamo e contatti", testaDellaPagina("Dove siamo e contatti", "Location and contacts") + mappaEContatti(t) + invito(t), False),
    }
    for p in t["interne"]:
        normale = lambda x: x.lower().rstrip(". ")
        doppio = normale(p["blocchi"][0][3][1]) == normale(p["voce"][0])
        # Michele, 11/11/2026: mai il titolo della pagina uguale al titolo della prima sezione
        corpo = (blocchi(p["blocchi"]).replace('<section class="blocco ', '<section class="blocco blocco--primo ', 1) if doppio
                 else testaDellaPagina(*p["voce"]) + blocchi(p["blocchi"]))
        if p.get("foto"):
            corpo += (f'<section class="blocco blocco--stretto" aria-label="{p["voce"][0]}" data-en-aria-label="{p["voce"][1]}"><div class="contenitore"><div class="galleria">'
                      + "".join(f'<figure class="galleria__voce" data-blocco-foto data-rivela><div class="foto">{pic(s, "16x9", "(max-width: 900px) 50vw, 33vw")}</div></figure>'
                                for s in p["foto"]) + '</div></div></section>')
        risultato[p["file"]] = (p["voce"][0], corpo + invito(t), False)
    return risultato


# ------------------------------------------------------------------------------------------------ config, stile, contratto

def config(t, scene):
    dati = {
        "bloccoDellaFoto": "[data-blocco-foto]", "servizi": [], "nome": "", "nomeBreve": "", "tipoSchema": t["tipoSchema"], "logo": "",
        "lingue": ["it", "en"], "linguaPredefinita": "it", "fotoDir": "media/foto/",
        "contatti": {"telefono": "", "whatsapp": "", "email": "", "via": "", "cap": "", "comune": "", "provincia": "", "paese": "IT",
                     "latitudine": "", "longitudine": "", "mappa": "", "instagram": "", "facebook": ""},
        "recensioni": {"placeId": "", "link": ""},
        "scene": {s: {"poster16": f"{s}_16x9.jpg", "poster9": f"{s}_9x16.jpg"} for s in scene},
    }
    return ("/* Configurazione del template Advanced: la fabbrica scrive qui i dati veri del cliente (window.SITO_CONFIG). */\n"
            "window.SITO_CONFIG = " + json.dumps(dati, ensure_ascii=False, indent=2) + ";\n")


def stile(t):
    nomeSerif, fileSerif, nomeSans, fileSans, fileSansForte = t["caratteri"]
    colori = ";".join(f"{k}:{v}" for k, v in t["colori"].items())
    return (f"/* Template Advanced {t['cartella']} (DepthX, 11/11/2026). Colori del tipo in :root, in esadecimale: la fabbrica li porta alla tinta del cliente. */\n"
            f":root{{{colori};--serif:\"{nomeSerif}\",Georgia,\"Times New Roman\",serif;--sans:\"{nomeSans}\",\"Helvetica Neue\",Arial,sans-serif}}\n"
            f"@font-face{{font-family:\"{nomeSerif}\";src:url(\"../fonts/{fileSerif}\") format(\"woff2\");font-weight:400;font-display:swap}}\n"
            f"@font-face{{font-family:\"{nomeSans}\";src:url(\"../fonts/{fileSans}\") format(\"woff2\");font-weight:400;font-display:swap}}\n"
            f"@font-face{{font-family:\"{nomeSans}\";src:url(\"../fonts/{fileSansForte}\") format(\"woff2\");font-weight:700;font-display:swap}}\n"
            + (COMUNI / "css" / "comune.css").read_text(encoding="utf-8"))


def contratto(t, scene, servizi_):
    interne = [{"file": p["file"], "scena": p["scena"]} for p in t["interne"]]
    return {
        "descrizione": "Contratto del template Advanced (Michele, 11/11/2026): sito multipagina con la lista Advanced della pagina Prodotti. "
                       "Costruito da _00_CostruzioneDeiTemplateAdvanced: le correzioni si fanno lì e si rilancia.",
        "template": t["cartella"], "tipoCrm": t["tipoCrm"], "pacchetto": "Advanced", "variabileDiConfigurazione": "window.SITO_CONFIG",
        "fileDiConfigurazione": "assets/js/config.js",
        "pagine": {
            "tutte": ["index.html", "camere.html", "galleria.html", "recensioni.html", "dove-siamo.html"] + [p["file"] for p in interne],
            "sempre": ["index.html", "dove-siamo.html"],
            "interne": interne,
            "massimoDiPagineInterne": 2,
            "sostituibiliDallePagineInterne": ["galleria.html", "recensioni.html"],
            "minimoDiFotoDellaGalleria": 4,
            "regola": "Michele, 11/11/2026: pagine standard Home, Camere, Galleria, Recensioni, Dove siamo e contatti; una pagina interna "
                      "(ristorante, centro benessere, piscina) nasce solo se la sua scena ha la foto del cliente; con una pagina interna "
                      "Galleria e Recensioni entrano nella Home (blocchi data-solo-con-pagine-interne). Una pagina senza materiale non nasce. "
                      "Al massimo 5 sezioni nel menu.",
        },
        "listaAdvanced": ["sito multipagina fino a 5 sezioni", "italiano e inglese", "3 animazioni di transizione", "1 elemento 3D di codice",
                          "6 recensioni Google nel sito", "pulsante WhatsApp e chiamata animati", "pulsante Prenota con la finestra delle date",
                          "mappa e indicazione della sede animata", "preparazione completa per Google", "galleria di foto statica"],
        "scenaDellaHome": t["home"],
        "scene": scene,
        "servizi": {"come": "li[data-servizio]: la fabbrica toglie le voci non vere", "voci": servizi_},
        "recensioni": {"quante": 6, "firma": "Un ospite di {nomestruttura}", "titolo": "Dicono di noi su Google.",
                       "regole": "Michele, 11/11/2026 (#577): nessun nome di persona, nessuna città, nessuna scritta Google con il logo sopra le stelle, "
                                 "Google solo nei titoli, mai la frase sul numero delle recensioni; voto e numero mai nel sito."},
        "paroleDelTemplate": ["{", "}"],
    }


def costruisci(t):
    cartella = MODELLI / t["cartella"]
    template, copiaTemplate = cartella / "template", cartella / f"template.{COPIA}"
    if not copiaTemplate.exists():
        shutil.copytree(template, copiaTemplate)
    if not (cartella / f"contratto.json.{COPIA}").exists():
        shutil.copy2(cartella / "contratto.json", cartella / f"contratto.json.{COPIA}")
    scene = {s: {"categorie": c, "forme": ["16x9", "9x16"]} for s, c in SCENE[t["cartella"]].items()}
    for p in t["interne"]:
        if p["scena"] not in scene:
            scene[p["scena"]] = {"categorie": SCENE_DELLE_PAGINE_INTERNE[p["scena"]]["categorie"], "forme": ["16x9", "9x16"]}
        for s in p.get("foto", []):
            if s not in scene:
                scene[s] = {"categorie": SCENE_DELLE_PAGINE_INTERNE[s]["categorie"], "forme": ["16x9", "9x16"]}
    scene.update({s: {"categorie": v["categorie"], "forme": v["forme"]} for s, v in SCENE_DELLA_GALLERIA.items()})
    # la cartolina dell'elemento 3D, in ogni tipo (Michele, 11/11/2026: le forme si alternano)
    scene.setdefault("cartolina", {"categorie": ["esterno della struttura", "esterni senza struttura", "terrazze e giardini"], "forme": ["16x9", "9x16"]})
    vociDeiServizi = [k for k, *_ in leggiLeVoci(copiaTemplate / "index.html", "data-servizio")] if t.get("servizi") else []
    # il template nuovo: si tolgono pagine e script di prima, restano caratteri e logo
    for voce in list(template.iterdir()):
        if voce.suffix == ".html":
            voce.unlink()
    js = template / "assets" / "js"
    for voce in js.glob("*.js"):
        voce.unlink()
    for nome in ("foto.js", "main.js", "pacchetto.js"):
        shutil.copy2(COMUNI / "js" / nome, js / nome)
    (js / "config.js").write_text(config(t, scene), encoding="utf-8")
    (template / "assets" / "css" / "style.css").write_text(stile(t), encoding="utf-8")
    (template / "assets" / "logo").mkdir(parents=True, exist_ok=True)
    if not (template / "assets" / "logo" / "icona.svg").exists():
        (template / "assets" / "logo" / "icona.svg").write_text(
            '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64"><rect width="64" height="64" rx="14" fill="#444"/></svg>', encoding="utf-8")
    for file, (titoloIt, corpo, conEroe) in pagine(t).items():
        (template / file).write_text(paginaIntera(t, file, titoloIt, corpo, conEroe), encoding="utf-8")
    (cartella / "contratto.json").write_text(json.dumps(contratto(t, scene, vociDeiServizi), ensure_ascii=False, indent=1), encoding="utf-8")
    return sorted(p.name for p in template.glob("*.html"))


if __name__ == "__main__":
    for tipo in (HOTEL, BEB, AGRI, CASA):
        print(tipo["cartella"], costruisci(tipo))

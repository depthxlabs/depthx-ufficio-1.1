"""Passo 4.1: una foto per ogni area della struttura del template, tra le foto scaricate nel passo 3.6.

Le aree della struttura (chiave "scene" del contratto) e l'area della home (scenaDellaHome) si leggono dal
contratto.json copiato nel passo 2.2. Ogni area dice le categorie di foto che
vuole, come lista (Agriturismo) o dentro "categorie" (Hotel, B&B, Casa Vacanza); le forme dentro "forme" (Casa Vacanza),
altrimenti 16x9 e 9x16.
1. Per prima l'area della home: la struttura vista da fuori; mai un prodotto, la colazione, il ristorante o un bagno come
   primo impatto. Se il cliente non ha la foto della struttura vista da fuori, nella home va un prodotto o un servizio
   (categorieDellaHomeSenzaEsterno, Michele 11/11/2026).
2. Poi le altre aree, ognuna con la categoria che chiede il contratto, nell'ordine in cui la chiede.
3. A parità di categoria vince la foto senza luce bruciata, poi quella con il voto di bellezza più alto (dato dal modello,
   Michele 8/11/2026), poi la foto orizzontale, poi la qualità. Mai la stessa foto due volte, nemmeno se arriva da fonti
   diverse: una foto con l'impronta quasi uguale a una già usata si scarta (Michele, 7/11/2026).
4. Un'area prende solo una foto della sua categoria: mai una camera con la foto del ristorante (Michele, 7/11/2026).
   Se il cliente non ha quella categoria l'area resta vuota e il suo blocco esce dalla pagina; anche una pagina
   con soli testi va bene.
5. Ogni forma (16x9 per il computer, 9x16 per il telefono) usa sempre la stessa foto dell'area, tagliata centrata sul
   soggetto: mai due foto diverse tra telefono e computer (Michele, 11/11/2026).
Restituisce idArea -> {foto, percorso, categoria, forme, perForma: forma -> {foto, percorso}}, nell'ordine delle aree
del contratto, solo per le aree con una foto.
"""

import json
from pathlib import Path

from PIL import Image

from ._02_LuceBruciataDiUnaFoto import luceBruciataDiUnaFoto
from ._03_ImprontaDiUnaFoto import improntaDiUnaFoto

FILE_DELLE_REGOLE = Path(__file__).absolute().parent / "_01_RegoleDellaScelta.json"
FORME_DI_OGNI_AREA = ["16x9", "9x16"]
RAPPORTI = {"16x9": 16 / 9, "9x16": 9 / 16}
VOTO_SENZA_GIUDIZIO = 5
MEMORIA_DELLE_MISURE = {}


def misuraVera(percorso):
    """Larghezza e altezza della foto nel verso giusto, come dopo il passo 4.2."""
    if percorso not in MEMORIA_DELLE_MISURE:
        with Image.open(percorso) as immagine:
            larghezza, altezza = immagine.size
            girata = immagine.getexif().get(0x0112, 1) in (5, 6, 7, 8)
        MEMORIA_DELLE_MISURE[percorso] = (altezza, larghezza) if girata else (larghezza, altezza)
    return MEMORIA_DELLE_MISURE[percorso]


def entraNelTaglio(voce, percorso, forma, margine):
    soggetto = voce.get("soggetto")
    if not soggetto or forma not in RAPPORTI:
        return True
    larghezza, altezza = misuraVera(percorso)
    rapporto = RAPPORTI[forma]
    if larghezza / altezza > rapporto:
        largo, alto = altezza * rapporto / larghezza, 1
    else:
        largo, alto = 1, larghezza / rapporto / altezza
    return soggetto[2] - soggetto[0] <= largo + margine and soggetto[3] - soggetto[1] <= alto + margine


class MaterialeInsufficiente(Exception):
    """Il cliente non ha il materiale minimo per una demo di qualità (Michele, 9/11/2026): la demo non si produce."""


def ingrandimentoDellaHome(percorso, larghezza):
    """Quante volte va ingrandita la foto per riempire la larghezza della home nel taglio 16x9."""
    base, alto = misuraVera(percorso)
    return larghezza / max(1, min(base, alto * 16 / 9))


def scegliUnaFotoPerOgniAreaDellaStruttura(contratto, fotoInOrdine, fotoScaricate):
    regole = json.loads(FILE_DELLE_REGOLE.read_text(encoding="utf-8-sig"))
    contratto = json.loads(Path(contratto).read_text(encoding="utf-8-sig"))
    aree = {idArea: (voce if isinstance(voce, list) else voce.get("categorie", []))
             for idArea, voce in contratto["scene"].items()}
    forme = {idArea: (voce.get("forme") if isinstance(voce, dict) and voce.get("forme") else FORME_DI_OGNI_AREA)
             for idArea, voce in contratto["scene"].items()}
    escluse = set(regole["categorieMaiNelleAree"])
    margine, votoInMeno = float(regole["margineDelSoggetto"]), float(regole["votoInMenoPerUnaForma"])
    ordinate = [voce for voce in fotoInOrdine if voce.get("categoria") not in escluse and voce["id"] in fotoScaricate]
    home = contratto.get("scenaDellaHome")
    # Michele, 11/11/2026: senza foto delle camere il cliente passa (la pagina delle camere nasce solo con il suo materiale);
    # senza foto dell'esterno il cliente passa e nella Home va un prodotto o un servizio (la bolla lo dice: home "prodotto o
    # servizio"). Il cliente si ferma solo se non ha nessuna foto per la Home.
    categorieDelCliente = [voce["categoria"] for voce in ordinate]
    senzaEsterno = "esterno della struttura" not in categorieDelCliente
    categorieDellaHome = regole["categorieDellaHomeSenzaEsterno"] if senzaEsterno else regole["categorieDellaPrimaFotoDellaHome"]
    if not any(categoria in categorieDellaHome for categoria in categorieDelCliente):
        raise MaterialeInsufficiente("materiale insufficiente: nessuna foto per la Home, né della struttura vista da fuori né di un prodotto o di un servizio")
    richieste = dict(aree)
    if home in richieste:
        richieste = {home: categorieDellaHome, **{k: v for k, v in richieste.items() if k != home}}
    usate, impronteUsate, scelte = set(), [], {}
    giaUsata = lambda voce: any(sum(a != b for a, b in zip(improntaDiUnaFoto(fotoScaricate[voce["id"]]), impronta))
                                < regole["differenzaMinimaTraDueFoto"] for impronta in impronteUsate)
    bellezza = lambda voce: voce.get("voto") or VOTO_SENZA_GIUDIZIO

    def usa(voce):
        usate.add(voce["id"])
        impronteUsate.append(improntaDiUnaFoto(fotoScaricate[voce["id"]]))

    for idArea, desiderate in richieste.items():
        eHome = idArea == home
        massimo = regole["luceBruciataMassimaNellaHome"] if eHome else regole["luceBruciataMassimaNelleAltreAree"]
        vietateQui = set(regole["categorieMaiNellaPrimaFotoDellaHome"]) if eHome and not senzaEsterno else set()
        troppoPiccola = (lambda voce: ingrandimentoDellaHome(fotoScaricate[voce["id"]], float(regole["larghezzaDellaHome"]))
                         > float(regole["ingrandimentoMassimoDellaHome"])) if eHome else (lambda voce: False)
        voto = lambda voce: (troppoPiccola(voce), luceBruciataDiUnaFoto(fotoScaricate[voce["id"]]) > massimo, desiderate.index(voce["categoria"]),
                             -bellezza(voce), (voce.get("larghezza") or 0) < (voce.get("altezza") or 0), ordinate.index(voce))
        candidate = sorted([voce for voce in ordinate if voce["id"] not in usate and voce["categoria"] in desiderate
                            and voce["categoria"] not in vietateQui], key=voto)
        scelta = next((voce for voce in candidate if not giaUsata(voce)), None)
        if not scelta:
            continue
        usa(scelta)
        # Michele, 11/11/2026: "non esiste che ci siano 2 diverse": ogni area ha una sola foto, la stessa sul computer (16x9)
        # e sul telefono (9x16), tagliata centrata sul soggetto; mai un'altra foto per una forma
        perForma = {forma: {"foto": scelta, "percorso": fotoScaricate[scelta["id"]]} for forma in forme[idArea]}
        scelte[idArea] = {"foto": scelta, "percorso": fotoScaricate[scelta["id"]], "categoria": scelta["categoria"],
                           "forme": forme[idArea], "perForma": perForma}
    return {idArea: scelte[idArea] for idArea in aree if idArea in scelte}

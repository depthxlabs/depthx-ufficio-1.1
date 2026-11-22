"""Verifica della scheda Google Maps con i dati del CRM: la scheda vale con almeno due dati uguali al CRM.

Le regole sono quelle del motore precedente (collegamento del CRM, poi ricerca verificata). Le usa il download da Google Maps.
"""

import sys

sys.dont_write_bytecode = True

import difflib
import math
import re
import time
import unicodedata
import urllib.parse

import _02_PercorsiChiaviEFunzioniComuni as comune

URL_RICERCA = "https://places.googleapis.com/v1/places:searchText"  # ricerca della scheda per testo
PROVE_MINIME = 2  # dati uguali al CRM perché una scheda sia verificata
SOMIGLIANZA_MINIMA_DEL_NOME = 0.85  # somiglianza tra nome del CRM e nome della scheda (da 0 a 1)
LETTERE_MINIME_DEL_NOME = 4  # lettere distintive minime perché un nome contenuto nell'altro valga
RAGGIO_INTORNO_AL_PUNTO = 300.0  # metri: ricerca intorno alle coordinate del collegamento del CRM
DISTANZA_MASSIMA_DAL_PUNTO = 150.0  # metri: la scheda deve stare a questa distanza dalle coordinate del CRM
MOTIVO_NON_VERIFICATA = "scheda Google non verificata"  # motivo scritto in dashboard
PROVE_DI_IDENTITA = ("telefono", "dominio del sito", "nome")  # dati che riguardano l'attività e non il luogo
DOMINI_DEI_SOCIAL = ("facebook.com", "instagram.com", "tiktok.com", "youtube.com", "youtu.be", "linktr.ee", "wa.me")  # non sono siti del cliente
PAROLE_GENERICHE_DEL_NOME = {
    "il", "lo", "la", "i", "gli", "le", "l", "di", "da", "del", "della", "dei", "al", "alla", "e", "ed", "and", "the",
    "srl", "srls", "snc", "sas", "spa", "ss", "sa", "societa", "cooperativa",
}  # parole che non distinguono un'attività da un'altra


# Lettura del collegamento della scheda scritto nel CRM.


def idDellaSchedaDalCrm(valore):
    """Identificativo della scheda (place id) scritto nel CRM, oppure stringa vuota."""
    trovato = re.search(r"(ChIJ[0-9A-Za-z_\-]{10,})", urllib.parse.unquote(valore or ""))
    return trovato.group(1) if trovato else ""


def cidDaCollegamento(valore):
    """Numero CID della scheda da un collegamento di Google Maps (cid=, ludocid= oppure 0x...:0x...), oppure stringa vuota."""
    testo = urllib.parse.unquote(valore or "")
    trovato = re.search(r"[?&](?:cid|ludocid)=(\d{5,})", testo)
    if trovato:
        return trovato.group(1)
    trovato = re.search(r"0x[0-9a-fA-F]+:0x([0-9a-fA-F]+)", testo)
    if trovato:
        return str(int(trovato.group(1), 16))
    return ""


def nomeECoordinateDaCollegamento(valore):
    """Nome e coordinate da un collegamento di Maps del tipo /place/Nome/@lat,lng oppure !3d lat !4d lng.

    Restituisce (nome, latitudine, longitudine); (stringa vuota, None, None) se mancano.
    """
    testo = urllib.parse.unquote_plus(valore or "")
    nome = re.search(r"/maps/place/([^/@?]+)", testo)
    punto = re.search(r"!3d(-?\d+\.\d+)!4d(-?\d+\.\d+)", testo) or re.search(r"@(-?\d+\.\d+),(-?\d+\.\d+)", testo)
    if not nome or not punto:
        return "", None, None
    return nome.group(1).strip(), float(punto.group(1)), float(punto.group(2))


def collegamentoMappeDelCrm(valore):
    """Vero se nel CRM c'è un collegamento a Google Maps (e non un testo come "presente")."""
    testo = (valore or "").strip().lower()
    return testo.startswith("http") and ("google." in testo or "goo.gl" in testo)


def apriCollegamentoBreve(valore):
    """Collegamento completo dietro un collegamento breve di Google Maps scritto nel CRM, con l'inizio della pagina."""
    try:
        risposta = comune.sessioneWeb().get(valore.strip(), timeout=(20, 40), allow_redirects=True)
    except Exception:
        return ""
    return risposta.url + " " + risposta.text[:200000]


# Confronto dei dati della scheda con i dati del CRM.


def testoSemplice(testo):
    """Testo minuscolo, senza accenti e senza segni, per confrontare nomi e comuni."""
    semplice = unicodedata.normalize("NFKD", str(testo or "")).encode("ascii", "ignore").decode("ascii").lower()
    return " ".join(re.sub(r"[^a-z0-9]+", " ", semplice).split())


def cifreDelTelefono(numero):
    """Cifre del numero, senza il prefisso internazionale dell'Italia."""
    cifre = re.sub(r"\D", "", str(numero or ""))
    if cifre.startswith("0039"):
        cifre = cifre[4:]
    elif cifre.startswith("39") and len(cifre) >= 11:
        cifre = cifre[2:]
    return cifre


def telefoniDelCrm(cliente):
    """Insieme dei numeri del CRM (telefono fisso e cellulare), anche se una cella ne contiene più di uno."""
    numeri = set()
    for valore in (cliente.get("telefono"), cliente.get("cellulare")):
        for pezzo in re.split(r"[;,/|\n]|\s-\s|\se\s|\so\s", str(valore or "")):
            cifre = cifreDelTelefono(pezzo)
            if len(cifre) >= 6:
                numeri.add(cifre)
    return numeri


def dominioDelSito(valore):
    """Dominio del sito senza www, oppure stringa vuota se manca o è un profilo social."""
    valore = (valore or "").strip()
    if not valore or " " in valore:
        return ""
    if not valore.lower().startswith("http"):
        valore = "https://" + valore
    nome = (urllib.parse.urlsplit(valore).hostname or "").lower().removeprefix("www.")
    if "." not in nome or any(nome == social or nome.endswith("." + social) for social in DOMINI_DEI_SOCIAL):
        return ""
    return nome


def componente(scheda, tipo):
    """Testo del componente della scheda con quel tipo (postal_code, locality, ...), oppure stringa vuota."""
    for voce in scheda.get("addressComponents", []) or []:
        if tipo in (voce.get("types") or []):
            return voce.get("longText") or voce.get("shortText") or ""
    return ""


def nomeDellaScheda(scheda):
    """Nome mostrato dalla scheda."""
    nome = scheda.get("displayName")
    return nome.get("text", "") if isinstance(nome, dict) else str(nome or "")


def nomiSimili(nomeCrm, nomeScheda):
    """Vero se i due nomi sono molto simili: quasi uguali, oppure le parole distintive di uno stanno tutte nell'altro."""
    primo, secondo = testoSemplice(nomeCrm), testoSemplice(nomeScheda)
    if not primo or not secondo:
        return False
    if difflib.SequenceMatcher(None, primo, secondo).ratio() >= SOMIGLIANZA_MINIMA_DEL_NOME:
        return True
    paroleUno = {parola for parola in primo.split() if parola not in PAROLE_GENERICHE_DEL_NOME and len(parola) >= 3}
    paroleDue = {parola for parola in secondo.split() if parola not in PAROLE_GENERICHE_DEL_NOME and len(parola) >= 3}
    if not paroleUno or not paroleDue:
        return False
    piccolo, grande = sorted((paroleUno, paroleDue), key=len)
    return piccolo <= grande and sum(len(parola) for parola in piccolo) >= LETTERE_MINIME_DEL_NOME


def proveDellaScheda(cliente, scheda):
    """Elenco dei dati della scheda uguali al CRM: telefono, CAP, comune, dominio del sito, nome."""
    prove = []
    telefoniScheda = {cifreDelTelefono(scheda.get(campo)) for campo in ("nationalPhoneNumber", "internationalPhoneNumber") if scheda.get(campo)}
    if telefoniScheda & telefoniDelCrm(cliente):
        prove.append("telefono")
    capCrm = re.sub(r"\D", "", str(cliente.get("cap") or ""))
    capScheda = re.sub(r"\D", "", componente(scheda, "postal_code"))
    if capCrm and capScheda and capCrm.zfill(5) == capScheda.zfill(5):
        prove.append("CAP")
    comuneCrm = testoSemplice(cliente.get("comune"))
    comuniScheda = {testoSemplice(componente(scheda, tipo)) for tipo in ("locality", "administrative_area_level_3")} - {""}
    if comuneCrm and comuneCrm in comuniScheda:
        prove.append("comune")
    dominioCrm = dominioDelSito(cliente.get("sito"))
    if dominioCrm and dominioCrm == dominioDelSito(scheda.get("websiteUri")):
        prove.append("dominio del sito")
    if nomiSimili(cliente.get("nome"), nomeDellaScheda(scheda)):
        prove.append("nome")
    return prove


def schedaVerificata(prove):
    """Una scheda è verificata con almeno due dati uguali al CRM, e almeno uno riguarda l'attività (telefono, dominio o nome).

    CAP e comune dicono il luogo e non l'attività: due locali vicini li hanno uguali.
    """
    return len(prove) >= PROVE_MINIME and any(prova in PROVE_DI_IDENTITA for prova in prove)


def distanzaInMetri(primaLat, primaLng, secondaLat, secondaLng):
    """Distanza tra due punti sulla Terra, in metri."""
    raggio = 6371000.0
    fiUno, fiDue = math.radians(primaLat), math.radians(secondaLat)
    deltaFi, deltaLambda = math.radians(secondaLat - primaLat), math.radians(secondaLng - primaLng)
    valore = math.sin(deltaFi / 2) ** 2 + math.cos(fiUno) * math.cos(fiDue) * math.sin(deltaLambda / 2) ** 2
    return 2 * raggio * math.asin(math.sqrt(valore))


def voceDiEsame(scheda, prove):
    """Riga di esame di un risultato, salvata su Drive per Michele."""
    return {"id": scheda.get("id", ""), "nome": nomeDellaScheda(scheda), "luogo": scheda.get("formattedAddress", ""), "prove": prove}


def scegliConLaVerifica(cliente, schede):
    """Sceglie tra i risultati la scheda verificata con più dati uguali al CRM.

    Restituisce (scheda, prove, esame di tutti i risultati); (None, [], esame) se nessuna è verificata.
    """
    esame = []
    migliore, proveMigliori = None, []
    for scheda in schede:
        prove = proveDellaScheda(cliente, scheda)
        voce = voceDiEsame(scheda, prove)
        voce["verificata"] = schedaVerificata(prove)
        esame.append(voce)
        if voce["verificata"] and len(prove) > len(proveMigliori):
            migliore, proveMigliori = scheda, prove
    return migliore, proveMigliori, esame


def scegliConIlCid(cliente, schede, cid):
    """Sceglie tra i risultati la scheda con lo stesso CID del collegamento del CRM. Restituisce (scheda, prove, esame)."""
    esame = []
    for scheda in schede:
        voce = voceDiEsame(scheda, proveDellaScheda(cliente, scheda))
        voce["verificata"] = cidDaCollegamento(scheda.get("googleMapsUri", "")) == cid
        esame.append(voce)
        if voce["verificata"]:
            return scheda, ["CID del collegamento del CRM"] + voce["prove"], esame
    return None, [], esame


def scegliConIlPunto(cliente, schede, nome, latitudine, longitudine):
    """Sceglie tra i risultati la scheda con nome molto simile a quello del collegamento del CRM e vicina alle sue coordinate.

    Restituisce (scheda, prove, esame).
    """
    esame = []
    migliore, distanzaMigliore = None, None
    for scheda in schede:
        voce = voceDiEsame(scheda, proveDellaScheda(cliente, scheda))
        punto = scheda.get("location") or {}
        distanza = None
        if punto.get("latitude") is not None and punto.get("longitude") is not None:
            distanza = distanzaInMetri(latitudine, longitudine, punto["latitude"], punto["longitude"])
        voce["metriDalPuntoDelCrm"] = round(distanza) if distanza is not None else None
        voce["verificata"] = distanza is not None and distanza <= DISTANZA_MASSIMA_DAL_PUNTO and nomiSimili(nome, nomeDellaScheda(scheda))
        esame.append(voce)
        if voce["verificata"] and (distanzaMigliore is None or distanza < distanzaMigliore):
            migliore, distanzaMigliore = scheda, distanza
    if migliore is None:
        return None, [], esame
    prove = ["nome e coordinate del collegamento del CRM"] + proveDellaScheda(cliente, migliore)
    return migliore, prove, esame


def testoDellaRicerca(cliente):
    """Testo della ricerca: nome commerciale, via e numero civico, CAP, comune e provincia."""
    parti = (cliente.get("nome"), cliente.get("via"), cliente.get("cap"), cliente.get("comune"), cliente.get("provincia"))
    return " ".join(str(parte).strip() for parte in parti if parte and str(parte).strip())


def testoBreveDellaRicerca(cliente):
    """Seconda ricerca: solo nome commerciale, comune e provincia (la via scritta nel CRM a volte non è quella di Google)."""
    parti = (cliente.get("nome"), cliente.get("comune"), cliente.get("provincia"))
    return " ".join(str(parte).strip() for parte in parti if parte and str(parte).strip())


def ricercaVerificata(cliente, cerca, giaLette=None):
    """Ricerca verificata con i dati del CRM su tutti i risultati: quelli già letti, la ricerca completa, la ricerca breve e il solo nome.

    Le schede uguali si esaminano una volta. Restituisce (scheda, prove, esame).
    """
    schede, visti = [], set()

    def aggiungi(risultati):
        for scheda in risultati or []:
            chiave = scheda.get("id") or id(scheda)
            if chiave not in visti:
                visti.add(chiave)
                schede.append(scheda)

    aggiungi(giaLette)
    aggiungi(cerca(testoDellaRicerca(cliente), None))
    scheda, prove, esame = scegliConLaVerifica(cliente, schede)
    if scheda is None and testoBreveDellaRicerca(cliente) != testoDellaRicerca(cliente):
        aggiungi(cerca(testoBreveDellaRicerca(cliente), None))
        scheda, prove, esame = scegliConLaVerifica(cliente, schede)
    nome = str(cliente.get("nome") or "").strip()
    if scheda is None and nome and nome != testoBreveDellaRicerca(cliente):
        # terza ricerca con il solo nome: con comune e provincia Google a volte mostra solo le strutture vicine
        aggiungi(cerca(nome, None))
        scheda, prove, esame = scegliConLaVerifica(cliente, schede)
    return scheda, prove, esame

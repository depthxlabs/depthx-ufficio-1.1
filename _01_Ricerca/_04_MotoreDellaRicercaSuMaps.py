"""MOTORE DELLA RICERCA SU MAPS, Linea 1.1 Outbound Websites, Ricerca clienti.

Un lavoro = un tipo (HOT, BEB, AGR, CAV) in un comune, per la ricerca indicata.
1. Cerca su Google Places API (New) le parole del tipo nel comune.
2. Tiene solo le strutture aperte, del comune, del tipo giusto, con un sito proprio non ancora noto.
3. Controlla ogni sito: email pubblicata (obbligatoria, il contatto è solo per email), sezione S2, S3 o S4, social, piattaforma.
4. Scrive i contatti in _03_Contatti/<Codice>/<TIPO>_<Comune>.csv e l'esito in _02_Giri/<Codice>/<TIPO>_<Comune>.json.

Uso:  python -B -I _04_MotoreDellaRicercaSuMaps.py --codice Ricerca001 --tipo HOT --comune Brescia --provincia BS
La chiave di Google Maps arriva dai segreti di GitHub (CHIAVE_GOOGLE_MAPS) e non si stampa mai.
"""
import argparse, datetime, glob, json, os, re, sys, time, unicodedata, urllib.parse
from multiprocessing.dummy import Pool
import requests
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import importlib
D = importlib.import_module("_01_DatiSuGitHub")
T = importlib.import_module("_02_TipiERegioni")
C = importlib.import_module("_03_ControlloDelSitoPerLaSezione")

COLONNE_CRM = ["ID cliente", "Nome commerciale", "Ragione sociale", "Forma giuridica", "Sottosettore", "Partita IVA", "Titolare o referente",
               "Ruolo del referente", "Via e numero civico", "CAP", "Comune", "Provincia", "Sede unica", "Numero di sedi", "Orari", "Codice CIN",
               "Numero di camere", "Motore di prenotazione attuale", "Telefono fisso", "Cellulare", "Tutti i contatti Email", "Ha Instagram?",
               "Ha Facebook?", "Ha gia un sito?", "Ha un Canale YouTube?", "Ha TikTok?", "Pagina LinkedIn aziendale", "Piattaforma del sito",
               "Agenzia o crediti", "Numero di pagine del sito attuale", "Google Maps", "Voto Google", "Recensioni Google", "Foto Google",
               "Verifica sito", "Verifica Registro Imprese", "Stato Commerciale", "Link demo"]
COLONNE = ["Codice ricerca", "Data", "Sezione", "Tipo", "Regione", "Dominio"] + COLONNE_CRM
PORTALI = re.compile(r"booking\.com|airbnb\.|expedia\.|tripadvisor\.|facebook\.com|instagram\.com|google\.|hotels\.com|trivago\.|agriturismo\.it|"
                     r"casevacanza\.it|bed-and-breakfast\.it|bbplanet|subito\.it|vrbo\.|holidu\.|wixsite\.com/?$", re.I)
CAMPI = ("places.id,places.displayName,places.websiteUri,places.internationalPhoneNumber,places.addressComponents,places.googleMapsUri,"
         "places.rating,places.userRatingCount,places.photos,places.primaryType,places.types,places.businessStatus,nextPageToken")
SITI_INSIEME = 8
# tipi principali di Google che sono un alloggio: ristoranti, bar, aree di sosta e campeggi restano fuori
ALLOGGIO = re.compile(r"hotel|motel|inn$|lodging|bed_and_breakfast|guest_house|farmstay|farm$|cottage|private_guest_room|vacation_rental|hostel|resort", re.I)


def semplice(t):
    return unicodedata.normalize("NFKD", t or "").encode("ascii", "ignore").decode().lower().replace("'", "").replace("-", " ").strip()


def chiave_maps():
    m = re.findall(r"AIza[0-9A-Za-z_\-]{35}", os.environ.get("CHIAVE_GOOGLE_MAPS", ""))
    if not m:
        sys.exit("Chiave Google Maps non trovata nei segreti.")
    return m[0]


def cerca_su_maps(parole, comune, provincia, chiave):
    visti, risultati = set(), []
    for parola in parole:
        corpo = {"textQuery": f"{parola} {comune} {provincia}", "languageCode": "it", "regionCode": "IT", "pageSize": 20}
        for _ in range(3):   # Google dà al massimo 60 risultati per ricerca, in 3 pagine
            r = requests.post("https://places.googleapis.com/v1/places:searchText", json=corpo, timeout=30,
                              headers={"X-Goog-Api-Key": chiave, "X-Goog-FieldMask": CAMPI})
            if r.status_code != 200:
                sys.exit(f"Places API: HTTP {r.status_code} {r.json().get('error', {}).get('status', '')}")
            d = r.json()
            for pl in d.get("places", []):
                if pl["id"] not in visti:
                    visti.add(pl["id"]); risultati.append(pl)
            if not d.get("nextPageToken"):
                break
            corpo = {**corpo, "pageToken": d["nextPageToken"]}
            time.sleep(2)
    return risultati


def componente(place, tipo, breve=False):
    for c in place.get("addressComponents", []):
        if tipo in c.get("types", []):
            return c.get("shortText" if breve else "longText", "")
    return ""


def gia_noti(codice):
    """Domini, email e telefoni del CRM e degli esclusi, più tutto quello già trovato da ogni ricerca."""
    domini, email, telefoni = set(), set(), set()
    for r in D.leggi_tabella("_00_Noti/Noti.csv"):
        if r.get("Dominio"): domini.add(r["Dominio"].lower())
        if r.get("Email"): email.add(r["Email"].lower())
        if r.get("Telefono"): telefoni.add(r["Telefono"])
    for f in glob.glob(os.path.join(D.RADICE, "_03_Contatti", "*", "*.csv")):
        for r in D.leggi_tabella(os.path.relpath(f, D.RADICE).replace(os.sep, "/")):
            domini.add(r.get("Dominio", "").lower())
            for e in r.get("Tutti i contatti Email", "").split(";"):
                email.add(e.strip().lower())
    return domini - {""}, email - {""}, telefoni - {""}


def cifre_telefono(t):
    return re.sub(r"\D", "", t or "")[-9:]


def main():
    a = argparse.ArgumentParser()
    a.add_argument("--codice", required=True)
    a.add_argument("--tipo", required=True, choices=list(T.TIPI))
    a.add_argument("--comune", required=True)
    a.add_argument("--provincia", required=True)
    p = a.parse_args()
    inizio = datetime.datetime.now().isoformat(timespec="seconds")
    file = f"{p.tipo}_{D.nome_file(p.comune)}"
    tipo = T.TIPI[p.tipo]
    altri = set().union(*[t["google"] for k, t in T.TIPI.items() if k != p.tipo]) - {"lodging"}
    domini, email_note, telefoni = gia_noti(p.codice)
    ricerca = next((r for r in D.leggi_tabella("_01_Ricerche/Ricerche.csv") if r["Codice"] == p.codice), {})
    sezioni = set((ricerca.get("Sezioni") or "S2 S3 S4").split())
    scarti, candidati = {}, []
    scarta = lambda motivo: scarti.__setitem__(motivo, scarti.get(motivo, 0) + 1)

    trovati = cerca_su_maps(tipo["parole"], p.comune, p.provincia, chiave_maps())
    for pl in trovati:
        sito = pl.get("websiteUri", "")
        dominio = urllib.parse.urlparse(sito).netloc.replace("www.", "").lower()
        if pl.get("businessStatus") not in (None, "OPERATIONAL"):
            scarta("struttura chiusa"); continue
        # dal 23/11/2026: le strutture dei comuni vicini che Google restituisce si tengono (prima il 92% dei risultati si scartava);
        # i doppioni restano fuori con il controllo su dominio, email e telefono
        if pl.get("primaryType") in altri:
            scarta("di un altro tipo"); continue
        if pl.get("primaryType") and not ALLOGGIO.search(pl["primaryType"]):
            scarta("non è un alloggio (" + pl["primaryType"] + ")"); continue
        if not sito:
            scarta("senza sito"); continue
        if PORTALI.search(sito):
            scarta("sito di un portale o social"); continue
        if dominio in domini or cifre_telefono(pl.get("internationalPhoneNumber")) in telefoni:
            scarta("già nel CRM o già trovato"); continue
        domini.add(dominio)
        candidati.append(pl)

    with Pool(SITI_INSIEME) as gruppo:
        controlli = gruppo.map(lambda pl: C.controlla_sito(pl["websiteUri"]), candidati)

    oggi, righe = datetime.date.today().isoformat(), []
    for pl, s in zip(candidati, controlli):
        if not s["letto"]:
            scarta("sito non raggiungibile"); continue
        if s["sezione"] not in sezioni:
            scarta(f"sezione {s['sezione']} non cercata"); continue
        email = [e for e in s["email"] if e not in email_note][:3]
        if not s["email"]:
            scarta("nessuna email pubblica"); continue
        if not email:
            scarta("email già nel CRM"); continue
        email_note.update(email)
        prov = componente(pl, "administrative_area_level_2", True) or p.provincia
        tel = (pl.get("internationalPhoneNumber") or "").replace(" ", "")
        via = " ".join(x for x in (componente(pl, "route"), componente(pl, "street_number")) if x)
        nome = pl.get("displayName", {}).get("text", "")
        crm = {c: "" for c in COLONNE_CRM}
        crm.update({"Nome commerciale": nome, "Sottosettore": T.sottocategoria(p.tipo, nome + " " + s["presentazione"]),
                    "Via e numero civico": via, "CAP": componente(pl, "postal_code"), "Comune": componente(pl, "locality") or p.comune,
                    "Provincia": prov, "Telefono fisso": "" if tel.startswith("+393") else tel, "Cellulare": tel if tel.startswith("+393") else "",
                    "Tutti i contatti Email": "; ".join(email), "Ha Instagram?": s["social"]["instagram"] or "no",
                    "Ha Facebook?": s["social"]["facebook"] or "no", "Ha gia un sito?": s["sito"], "Ha un Canale YouTube?": s["social"]["youtube"] or "no",
                    "Ha TikTok?": s["social"]["tiktok"] or "no", "Pagina LinkedIn aziendale": s["social"]["linkedin"] or "no",
                    "Piattaforma del sito": s["piattaforma"], "Numero di pagine del sito attuale": s["pagine"], "Google Maps": pl.get("googleMapsUri", ""),
                    "Voto Google": pl.get("rating", ""), "Recensioni Google": pl.get("userRatingCount", ""), "Foto Google": len(pl.get("photos", [])),
                    "Verifica sito": "sì, " + s["motivo"], "Stato Commerciale": "Appena inserito"})
        righe.append({"Codice ricerca": p.codice, "Data": oggi, "Sezione": s["sezione"], "Tipo": p.tipo,
                      "Regione": T.REGIONE_DELLA_PROVINCIA.get(prov, ""), "Dominio": s["dominio"], **crm})

    esito = {"codice": p.codice, "tipo": p.tipo, "comune": p.comune, "provincia": p.provincia, "inizio": inizio,
             "fine": datetime.datetime.now().isoformat(timespec="seconds"), "risultatiMaps": len(trovati), "sitiControllati": len(candidati),
             "contatti": len(righe), "perSezione": {k: sum(1 for r in righe if r["Sezione"] == k) for k in ("S2", "S3", "S4")}, "scartati": scarti}

    def scrivi():
        D.scrivi_tabella(f"_03_Contatti/{p.codice}/{file}.csv", COLONNE, righe)
        D.scrivi_json(f"_02_Giri/{p.codice}/{file}.json", esito)
    D.salva(scrivi, f"{p.codice}: {p.tipo} {p.comune}, {len(righe)} contatti")
    print(json.dumps(esito, ensure_ascii=False))


if __name__ == "__main__":
    try:
        main()
    except BaseException as e:
        if isinstance(e, SystemExit) and e.code in (0, None):
            raise
        a = dict(zip(sys.argv[1::2], sys.argv[2::2]))
        codice, file = a.get("--codice", ""), f"{a.get('--tipo', '')}_{D.nome_file(a.get('--comune', ''))}"
        if codice and file:
            esito = {"codice": codice, "tipo": a.get("--tipo"), "comune": a.get("--comune"), "provincia": a.get("--provincia"),
                     "fine": datetime.datetime.now().isoformat(timespec="seconds"), "contatti": 0, "notgo": str(e.code if isinstance(e, SystemExit) else e)}
            D.salva(lambda: D.scrivi_json(f"_02_Giri/{codice}/{file}.json", esito), f"{codice}: {file} NOTGO")
        raise

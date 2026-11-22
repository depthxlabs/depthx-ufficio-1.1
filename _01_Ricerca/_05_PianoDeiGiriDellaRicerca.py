"""PIANO DEI GIRI DELLA RICERCA, Linea 1.1 Outbound Websites, Ricerca clienti.

La ricerca parte dal Centro Gestione e va avanti da sola, un giro dopo l'altro, senza orari fissi:
  --fase piano     legge la ricerca; al primo giro trova i comuni intorno alla partenza, dal più vicino;
                   dà ai motori le prossime coppie tipo e comune non ancora fatte, fino a 20 motori insieme, 5 coppie per motore.
                   Quando tutti i comuni sono fatti il raggio si allarga di 20 km, fino a 400 km.
  --fase continua  a giro finito conta i contatti raccolti: se l'obiettivo non è raggiunto e la ricerca
                   è ancora attiva, il giro successivo parte subito.
"""
import argparse, datetime, glob, json, os, sys
import requests
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import importlib
D = importlib.import_module("_01_DatiSuGitHub")

MOTORI_INSIEME = 20
COPPIE_PER_MOTORE = 5   # ogni motore lavora 5 coppie tipo e comune una dopo l'altra: 100 coppie per giro
PASSO_KM, RAGGIO_MASSIMO_KM = 20, 400
AGENTE_WEB = {"User-Agent": "DepthX-Ricerca/1.1 (comuni della ricerca)", "Accept": "application/json"}
ADESSO = lambda: datetime.datetime.now().isoformat(timespec="seconds")


def comuni_intorno(lat, lon, km):
    q = ('SELECT ?nome ?sigla ?dist WHERE { SERVICE wikibase:around { ?c wdt:P625 ?pos . '
         f'bd:serviceParam wikibase:center "Point({lon} {lat})"^^geo:wktLiteral . bd:serviceParam wikibase:radius "{km}" . '
         'bd:serviceParam wikibase:distance ?dist . } ?c wdt:P31 wd:Q747074 . ?c wdt:P131 ?prov . ?prov wdt:P395 ?sigla . '
         '?c rdfs:label ?nome . FILTER(lang(?nome)="it") } ORDER BY ?dist LIMIT 3000')
    r = requests.get("https://query.wikidata.org/sparql", params={"query": q, "format": "json"}, headers=AGENTE_WEB, timeout=120)
    r.raise_for_status()
    visti, comuni = set(), []
    for x in r.json()["results"]["bindings"]:
        nome = x["nome"]["value"]
        if nome.lower() not in visti:
            visti.add(nome.lower()); comuni.append([nome, x["sigla"]["value"], str(round(float(x["dist"]["value"]), 1))])
    return comuni


def contatti_raccolti(codice):
    return sum(len(D.leggi_tabella(os.path.relpath(f, D.RADICE).replace(os.sep, "/")))
               for f in glob.glob(os.path.join(D.RADICE, "_03_Contatti", codice, "*.csv")))


def giri_fatti(codice):
    return {os.path.basename(f)[:-5] for f in glob.glob(os.path.join(D.RADICE, "_02_Giri", codice, "*.json"))}


def ricerca(codice):
    return next((r for r in D.leggi_tabella("_01_Ricerche/Ricerche.csv") if r["Codice"] == codice), None)


def aggiorna(codice, valori, zone=None):
    """Scrive i valori sulla riga della ricerca nell'ultima versione dei dati: uno stato "fermata" scritto nel frattempo resta."""
    def scrivi():
        righe = D.leggi_tabella("_01_Ricerche/Ricerche.csv")
        for r in righe:
            if r["Codice"] == codice:
                v = dict(valori)
                if r["Stato"] != "attivo":
                    v.pop("Stato", None)
                r.update({k: str(x) for k, x in v.items()}, Aggiornato=ADESSO())
        D.scrivi_tabella("_01_Ricerche/Ricerche.csv", D.COLONNE_RICERCHE, righe)
        if zone is not None:
            D.scrivi_csv(f"_01_Ricerche/Zone/{codice}.csv", [["Comune", "Provincia", "Km"]] + zone)
    D.salva(scrivi, f"{codice}: piano del giro")


def uscita(nome, valore):
    print(f"{nome}={valore}")
    if os.environ.get("GITHUB_OUTPUT"):
        with open(os.environ["GITHUB_OUTPUT"], "a", encoding="utf-8") as f:
            f.write(f"{nome}={valore}\n")


def piano(codice):
    r = ricerca(codice)
    if not r or r["Stato"] != "attivo":
        return uscita("lavori", "[]")
    raccolti, obiettivo = contatti_raccolti(codice), int(r["Obiettivo"] or 0)
    if raccolti >= obiettivo:
        aggiorna(codice, {"Stato": "raggiunta", "Raggiunti": raccolti})
        return uscita("lavori", "[]")
    zone = D.leggi_csv(f"_01_Ricerche/Zone/{codice}.csv")[1:]
    nuove_zone, raggio = None, float(r["RaggioKm"] or 30)
    if not zone:
        zone = nuove_zone = comuni_intorno(r["Latitudine"], r["Longitudine"], raggio)
    tipi, fatti = r["Tipi"].split(), giri_fatti(codice)
    scegli = lambda zone: [(t, z) for z in zone for t in tipi if f"{t}_{D.nome_file(z[0])}" not in fatti][:MOTORI_INSIEME * COPPIE_PER_MOTORE]
    coppie = scegli(zone)
    while not coppie and raggio < RAGGIO_MASSIMO_KM:
        raggio += PASSO_KM
        note = {z[0].lower() for z in zone}
        aggiunte = [z for z in comuni_intorno(r["Latitudine"], r["Longitudine"], raggio) if z[0].lower() not in note]
        if aggiunte:
            zone = nuove_zone = zone + aggiunte
            coppie = scegli(aggiunte)
    valori = {"Raggiunti": raccolti, "Giri": int(r["Giri"] or 0) + 1, "RaggioKm": int(raggio)}
    if not coppie:
        valori["Stato"] = "zone finite"
    aggiorna(codice, valori, nuove_zone)
    voci = [f"{t}|{z[0]}|{z[1]}" for t, z in coppie]
    gruppi = [";".join(voci[k::MOTORI_INSIEME]) for k in range(min(MOTORI_INSIEME, len(voci)))]
    uscita("lavori", json.dumps(gruppi, ensure_ascii=False))


def continua(codice):
    D.git("fetch", "-q", "origin", "main"); D.git("reset", "-q", "--hard", "origin/main")
    r = ricerca(codice)
    raccolti = contatti_raccolti(codice)
    attiva = bool(r) and r["Stato"] == "attivo"
    if attiva:
        valori = {"Raggiunti": raccolti}
        if raccolti >= int(r["Obiettivo"] or 0):
            valori["Stato"], attiva = "raggiunta", False
        aggiorna(codice, valori)
    uscita("attiva", "si" if attiva else "no")


if __name__ == "__main__":
    a = argparse.ArgumentParser()
    a.add_argument("--fase", choices=["piano", "continua"], required=True)
    a.add_argument("--codice", required=True)
    p = a.parse_args()
    piano(p.codice) if p.fase == "piano" else continua(p.codice)

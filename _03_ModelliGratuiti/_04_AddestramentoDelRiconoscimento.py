"""ADDESTRAMENTO DEL RICONOSCIMENTO DELLE FOTO, Linea 1.1 Outbound Websites.

Insegna al modello di immagini le 12 categorie dell'ospitalità con le risposte già date da Claude sui clienti scaricati.
1. Trova su Drive tutti i riconoscimenti fatti da Claude (_01_RiconoscimentoDelleFoto.json), tranne i clienti della prova.
2. Prende un campione bilanciato: fino a FOTO_PER_CATEGORIA foto per categoria, da clienti diversi.
3. Scarica le foto, ne calcola la rappresentazione con il modello di immagini e addestra uno strato di decisione (regressione logistica).
4. Misura su un 20% di foto tenute fuori quante categorie indovina, categoria per categoria.
Il modello addestrato va in dati/_06_ModelloDelleFoto/_01_StratoDiDecisione.json (archivio privato); nel registro pubblico solo numeri.
"""
import collections, glob, json, os, random, sys, time
import numpy, requests
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import importlib
R = importlib.import_module("_01_RiconoscimentoDelleFotoSullaMacchina")

DATI = os.environ.get("DATI_RICERCA", "dati")
FOTO_PER_CATEGORIA = int(os.environ.get("FOTO_PER_CATEGORIA", "400"))
CARTELLA = "foto_dell_addestramento"
random.seed(23)


def accesso_drive():
    t = json.loads(os.environ["MOTORE_DRIVE_TOKEN"])
    r = requests.post(t.get("token_uri") or "https://oauth2.googleapis.com/token", timeout=60,
                      data={"client_id": t["client_id"], "client_secret": t["client_secret"], "refresh_token": t["refresh_token"], "grant_type": "refresh_token"})
    r.raise_for_status()
    return r.json()["access_token"]


def drive(accesso, percorso, **parametri):
    r = requests.get("https://www.googleapis.com/drive/v3/" + percorso, headers={"Authorization": "Bearer " + accesso}, params=parametri, timeout=120)
    r.raise_for_status()
    return r


def riconoscimenti_di_claude(accesso):
    file, pagina = [], None
    while True:
        d = drive(accesso, "files", q="name = '_01_RiconoscimentoDelleFoto.json' and trashed = false", fields="nextPageToken, files(id)",
                  pageSize=1000, pageToken=pagina).json()
        file += [f["id"] for f in d.get("files", [])]
        pagina = d.get("nextPageToken")
        if not pagina:
            return file


def main():
    os.makedirs(CARTELLA, exist_ok=True)
    accesso, inizio = accesso_drive(), time.time()
    della_prova = {os.path.basename(c) for c in glob.glob(os.path.join(DATI, "_05_ProveDeiModelli", "*"))}
    perCategoria = collections.defaultdict(list)
    elenco = riconoscimenti_di_claude(accesso)
    random.shuffle(elenco)
    clienti = 0
    for identita in elenco:
        try:
            d = drive(accesso, f"files/{identita}", alt="media").json()
        except Exception:
            continue
        if d.get("idCliente") in della_prova:
            continue
        clienti += 1
        # da ogni cliente al massimo 6 foto per categoria: il campione resta vario
        for categoria in R.CATEGORIE:
            foto = [v["id"] for v in d.get("valide", []) if v.get("categoria") == categoria and v.get("id")]
            perCategoria[categoria] += [(f, categoria) for f in random.sample(foto, min(6, len(foto)))]
        if all(len(perCategoria[c]) >= FOTO_PER_CATEGORIA for c in R.CATEGORIE) or clienti >= 600:
            break
    campione = [x for c in R.CATEGORIE for x in random.sample(perCategoria[c], min(FOTO_PER_CATEGORIA, len(perCategoria[c])))]
    print(f"riconoscimenti di Claude trovati {len(elenco)}, clienti letti {clienti}, foto nel campione {len(campione)}")
    print("foto per categoria: " + ", ".join(f"{c} {min(FOTO_PER_CATEGORIA, len(perCategoria[c]))}" for c in R.CATEGORIE))

    percorsi, etichette = [], []
    for n, (identita, categoria) in enumerate(campione):
        p = os.path.join(CARTELLA, f"{n:05d}.jpg")
        try:
            r = drive(accesso, f"files/{identita}", alt="media")
            with open(p, "wb") as f:
                f.write(r.content)
            percorsi.append(p); etichette.append(categoria)
        except Exception:
            continue
        if n % 500 == 499:
            accesso = accesso_drive()
    print(f"foto scaricate {len(percorsi)} in {round(time.time() - inizio)} s")

    riconoscimento = R.Riconoscimento()
    vettori = riconoscimento.vettori(percorsi)
    print(f"rappresentazioni calcolate in {round(time.time() - inizio)} s")

    from sklearn.linear_model import LogisticRegression
    from sklearn.model_selection import train_test_split
    X, y = numpy.array(vettori), numpy.array(etichette)
    # esempi giusti ed esempi sbagliati (Michele): dove il modello da solo sbaglia, la foto con la risposta giusta di Claude conta tre volte
    daSolo = numpy.array(riconoscimento.categorie_da_vettori(X))
    peso = numpy.where(daSolo == y, 1.0, 3.0)
    print(f"esempi sbagliati dal modello da solo: {int((daSolo != y).sum())} su {len(y)}")
    Xa, Xp, ya, yp, pa, _ = train_test_split(X, y, peso, test_size=0.2, random_state=23, stratify=y)
    strato = LogisticRegression(max_iter=3000, C=4.0, class_weight="balanced").fit(Xa, ya, sample_weight=pa)
    previsti = strato.predict(Xp)
    giusti = (previsti == yp).mean()
    senza = numpy.array(riconoscimento.categorie_da_vettori(Xp))
    print(f"foto tenute fuori {len(yp)}: giuste con l'addestramento {round(100 * giusti, 1)}%, senza addestramento {round(100 * (senza == yp).mean(), 1)}%")
    for c in R.CATEGORIE:
        m = yp == c
        if m.sum():
            print(f"  {c}: {round(100 * (previsti[m] == c).mean(), 1)}% su {int(m.sum())}")
    # il modello finale si addestra su tutte le foto
    strato = LogisticRegression(max_iter=3000, C=4.0, class_weight="balanced").fit(X, y, sample_weight=peso)
    os.makedirs(os.path.join(DATI, "_06_ModelloDelleFoto"), exist_ok=True)
    with open(os.path.join(DATI, "_06_ModelloDelleFoto", "_01_StratoDiDecisione.json"), "w", encoding="utf-8") as f:
        json.dump({"modello": "ViT-B-32 laion2b_s34b_b79k", "categorie": strato.classes_.tolist(), "pesi": strato.coef_.tolist(),
                   "scarti": strato.intercept_.tolist(), "fotoDiAddestramento": len(y), "giusteSulleFotoTenuteFuori": round(float(giusti), 4)}, f)


if __name__ == "__main__":
    main()

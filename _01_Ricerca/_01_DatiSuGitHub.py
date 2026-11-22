"""DATI SU GITHUB, Linea 1.1 Outbound Websites, Ricerca clienti.

I programmi leggono e scrivono i file CSV del repository privato depthx-dati-1.1,
scaricato nella cartella indicata da DATI_RICERCA (su GitHub: "dati").
  _00_Noti/Noti.csv                          domini, email e telefoni già nel CRM o negli esclusi: mai doppioni
  _01_Ricerche/Ricerche.csv                  una riga per ricerca: codice, tipi, obiettivo, partenza, raggio, stato
  _01_Ricerche/Zone/<Codice>.csv             i comuni della ricerca, dal più vicino
  _02_Giri/<Codice>/<TIPO>_<comune>.json     l'esito del lavoro di un motore su un tipo e un comune
  _03_Contatti/<Codice>/<TIPO>_<comune>.csv  i contatti trovati da quel lavoro
Ogni motore scrive file suoi, con il suo nome: due motori insieme non toccano mai lo stesso file.
salva(scrivi) rilegge l'ultima versione del repository, riapplica le scritture e la carica, ripetendo finché riesce.
"""
import csv, json, os, re, subprocess, time, unicodedata

RADICE = os.environ.get("DATI_RICERCA", "dati")


def percorso(rel):
    return os.path.join(RADICE, *rel.split("/"))


def leggi_csv(rel):
    p = percorso(rel)
    if not os.path.exists(p):
        return []
    with open(p, encoding="utf-8-sig", newline="") as f:
        return [r for r in csv.reader(f) if any(r)]


def leggi_tabella(rel):
    righe = leggi_csv(rel)
    if not righe:
        return []
    testa = righe[0]
    return [dict(zip(testa, r + [""] * (len(testa) - len(r)))) for r in righe[1:]]


def scrivi_csv(rel, righe):
    p = percorso(rel)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8", newline="") as f:
        csv.writer(f).writerows(righe)


def scrivi_tabella(rel, colonne, righe):
    scrivi_csv(rel, [colonne] + [[str(r.get(c, "")) for c in colonne] for r in righe])


def leggi_json(rel, vuoto=None):
    try:
        with open(percorso(rel), encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return vuoto


def scrivi_json(rel, dati):
    p = percorso(rel)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        json.dump(dati, f, ensure_ascii=False, indent=1)


def nome_file(testo):
    """Il nome di un comune come pezzo di nome di file: Sant'Angelo Lodigiano diventa SantAngeloLodigiano."""
    t = unicodedata.normalize("NFKD", testo).encode("ascii", "ignore").decode()
    return "".join(p[:1].upper() + p[1:] for p in re.split(r"[^A-Za-z0-9]+", t) if p) or "Comune"


def git(*a):
    return subprocess.run(["git", "-C", RADICE, *a], capture_output=True, text=True)


def salva(scrivi, messaggio):
    """scrivi() fa le scritture sull'ultima versione dei dati; poi si carica su GitHub, fino a 10 giri."""
    for n in range(10):
        git("fetch", "-q", "origin", "main")
        git("reset", "-q", "--hard", "origin/main")
        scrivi()
        git("add", "-A", ".")
        if not git("status", "--porcelain").stdout.strip():
            return True
        git("-c", "user.name=DepthX Ricerca 1.1", "-c", "user.email=outbound@depthxlabs.com", "commit", "-q", "-m", messaggio)
        if git("push", "-q", "origin", "HEAD:main").returncode == 0:
            return True
        time.sleep(2 + 3 * n)
    print("ATTENZIONE: dati non caricati su GitHub dopo 10 giri")
    return False


COLONNE_RICERCHE = ["Codice", "Tipi", "Obiettivo", "Dal", "Partenza", "Latitudine", "Longitudine", "RaggioKm", "Stato", "Raggiunti", "Giri", "Aggiornato"]

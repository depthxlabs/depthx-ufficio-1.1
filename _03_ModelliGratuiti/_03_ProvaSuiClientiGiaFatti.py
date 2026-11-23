"""PROVA DEI MODELLI GRATUITI SUI CLIENTI GIÀ FATTI DA CLAUDE, Linea 1.1 Outbound Websites.

Per ogni cliente in dati/_05_ProveDeiModelli/<idCliente> (riconoscimento, recensioni, rapporto e dati del CRM fatti con Claude):
1. scarica da Drive fino a FOTO_PER_CLIENTE foto valide e le riconosce sulla macchina; conta in quante la categoria è uguale a quella di Claude;
2. rifà il rapporto di unicità con il modello gratuito e lo mette accanto a quello di Claude.
L'esito va in dati/_05_ProveDeiModelli/<idCliente>/_02_EsitoDellaProva.json (archivio privato).
Nei registri pubblici del workflow si stampano solo numeri: nessun nome, testo o dato dei clienti.
"""
import glob, json, os, sys, time, collections
import requests
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import importlib
R = importlib.import_module("_01_RiconoscimentoDelleFotoSullaMacchina")
U = importlib.import_module("_02_RapportoDiUnicitaConModelloGratuito")

DATI = os.environ.get("DATI_RICERCA", "dati")
FOTO_PER_CLIENTE = int(os.environ.get("FOTO_PER_CLIENTE", "90"))
CARTELLA_FOTO = "foto_della_prova"


def leggi(percorso, vuoto=None):
    try:
        with open(percorso, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return vuoto


def accesso_drive():
    t = json.loads(os.environ["MOTORE_DRIVE_TOKEN"])
    r = requests.post(t.get("token_uri") or "https://oauth2.googleapis.com/token", timeout=60,
                      data={"client_id": t["client_id"], "client_secret": t["client_secret"], "refresh_token": t["refresh_token"], "grant_type": "refresh_token"})
    r.raise_for_status()
    return r.json()["access_token"]


def scarica(accesso, identita, percorso):
    r = requests.get(f"https://www.googleapis.com/drive/v3/files/{identita}?alt=media", headers={"Authorization": "Bearer " + accesso}, timeout=120)
    if r.status_code != 200:
        return False
    with open(percorso, "wb") as f:
        f.write(r.content)
    return True


def main():
    os.makedirs(CARTELLA_FOTO, exist_ok=True)
    riconoscimento, accesso = R.Riconoscimento(), accesso_drive()
    for cartella in sorted(glob.glob(os.path.join(DATI, "_05_ProveDeiModelli", "*"))):
        idCliente = os.path.basename(cartella)
        claude = leggi(os.path.join(cartella, "_01_RiconoscimentoDelleFoto.json"), {})
        crm = leggi(os.path.join(cartella, "_01_DatiDalCrm.json"), {})
        recensioni = (leggi(os.path.join(cartella, "_01_RecensioniGoogle.json"), {}) or {}).get("recensioni", [])
        rapportoClaude = leggi(os.path.join(cartella, "_05_RapportoDiUnicita.json"), {})
        # foto: un campione distribuito su tutte le valide, con la categoria data da Claude
        valide = [v for v in claude.get("valide", []) if v.get("id") and v.get("categoria")]
        passo = max(1, len(valide) // FOTO_PER_CLIENTE)
        campione = valide[::passo][:FOTO_PER_CLIENTE]
        inizio, percorsi, categorieClaude = time.time(), [], []
        for n, v in enumerate(campione):
            p = os.path.join(CARTELLA_FOTO, f"{idCliente}_{n:03d}.jpg")
            if scarica(accesso, v["id"], p):
                percorsi.append(p); categorieClaude.append(v["categoria"])
        scaricamento = round(time.time() - inizio, 1)
        inizio = time.time()
        categorieMacchina = riconoscimento.categorie(percorsi) if percorsi else []
        uguali = sum(1 for a, b in zip(categorieClaude, categorieMacchina) if a == b)
        diverse = collections.Counter(f"{a} -> {b}" for a, b in zip(categorieClaude, categorieMacchina) if a != b)
        foto = {"fotoConfrontate": len(percorsi), "uguali": uguali, "percentualeUguali": round(100 * uguali / len(percorsi), 1) if percorsi else 0,
                "secondiDiScaricamento": scaricamento, "secondiDiRiconoscimento": round(time.time() - inizio, 1),
                "categorieClaude": collections.Counter(categorieClaude), "categorieMacchina": collections.Counter(categorieMacchina),
                "differenzePiuFrequenti": diverse.most_common(10)}
        try:
            gratuito = U.rapporto(crm.get("Nome commerciale") or crm.get("nome") or idCliente, "struttura ricettiva", crm, recensioni)
        except Exception as e:
            gratuito = {"codiceHttp": 0, "settori": {}, "settoriScartatiPerCitazioneNonTrovata": [], "secondi": 0, "limiti": [], "errore": type(e).__name__}
        esito = {"idCliente": idCliente, "foto": foto,
                 "rapporto": {"gratuito": gratuito, "claude": {"sintesi": rapportoClaude.get("sintesi", ""), "settori": rapportoClaude.get("settori", {})}}}
        with open(os.path.join(cartella, "_02_EsitoDellaProva.json"), "w", encoding="utf-8") as f:
            json.dump(esito, f, ensure_ascii=False, indent=1)
        # nel registro pubblico solo numeri
        print(f"cliente {list(sorted(glob.glob(os.path.join(DATI, '_05_ProveDeiModelli', '*')))).index(cartella) + 1}: "
              f"foto {len(percorsi)}, uguali a Claude {foto['percentualeUguali']}%, riconoscimento {foto['secondiDiRiconoscimento']} s; "
              f"rapporto HTTP {gratuito['codiceHttp']}, settori validi {len(gratuito['settori'])}, scartati {len(gratuito['settoriScartatiPerCitazioneNonTrovata'])}, "
              f"{gratuito['secondi']} s, limiti {gratuito['limiti']}")


if __name__ == "__main__":
    main()

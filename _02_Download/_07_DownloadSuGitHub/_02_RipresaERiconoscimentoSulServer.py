"""Ripresa dei risultati del download su GitHub e riconoscimento sul server, Linea 1.1 (dal 23/11/2026).

1. Legge le righe del registro scritte dai motori su GitHub (_04_Download/Esiti/<codice>/GruppoN.jsonl nel repository dei dati)
   e le rimette nel registro del motore del server: lo stato dei clienti si aggiorna come se avesse scaricato il server.
2. Per ogni cliente scaricato ("DA RICONOSCERE") fa sul server il riconoscimento delle foto e il rapporto di unicità con Claude,
   con i comandi del motore (--soloFoto e --unicita), più clienti insieme.
3. Chiude il cliente: GO se il riconoscimento è GO, altrimenti NOTGO con il motivo; scrive la bolla con tutto il materiale.
   Solo da GO la fabbrica vede il cliente.

Uso:  python -B _02_RipresaERiconoscimentoSulServer.py [--insieme 4]
"""

import sys

sys.dont_write_bytecode = True

import argparse
import glob
import json
import os
import re
import subprocess
from multiprocessing.dummy import Pool

MOTORE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
COORDINATORE = os.path.join(MOTORE, "_01_StrumentiDelMotore", "_04_CoordinatoreDelMotore")
sys.path.insert(0, COORDINATORE)
sys.path.insert(0, os.path.join(MOTORE, "_06_CaricamentoSuDrive"))
import _02_PercorsiChiaviEFunzioniComuni as comune  # noqa: E402
import _03_RegistroDegliEventiEDelloStato as registro  # noqa: E402
import _03_BollaDelClienteDopoIlDownload as bolla  # noqa: E402

DATI = r"C:\_02_DepthXSoftware\_06_DatiDownload1.1DaGitHub"  # copia del download, separata da quella della ricerca
RIPORTATI = os.path.join(comune.CARTELLA_DEL_REGISTRO, "_06_EsitiDaGitHubRiportati.json")
TIPI_DEL_CLIENTE = ("inizio_cliente", "passo", "fine_cliente", "errore")
STATO_DELLA_RACCOLTA = "_01_RaccoltaMateriale/_10_IlRestoDeiDati/_02_StatoDellaRaccolta.json"


def riprendiGliEsiti():
    subprocess.run(["git", "-C", DATI, "fetch", "-q", "origin", "main"], capture_output=True)
    subprocess.run(["git", "-C", DATI, "reset", "-q", "--hard", "origin/main"], capture_output=True)
    riportati = comune.leggiJson(RIPORTATI, {}) or {}
    nuovi = 0
    for file in sorted(glob.glob(os.path.join(DATI, "_04_Download", "Esiti", "*", "*.jsonl"))):
        chiave = os.path.relpath(file, DATI).replace("\\", "/")
        righe = [r for r in open(file, encoding="utf-8").read().splitlines() if r.strip()]
        for riga in righe[riportati.get(chiave, 0):]:
            try:
                voce = json.loads(riga)
            except ValueError:
                continue
            if voce.get("tipo") in TIPI_DEL_CLIENTE:
                voce["daGitHub"] = chiave.split("/")[2]
                registro.riportaEvento(voce)
                nuovi += 1
        riportati[chiave] = len(righe)
    comune.scriviJsonSulDisco(RIPORTATI, riportati)
    return nuovi


def idDellaCartella(link):
    trovato = re.search(r"/folders/([A-Za-z0-9_-]+)", str(link or ""))
    return trovato.group(1) if trovato else ""


def riconosciEChiudi(voce):
    idCliente, cliente = voce
    industria = next((v for v in comune.TUTTI_I_FOGLI if v["cartellaDrive"] == cliente.get("industria")), None)
    if not industria:
        return idCliente, "NOTGO: blocco del CRM non trovato"
    python = comune.PYTHON_DEL_MOTORE
    script = os.path.join(COORDINATORE, "_01_CoordinatoreELavoratoriDelMotore.py")
    for modo in ("--soloFoto", "--unicita"):
        subprocess.run([python, "-B", script, modo, "--industria", industria["numero"], "--clienti", idCliente],
                       capture_output=True, text=True, encoding="utf-8", errors="ignore", timeout=1800, cwd=COORDINATORE,
                       creationflags=comune.SENZA_FINESTRA)
    idDrive = idDellaCartella(cliente.get("cartellaDrive"))
    raccolta = bolla.leggi(idDrive, STATO_DELLA_RACCOLTA) or {}
    riconoscimento = (raccolta.get("passi") or {}).get("Riconoscimento delle foto") or {}
    esito = "GO" if riconoscimento.get("esito") == "GO" else "NOTGO"
    motivo = cliente.get("motivo", "") if esito == "GO" else f"Riconoscimento delle foto: {riconoscimento.get('motivo') or 'non riuscito sul server'}"
    registro.evento("fine_cliente", industria=cliente.get("industria"), idCliente=idCliente, esito=esito, motivo=motivo, cartellaDrive=cliente.get("cartellaDrive"))
    if esito == "GO":
        bolla.scriviLaBolla(idCliente, idDrive, cliente.get("nome", ""), bolla.materialeDalRiepilogo({**raccolta, "esito": "GO", "motivo": motivo}))
    return idCliente, esito


def codeFinite():
    """I codici delle code il cui giro su GitHub è finito (riuscito o no)."""
    esito = subprocess.run(["gh", "run", "list", "-R", "depthxlabs/depthx-ufficio-1.1", "-w", "_02_DownloadClienti.yml", "-L", "30",
                            "--json", "displayTitle,status"], capture_output=True, text=True, encoding="utf-8")
    try:
        giri = json.loads(esito.stdout or "[]")
    except ValueError:
        return set()
    attivi = {g["displayTitle"] for g in giri if g["status"] != "completed"}
    finite = {g["displayTitle"] for g in giri if g["status"] == "completed"} - attivi
    numeri = [int(m.group(1)) for g in giri for m in [re.match(r"Download(\d+)$", g["displayTitle"])] if m]
    if numeri:  # una coda più vecchia dell'ultima lanciata e senza alcun giro non è mai partita
        finite |= {f"Download{n:03d}" for n in range(1, max(numeri))} - {g["displayTitle"] for g in giri}
    return finite


def rimettiDaScaricare():
    """Un cliente rimasto "IN CODA SU GITHUB" dopo la fine del giro della sua coda non ha avuto risultato: torna da scaricare."""
    finite, rimessi = codeFinite(), 0
    for idCliente, voce in registro.leggiStato().get("clienti", {}).items():
        codice = (re.search(r"(Download\d+)", str(voce.get("motivo", ""))) or [None, None])[1]
        if voce.get("esito") == "IN CODA SU GITHUB" and codice in finite:
            registro.evento("fine_cliente", industria=voce.get("industria"), idCliente=idCliente, esito="NOTGO",
                            motivo=f"{codice}: il giro su GitHub è finito senza risultato per questo cliente, da riprendere")
            rimessi += 1
    return rimessi


def main():
    a = argparse.ArgumentParser()
    a.add_argument("--insieme", type=int, default=4)
    p = a.parse_args()
    nuovi = riprendiGliEsiti()
    print(json.dumps({"rimessiDaScaricare": rimettiDaScaricare()}), flush=True)
    comune.aggiornaIBlocchiDelCrm()  # una volta sola: i clienti si lavorano in parallelo
    clienti = [(k, v) for k, v in registro.leggiStato().get("clienti", {}).items() if v.get("esito") == "DA RICONOSCERE"]
    print(json.dumps({"righeRiportate": nuovi, "daRiconoscere": len(clienti)}), flush=True)
    with Pool(p.insieme) as gruppo:
        for idCliente, esito in gruppo.imap_unordered(riconosciEChiudi, clienti):
            print(idCliente, esito, flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())

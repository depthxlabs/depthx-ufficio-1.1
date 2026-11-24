"""Coda e partenza del download su GitHub, Linea 1.1 (dal 23/11/2026).

Sceglie i clienti da scaricare (S2 e S3 prima, poi S1), a lotti di 3 dello stesso blocco, divisi in 20 gruppi,
e scrive la coda nel repository privato dei dati (_04_Download/Coda/DownloadNNN.json) con le righe del CRM di quei clienti.
Poi fa partire il workflow "Download clienti" su GitHub con il codice della coda.
Un cliente in coda è segnato nel registro del motore come "IN CODA SU GITHUB", così il motore del server non lo riprende.

Uso:  python -B _01_CodaEPartenzaSuGitHub.py --lotti 40
"""

import sys

sys.dont_write_bytecode = True

import argparse
import json
import os
import re
import subprocess

MOTORE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(MOTORE, "_01_StrumentiDelMotore", "_04_CoordinatoreDelMotore"))
import _02_PercorsiChiaviEFunzioniComuni as comune  # noqa: E402
import _03_RegistroDegliEventiEDelloStato as registro  # noqa: E402
import _02_ClientiDalCrmASezioni as crm  # noqa: E402

DATI = r"C:\_02_DepthXSoftware\_06_DatiDownload1.1DaGitHub"  # copia del download, separata da quella della ricerca
REPO_CODICE = "depthxlabs/depthx-ufficio-1.1"
GRUPPI = 20
CLIENTI_PER_LOTTO = 3
CHIUSI = ("GO", "ESCLUSO", "DA RICONOSCERE", "IN CODA SU GITHUB")
ORDINE_DELLE_SEZIONI = ("[02]", "[03]", "[01]")


def git(*a):
    return subprocess.run(["git", "-C", DATI, *a], capture_output=True, text=True, encoding="utf-8")


def main():
    a = argparse.ArgumentParser()
    a.add_argument("--lotti", type=int, default=40)
    p = a.parse_args()
    comune.aggiornaIBlocchiDelCrm()
    stato = registro.leggiStato().get("clienti", {})
    lotti, fogli = [], {}
    for sezione in ORDINE_DELLE_SEZIONI:
        for voce in [v for v in comune.INDUSTRIE if v["sezione"].startswith(sezione)]:
            if len(lotti) >= p.lotti:
                break
            righe = crm.righeDelFoglio(voce["idCrm"])
            clienti = [c for c in crm.leggiClientiDelFoglio(voce)
                       if stato.get(c["idCliente"], {}).get("esito") not in CHIUSI and int(stato.get(c["idCliente"], {}).get("blocchi", 0) or 0) < 2]
            if not clienti:
                continue
            scelti = {c["idCliente"] for c in clienti[:(p.lotti - len(lotti)) * CLIENTI_PER_LOTTO]}
            fogli[voce["idCrm"]] = righe[:2] + [r for r in righe[2:] if r and str(r[0]).strip() in scelti]
            ordinati = [c["idCliente"] for c in clienti if c["idCliente"] in scelti]
            for k in range(0, len(ordinati), CLIENTI_PER_LOTTO):
                lotti.append({"industria": voce["numero"], "blocco": voce["nome"], "clienti": ordinati[k:k + CLIENTI_PER_LOTTO]})
    if not lotti:
        print("Nessun cliente da scaricare.")
        return 0
    gruppi = [lotti[k::GRUPPI] for k in range(min(GRUPPI, len(lotti)))]
    git("fetch", "-q", "origin", "main"); git("reset", "-q", "--hard", "origin/main")
    cartella = os.path.join(DATI, "_04_Download", "Coda")
    os.makedirs(cartella, exist_ok=True)
    numeri = [int(m.group(1)) for f in os.listdir(cartella) for m in [re.match(r"Download(\d+)\.json$", f)] if m]
    codice = f"Download{max(numeri + [0]) + 1:03d}"
    elenco = json.load(open(comune.FILE_DEI_FOGLI_DEL_CRM, encoding="utf-8"))
    with open(os.path.join(cartella, codice + ".json"), "w", encoding="utf-8") as f:
        json.dump({"codice": codice, "creata": comune.adesso(), "elenco": elenco, "fogli": fogli, "gruppi": gruppi}, f, ensure_ascii=False)
    git("add", "-A")
    git("-c", "user.name=DepthX Centro Gestione", "-c", "user.email=outbound@depthxlabs.com", "commit", "-q", "-m", f"{codice}: coda del download")
    # la ricerca carica dati di continuo: si riprende l'ultima versione e si carica subito, fino a 30 giri
    for giro in range(30):
        if git("pull", "-q", "--rebase", "origin", "main").returncode == 0 and git("push", "-q", "origin", "HEAD:main").returncode == 0:
            break
    else:
        print("NOTGO: coda non caricata su GitHub dopo 30 giri"); return 1
    for lotto in lotti:
        for idCliente in lotto["clienti"]:
            registro.evento("fine_cliente", industria=next(v["cartellaDrive"] for v in comune.INDUSTRIE if v["numero"] == lotto["industria"]),
                            idCliente=idCliente, esito="IN CODA SU GITHUB", motivo=f"in coda su GitHub: {codice}")
    partenza = subprocess.run(["gh", "workflow", "run", "_02_DownloadClienti.yml", "-R", REPO_CODICE, "-f", f"codice={codice}"],
                              capture_output=True, text=True)
    print(json.dumps({"codice": codice, "lotti": len(lotti), "clienti": sum(len(l["clienti"]) for l in lotti), "gruppi": len(gruppi),
                      "partito": partenza.returncode == 0}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())

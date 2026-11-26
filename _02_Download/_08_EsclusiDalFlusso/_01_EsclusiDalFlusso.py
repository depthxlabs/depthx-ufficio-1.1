"""Esclusi dal flusso, Linea 1.1 (dal 23/11/2026).

Un cliente esce dal flusso quando:
  1. il motore di download lo ha escluso per materiale insufficiente (meno di 6 recensioni);
  2. la fabbrica lo ha escluso per materiale insufficiente (troppo poche foto per la galleria);
  3. nel CRM non ha né un'email né un profilo Instagram: non si può contattare.
Per ognuno l'automazione: sposta la cartella del cliente su Drive nel cestino, sposta la sua riga del CRM negli esclusi
([99] CRM Clienti Esclusi/[03] Esclusi dal flusso/[01] EsclusiDalFlusso su Drive, con il motivo e la data), toglie la sua demo
da approvazione e pubblicazione.
  --prova    elenca soltanto cosa farebbe, con i numeri (nessuna modifica)
"""

import sys

sys.dont_write_bytecode = True

import argparse
import collections
import datetime
import glob
import json
import os
import re
import shutil
import subprocess

MOTORE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, r"C:\_02_DepthXSoftware\_01_CentroGestioneDepthX\V1.0(161126_1124)\_01_StrumentiDiLavoroPerIlServer\_02_ServerAutonomiDelCentroGestione\_01_UfficiLinea1Produzione\_10_ServerRicercaClienti")
import _00_CrmSuGoogleSheets as CRM_SU_DRIVE  # noqa: E402  il CRM sta soltanto su Drive, in Fogli Google
STATO = os.path.join(MOTORE, "_01_StrumentiDelMotore", "_05_RegistroEStatoDelMotore", "stato.json")
CARTELLE = os.path.join(MOTORE, "_06_CaricamentoSuDrive", "_02_CartelleDeiClientiSuDrive.json")
FABBRICA = r"C:\_01_DepthX\_01_Linea1_ProductionDepartement\_01_Linea_1.1_OUTBOUND_WEBSITES\_05_1.1_D_FabbricaProduzioneDemoDelSito"
EVENTI = os.path.join(FABBRICA, "_01_StrumentiDellaFabbrica", "_04_RegistroLogDellaFabbrica", "_02_RegistroProduzione", "_01_EventiDellaProduzione")
DEMO = os.path.join(FABBRICA, "_01_StrumentiDellaFabbrica", "_09_DemoInApprovazione")
ESCLUSI = "[99] CRM Clienti Esclusi/[03] Esclusi dal flusso/[01] EsclusiDalFlusso"
ESITO = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_03_EsitoDegliEsclusi.json")
RCLONE = r"C:\_02_DepthXSoftware\_02_RCloneDepthX\rclone.exe"
SCRITTURA_DRIVE = r"C:\_02_DepthXSoftware\_02_RCloneDepthX\rclone_scrittura.conf"
AREA_1B = "1Lf_1OndQT_30Doj3HE8XMfaMKauQfXHZ"
PUBBLICAZIONE = r"C:\_02_DepthXSoftware\_01_CentroGestioneDepthX\V1.0(161126_1124)\_01_StrumentiDiLavoroPerIlServer\_02_ServerAutonomiDelCentroGestione\_01_UfficiLinea1Produzione\_08_ServerScadenzaDemo12GiorniECancellazione72Ore\_01_RegistroDelleDemoPubblicate.py"
PRIMA_RIGA_CLIENTI = 3


def clientiDelCrm():
    """I clienti delle sezioni S1, S2, S3 e S4 dai Fogli Google del CRM su Drive: per ognuno il foglio e il numero della riga."""
    from concurrent.futures import ThreadPoolExecutor
    fogli = [f for f in CRM_SU_DRIVE.fogli() if re.match(r"^\[0[1-4]\]", f["percorso"])]
    with ThreadPoolExecutor(max_workers=6) as insieme:
        letti = list(insieme.map(lambda f: CRM_SU_DRIVE.leggi(f["id"]), fogli))
    righe = {}
    for f, tutte in zip(fogli, letti):
        if len(tutte) < 3:
            continue
        colonne = tutte[1]
        for numero, x in enumerate(tutte[2:], PRIMA_RIGA_CLIENTI):
            if x and x[0].strip():
                righe[x[0].strip()] = {"foglio": f["id"], "riga": numero, **{c: (x[i] if i < len(x) else "") for i, c in enumerate(colonne) if c}}
    return righe


def main():
    a = argparse.ArgumentParser()
    a.add_argument("--prova", action="store_true")
    a.add_argument("--ripresa", action="store_true", help="stato del motore e Drive già fatti: solo pubblicazione, approvazione e CRM")
    p = a.parse_args()
    crm = clientiDelCrm()
    stato = (json.load(open(STATO, encoding="utf-8")) or {}).get("clienti", {})
    cartelle = json.load(open(CARTELLE, encoding="utf-8"))
    motivi = {}
    for idCliente, v in stato.items():
        if v.get("esito") == "ESCLUSO":
            motivo = str(v.get("motivo", ""))
            motivi[idCliente] = motivo[len("escluso dal flusso: "):] if motivo.startswith("escluso dal flusso: ") else "download: " + motivo[:120]
    for f in glob.glob(os.path.join(EVENTI, "**", "_01_EventiDelGiorno.jsonl"), recursive=True):
        for riga in open(f, encoding="utf-8"):
            try:
                e = json.loads(riga)
            except ValueError:
                continue
            if e.get("tipo") == "fine_cliente" and "materiale insufficiente" in str(e.get("motivo", "")).lower():
                motivi.setdefault(e["idCliente"], "fabbrica: materiale insufficiente, troppo poche foto per la galleria")
    for idCliente, r in crm.items():
        email = re.findall(r"[\w.+-]+@[\w-]+\.[\w.-]+", r.get("Tutti i contatti Email", ""))
        instagram = re.match(r"^https?://(www\.)?instagram\.com/", r.get("Ha Instagram?", ""), re.I)
        if not email and not instagram:
            motivi.setdefault(idCliente, "senza canale: né email né Instagram nel CRM")
    demo = set(n for n in os.listdir(DEMO) if re.match(r"^S\d_", n))
    piano = []
    for idCliente, motivo in sorted(motivi.items()):
        piano.append({"idCliente": idCliente, "motivo": motivo, "rigaNelCrm": idCliente in crm, "cartellaSuDrive": idCliente in cartelle, "demo": idCliente in demo})
    conta = collections.Counter(v["motivo"].split(":")[0] for v in piano)
    print(json.dumps({"esclusi": len(piano), "perMotivo": dict(conta), "conRigaNelCrm": sum(v["rigaNelCrm"] for v in piano),
                      "conCartellaSuDrive": sum(v["cartellaSuDrive"] for v in piano), "conDemo": sum(v["demo"] for v in piano),
                      "perSezione": dict(collections.Counter(v["idCliente"][:2] for v in piano))}, ensure_ascii=False))
    if p.prova:
        with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "_02_PianoDegliEsclusi.json"), "w", encoding="utf-8") as f:
            json.dump(piano, f, ensure_ascii=False, indent=1)
        return 0
    return esegui(piano, crm, cartelle, p.ripresa)


def nelCestinoDiDrive(voce):
    sys.path.insert(0, os.path.join(MOTORE, "_01_StrumentiDelMotore", "_04_CoordinatoreDelMotore"))
    import _02_PercorsiChiaviEFunzioniComuni as comune
    percorso = "/".join([comune.SEZIONE_SU_DRIVE.get(voce["sezione"], voce["sezione"]), voce["tipo"], voce["blocco"], voce["cartella"]])
    esito = subprocess.run([RCLONE, "purge", "gdrivescrittura:" + percorso, "--drive-root-folder-id", AREA_1B, "--config", SCRITTURA_DRIVE],
                           capture_output=True, text=True, encoding="utf-8", errors="ignore", timeout=600)
    return "nel cestino di Drive" if esito.returncode == 0 else "Drive: " + (esito.stderr.strip().splitlines() or ["errore"])[-1][:160]


def nelCestinoDiWindows(percorsi):
    """Più cartelle insieme nel cestino di Windows (SHFileOperation con annullamento)."""
    import ctypes
    from ctypes import wintypes

    class Operazione(ctypes.Structure):
        _fields_ = [("hwnd", wintypes.HWND), ("wFunc", wintypes.UINT), ("pFrom", wintypes.LPCWSTR), ("pTo", wintypes.LPCWSTR),
                    ("fFlags", ctypes.c_ushort), ("fAnyOperationsAborted", wintypes.BOOL), ("hNameMappings", ctypes.c_void_p),
                    ("lpszProgressTitle", wintypes.LPCWSTR)]
    if not percorsi:
        return 0
    operazione = Operazione(None, 3, "\0".join(percorsi) + "\0\0", None, 0x40 | 0x10 | 0x400 | 0x4, False, None, None)
    return ctypes.windll.shell32.SHFileOperationW(ctypes.byref(operazione))


def demoPubblicata(idCliente):
    try:
        link = json.load(open(os.path.join(DEMO, idCliente, "scheda.json"), encoding="utf-8")).get("link", "")
    except (OSError, ValueError):
        return ""
    return link.rstrip("/").rsplit("/", 1)[-1] if "/demo/" in link else ""


def toltaDaPubblicazione(nome, python):
    if not nome:
        return "nessuna demo pubblicata"
    ambiente = {**os.environ, "APPDATA": r"C:\Users\Administrator\AppData\Roaming"}
    try:
        esito = subprocess.run([python, "-B", PUBBLICAZIONE, "--rimuovi", nome], capture_output=True, text=True, encoding="utf-8",
                               errors="ignore", timeout=120, env=ambiente)
    except subprocess.TimeoutExpired:
        return "pubblicazione: nessuna risposta in 2 minuti"
    return "tolta da depthxlabs.com/demo" if esito.returncode == 0 else "pubblicazione: " + ((esito.stdout + esito.stderr).strip().splitlines() or ["errore"])[-1][:160]


def righeNegliEsclusi(piano, crm):
    """Le righe dei clienti esclusi passano dal loro foglio del CRM al foglio degli esclusi, con il motivo e la data."""
    voci = [v for v in piano if v["idCliente"] in crm]
    if not voci:
        return 0
    esclusi = next((f for f in CRM_SU_DRIVE.fogli() if f["percorso"] == ESCLUSI), None)
    if not esclusi:
        raise RuntimeError("su Drive manca il foglio degli esclusi: " + ESCLUSI)
    tutte = CRM_SU_DRIVE.leggi(esclusi["id"])
    colonneE = tutte[1] if len(tutte) > 1 else []
    rigaE = PRIMA_RIGA_CLIENTI
    while rigaE - 1 < len(tutte) and tutte[rigaE - 1] and tutte[rigaE - 1][0].strip():
        rigaE += 1
    oggi = datetime.date.today().isoformat()
    nuove = []
    for v in voci:
        riga = crm[v["idCliente"]]
        valori = {**riga, "Motivo esclusione": v["motivo"], "Data esclusione": oggi}
        nuove.append([str(valori.get(c, "")) for c in colonneE])
    CRM_SU_DRIVE.scriviRighe(esclusi["id"], rigaE, nuove)
    perFoglio = collections.defaultdict(list)
    for v in voci:
        perFoglio[crm[v["idCliente"]]["foglio"]].append(crm[v["idCliente"]]["riga"])
    for foglio, numeri in perFoglio.items():
        CRM_SU_DRIVE.cancellaRighe(foglio, numeri)
    return len(voci)


def esegui(piano, crm, cartelle, ripresa=False):
    from multiprocessing.dummy import Pool
    sys.path.insert(0, os.path.join(MOTORE, "_01_StrumentiDelMotore", "_04_CoordinatoreDelMotore"))
    import _03_RegistroDegliEventiEDelloStato as registro
    python = glob.glob(os.path.join(glob.escape(FABBRICA), "_01_StrumentiDellaFabbrica", "*", "Scripts", "python.exe"))[0]
    esito = {v["idCliente"]: {"motivo": v["motivo"]} for v in piano}
    statoMotore = (json.load(open(STATO, encoding="utf-8")) or {}).get("clienti", {})
    if not ripresa:
        for v in piano:  # il motore e la fabbrica non lo prendono più
            registro.evento("fine_cliente", industria=(statoMotore.get(v["idCliente"]) or {}).get("industria"), idCliente=v["idCliente"],
                            esito="ESCLUSO", motivo="escluso dal flusso: " + v["motivo"])
        print("stato del motore: ESCLUSO", flush=True)
        with Pool(8) as gruppo:
            for idCliente, testo in gruppo.imap_unordered(lambda v: (v["idCliente"], nelCestinoDiDrive(cartelle[v["idCliente"]])),
                                                          [v for v in piano if v["cartellaSuDrive"]]):
                esito[idCliente]["drive"] = testo
        print("Drive fatto", flush=True)
    for v in piano:  # una alla volta: più rimozioni insieme si bloccano a vicenda
        if v["demo"]:
            esito[v["idCliente"]]["pubblicazione"] = toltaDaPubblicazione(demoPubblicata(v["idCliente"]), python)
    print("pubblicazione fatta", flush=True)
    cartelleDemo = [os.path.join(DEMO, v["idCliente"]) for v in piano if v["demo"]]
    for i in range(0, len(cartelleDemo), 100):
        nelCestinoDiWindows(cartelleDemo[i:i + 100])
    for v in piano:
        if v["demo"]:
            esito[v["idCliente"]]["approvazione"] = "ancora nella cartella" if os.path.exists(os.path.join(DEMO, v["idCliente"])) else "nel cestino di Windows"
    spostate = righeNegliEsclusi(piano, crm)
    with open(ESITO, "w", encoding="utf-8") as f:
        json.dump(esito, f, ensure_ascii=False, indent=1)
    conta = lambda chiave, testo: sum(1 for x in esito.values() if x.get(chiave, "").startswith(testo))
    altri = collections.Counter(x[k][:70] for x in esito.values() for k in ("drive", "pubblicazione", "approvazione")
                                if x.get(k) and not re.match(r"nel cestino|tolta|nessuna", x[k]))
    print(json.dumps({"esclusi": len(piano), "righeSpostateNegliEsclusi": spostate, "cartelleNelCestinoDiDrive": conta("drive", "nel cestino"),
                      "demoTolteDaPubblicazione": conta("pubblicazione", "tolta"), "demoNelCestinoDiWindows": conta("approvazione", "nel cestino"),
                      "altriEsiti": altri.most_common(8)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())

"""Le uscite automatiche dal CRM, su GitHub: i clienti esclusi che hanno ancora la riga nel CRM escono con righe e materiale.

Motivi, gli stessi di _01_EsclusiDalFlusso.py: escluso dal motore di download (per esempio meno di 6 recensioni con il testo),
escluso dalla fabbrica per materiale insufficiente, nessuna email e nessun Instagram nel CRM.
Un cliente con una demo in approvazione, approvata, in coda o inviata non esce mai; un NOTGO non fa uscire nessuno.
Per ognuno: la riga si cancella dal CRM (non va negli esclusi), la cartella su Drive va nel cestino di Drive, la demo esce da
depthxlabs.com/demo (R2 di Cloudflare), l'evento ESCLUSO va nell'archivio privato. La cartella di approvazione sul server
non si tocca da qui: l'esito la segna "sul server".

Lo lancia il workflow _07_UsciteAutomaticheDalCrm.yml ogni 15 minuti. I percorsi arrivano dalle variabili:
  USCITE_DATI        la cartella _08_Fabbrica dell'archivio privato (stato.json, _02_CartelleDeiClientiSuDrive.json, esiti, uscite)
  USCITE_FABBRICA    la cartella della fabbrica nel codice (per togliere la demo da R2)
  USCITE_RCLONE, USCITE_RCLONE_CONFIGURAZIONE   rclone e la sua configurazione di scrittura (sezione gdrivescrittura)
  --prova    elenca soltanto chi uscirebbe e perché (nessuna modifica)
Stampa sempre un JSON.
"""

import collections
import datetime
import glob
import json
import os
import re
import sys

sys.dont_write_bytecode = True
CARTELLA = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, CARTELLA)
import _01_EsclusiDalFlusso as E  # noqa: E402

DATI = os.environ.get("USCITE_DATI", "")
STATO = os.path.join(DATI, "stato.json")
CARTELLE = os.path.join(DATI, "_02_CartelleDeiClientiSuDrive.json")
EVENTI_DELLA_FABBRICA = os.path.join(DATI, "esiti")
USCITE = os.path.join(DATI, "uscite")
EVENTI_DELLE_USCITE = os.path.join(USCITE, "_01_EventiDelleUscite.jsonl")
ESITO = os.path.join(USCITE, "_08_EsitoDelleUsciteAutomatiche.json")
PIANO = os.path.join(USCITE, "_02_PianoDellUltimoGiro.json")

STATI_PROTETTI = {"Demo da approvare", "Demo approvata", "Email in coda", "Inviato via email", "Inviato via Instagram",
                  "Inviato (presentazione spedita)", "Demo pubblicata, in controllo", "Demo in correzione", "Demo in produzione"}
ESITI_CHE_NON_ESCONO = ("NOTGO", "IN CORSO", "IN CODA SU GITHUB", "DA RICONOSCERE")


def adesso():
    return datetime.datetime.now().astimezone().isoformat(timespec="seconds")


def motiviDegliEsclusi(crm, stato):
    """Il motivo di ogni cliente da togliere, solo tra quelli che hanno ancora la riga nel CRM e nessuno stato protetto."""
    motivi = {}
    for idCliente, voce in stato.items():
        if idCliente in crm and voce.get("esito") == "ESCLUSO":
            motivo = str(voce.get("motivo", ""))
            motivi[idCliente] = motivo[len("escluso dal flusso: "):] if motivo.startswith("escluso dal flusso: ") else "download: " + motivo[:120]
    for file in glob.glob(os.path.join(EVENTI_DELLA_FABBRICA, "**", "_01_EventiDelGiorno.jsonl"), recursive=True):
        for riga in open(file, encoding="utf-8", errors="ignore"):
            try:
                evento = json.loads(riga)
            except ValueError:
                continue
            # solo la chiusura ESCLUSO della fabbrica: un NOTGO non fa uscire nessuno
            if (evento.get("tipo") == "fine_cliente" and evento.get("idCliente") in crm and evento.get("esito") == "ESCLUSO"
                    and "materiale insufficiente" in str(evento.get("motivo", "")).lower()):
                motivi.setdefault(evento["idCliente"], "fabbrica: " + str(evento.get("motivo", ""))[:120])
    for idCliente, riga in crm.items():
        email = re.findall(r"[\w.+-]+@[\w-]+\.[\w.-]+", riga.get("Tutti i contatti Email", ""))
        instagram = re.match(r"^https?://(www\.)?instagram\.com/", riga.get("Ha Instagram?", ""), re.I)
        if not email and not instagram:
            motivi.setdefault(idCliente, "senza canale: né email né Instagram nel CRM")
    return {idCliente: motivo for idCliente, motivo in motivi.items()
            if crm[idCliente].get("Stato Commerciale", "").strip() not in STATI_PROTETTI
            and (stato.get(idCliente) or {}).get("esito") not in ESITI_CHE_NON_ESCONO}


def nomeDellaDemo(riga):
    link = str(riga.get("Link demo", "") or "").split("?")[0].rstrip("/")
    return link.rsplit("/", 1)[-1] if "/demo/" in link else ""


def toltaDaR2(nome):
    if not nome:
        return "nessuna demo pubblicata"
    sys.path.insert(0, os.environ["USCITE_FABBRICA"])
    try:
        from _03_CicloDiProduzionePerOgniCliente._06_PubblicazioneSuDepthxlabsDemo._04_PubblicazioneDellaDemoSulLink._13_PubblicazioneSuR2 import (
            togliLaDemoDaR2)
        return f"tolta da depthxlabs.com/demo ({togliLaDemoDaR2(nome)} file)"
    except Exception as errore:
        return "pubblicazione: " + str(errore)[:160]


def soloCancellaLeRighe(piano, crm):
    """Le righe si cancellano dal loro Foglio Google del CRM: non vanno nel foglio degli esclusi."""
    perFoglio = collections.defaultdict(list)
    for voce in piano:
        perFoglio[crm[voce["idCliente"]]["foglio"]].append(crm[voce["idCliente"]]["riga"])
    return sum(E.CRM_SU_DRIVE.cancellaRighe(foglio, numeri) for foglio, numeri in perFoglio.items())


def esegui(piano, crm, cartelle, stato):
    from multiprocessing.dummy import Pool

    os.makedirs(USCITE, exist_ok=True)
    esito = {voce["idCliente"]: {"motivo": voce["motivo"], "quando": adesso()} for voce in piano}
    # l'evento ESCLUSO nell'archivio: la fabbrica su GitHub lo vede subito, il server lo riporta nel registro del motore
    with open(EVENTI_DELLE_USCITE, "a", encoding="utf-8") as file:
        for voce in piano:
            evento = {"ora": adesso(), "tipo": "fine_cliente", "industria": (stato.get(voce["idCliente"]) or {}).get("industria"),
                      "idCliente": voce["idCliente"], "esito": "ESCLUSO", "motivo": "escluso dal flusso: " + voce["motivo"]}
            evento = {chiave: valore for chiave, valore in evento.items() if valore is not None}
            file.write(json.dumps(evento, ensure_ascii=False) + "\n")
            cliente = stato.setdefault(voce["idCliente"], {"passi": {}})
            cliente.update({"esito": "ESCLUSO", "motivo": evento["motivo"], "concluso": evento["ora"]})
    tutto = json.load(open(STATO, encoding="utf-8-sig"))
    tutto["clienti"] = stato
    with open(STATO, "w", encoding="utf-8") as file:
        json.dump(tutto, file, ensure_ascii=False, indent=1)
    with Pool(8) as gruppo:
        for idCliente, testo in gruppo.imap_unordered(lambda v: (v["idCliente"], E.nelCestinoDiDrive(cartelle[v["idCliente"]])),
                                                      [v for v in piano if v["cartellaSuDrive"]]):
            esito[idCliente]["drive"] = testo
    for voce in piano:  # una alla volta: più rimozioni insieme si bloccano a vicenda
        if voce["demo"]:
            esito[voce["idCliente"]]["pubblicazione"] = toltaDaR2(voce["demo"])
            esito[voce["idCliente"]]["approvazione"] = "sul server: la cartella di approvazione, se c'è, resta sul server"
    righe = soloCancellaLeRighe(piano, crm)
    precedenti = {}
    try:
        precedenti = json.load(open(ESITO, encoding="utf-8"))
    except (OSError, ValueError):
        pass
    precedenti.update(esito)
    with open(ESITO, "w", encoding="utf-8") as file:
        json.dump(precedenti, file, ensure_ascii=False, indent=1)
    return righe


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    prova = "--prova" in sys.argv[1:]
    if not DATI or not os.path.isfile(STATO):
        print(json.dumps({"errore": "manca lo stato del download dell'archivio privato (variabile USCITE_DATI)"}, ensure_ascii=False))
        return 1
    E.CRM_SU_DRIVE.RCLONE = os.environ.get("USCITE_RCLONE", E.CRM_SU_DRIVE.RCLONE)
    E.CRM_SU_DRIVE.CONFIGURAZIONE = os.environ.get("USCITE_RCLONE_CONFIGURAZIONE", E.CRM_SU_DRIVE.CONFIGURAZIONE)
    E.RCLONE, E.SCRITTURA_DRIVE = E.CRM_SU_DRIVE.RCLONE, E.CRM_SU_DRIVE.CONFIGURAZIONE
    crm = E.clientiDelCrm()
    stato = (json.load(open(STATO, encoding="utf-8-sig")) or {}).get("clienti", {})
    motivi = motiviDegliEsclusi(crm, stato)
    cartelle = json.load(open(CARTELLE, encoding="utf-8-sig")) if os.path.isfile(CARTELLE) else {}
    piano = [{"idCliente": idCliente, "motivo": motivo, "cartellaSuDrive": idCliente in cartelle, "demo": nomeDellaDemo(crm[idCliente]),
              "statoCommerciale": crm[idCliente].get("Stato Commerciale", ""), "esitoDelDownload": (stato.get(idCliente) or {}).get("esito", "")}
             for idCliente, motivo in sorted(motivi.items())]
    protetti = sum(1 for riga in crm.values() if riga.get("Stato Commerciale", "").strip() in STATI_PROTETTI)
    # il registro di GitHub è pubblico: lì vanno solo i numeri, il piano con i codici va nell'archivio privato
    os.makedirs(USCITE, exist_ok=True)
    with open(PIANO, "w", encoding="utf-8") as file:
        json.dump({"quando": adesso(), "prova": prova, "piano": piano}, file, ensure_ascii=False, indent=1)
    riepilogo = {"prova": prova, "clientiNelCrm": len(crm), "conStatoProtetto": protetti, "daTogliere": len(piano),
                 "perMotivo": dict(collections.Counter(v["motivo"].split(":")[0] for v in piano)),
                 "conStatoProtettoNelPiano": sum(1 for v in piano if v["statoCommerciale"].strip() in STATI_PROTETTI),
                 "conNotgoNelPiano": sum(1 for v in piano if v["esitoDelDownload"] in ESITI_CHE_NON_ESCONO)}
    if not prova and piano:
        riepilogo["righeCancellate"] = esegui(piano, crm, cartelle, stato)
        riepilogo["tolti"] = len(piano)
    print(json.dumps(riepilogo, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())

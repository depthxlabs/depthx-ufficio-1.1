"""Le uscite automatiche dal CRM: i clienti esclusi che hanno ancora la riga nel CRM escono con righe e materiale cancellati.

Motivi, gli stessi di _01_EsclusiDalFlusso.py: escluso dal motore di download (per esempio meno di 6 recensioni con il testo),
escluso dalla fabbrica per materiale insufficiente, nessuna email e nessun Instagram nel CRM.
Per ognuno: la riga si cancella dal CRM (non va negli esclusi), la cartella su Drive va nel cestino di Drive, la demo esce da
depthxlabs.com/demo e la sua cartella di approvazione va nel cestino di Windows.
Lo lancia il server della ricerca ogni 5 minuti; se non c'è nessuno da togliere finisce subito. Stampa sempre un JSON.
"""

import collections
import glob
import json
import os
import re
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _01_EsclusiDalFlusso as E  # noqa: E402

ESITO = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_08_EsitoDelleUsciteAutomatiche.json")


def motiviDegliEsclusi(crm):
    """Il motivo di ogni cliente da togliere, solo tra quelli che hanno ancora la riga nel CRM."""
    stato = (json.load(open(E.STATO, encoding="utf-8")) or {}).get("clienti", {})
    motivi = {}
    for idCliente, voce in stato.items():
        if idCliente in crm and voce.get("esito") == "ESCLUSO":
            motivo = str(voce.get("motivo", ""))
            motivi[idCliente] = motivo[len("escluso dal flusso: "):] if motivo.startswith("escluso dal flusso: ") else "download: " + motivo[:120]
    for file in glob.glob(os.path.join(E.EVENTI, "**", "_01_EventiDelGiorno.jsonl"), recursive=True):
        for riga in open(file, encoding="utf-8", errors="ignore"):
            try:
                evento = json.loads(riga)
            except ValueError:
                continue
            if (evento.get("tipo") == "fine_cliente" and evento.get("idCliente") in crm
                    and "materiale insufficiente" in str(evento.get("motivo", "")).lower()):
                motivi.setdefault(evento["idCliente"], "fabbrica: " + str(evento.get("motivo", ""))[:120])
    for idCliente, riga in crm.items():
        email = re.findall(r"[\w.+-]+@[\w-]+\.[\w.-]+", riga.get("Tutti i contatti Email", ""))
        instagram = re.match(r"^https?://(www\.)?instagram\.com/", riga.get("Ha Instagram?", ""), re.I)
        if not email and not instagram:
            motivi.setdefault(idCliente, "senza canale: né email né Instagram nel CRM")
    # un cliente che ha già una demo in approvazione, approvata, in coda o inviata non esce mai in automatico
    return {idCliente: motivo for idCliente, motivo in motivi.items()
            if crm[idCliente].get("Stato Commerciale", "") not in STATI_PROTETTI}


STATI_PROTETTI = {"Demo da approvare", "Demo approvata", "Email in coda", "Inviato via email", "Inviato via Instagram",
                  "Demo pubblicata, in controllo", "Demo in correzione", "Demo in produzione"}


def soloCancellaLeRighe(piano, crm):
    """Le righe si cancellano dal loro Foglio Google del CRM: non vanno nel foglio degli esclusi."""
    perFoglio = collections.defaultdict(list)
    for voce in piano:
        perFoglio[crm[voce["idCliente"]]["foglio"]].append(crm[voce["idCliente"]]["riga"])
    return sum(E.CRM_SU_DRIVE.cancellaRighe(foglio, numeri) for foglio, numeri in perFoglio.items())


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    crm = E.clientiDelCrm()
    motivi = motiviDegliEsclusi(crm)
    if not motivi:
        print(json.dumps({"tolti": 0}))
        return 0
    cartelle = json.load(open(E.CARTELLE, encoding="utf-8"))
    demo = set(os.listdir(E.DEMO))
    piano = [{"idCliente": idCliente, "motivo": motivo, "rigaNelCrm": True, "cartellaSuDrive": idCliente in cartelle, "demo": idCliente in demo}
             for idCliente, motivo in sorted(motivi.items())]
    E.righeNegliEsclusi = soloCancellaLeRighe
    E.ESITO = ESITO
    # i messaggi dello strumento degli esclusi vanno sul canale degli errori: sull'uscita resta solo il JSON finale
    uscita, sys.stdout = sys.stdout, sys.stderr
    try:
        E.esegui(piano, crm, cartelle, False)
    finally:
        sys.stdout = uscita
    print(json.dumps({"tolti": len(piano), "clienti": [voce["idCliente"] for voce in piano]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())

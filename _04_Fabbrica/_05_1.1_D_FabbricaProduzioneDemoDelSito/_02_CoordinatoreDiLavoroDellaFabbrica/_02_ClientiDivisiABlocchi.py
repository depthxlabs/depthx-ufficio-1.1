"""La lista dei clienti divisa a blocchi, per il coordinatore.

I clienti sono quelli che il motore di download ha scaricato con esito GO o PARZIALE (il suo stato.json). Un blocco è un
foglio del CRM (l'industria del motore, per esempio 004): i blocchi vanno in ordine dal primo, e dentro ogni blocco i
clienti vanno in ordine di ID. Con un elenco di blocchi (per esempio 004,005) si lavorano solo quelli.

Priorità ai contatti (Michele, 13/11/2026): prima tutti i clienti con Instagram, poi quelli con l'email (senza Instagram),
poi tutti gli altri. Dentro ogni gruppo resta l'ordine dei blocchi e degli ID. I contatti si leggono dalla copia locale del
CRM del Centro Gestione (_09_CrmLinea11/fogli.json) con le stesse regole dell'Invio (invio.js): Instagram è un link vero
(http...), l'email è un indirizzo vero, mai una PEC, e il testo "Nessuna..." vuol dire nessun contatto. Se la copia del CRM
non si legge, l'ordine resta quello di prima.
Restituisce l'elenco ordinato di (blocco, [idCliente...]); lo stesso blocco può comparire una volta per ogni gruppo.
"""

import json
import re
from pathlib import Path

STATO_DEL_MOTORE = (Path(__file__).absolute().parents[2] / "_04_1.1_C_DownloadMaterialeClienti"
                    / "_01_StrumentiDelMotore" / "_05_RegistroEStatoDelMotore" / "stato.json")
CRM_LOCALE = Path(r"C:\_02_DepthXSoftware\_01_CentroGestioneDepthX\_08_MemoriaDatiDelCentroDiGestione\_09_CrmLinea11\fogli.json")
ESITI_SCARICATI = ("GO", "PARZIALE")
EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
PEC = re.compile(r"@pec\.|\.pec\.|legalmail", re.I)


def contattiDalCrm():
    """{idCliente: 1 se ha Instagram, 2 se ha solo l'email}; {} se la copia del CRM non si legge."""
    try:
        fogli = json.loads(CRM_LOCALE.read_text(encoding="utf-8-sig")).get("fogli", {})
    except Exception:
        return {}
    gruppo = {}
    for foglio in fogli.values():
        colonne = [str(c).strip().lower() for c in foglio.get("colonne", [])]
        iEmail = colonne.index("tutti i contatti email") if "tutti i contatti email" in colonne else -1
        iIg = colonne.index("ha instagram?") if "ha instagram?" in colonne else -1
        for riga in foglio.get("righe", []):
            if not riga or not riga[0]:
                continue
            cella = lambda i: str(riga[i]) if 0 <= i < len(riga) and riga[i] is not None else ""
            instagram = re.match(r"^\s*https?://", cella(iIg), re.I) is not None
            testoEmail = cella(iEmail)
            email = not re.match(r"^\s*nessun", testoEmail, re.I) and any(not PEC.search(e) for e in EMAIL.findall(testoEmail))
            if instagram:
                gruppo[riga[0]] = 1
            elif email:
                gruppo[riga[0]] = 2
    return gruppo


def clientiDivisiABlocchi(soloQuestiBlocchi=()):
    clienti = json.loads(STATO_DEL_MOTORE.read_text(encoding="utf-8-sig")).get("clienti", {})
    blocchi = {}
    for idCliente, voce in clienti.items():
        blocco = str(voce.get("industria", ""))
        if voce.get("esito") in ESITI_SCARICATI and (not soloQuestiBlocchi or blocco in soloQuestiBlocchi):
            blocchi.setdefault(blocco, []).append(idCliente)
    ordinati = [(blocco, sorted(blocchi[blocco])) for blocco in sorted(blocchi)]
    gruppo = contattiDalCrm()
    if not gruppo:
        return ordinati
    elenco = []
    for priorita in (1, 2, 3):
        for blocco, ids in ordinati:
            scelti = [i for i in ids if gruppo.get(i, 3) == priorita]
            if scelti:
                elenco.append((blocco, scelti))
    return elenco

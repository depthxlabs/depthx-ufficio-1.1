"""Passo 5.8.3: per ogni frase del copywriting nella pagina del template, le frasi approvate che possono andare al suo posto.

Ogni frase approvata nei 17 file di _02_CopywritingDellOspitalità porta la sua prova: [prova: dati] se bastano i dati
del CRM, oppure [prova: chiave, chiave] con i fatti che afferma (_00_FattiDaProvare.json); il passo 5.8.4 la usa solo
se ogni fatto è provato dal materiale del cliente (Michele: una frase vale solo se un fatto la prova).
Si prendono le frasi della pagina con le graffe e anche quelle senza graffe che sono nel copywriting, comprese le voci
degli elenchi (per esempio "Torte fatte in casa"). Il file in cui si trova la frase è la sua sezione. Le candidate sono,
in ordine, la frase del template e poi le altre frasi approvate numerate della stessa sezione e dello stesso gruppo (un
titolo al posto di un titolo, un testo al posto di un testo); una voce di elenco ha come candidata solo se stessa. Una frase che non è nel copywriting (per esempio solo {nomestruttura}) ha come candidata
solo se stessa. Le frasi delle recensioni ({recensioneInEvidenza}, {testoRecensione1}...) le scrive il passo 5.9.
"""

import html
import re
from pathlib import Path

CARTELLA_DEL_COPYWRITING = Path(__file__).absolute().parents[1] / "_02_CopywritingDellOspitalità"
TESTO_DI_UN_ELEMENTO = re.compile(r"<([a-zA-Z0-9]+)((?:\s[^>]*)?)>([^<]+)(?=<)")
GRAFFA = re.compile(r"\{\w+\}")
SEGNAPOSTO_DELLE_RECENSIONI = re.compile(r"\{(?:recensione\w*|testoDellaRecensione|testoRecensione\d|stelleRecensione\d)\}")
RIGA_DEL_COPYWRITING = re.compile(r"^\s*(\d+\.|-)\s+(.*?\S)\s*(?:\[prova:\s*([^\]]*)\])?\s*$", re.M)


def frasiApprovateConLaProva():
    """sezione -> elenco di {frase, prove, voce, gruppo}: prove è [] per [prova: dati], l'elenco dei fatti, o None senza
    prova; il gruppo è il titolo ## sotto cui sta la frase nel file (Titoli, Testi, Le voci...)."""
    sezioni = {}
    for file in sorted(CARTELLA_DEL_COPYWRITING.glob("*.md")):
        frasi, gruppo = [], ""
        for riga in file.read_text(encoding="utf-8-sig").splitlines():
            if riga.startswith("## "):
                gruppo = riga[3:].strip()
                continue
            trovata = RIGA_DEL_COPYWRITING.match(riga)
            if not trovata:
                continue
            segno, frase, prova = trovata.groups()
            prove = None if not (prova or "").strip() else \
                [chiave.strip() for chiave in prova.split(",") if chiave.strip() and chiave.strip() != "dati"]
            frasi.append({"frase": frase, "prove": prove, "voce": segno == "-", "gruppo": gruppo})
        sezioni[file.stem] = frasi
    return sezioni


def scegliUnaFraseApprovataPerOgniSezione(sito):
    sezioni = frasiApprovateConLaProva()
    trovaLaSezione = {voce["frase"]: (sezione, voce) for sezione, voci in sezioni.items() for voce in voci}
    # la stessa frase senza il punto finale (per esempio un titolo o un link) è la stessa frase approvata (Michele, 9/11/2026)
    senzaPunto = lambda testo: re.sub(r"[.!?:;,\s]+$", "", testo)
    for frase, voce in list(trovaLaSezione.items()):
        trovaLaSezione.setdefault(senzaPunto(frase), voce)
    # la frase si riconosce come la riconosce il collaudo 7.7: apostrofo curvo o dritto, maiuscole e spazi non contano
    # (Michele, 9/11/2026: la didascalia "C'è la vasca idromassaggio..." sfuggiva alla verifica e il collaudo la bocciava)
    normale = lambda testo: " ".join(senzaPunto(testo).lower().replace("’", "'").split())
    perNormale = {normale(frase): (frase, voce) for frase, voce in trovaLaSezione.items()}
    elenco = []
    for pagina in sorted(Path(sito).glob("*.html")):
        codice = pagina.read_text(encoding="utf-8-sig")
        # il titolo della scheda del browser non è una frase del copy: nome e comune li completa il passo 5 (11/11/2026)
        codice = re.sub(r"<(script|style|title)\b.*?</\1\s*>", lambda m: " " * len(m.group(0)), codice, flags=re.S | re.I)
        for trovata in TESTO_DI_UN_ELEMENTO.finditer(codice):
            tag, attributi, testo = trovata.groups()
            frase = html.unescape(testo).strip()
            # il titolo grande della Home è il nome della struttura e nessuna frase lo sostituisce (Michele, 11/11/2026)
            if not frase or SEGNAPOSTO_DELLE_RECENSIONI.search(testo) or "data-nome-eroe" in attributi:
                continue
            sezione, voce = trovaLaSezione.get(frase, (None, None))
            if sezione is None and normale(frase) in perNormale:
                frase, (sezione, voce) = perNormale[normale(frase)][0], perNormale[normale(frase)][1]
            if sezione is None and not GRAFFA.search(testo):
                continue
            if voce and voce["voce"]:
                candidate = [frase]
            else:
                gruppo = voce["gruppo"] if voce else None
                candidate = [frase] + [altra["frase"] for altra in sezioni.get(sezione, [])
                                       if senzaPunto(altra["frase"]) != senzaPunto(frase) and not altra["voce"] and altra["gruppo"] == gruppo]
            # la frase sotto il nome non ripete il nome (Michele, 11/11/2026: niente "Terrazze Caracciolo, a Pescara." sotto il nome)
            if "eroe__frase" in attributi:
                candidate = [c for c in candidate if "{nomestruttura}" not in c] or candidate
            prove = {candidata: (trovaLaSezione[candidata][1]["prove"] if candidata in trovaLaSezione else [])
                     for candidata in candidate}
            inglese = re.search(r'\sdata-en="([^"]*)"', attributi)
            elenco.append({"pagina": str(pagina), "originale": trovata.group(0), "tag": tag, "attributi": attributi,
                           "testo": testo, "sezione": sezione, "gruppo": voce["gruppo"] if voce and not voce["voce"] else None,
                           "candidate": candidate, "prove": prove,
                           "inglese": inglese.group(1) if inglese else None})
    return elenco

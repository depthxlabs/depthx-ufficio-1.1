"""Passo 5.1: il nome esatto della struttura nel file di configurazione del sito (assets/js/config.js).

Il nome viene dai dati del CRM, altrimenti dalla scheda Google. Il nome breve è il nome senza le parole del tipo
di struttura (Albergo Ristorante Risorgimento -> Risorgimento). Il template resta com'è: i valori del cliente si
aggiungono in fondo al file. I campi di ogni template sono in _01_CampiNelFileDiConfigurazione.json.
"""

import json
import re
from pathlib import Path

FILE_DEI_CAMPI = Path(__file__).absolute().parent / "_01_CampiNelFileDiConfigurazione.json"
PAROLE_DEL_TIPO = re.compile(r"^(hotel|albergo|ristorante|pizzeria|locanda|b&b|bnb|bed and breakfast|agriturismo|"
                             r"casa vacanze?|casa|villa|residence|affittacamere)\s+", re.I)


def scriviIlNomeDelClienteNelFileDiConfigurazione(sito, datiUnici):
    nome = (datiUnici["crm"].get("nome") or (datiUnici["schedaGoogle"].get("displayName") or {}).get("text") or "").strip()
    if not nome:
        raise RuntimeError("il cliente non ha un nome né nel CRM né nella scheda Google")
    # il nome breve si ferma prima di " - ", " | " o " · ": "La Portesina - Casa Vacanza a Mantova" diventa "La Portesina" (Michele, 9/11/2026)
    nomeBreve = re.split(r"\s+[-\u2013|\u00b7]\s+", nome)[0].strip() or nome
    while PAROLE_DEL_TIPO.match(nomeBreve):
        nomeBreve = PAROLE_DEL_TIPO.sub("", nomeBreve, count=1)
    # il nome resta completo, ma il trattino " - " nel font dei titoli si vede storto: diventa " · " (Michele, 9/11/2026)
    nome = re.sub(r"\s+[-–—]\s+", " · ", nome)
    valori = {"nome": nome, "nomeBreve": nomeBreve or nome}
    file = Path(sito) / "assets" / "js" / "config.js"
    variabile = re.search(r"window\.(\w+)\s*=", file.read_text(encoding="utf-8-sig")).group(1)
    campi = json.loads(FILE_DEI_CAMPI.read_text(encoding="utf-8-sig"))[variabile]
    righe = [f"window.{variabile}.{campi[campo]} = {json.dumps(valore, ensure_ascii=False)};"
             for campo, valore in valori.items() if campi.get(campo) and valore]
    with file.open("a", encoding="utf-8") as config:
        config.write("\n/* DepthX, fabbrica dei siti: il nome del cliente. */\n" + "\n".join(righe) + "\n")
    return valori

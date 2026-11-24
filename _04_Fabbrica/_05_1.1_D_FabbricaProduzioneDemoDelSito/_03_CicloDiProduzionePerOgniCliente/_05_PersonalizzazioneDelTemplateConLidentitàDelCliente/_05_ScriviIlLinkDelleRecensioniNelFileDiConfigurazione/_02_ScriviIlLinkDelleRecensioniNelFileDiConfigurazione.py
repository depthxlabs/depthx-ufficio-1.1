"""Passo 5.5: il link alla pagina delle recensioni Google nel file di configurazione.

Nel sito delle recensioni restano solo i testi degli ospiti: voto e numero non si scrivono mai, perché un numero scritto
nel sito non segue Google quando cambia (Michele, 8/11/2026). Il link porta sempre alle recensioni Google, mai a Google
Maps: con il place id https://search.google.com/local/reviews?placeid=<id>, senza la ricerca Google del nome esatto con
"recensioni". I campi di ogni template sono in _01_CampiNelFileDiConfigurazione.json.
"""

import json
import re
from pathlib import Path
from urllib.parse import quote_plus

FILE_DEI_CAMPI = Path(__file__).absolute().parent / "_01_CampiNelFileDiConfigurazione.json"


def scriviIlLinkDelleRecensioniNelFileDiConfigurazione(sito, datiUnici):
    crm = datiUnici["crm"]
    placeId = (crm.get("googleMaps") or "").strip()
    placeId = placeId if placeId.startswith("ChIJ") else ""
    nome = (crm.get("nome") or "").strip()
    link = (f"https://search.google.com/local/reviews?placeid={placeId}" if placeId
            else f"https://www.google.com/search?q={quote_plus(nome + ' recensioni')}" if nome else "")
    valori = {"placeId": placeId, "link": link}
    file = Path(sito) / "assets" / "js" / "config.js"
    variabile = re.search(r"window\.(\w+)\s*=", file.read_text(encoding="utf-8-sig")).group(1)
    campi = json.loads(FILE_DEI_CAMPI.read_text(encoding="utf-8-sig"))[variabile]
    righe = [f"window.{variabile}.{campi[campo]} = {json.dumps(valore, ensure_ascii=False)};"
             for campo, valore in valori.items() if campi.get(campo) and valore]
    with file.open("a", encoding="utf-8") as config:
        config.write("\n/* DepthX, fabbrica dei siti: il link delle recensioni Google. */\n" + "\n".join(righe) + "\n")
    return valori

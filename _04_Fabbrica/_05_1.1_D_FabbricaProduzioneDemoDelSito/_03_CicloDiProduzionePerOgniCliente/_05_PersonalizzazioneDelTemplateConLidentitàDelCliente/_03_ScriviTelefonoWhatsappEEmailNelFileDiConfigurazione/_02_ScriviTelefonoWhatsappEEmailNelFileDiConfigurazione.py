"""Passo 5.3: telefono, WhatsApp ed email veri del cliente nel file di configurazione (assets/js/config.js).

Il telefono si scrive come si legge. WhatsApp è un cellulare italiano (+39 3...), solo cifre con il prefisso
(per esempio 393330000000): il cellulare del CRM o, se è un cellulare, il telefono. Se manca, il campo resta vuoto
e il template toglie i pulsanti WhatsApp. I campi di ogni template sono in _01_CampiNelFileDiConfigurazione.json.
"""

import json
import re
from pathlib import Path

FILE_DEI_CAMPI = Path(__file__).absolute().parent / "_01_CampiNelFileDiConfigurazione.json"


def scriviTelefonoWhatsappEEmailNelFileDiConfigurazione(sito, datiUnici):
    crm = datiUnici["crm"]
    telefono = (crm.get("telefono") or crm.get("cellulare") or "").strip()
    whatsapp = ""
    for numero in (crm.get("cellulare"), crm.get("telefono")):
        cifre = re.sub(r"\D", "", numero or "")
        cifre = cifre[2:] if cifre.startswith("39") and len(cifre) > 10 else cifre
        if cifre.startswith("3") and 9 <= len(cifre) <= 10:
            whatsapp = "39" + cifre
            break
    valori = {"telefono": telefono, "whatsapp": whatsapp, "email": (crm.get("email") or "").strip()}
    file = Path(sito) / "assets" / "js" / "config.js"
    variabile = re.search(r"window\.(\w+)\s*=", file.read_text(encoding="utf-8-sig")).group(1)
    campi = json.loads(FILE_DEI_CAMPI.read_text(encoding="utf-8-sig"))[variabile]
    righe = [f"window.{variabile}.{campi[campo]} = {json.dumps(valore, ensure_ascii=False)};"
             for campo, valore in valori.items() if campi.get(campo) and valore]
    with file.open("a", encoding="utf-8") as config:
        config.write("\n/* DepthX, fabbrica dei siti: telefono, WhatsApp ed email del cliente. */\n" + "\n".join(righe) + "\n")
    return valori


def togliIlWhatsappDalFileDiConfigurazione(sito):
    """Il cliente non dice di usare WhatsApp (fatto usaWhatsapp, passo 5.8.4): il campo torna vuoto e il template toglie
    i pulsanti WhatsApp (Michele, 8/11/2026)."""
    file = Path(sito) / "assets" / "js" / "config.js"
    variabile = re.search(r"window\.(\w+)\s*=", file.read_text(encoding="utf-8-sig")).group(1)
    campo = json.loads(FILE_DEI_CAMPI.read_text(encoding="utf-8-sig"))[variabile].get("whatsapp")
    if campo:
        with file.open("a", encoding="utf-8") as config:
            config.write(f"/* DepthX: il cliente non dice di usare WhatsApp. */\nwindow.{variabile}.{campo} = \"\";\n")

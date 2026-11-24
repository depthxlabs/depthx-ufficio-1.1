"""Passo 5.7: le aree della struttura nel file di configurazione, con i nomi delle foto salvate nel passo 4.

Per ogni area con una foto: poster16 (16x9) e poster9 (9x16). Le aree senza foto si tolgono o si svuotano come dice
_01_AreeVuoteNelFileDiConfigurazione.json, così il loro blocco esce dalla pagina. Nessuna foto del template resta.
"""

import json
import re
from pathlib import Path

FILE_DELLE_AREE_VUOTE = Path(__file__).absolute().parent / "_01_AreeVuoteNelFileDiConfigurazione.json"


def scriviLeAreeDellaStrutturaNelFileDiConfigurazione(sito, contratto, fotoSalvate):
    aree = json.loads(Path(contratto).read_text(encoding="utf-8-sig"))["scene"]
    file = Path(sito) / "assets" / "js" / "config.js"
    variabile = re.search(r"window\.(\w+)\s*=", file.read_text(encoding="utf-8-sig")).group(1)
    areaVuota = json.loads(FILE_DELLE_AREE_VUOTE.read_text(encoding="utf-8-sig"))[variabile]
    righe = []
    for idArea in aree:
        foto = fotoSalvate.get(idArea) or {}
        if foto:
            valori = {"poster16": foto.get("16x9", ""), "poster9": foto.get("9x16", "")}
            righe.append(f"window.{variabile}.scene[{json.dumps(idArea)}] = Object.assign("
                         f"window.{variabile}.scene[{json.dumps(idArea)}] || {{}}, {json.dumps(valori)});")
        elif areaVuota == "togli":
            righe.append(f"delete window.{variabile}.scene[{json.dumps(idArea)}];")
        else:
            righe.append(f"window.{variabile}.scene[{json.dumps(idArea)}] = Object.assign("
                         f"window.{variabile}.scene[{json.dumps(idArea)}] || {{}}, {{\"poster16\": \"\", \"poster9\": \"\"}});")
    with file.open("a", encoding="utf-8") as config:
        config.write("\n/* DepthX, fabbrica dei siti: le aree della struttura con le foto del cliente. */\n" + "\n".join(righe) + "\n")
    # implementare post template: il B&B richiama le foto per nome direttamente nella pagina (index.html), non dal file
    # di configurazione; le aree vuote del B&B vanno tolte anche dalla pagina. Agriturismo: anche sezioni.<id> = false.
    return {idArea: bool(fotoSalvate.get(idArea)) for idArea in aree}

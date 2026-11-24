"""I valori del file di configurazione (assets/js/config.js) come li riceve il sito.

Il config.js si carica con node: così contano i valori scritti dai passi 5.x, non quelli del template che hanno sostituito.
Senza campo restituisce l'elenco di tutti i testi del file (nomi, contatti, foto, frasi...); con un campo (per esempio
"recensioni.link") restituisce i testi di quel campo soltanto.
"""

import json
import shutil
import subprocess
from pathlib import Path

LETTURA = """
global.window = {}; global.self = global.window; require(process.argv[1]);
const campo = process.argv[2] || ''; const valori = [];
const vedi = v => { if (typeof v === 'string' || typeof v === 'number') valori.push(String(v));
  else if (v && typeof v === 'object') Object.values(v).forEach(vedi); };
Object.values(window).forEach(c => vedi(campo ? campo.split('.').reduce((o, x) => o == null ? o : o[x], c) : c));
console.log(JSON.stringify(valori));
"""


def valoriDelFileDiConfigurazione(sito, campo=""):
    file = (Path(sito) / "assets" / "js" / "config.js").absolute()
    if not file.is_file():
        return []
    node = shutil.which("node")
    if not node:
        raise RuntimeError("node non è installato sul server")
    esito = subprocess.run([node, "-e", LETTURA, str(file), campo], capture_output=True, text=True, encoding="utf-8",
                           errors="ignore", timeout=60, creationflags=subprocess.CREATE_NO_WINDOW)
    if esito.returncode != 0:
        raise RuntimeError("il file di configurazione non si carica: " + (esito.stderr or "").strip()[-200:])
    return json.loads(esito.stdout)

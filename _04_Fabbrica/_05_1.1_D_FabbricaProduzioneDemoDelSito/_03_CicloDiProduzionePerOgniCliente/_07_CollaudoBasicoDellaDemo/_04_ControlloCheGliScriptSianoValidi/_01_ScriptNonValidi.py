"""Passo 7.4: ogni script del sito è JavaScript valido (node --check, che legge lo script senza eseguirlo).
Restituisce l'elenco dei problemi trovati.
"""

import shutil
import subprocess
from pathlib import Path


def scriptNonValidi(sito):
    node = shutil.which("node")
    if not node:
        raise RuntimeError("node non è installato sul server")
    problemi = []
    for script in sorted(Path(sito).rglob("*.js")):
        esito = subprocess.run([node, "--check", str(script)], capture_output=True, text=True, encoding="utf-8",
                               errors="ignore", timeout=60, creationflags=subprocess.CREATE_NO_WINDOW)
        if esito.returncode != 0:
            righe = [riga for riga in (esito.stderr or "").strip().splitlines() if riga.strip()]
            problemi.append(f"script non valido: {script.relative_to(sito)}: {righe[-1] if righe else ''}")
    return problemi

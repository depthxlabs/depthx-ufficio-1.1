"""Passo 8.1: le fotografie di tutte le pagine della demo, come le vede il visitatore sul computer e sul telefono.

Pacchetto Advanced (Michele, 11/11/2026, task #580): il product manager guarda tutte le pagine del sito, non solo la home.
Le fotografie della home hanno le chiavi "computer" e "telefono"; quelle delle altre pagine "<pagina>|computer" e
"<pagina>|telefono" (per esempio "camere.html|telefono").

Chrome apre la pagina senza finestra, con "riduci movimento" attivo: così ogni blocco che compare allo scorrere è già
visibile nella fotografia. Dalla cartella del cliente in corso i percorsi superano i 260 caratteri che Windows ammette:
il sito si copia in una cartella temporanea dal percorso corto, con un profilo di Chrome suo (il Chrome di Michele non
si tocca). Le fotografie vanno poi nella cartella del cliente in corso, in _ApprovazioneProductManager; la cartella
temporanea si cancella. Restituisce forma -> percorso della fotografia.
"""

import json
import shutil
import subprocess
import tempfile
import time
from pathlib import Path

FILE_DELLE_REGOLE = Path(__file__).absolute().parent / "_01_RegoleDelleFotografie.json"
FOTOGRAFIA_DELLA_PAGINA_INTERA = Path(__file__).absolute().parent / "_03_FotografiaDellaPaginaIntera.js"


def togliLaCartella(cartella):
    for voce in sorted(cartella.rglob("*"), key=lambda p: len(p.parts), reverse=True):
        voce.rmdir() if voce.is_dir() else voce.unlink()
    cartella.rmdir()


def fotografieDellaDemo(sito, cartellaDelClienteInCorso):
    regole = json.loads(FILE_DELLE_REGOLE.read_text(encoding="utf-8-sig"))
    if not Path(regole["chrome"]).is_file():
        raise RuntimeError(f"Chrome non è installato sul server: {regole['chrome']}")
    arrivo = Path(cartellaDelClienteInCorso) / "_ApprovazioneProductManager"
    arrivo.mkdir(parents=True, exist_ok=True)
    corta = Path(tempfile.mkdtemp(prefix="dxpm_"))
    fotografie = {}
    try:
        for voce in sorted(Path(sito).rglob("*")):
            copia = corta / "sito" / voce.relative_to(sito)
            if voce.is_dir():
                copia.mkdir(parents=True, exist_ok=True)
            else:
                copia.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(voce, copia)
        node = shutil.which("node")
        if not node:
            raise RuntimeError("node non è installato sul server")
        pagine = sorted((corta / "sito").glob("*.html"), key=lambda p: (p.name != "index.html", p.name))
        # Pitstop 6 (task #611, Michele 11/11/2026): le fotografie delle pagine partono in parallelo, fino a 4 alla volta
        from concurrent.futures import ThreadPoolExecutor

        def fotografa(file, forma, larghezza, altezza, telefono):
            nomeDellaPagina = "home" if file.name == "index.html" else file.stem
            fotografia = corta / f"{nomeDellaPagina}_{forma}.png"
            esito = subprocess.run([node, str(FOTOGRAFIA_DELLA_PAGINA_INTERA), regole["chrome"], str(corta / f"profilo_{nomeDellaPagina}_{forma}"),
                                    file.as_uri(), str(larghezza), str(altezza), "1" if telefono else "0", str(fotografia),
                                    str(int(regole["millisecondiPerCaricare"]))],
                                   capture_output=True, text=True, encoding="utf-8", errors="ignore", cwd=str(corta),
                                   timeout=int(regole["secondiMassimi"]), creationflags=subprocess.CREATE_NO_WINDOW)
            if not fotografia.is_file():
                raise RuntimeError(f"la fotografia di {file.name} sul {forma} non è riuscita: {(esito.stderr or '').strip()[-200:]}")
            shutil.copy2(fotografia, arrivo / fotografia.name)
            for accanto in (".txt", ".json"):
                if fotografia.with_suffix(accanto).is_file():
                    shutil.copy2(fotografia.with_suffix(accanto), arrivo / fotografia.with_suffix(accanto).name)
            return (forma if file.name == "index.html" else f"{file.name}|{forma}"), str(arrivo / fotografia.name)

        lavori = [(file, forma, *misure) for file in pagine for forma, misure in regole["fotografie"].items()]
        with ThreadPoolExecutor(max_workers=int(regole.get("fotografieInsieme", 4))) as fili:
            for chiave, percorso in fili.map(lambda lavoro: fotografa(*lavoro), lavori):
                fotografie[chiave] = percorso
    finally:
        for volta in range(5):
            try:
                togliLaCartella(corta)
                break
            except OSError:
                time.sleep(2)
    return fotografie

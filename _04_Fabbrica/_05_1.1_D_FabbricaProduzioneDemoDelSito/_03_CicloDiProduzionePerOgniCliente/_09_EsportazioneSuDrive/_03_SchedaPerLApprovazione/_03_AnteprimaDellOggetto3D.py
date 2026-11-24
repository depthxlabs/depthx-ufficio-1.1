"""Passo 9.3: l'anteprima dell'oggetto 3D che gira, nella scheda di Approvazione (Michele, 12/11/2026, task #681).

Michele controlla il 3D dentro la scheda, senza aprire il sito: per il computer (1440 largo) e per il telefono (390 largo)
si fa girare l'oggetto 3D della home per un giro intero (36 fotogrammi, _02_CatturaDellOggetto3D.js) e i fotogrammi si
mettono in fila in un solo JPEG (oggetto3d_computer.jpg, oggetto3d_telefono.jpg). La pagina Approvazione li fa scorrere
a passi e l'oggetto gira. Una pagina alla volta, Chrome chiuso alla fine, nessuna finestra.
"""

import json
import shutil
import subprocess
import tempfile
from pathlib import Path

from PIL import Image

QUI = Path(__file__).absolute().parent
CATTURA = QUI / "_02_CatturaDellOggetto3D.js"
REGOLE_DELLE_FOTOGRAFIE = QUI.parents[1] / "_08_ApprovazioneProductManager" / "_01_FotografieDellaDemo" / "_01_RegoleDelleFotografie.json"
FORME = {"computer": (1440, 900, False), "telefono": (390, 844, True)}
FOTOGRAMMI = 36
LARGHEZZA_MASSIMA = 480
SECONDI_DEL_GIRO = 4.5


def anteprimaDellOggetto3D(pagina, arrivo):
    """Crea oggetto3d_<forma>.jpg in arrivo e restituisce la voce per scheda.json; solleva un errore col motivo se non riesce."""
    regole = json.loads(REGOLE_DELLE_FOTOGRAFIE.read_text(encoding="utf-8-sig"))
    if not Path(regole["chrome"]).is_file():
        raise RuntimeError(f"Chrome non è installato sul server: {regole['chrome']}")
    node = shutil.which("node")
    if not node:
        raise RuntimeError("node non è installato sul server")
    arrivo = Path(arrivo)
    voce = {"giro": SECONDI_DEL_GIRO}
    for forma, (larghezza, altezza, telefono) in FORME.items():
        corta = Path(tempfile.mkdtemp(prefix="o3d_"))
        try:
            esito = subprocess.run([node, str(CATTURA), regole["chrome"], str(corta / "profilo"), pagina, str(larghezza), str(altezza),
                                    "1" if telefono else "0", str(corta / "f"), str(FOTOGRAMMI)],
                                   capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=180,
                                   creationflags=subprocess.CREATE_NO_WINDOW)
            if esito.returncode != 0:
                raise RuntimeError(f"{forma}: {(esito.stderr or esito.stdout).strip()[-300:]}")
            fotogrammi = sorted((corta / "f").glob("f*.jpg"))
            if len(fotogrammi) != FOTOGRAMMI:
                raise RuntimeError(f"{forma}: {len(fotogrammi)} fotogrammi su {FOTOGRAMMI}")
            immagini = [Image.open(f).convert("RGB") for f in fotogrammi]
            l, a = immagini[0].size
            if l > LARGHEZZA_MASSIMA:
                l, a = LARGHEZZA_MASSIMA, round(a * LARGHEZZA_MASSIMA / l)
                immagini = [i.resize((l, a), Image.LANCZOS) for i in immagini]
            striscia = Image.new("RGB", (l * len(immagini), a), "white")
            for n, immagine in enumerate(immagini):
                striscia.paste(immagine, (n * l, 0))
            nome = f"oggetto3d_{forma}.jpg"
            striscia.save(arrivo / nome, "JPEG", quality=76, optimize=True, progressive=True)
            voce[forma] = {"file": nome, "fotogrammi": len(immagini), "larghezza": l, "altezza": a}
        finally:
            shutil.rmtree(corta, ignore_errors=True)
    return voce

"""Passo 4.5: le foto piccole ingrandite con l'intelligenza artificiale (Michele, 8/11/2026).

Molte foto dei clienti arrivano da Google Maps o dai social, larghe 1000 punti o meno: a tutto schermo su un computer o su
un telefono moderno si vedevano morbide. Un taglio con il lato lungo più piccolo di latoLungoDelleFoto (passo 4.9) si
ingrandisce con il modello Real-ESRGAN generale x4v3 (_02_ModelloRealEsrganGeneraleX4v3.onnx, convertito dal file ufficiale
del progetto Real-ESRGAN), che ricostruisce i dettagli invece di allargare i punti. Il modello gira sul processore con
onnxruntime, a pezzi quadrati con un bordo comune (_01_RegoleDellIngrandimento.json), poi la foto torna alla misura che
serve, mai oltre 4 volte l'originale. Una foto già grande resta com'è. Una foto con insegne o scritte (giudizio del
passo 4.1) si ingrandisce solo nel modo classico, così le lettere restano leggibili (Michele, 9/11/2026).
"""

import json
from pathlib import Path

import numpy as np
from PIL import Image

CARTELLA = Path(__file__).absolute().parent
FILE_DELLE_REGOLE = CARTELLA / "_01_RegoleDellIngrandimento.json"
FILE_DEL_MODELLO = CARTELLA / "_02_ModelloRealEsrganGeneraleX4v3.onnx"
FILE_DEL_SALVATAGGIO = CARTELLA.parent / "_09_SalvaLaFotoInJpegNelSitoDelCliente" / "_01_RegoleDelSalvataggio.json"
SCALA_DEL_MODELLO = 4
SESSIONE = []


def sessioneDelModello():
    if not SESSIONE:
        import onnxruntime
        opzioni = onnxruntime.SessionOptions()
        opzioni.log_severity_level = 3
        # i processori divisi tra le fabbriche accese e le aree lavorate in parallelo (Pitstop, 11/11/2026)
        import os
        try:
            insieme = int(json.loads((CARTELLA.parents[3] / "_02_CoordinatoreDiLavoroDellaFabbrica" / "_03_RegoleDelCoordinatore.json")
                                     .read_text(encoding="utf-8-sig")).get("fabbricheInsieme", 1))
        except (OSError, ValueError):
            insieme = 1
        opzioni.intra_op_num_threads = max(1, (os.cpu_count() or 4) // max(1, insieme) // 2)
        SESSIONE.append(onnxruntime.InferenceSession(str(FILE_DEL_MODELLO), opzioni, providers=["CPUExecutionProvider"]))
    return SESSIONE[0]


def quattroVolte(immagine, lato, bordo):
    dati = np.asarray(immagine, dtype=np.float32).transpose(2, 0, 1) / 255
    _, alto, largo = dati.shape
    uscita = np.zeros((3, alto * SCALA_DEL_MODELLO, largo * SCALA_DEL_MODELLO), np.float32)
    for y in range(0, alto, lato):
        for x in range(0, largo, lato):
            y0, x0 = max(0, y - bordo), max(0, x - bordo)
            y1, x1 = min(alto, y + lato + bordo), min(largo, x + lato + bordo)
            pezzo = sessioneDelModello().run(None, {"foto": np.ascontiguousarray(dati[None, :, y0:y1, x0:x1])})[0][0]
            dentroY, dentroX = (y - y0) * SCALA_DEL_MODELLO, (x - x0) * SCALA_DEL_MODELLO
            h, w = (min(y + lato, alto) - y) * SCALA_DEL_MODELLO, (min(x + lato, largo) - x) * SCALA_DEL_MODELLO
            uscita[:, y * SCALA_DEL_MODELLO:y * SCALA_DEL_MODELLO + h, x * SCALA_DEL_MODELLO:x * SCALA_DEL_MODELLO + w] = \
                pezzo[:, dentroY:dentroY + h, dentroX:dentroX + w]
    return Image.fromarray((uscita.clip(0, 1) * 255).round().astype(np.uint8).transpose(1, 2, 0))


def latoDellArea(idArea):
    """La misura che il sito mostra per l'area (Pitstop, Michele 11/11/2026): oltre non serve ingrandire."""
    salvataggio = json.loads(FILE_DEL_SALVATAGGIO.read_text(encoding="utf-8-sig"))
    piccola = any(str(idArea or "").startswith(inizio) for inizio in salvataggio.get("inizioDelleAreePiccole", []))
    return int(salvataggio["latoLungoDelleAreePiccole"] if piccola else salvataggio["latoLungoDelleFoto"])


def ingrandisciLeFotoPiccole(immagine, conScritte=False, idArea=""):
    regole = json.loads(FILE_DELLE_REGOLE.read_text(encoding="utf-8-sig"))
    latoLungo = latoDellArea(idArea)
    scala = min(latoLungo / max(immagine.size), SCALA_DEL_MODELLO)
    if scala < float(regole["scalaMinima"]):
        return immagine
    immagine = immagine.convert("RGB")
    misura = (round(immagine.width * scala), round(immagine.height * scala))
    if conScritte:
        # insegne e scritte restano leggibili: il modello le impasta, l'ingrandimento classico no (Michele, 9/11/2026)
        return immagine.resize(misura, Image.LANCZOS)
    grande = quattroVolte(immagine, int(regole["latoDelPezzo"]), int(regole["bordoDelPezzo"])).resize(misura, Image.LANCZOS)
    forza = float(regole["forzaDellIngrandimento"])
    return grande if forza >= 1 else Image.blend(immagine.resize(misura, Image.LANCZOS), grande, forza)

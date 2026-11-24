"""Passo 7.3: ogni file richiamato dal sito esiste.

Si controllano i file richiamati dalle pagine (stile, script, immagini, video, altre pagine: src, href, srcset, poster),
le foto e i video tra i valori del file di configurazione (letti dal passo 7.1) e le foto delle scene salvate nel passo 4.
Un nome senza cartella si cerca anche in media/foto e media/video. I link esterni, email e telefono non si controllano.
Restituisce l'elenco dei problemi trovati.
"""

import json
import re
from pathlib import Path
from urllib.parse import unquote

ESTERNO = re.compile(r"^(?:[a-z]+:|//|#|\{)", re.I)
FOTO_DI_SCENA = re.compile(r"^(?:.*/)?(\w+_(16x9|9x16))\.jpg$")
FILE_DELLE_LARGHEZZE = (Path(__file__).absolute().parents[2] / "_04_MiglioramentoDelleFotoEsistentiDelCliente"
                        / "_09_SalvaLaFotoInJpegNelSitoDelCliente" / "_01_RegoleDelSalvataggio.json")
MEDIA = re.compile(r"^[^\s]+\.(?:jpe?g|png|webp|avif|gif|svg|mp4|webm)$", re.I)


def esiste(sito, cartella, richiamato):
    richiamato = unquote(richiamato.split("?")[0].split("#")[0]).lstrip("/")
    radice = Path(sito)
    return not richiamato or any((base / richiamato).exists() for base in
                                 (cartella, radice, radice / "media" / "foto", radice / "media" / "video"))


def fileRichiamatiMancanti(sito, codici, valoriDelConfig, fotoSalvate):
    fotoEVideoDelConfig = sorted({valore for valore in valoriDelConfig if MEDIA.match(valore.split("?")[0])})
    problemi = []
    for percorso, codice in codici.items():
        file = Path(percorso)
        if file.suffix != ".html":
            continue
        richiamati = re.findall(r'\s(?:src|href|poster)="([^"]+)"', codice)
        richiamati += [voce.split()[0] for gruppo in re.findall(r'\ssrcset="([^"]+)"', codice)
                       for voce in gruppo.split(",") if voce.strip()]
        for richiamato in sorted(set(richiamati)):
            if not ESTERNO.match(richiamato) and not esiste(sito, file.parent, richiamato):
                problemi.append(f"{file.name} richiama un file che non c'è: {richiamato}")
    for nome in fotoEVideoDelConfig:
        if not ESTERNO.match(nome) and not esiste(sito, Path(sito), nome):
            problemi.append(f"config.js richiama un file che non c'è: {nome}")
        foto = FOTO_DI_SCENA.match(nome)
        if foto:
            larghezze = json.loads(FILE_DELLE_LARGHEZZE.read_text(encoding="utf-8-sig"))["larghezzeDelleFoto"].get(foto.group(2), [])
            for larghezza in larghezze:
                for estensione in ("jpg", "webp"):
                    variante = f"{foto.group(1)}-{larghezza}.{estensione}"
                    if not esiste(sito, Path(sito), variante):
                        problemi.append(f"manca la foto in larghezza {larghezza}: {variante}")
    for forme in fotoSalvate.values():
        for nome in forme.values():
            if not (Path(sito) / "media" / "foto" / nome).is_file():
                problemi.append(f"manca la foto {nome}")
    return problemi

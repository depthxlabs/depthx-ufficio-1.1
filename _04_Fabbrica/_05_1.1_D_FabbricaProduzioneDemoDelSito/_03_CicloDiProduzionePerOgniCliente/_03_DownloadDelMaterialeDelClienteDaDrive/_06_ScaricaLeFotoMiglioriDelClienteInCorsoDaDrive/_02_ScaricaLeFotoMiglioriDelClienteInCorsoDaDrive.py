"""Passo 3.6: le foto migliori del cliente in corso, scaricate da Drive a grandezza originale in <cliente in corso>/originali.

Riceve le foto valide già in ordine di qualità (passo 3.2). Si prendono le migliori di ogni categoria, poi le migliori
rimaste fino al massimo, più il logo migliore (regole in _01_RegoleDelloScaricamento.json).
Restituisce id su Drive -> percorso sul disco. Drive si legge soltanto, con rclone.
Pitstop 8 (Michele, 12/11/2026, task #613): si scaricano SOLO le foto che servono alle aree del template (contratto.json):
per ogni area, nell'ordine del contratto, la foto migliore non ancora presa di una delle sue categorie (nell'ordine in cui
l'area le chiede), più una foto di riserva per ogni categoria che le aree chiedono (per le foto doppie o con la luce
bruciata, che il passo 4.1 scarta), più il logo, sempre entro fotoMassimeDaScaricare. La categoria è quella già data da
Claude alla foto (giudizio salvato del passo 4.1) e, per una foto mai vista, quella del motore. Tutte le foto scelte si
scaricano nello stesso momento (prima 10 alla volta). Copia di prima: .copiaPrimaVelocita.
"""

import json
import subprocess
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

RCLONE = r"C:\_02_DepthXSoftware\_02_RCloneDepthX\rclone.exe"
CONFIGURAZIONE = r"C:\_02_DepthXSoftware\_02_RCloneDepthX\rclone.conf"
FILE_DELLE_REGOLE = Path(__file__).absolute().parent / "_01_RegoleDelloScaricamento.json"
SCARICAMENTI_INSIEME = 10  # le foto si scaricano 10 alla volta, per la velocità (Michele, 8/11/2026)
SCARICAMENTI_INSIEME_PER_AREE = 25  # pitstop 8 (12/11/2026): le foto delle aree, tutte nello stesso momento


def categoriaGiaNota(voce):
    """La categoria precisa già data da Claude a questa foto (passo 4.1), altrimenti quella del motore."""
    from ..._04_MiglioramentoDelleFotoEsistentiDelCliente._01_ScegliUnaFotoPerOgniAreaDellaStruttura._07_CategoriePreciseDelleFoto import \
        giudizioGiaDato
    giudizio = giudizioGiaDato(voce.get("id")) or {}
    return giudizio.get("categoria") or voce.get("categoria")


def fotoPerLeAree(adatte, contratto, massime):
    """Pitstop 8: per ogni area la foto migliore di una sua categoria, poi una di riserva per ogni categoria chiesta."""
    scene = json.loads(Path(contratto).read_text(encoding="utf-8-sig"))["scene"]
    aree = [voce if isinstance(voce, list) else voce.get("categorie", []) for voce in scene.values()]
    categoria = {voce["id"]: categoriaGiaNota(voce) for voce in adatte}
    scelte = []
    for desiderate in aree:
        candidate = [voce for voce in adatte if voce not in scelte and categoria[voce["id"]] in desiderate]
        candidate.sort(key=lambda voce: desiderate.index(categoria[voce["id"]]))  # sort stabile: poi l'ordine di qualità
        if candidate and len(scelte) < massime:
            scelte.append(candidate[0])
    for chiesta in dict.fromkeys(c for desiderate in aree for c in desiderate):
        riserva = next((voce for voce in adatte if voce not in scelte and categoria[voce["id"]] == chiesta), None)
        if riserva and len(scelte) < massime:
            scelte.append(riserva)
    return scelte


def scaricaLeFotoMiglioriDelClienteInCorsoDaDrive(fotoInOrdine, cartellaDelClienteInCorso, contratto=None):
    regole = json.loads(FILE_DELLE_REGOLE.read_text(encoding="utf-8-sig"))
    perCategoria, massime = int(regole["fotoMiglioriPerCategoria"]), int(regole["fotoMassimeDaScaricare"])
    escluse = set(regole["categorieDaNonScaricare"])
    adatte = [voce for voce in fotoInOrdine if voce.get("categoria") not in escluse]
    if contratto:
        return scaricaLeScelte(fotoPerLeAree(adatte, contratto, massime), fotoInOrdine, cartellaDelClienteInCorso,
                               SCARICAMENTI_INSIEME_PER_AREE)
    scelte, quanteDellaCategoria = [], {}
    for voce in adatte:
        categoria = voce.get("categoria")
        if quanteDellaCategoria.get(categoria, 0) < perCategoria and len(scelte) < massime:
            scelte.append(voce)
            quanteDellaCategoria[categoria] = quanteDellaCategoria.get(categoria, 0) + 1
    for voce in adatte:
        if len(scelte) >= massime:
            break
        if voce not in scelte:
            scelte.append(voce)
    return scaricaLeScelte(scelte, fotoInOrdine, cartellaDelClienteInCorso, SCARICAMENTI_INSIEME)


def scaricaLeScelte(scelte, fotoInOrdine, cartellaDelClienteInCorso, insiemeMassimo):
    logo = next((voce for voce in fotoInOrdine if voce.get("categoria") == "logo"), None)
    if logo:
        scelte.append(logo)
    originali = Path(cartellaDelClienteInCorso) / "originali"
    originali.mkdir(parents=True, exist_ok=True)
    with ThreadPoolExecutor(max_workers=max(1, min(insiemeMassimo, len(scelte)))) as insieme:
        scaricate = list(insieme.map(lambda voce: scaricaUnaFoto(voce, originali), scelte))
    return {voce["id"]: percorso for voce, percorso in zip(scelte, scaricate)}


def scaricaUnaFoto(voce, originali):
    percorso = originali / (voce["id"] + (Path(voce.get("nome") or "").suffix or ".jpg"))
    if not percorso.is_file():
        esito = subprocess.run([RCLONE, "backend", "copyid", "gdrive:", voce["id"], str(percorso),
                                "--config", CONFIGURAZIONE], capture_output=True, text=True, encoding="utf-8")
        if esito.returncode != 0 or not percorso.is_file():
            raise RuntimeError(f"la foto {voce.get('nome')} ({voce['id']}) non si è scaricata da Drive")
    return str(percorso)

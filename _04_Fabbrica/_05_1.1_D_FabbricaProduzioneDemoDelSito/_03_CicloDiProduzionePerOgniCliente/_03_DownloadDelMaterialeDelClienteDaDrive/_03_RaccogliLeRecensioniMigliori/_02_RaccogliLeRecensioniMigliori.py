"""Passo 3.3: le recensioni migliori del cliente, al massimo quante dice recensioniDaTenere (_01_RegoleDelleRecensioni.json).

Il file è _01_RaccoltaMateriale/_03_RecensioniDaGoogleMaps/_01_RecensioniGoogle.json.
Il testo dell'ospite si tiene com'è scritto, senza emoji e senza le virgolette attorno (le mette la pagina).
Si tengono solo le recensioni con un testo: prima il voto più alto, poi quelle intere (non tagliate con i tre puntini),
poi il testo più lungo.
Senza recensioni la lista è vuota e la sezione recensioni si toglie più avanti.
Pitstop 8 (Michele, 12/11/2026, task #613): il file si prende dalla lettura unica del materiale
(_07_LeggiIFileDelMaterialeInUnaSolaLettura.py); se non c'è, si legge da Drive come prima. Copia di prima: .copiaPrimaVelocita.
"""

import json
import re
import subprocess
from pathlib import Path

from .._07_LeggiIFileDelMaterialeInUnaSolaLettura import fileLetto

RCLONE = r"C:\_02_DepthXSoftware\_02_RCloneDepthX\rclone.exe"
CONFIGURAZIONE = r"C:\_02_DepthXSoftware\_02_RCloneDepthX\rclone.conf"
FILE_DELLE_RECENSIONI = "_03_RecensioniDaGoogleMaps/_01_RecensioniGoogle.json"
FILE_DELLE_REGOLE = Path(__file__).absolute().parent / "_01_RegoleDelleRecensioni.json"
EMOJI = re.compile("[🀀-🫿☀-➿️‍]")
VIRGOLETTE = "\"'«»“”„‘’ "


def testoPulito(testo):
    # il segno | del testo scaricato è un a capo dell'ospite: diventa uno spazio (Michele, 11/11/2026)
    return " ".join(EMOJI.sub("", (testo or "").replace("|", " ")).split()).strip(VIRGOLETTE)


def raccogliLeRecensioniMigliori(cartellaDiLavoro):
    quante = int(json.loads(FILE_DELLE_REGOLE.read_text(encoding="utf-8-sig"))["recensioniDaTenere"])
    letto, contenuto = fileLetto(cartellaDiLavoro, FILE_DELLE_RECENSIONI)
    if letto:
        tutte = (contenuto or {}).get("recensioni", [])
    else:
        esito = subprocess.run([RCLONE, "cat", f"gdrive:{cartellaDiLavoro['raccolta']}/{FILE_DELLE_RECENSIONI}",
                                "--drive-root-folder-id", cartellaDiLavoro["idDrive"], "--config", CONFIGURAZIONE],
                               capture_output=True)
        tutte = json.loads(esito.stdout.decode("utf-8-sig")).get("recensioni", []) if esito.returncode == 0 else []
    conTesto = [{**voce, "testo": testoPulito(voce.get("testo"))} for voce in tutte if testoPulito(voce.get("testo"))]
    conTesto.sort(key=lambda voce: (-(voce.get("voto") or 0), voce["testo"].endswith(("…", "...")), -len(voce["testo"])))
    return conTesto[:quante]

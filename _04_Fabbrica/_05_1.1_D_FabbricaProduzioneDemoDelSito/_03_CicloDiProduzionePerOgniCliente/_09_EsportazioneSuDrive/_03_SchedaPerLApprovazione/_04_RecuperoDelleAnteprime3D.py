"""Recupero (Michele, 12/11/2026, task #681): l'anteprima dell'oggetto 3D per le demo già in _09_DemoInApprovazione che non
ce l'hanno, dal loro link online (depthxlabs.com/demo/...). Una demo alla volta, Chrome chiuso dopo ogni demo.
Si aggiunge solo la voce "oggetto3d" a scheda.json: "pronta" e la decisione restano come sono.
Uso: python _04_RecuperoDelleAnteprime3D.py [idCliente ...]   (senza id: tutte quelle senza anteprima)
"""

import importlib.util
import json
import sys
from pathlib import Path

QUI = Path(__file__).absolute().parent
FABBRICA = QUI.parents[2]
CARTELLA = FABBRICA / "_01_StrumentiDellaFabbrica" / "_09_DemoInApprovazione"
REGISTRO = CARTELLA / "_00_RegistroDelleAnteprime3D.jsonl"

specifica = importlib.util.spec_from_file_location("anteprima3d", QUI / "_03_AnteprimaDellOggetto3D.py")
modulo = importlib.util.module_from_spec(specifica)
specifica.loader.exec_module(modulo)


def haLAnteprima(cartella, scheda):
    o = scheda.get("oggetto3d") or {}
    return all((cartella / (o.get(f) or {}).get("file", "-")).is_file() for f in ("computer", "telefono"))


def main(soloQuesti):
    import datetime
    fatte, mancate = 0, []
    for cartella in sorted(p for p in CARTELLA.iterdir() if p.is_dir()):
        if soloQuesti and cartella.name not in soloQuesti:
            continue
        f = cartella / "scheda.json"
        if not f.is_file():
            continue
        scheda = json.loads(f.read_text(encoding="utf-8"))
        if haLAnteprima(cartella, scheda) or not scheda.get("link"):
            continue
        try:
            voce = modulo.anteprimaDellOggetto3D(scheda["link"], cartella)
            scheda = json.loads(f.read_text(encoding="utf-8"))  # riletta: la fabbrica può averla rifatta nel frattempo
            scheda["oggetto3d"] = voce
            f.write_text(json.dumps(scheda, ensure_ascii=False, indent=1), encoding="utf-8")
            fatte += 1
            esito = {"idCliente": cartella.name, "esito": "GO"}
        except Exception as errore:
            mancate.append(cartella.name)
            esito = {"idCliente": cartella.name, "esito": "NOTGO", "motivo": str(errore)[:300]}
        esito["ora"] = datetime.datetime.now().astimezone().isoformat(timespec="seconds")
        with REGISTRO.open("a", encoding="utf-8") as r:
            r.write(json.dumps(esito, ensure_ascii=False) + "\n")
        print(json.dumps(esito, ensure_ascii=False), flush=True)
    print(json.dumps({"fatte": fatte, "mancate": mancate}, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main(set(sys.argv[1:]))

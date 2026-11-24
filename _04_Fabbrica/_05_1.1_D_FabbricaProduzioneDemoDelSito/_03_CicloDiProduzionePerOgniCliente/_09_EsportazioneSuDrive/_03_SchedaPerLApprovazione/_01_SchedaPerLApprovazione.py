"""Passo 9.3: la scheda della demo per l'Approvazione del Centro Gestione (Michele, 11/11/2026).

La fabbrica mette ogni demo pronta nella pagina Approvazione: il link, il blocco del CRM, il tipo, il pacchetto della demo e
le schermate di tutte le pagine sul computer e sul telefono (quelle del product manager, passo 8.1, pagine intere). Le
schermate passano da PNG a JPEG (più leggere da aprire) e vanno, con la scheda, in
_01_StrumentiDellaFabbrica/_09_DemoInApprovazione/<idCliente>/. Il Centro Gestione legge solo questa cartella; la decisione
di Michele (Approva o Scarta) la scrive il Centro Gestione nello stesso posto, in decisione.json.
Una demo rifatta sostituisce la sua scheda e torna da approvare.
"""

import datetime
import json
import shutil
from pathlib import Path

from PIL import Image

Image.MAX_IMAGE_PIXELS = None
FABBRICA = Path(__file__).absolute().parents[3]
CARTELLA_DELLE_DEMO_IN_APPROVAZIONE = FABBRICA / "_01_StrumentiDellaFabbrica" / "_09_DemoInApprovazione"
NOMI_DELLE_PAGINE = {"home": "Home", "camere": "Camere", "galleria": "Galleria", "recensioni": "Recensioni", "dove-siamo": "Dove siamo",
                     "ristorante": "Ristorante", "spa": "Spa", "piscina": "Piscina", "terme": "Terme"}


def nomeDelBlocco(industria):
    return " · ".join(p.split("] ", 1)[-1].replace("CRM_", "").replace("_", " ") for p in str(industria or "").split("/") if p)


def schedaPerLApprovazione(scheda, copia, link):
    idCliente = scheda["idCliente"]
    fotografie = Path(copia["cartellaDelClienteInCorso"]) / "_ApprovazioneProductManager"
    arrivo = CARTELLA_DELLE_DEMO_IN_APPROVAZIONE / idCliente
    if arrivo.is_dir():
        shutil.rmtree(arrivo)
    arrivo.mkdir(parents=True)
    pagine = {}
    for png in sorted(fotografie.glob("*_*.png")):
        pagina, forma = png.stem.rsplit("_", 1)
        if forma not in ("computer", "telefono"):
            continue
        with Image.open(png) as immagine:
            immagine.convert("RGB").save(arrivo / f"{pagina}_{forma}.jpg", "JPEG", quality=82, optimize=True, progressive=True)
            if pagina == "home" and forma == "computer":
                prima = immagine.convert("RGB").crop((0, 0, immagine.width, min(immagine.height, round(immagine.width * 900 / 1440))))
                prima.thumbnail((480, 300))
                prima.save(arrivo / "anteprima.jpg", "JPEG", quality=80)
        pagine.setdefault(pagina, {})[forma] = f"{pagina}_{forma}.jpg"
    if "home" not in pagine:
        raise RuntimeError(f"{idCliente}: mancano le schermate della home del product manager in {fotografie}")
    contratto = json.loads(Path(copia["contratto"]).read_text(encoding="utf-8-sig")) if Path(copia["contratto"]).is_file() else {}
    ordine = list(NOMI_DELLE_PAGINE)
    schermate = [{"pagina": NOMI_DELLE_PAGINE.get(p, p.replace("-", " ").capitalize()), **pagine[p]}
                 for p in sorted(pagine, key=lambda p: (ordine.index(p) if p in ordine else len(ordine), p))]
    voce = {"idCliente": idCliente, "nome": scheda.get("nome", ""), "tipo": scheda.get("tipo", ""),
            "blocco": nomeDelBlocco(scheda.get("industria")), "industria": scheda.get("industria", ""),
            "sezione": scheda.get("sezioneCompleta", ""), "pacchetto": contratto.get("pacchetto", ""), "modello": copia.get("modello", ""),
            "link": link, "pronta": datetime.datetime.now().astimezone().isoformat(timespec="seconds"),
            "anteprima": "anteprima.jpg" if (arrivo / "anteprima.jpg").is_file() else "", "schermate": schermate}
    # l'oggetto 3D che gira, computer e telefono, dal link online (Michele, 12/11/2026, task #681): se la cattura non riesce
    # la scheda nasce lo stesso e il motivo va nel registro del passo
    try:
        from ._03_AnteprimaDellOggetto3D import anteprimaDellOggetto3D
        voce["oggetto3d"] = anteprimaDellOggetto3D(link, arrivo)
        motivo3d = ""
    except Exception as errore:
        motivo3d = f"anteprima 3D non creata: {errore}"[:300]
    # tutte le pagine in una sola schermata, computer e telefono (Michele, 13/11/2026): se non riesce restano le pagine singole
    try:
        from ._05_TutteLePagineInUnaSchermata import tutteLePagineInUnaSchermata
        voce["unica"] = tutteLePagineInUnaSchermata(arrivo, schermate)
    except Exception as errore:
        motivo3d = (motivo3d + " | " if motivo3d else "") + f"schermata unica non creata: {errore}"[:200]
    (arrivo / "scheda.json").write_text(json.dumps(voce, ensure_ascii=False, indent=1), encoding="utf-8")
    return {"esito": "GO", "cartella": str(arrivo), "pagine": len(schermate), "oggetto3d": motivo3d or "creata"}

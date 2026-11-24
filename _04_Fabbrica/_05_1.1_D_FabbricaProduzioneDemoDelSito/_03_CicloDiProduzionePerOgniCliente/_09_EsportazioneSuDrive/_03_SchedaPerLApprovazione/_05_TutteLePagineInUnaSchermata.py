"""Passo 9.3: tutte le pagine della demo in una sola schermata, una per il computer e una per il telefono (Michele, 13/11/2026).

Michele apre una schermata sola e vede tutte le pagine, una sotto l'altra, divise da una fascia con il nome della pagina.
Le schermate delle singole pagine restano (servono a comporre questa). Nella scheda: "unica" = {forma: {file, sezioni}}, dove
le sezioni dicono a che altezza inizia ogni pagina, così il Centro Gestione può saltare alla pagina con un clic.
Uso da riga di comando, per le demo già in Approvazione: python _05_TutteLePagineInUnaSchermata.py [codice cliente]
"""

import json
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

Image.MAX_IMAGE_PIXELS = None
ALTEZZA_MASSIMA_DEL_JPEG = 65000
FASCIA = {"computer": 72, "telefono": 48}
CARATTERE = {"computer": 30, "telefono": 20}
SFONDO_DELLA_FASCIA, TESTO_DELLA_FASCIA, LINEA_DELLA_FASCIA = (8, 26, 36), (255, 255, 255), (23, 162, 255)


def carattere(misura):
    for nome in ("segoeuib.ttf", "arialbd.ttf", "arial.ttf"):
        try:
            return ImageFont.truetype(str(Path("C:/Windows/Fonts") / nome), misura)
        except OSError:
            continue
    return ImageFont.load_default()


def unaSchermata(cartella, schermate, forma):
    pezzi = [(voce["pagina"], cartella / voce[forma]) for voce in schermate if voce.get(forma) and (cartella / voce[forma]).is_file()]
    if not pezzi:
        return None
    immagini = [(pagina, Image.open(file).convert("RGB")) for pagina, file in pezzi]
    larghezza = max(im.width for _, im in immagini)
    fascia = FASCIA[forma]
    totale = sum(fascia + round(im.height * larghezza / im.width) for _, im in immagini)
    scala = min(1.0, ALTEZZA_MASSIMA_DEL_JPEG / totale)
    larghezzaFinale = max(1, round(larghezza * scala))
    fasciaFinale = max(24, round(fascia * scala))
    altezze = [round(im.height * larghezzaFinale / im.width) for _, im in immagini]
    tela = Image.new("RGB", (larghezzaFinale, sum(altezze) + fasciaFinale * len(immagini)), SFONDO_DELLA_FASCIA)
    disegno = ImageDraw.Draw(tela)
    scritta = carattere(max(12, round(CARATTERE[forma] * scala)))
    y, sezioni = 0, []
    for (pagina, im), altezza in zip(immagini, altezze):
        sezioni.append({"pagina": pagina, "y": y, "altezza": fasciaFinale + altezza})
        disegno.rectangle((0, y, larghezzaFinale, y + fasciaFinale - 1), fill=SFONDO_DELLA_FASCIA)
        disegno.rectangle((0, y + fasciaFinale - 4, larghezzaFinale, y + fasciaFinale - 1), fill=LINEA_DELLA_FASCIA)
        disegno.text((round(fasciaFinale * 0.4), y + (fasciaFinale - 4) / 2), pagina.upper(), font=scritta, fill=TESTO_DELLA_FASCIA, anchor="lm")
        tela.paste(im if im.width == larghezzaFinale and im.height == altezza else im.resize((larghezzaFinale, altezza), Image.LANCZOS),
                   (0, y + fasciaFinale))
        y += fasciaFinale + altezza
        im.close()
    nome = f"tutte-le-pagine_{forma}.jpg"
    tela.save(cartella / nome, "JPEG", quality=80, optimize=True, progressive=True)
    return {"file": nome, "larghezza": tela.width, "altezza": tela.height, "sezioni": sezioni}


def tutteLePagineInUnaSchermata(cartella, schermate):
    cartella = Path(cartella)
    unica = {}
    for forma in ("computer", "telefono"):
        risultato = unaSchermata(cartella, schermate, forma)
        if risultato:
            unica[forma] = risultato
    return unica


def recupero(soloQuesto=None):
    radice = Path(__file__).absolute().parents[3] / "_01_StrumentiDellaFabbrica" / "_09_DemoInApprovazione"
    fatte, errori = 0, []
    for file in sorted(radice.glob("*/scheda.json")):
        if soloQuesto and file.parent.name != soloQuesto:
            continue
        try:
            voce = json.loads(file.read_text(encoding="utf-8-sig"))
            voce["unica"] = tutteLePagineInUnaSchermata(file.parent, voce.get("schermate") or [])
            file.write_text(json.dumps(voce, ensure_ascii=False, indent=1), encoding="utf-8")
            fatte += 1
        except Exception as errore:
            errori.append(f"{file.parent.name}: {errore}")
    print(f"schermate uniche create: {fatte}, errori: {len(errori)}")
    for riga in errori:
        print(riga)


if __name__ == "__main__":
    recupero(sys.argv[1] if len(sys.argv) > 1 else None)

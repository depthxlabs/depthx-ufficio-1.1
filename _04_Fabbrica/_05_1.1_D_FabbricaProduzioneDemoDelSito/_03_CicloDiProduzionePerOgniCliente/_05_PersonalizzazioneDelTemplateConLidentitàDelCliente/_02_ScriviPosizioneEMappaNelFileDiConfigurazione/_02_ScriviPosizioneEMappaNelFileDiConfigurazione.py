"""Passo 5.2: via, CAP, comune, provincia e link della mappa del cliente nel file di configurazione (assets/js/config.js).

La posizione viene dai dati del CRM. Il link della mappa apre Google Maps sulla struttura (con il place id, se c'è).
Si scrivono solo i valori che esistono. I campi di ogni template sono in _01_CampiNelFileDiConfigurazione.json.
"""

import json
import re
from pathlib import Path
from urllib.parse import quote_plus

FILE_DEI_CAMPI = Path(__file__).absolute().parent / "_01_CampiNelFileDiConfigurazione.json"


def scriviPosizioneEMappaNelFileDiConfigurazione(sito, datiUnici):
    crm = datiUnici["crm"]
    valori = {campo: (crm.get(campo) or "").strip() for campo in ("via", "cap", "comune", "provincia")}
    ricerca = quote_plus(" ".join(v for v in (crm.get("nome"), valori["via"], valori["comune"]) if v))
    placeId = (crm.get("googleMaps") or "").strip()
    valori["mappa"] = (f"https://www.google.com/maps/search/?api=1&query={ricerca}"
                       + (f"&query_place_id={placeId}" if placeId.startswith("ChIJ") else "")) if ricerca else ""
    file = Path(sito) / "assets" / "js" / "config.js"
    variabile = re.search(r"window\.(\w+)\s*=", file.read_text(encoding="utf-8-sig")).group(1)
    campi = json.loads(FILE_DEI_CAMPI.read_text(encoding="utf-8-sig"))[variabile]
    righe = [f"window.{variabile}.{campi[campo]} = {json.dumps(valore, ensure_ascii=False)};"
             for campo, valore in valori.items() if campi.get(campo) and valore]
    # le coordinate per la mappa di OpenStreetMap (Michele, 11/11/2026)
    from ._03_CoordinateDellaStrutturaDaOpenStreetMap import coordinateDellaStrutturaDaOpenStreetMap
    valori["latitudine"], valori["longitudine"] = coordinateDellaStrutturaDaOpenStreetMap(valori["via"], valori["cap"], valori["comune"], valori["provincia"])
    if valori["latitudine"] and variabile == "SITO_CONFIG":
        righe += [f"window.{variabile}.contatti.latitudine = {json.dumps(valori['latitudine'])};",
                  f"window.{variabile}.contatti.longitudine = {json.dumps(valori['longitudine'])};"]
    with file.open("a", encoding="utf-8") as config:
        config.write("\n/* DepthX, fabbrica dei siti: posizione e mappa del cliente. */\n" + "\n".join(righe) + "\n")
    # l'indirizzo sulla faccia dell'elemento 3D: solo le parti che esistono. Con un segnaposto vuoto (per esempio la provincia)
    # la frase restava incompleta e la faccia usciva con la sola icona della posizione.
    indirizzo = ", ".join(x for x in (valori["via"], " ".join(y for y in (valori["cap"], valori["comune"]) if y)) if x)
    if indirizzo and valori["provincia"]:
        indirizzo += f" ({valori['provincia']})"
    if indirizzo:
        import html as _html
        for pagina in Path(sito).glob("*.html"):
            codice = pagina.read_text(encoding="utf-8-sig")
            if "{via}, {cap} {comune} ({provincia})" in codice:
                pagina.write_text(codice.replace("{via}, {cap} {comune} ({provincia})", _html.escape(indirizzo, quote=False)), encoding="utf-8")
    # implementare post template: latitudine e longitudine, quando il motore di download le salverà nella scheda Google.
    return valori

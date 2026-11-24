"""Manager del passo 5.8.4: i fatti veri del cliente, i fatti provati dal suo materiale, la verifica di ogni frase
completa e le frasi completate con loro.

I valori delle graffe ricavati dal materiale (con la loro citazione) si aggiungono ai fatti veri del CRM, senza mai
sostituirli. Il WhatsApp del cliente resta solo se il suo materiale dice che lo usa (fatto usaWhatsapp). Poi ogni frase completa si verifica sul materiale: nella pagina entrano solo frasi verificate.
I fatti provati e la verifica delle frasi si fanno insieme (_11_FattiEVerificaInUnaSolaChiamata.py, stesse regole di _06 e
_09): una parte per ogni gruppo di materiale del cliente e le verifiche delle altre frasi, tutte in parallelo, ai modelli
gratuiti di FreeLLMAPI. Se nessun modello risponde il passo dà NOTGO di sistema e si rifà al giro dopo.
"""

import json
from pathlib import Path

from ._01_FattiVeriDelCliente import fattiVeriDelCliente
from ._02_CompletaLaFraseConIFattiVeriDelCliente import completaLaFraseConIFattiVeriDelCliente
from ._11_FattiEVerificaInUnaSolaChiamata import fattiEVerificaInUnaSolaChiamata

FILE_DEI_FATTI_DALLE_FOTO = Path(__file__).absolute().parent / "_10_FattiProvatiDalleFotoDelCliente.json"


def completaLaFraseConIFattiVeriDelClienteManager(frasi, datiUnici, schedaDelCliente, recensioni, sceneConFoto=()):
    fatti = fattiVeriDelCliente(datiUnici, schedaDelCliente)
    if sceneConFoto:
        fatti["fotoDelCliente"] = ", ".join(sorted(sceneConFoto))  # il modello le vede nei dati della verifica
    insieme = fattiEVerificaInUnaSolaChiamata(frasi, datiUnici, recensioni, fatti)
    trovati = insieme
    # le foto del cliente provano le loro aree: la foto del ristorante prova il ristorante (Michele, 8/11/2026)
    dalleFoto = json.loads(FILE_DEI_FATTI_DALLE_FOTO.read_text(encoding="utf-8-sig"))["scene"]
    for scena in sceneConFoto:
        if dalleFoto.get(scena):
            trovati["provati"].setdefault(dalleFoto[scena], {"citazione": f"la foto del cliente della scena {scena}",
                                                              "fonte": "foto del cliente"})
    for graffa, voce in trovati["dati"].items():
        fatti.setdefault(graffa, voce["valore"])
    if "usaWhatsapp" not in trovati["provati"]:
        # il cliente non dice di usare WhatsApp: il passo 5.8.6 toglie pulsanti, link e frasi WhatsApp (Michele, 8/11/2026)
        fatti.pop("whatsapp", None)
    verifica = insieme
    return {"frasi": completaLaFraseConIFattiVeriDelCliente(frasi, fatti, trovati["provati"], verifica["verificate"]),
            "fatti": fatti, "provati": trovati["provati"], "datiDalMateriale": trovati["dati"],
            "verificate": verifica["verificate"], "dalSito": verifica["dalSito"], "inglese": verifica.get("inglese", {})}

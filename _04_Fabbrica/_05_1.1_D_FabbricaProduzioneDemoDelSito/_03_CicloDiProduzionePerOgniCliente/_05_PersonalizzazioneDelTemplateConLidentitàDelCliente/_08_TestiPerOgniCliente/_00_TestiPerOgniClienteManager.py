"""Manager del passo 5.8: i testi del cliente, con le sole frasi approvate e verificate, completate con i fatti veri.

Una sezione con le foto del cliente non esce mai (Michele, 8/11/2026). Ogni sezione finisce con 2 o 3 frasi verificate (passo 5.8.7, che gira prima del 5.8.6 per vedere anche le frasi che
escono). L'elenco delle frasi verificate (del copywriting e del sito
del cliente) va in frasiVerificate.json nella cartella del cliente in corso, accanto al sito: il collaudo 7.7 lo usa per
fermare qualunque frase non verificata e la correzione del passo 10 può usare solo quelle.
Sostituzioni (Michele, 9/11/2026): subito dopo il passo 5.8.5, una frase non verificata si sostituisce nel suo elemento
con una verificata della sezione, poi con una del sito del cliente, poi con una approvata senza fatti (passo 5.8.6); esce
solo se non c'è nessuna sostituta. Le sostituzioni vanno nel risultato (frasiSostituite) e le sostitute in frasiVerificate.json.
"""

import html
import json
from pathlib import Path

from ._03_ScegliUnaFraseApprovataPerOgniSezione._00_ScegliUnaFraseApprovataPerOgniSezioneManager import \
    scegliUnaFraseApprovataPerOgniSezioneManager
from ._04_CompletaLaFraseConIFattiVeriDelCliente._00_CompletaLaFraseConIFattiVeriDelClienteManager import \
    completaLaFraseConIFattiVeriDelClienteManager
from ._05_ScriviIlTestoNellaPagina._00_ScriviIlTestoNellaPaginaManager import scriviIlTestoNellaPaginaManager
from ._06_TogliLeSezioniSenzaUnaFraseCompleta._00_TogliLeSezioniSenzaUnaFraseCompletaManager import \
    sostituisciLeFrasiNonVerificateManager, togliLeSezioniSenzaUnaFraseCompletaManager
from ._07_DueOTreFrasiPerOgniSezione._00_DueOTreFrasiPerOgniSezioneManager import dueOTreFrasiPerOgniSezioneManager

NOME_DELLE_FRASI_VERIFICATE = "frasiVerificate.json"


def testiPerOgniClienteManager(sito, datiUnici, schedaDelCliente, recensioni, sceneConFoto=()):
    frasi = scegliUnaFraseApprovataPerOgniSezioneManager(sito)
    completate = completaLaFraseConIFattiVeriDelClienteManager(frasi, datiUnici, schedaDelCliente, recensioni, sceneConFoto)
    scritte = scriviIlTestoNellaPaginaManager(sito, completate)
    sostituite = sostituisciLeFrasiNonVerificateManager(sito, completate)
    sezioni = dueOTreFrasiPerOgniSezioneManager(sito, completate, sceneConFoto)
    tolte = togliLeSezioniSenzaUnaFraseCompletaManager(sito, completate["frasi"], completate["fatti"], sceneConFoto)
    verificate = sorted({html.unescape(frase) for frase in completate["verificate"]}
                        | {html.unescape(frase) for elenco in completate["dalSito"].values() for frase in elenco}
                        | {html.unescape(voce["sostituta"]) for voce in sostituite})
    (Path(sito).parent / NOME_DELLE_FRASI_VERIFICATE).write_text(json.dumps(verificate, ensure_ascii=False, indent=1),
                                                                 encoding="utf-8")
    prove = {frase["italiano"]: frase["prova"] for frase in completate["frasi"] if frase.get("prova")}
    for voce in sezioni["aggiunte"]:
        prove.setdefault(voce["frase"], completate["verificate"].get(voce["frase"]) or {"fonte": "sito del cliente"})
    return {"frasiScritte": scritte, "frasiSostituite": sostituite, "frasiTolte": tolte, "sezioni": sezioni, "fatti": completate["fatti"],
            "provati": completate["provati"], "verificate": verificate, "prove": prove}

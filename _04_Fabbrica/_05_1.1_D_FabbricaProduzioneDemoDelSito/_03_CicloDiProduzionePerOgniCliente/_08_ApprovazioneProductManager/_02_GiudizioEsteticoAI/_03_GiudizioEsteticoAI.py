"""Passo 8.2: il product manager controlla che la demo rispetti la direzione fissa della fabbrica.

La fabbrica produce ogni demo in una direzione lineare, già perfetta; il product manager non giudica a caso, controlla
solo i punti fissi della checklist di _02_IstruzioniPerIlProductManager.md (apertura intera, niente sovrapposizioni,
niente riquadri vuoti, testo leggibile, niente graffe o inglese, niente frasi ripetute, ogni azione con il suo
pulsante, menu leggibile sul telefono). Passa o non passa: niente note e niente consigli (Michele, 8/11/2026).
Una chiamata ai modelli gratuiti di FreeLLMAPI che leggono le immagini, con le ripetizioni: legge le fotografie
di tutte le pagine del passo 8.1 (pacchetto Advanced, Michele 11/11/2026) e il testo che il visitatore vede nella pagina (letto da Chrome con la fotografia del computer;
senza, le frasi italiane del codice), senza le recensioni, che sono degli ospiti.
Restituisce l'esito e, solo se non passa, i punti della checklist non passati. Se nessun modello risponde dopo le
ripetizioni, NOTGO di sistema: il passo si rifà al giro dopo.
"""

import json
import tempfile
from pathlib import Path

from ..._07_CollaudoBasicoDellaDemo._07_ControlloCheOgniFraseSiaDelCopywritingApprovato._01_FrasiItalianeDellePagine import \
    frasiItalianeDellePagine

CARTELLA = Path(__file__).absolute().parent
FILE_DELLE_REGOLE = CARTELLA / "_01_RegoleDelGiudizio.json"
FILE_DELLE_ISTRUZIONI = CARTELLA / "_02_IstruzioniPerIlProductManager.md"
PUNTI_DELLA_CHECKLIST = tuple(str(numero) for numero in range(1, 19))  # i 18 punti, dall'11/11/2026 (Michele, pacchetto Advanced)


LATO_MASSIMO_DELLA_FOTOGRAFIA = 1600


def esitoDelGiudizio(giudizio):
    punti = giudizio.get("punti") if isinstance(giudizio.get("punti"), dict) else {}
    nonPassati = [str(voce) for voce in giudizio.get("nonPassati") or []]
    falliti = [numero for numero in PUNTI_DELLA_CHECKLIST if punti.get(numero) is not True]
    if falliti and not nonPassati:
        nonPassati = [f"punto {numero}: non passa" for numero in falliti]
    approvata = not falliti and not nonPassati
    return {"esito": "GO" if approvata else "NOTGO", "note": {} if approvata else {"checklist": nonPassati}}


def giudizioDaiModelliGratuiti(fotografie, frasi):
    """Il giudizio da FreeLLMAPI: le fotografie delle pagine allegate, ridotte a 1600 pixel sul lato lungo, nell'ordine
    in cui le istruzioni le nominano. Il risultato {esito, note}; se nessun modello risponde, NessunModelloRisponde."""
    from PIL import Image
    from _03_CicloDiProduzionePerOgniCliente._05_PersonalizzazioneDelTemplateConLidentitàDelCliente._08_TestiPerOgniCliente._04_CompletaLaFraseConIFattiVeriDelCliente._07_FattiProvatiDalMaterialeDelCliente import chiediAFreeLLM
    # al massimo 10 fotografie per chiamata: la home sul computer e sul telefono, poi le altre pagine
    ordine = (["computer", "telefono"] + [chiave for chiave in fotografie if "|" in chiave])[:10]
    with tempfile.TemporaryDirectory(prefix="dxgiudizio_", ignore_cleanup_errors=True) as corta:
        allegati, nomi = [], {}
        for numero, chiave in enumerate(ordine, 1):
            try:
                with Image.open(fotografie[chiave]) as immagine:
                    immagine = immagine.convert("RGB")
                    immagine.thumbnail((LATO_MASSIMO_DELLA_FOTOGRAFIA, LATO_MASSIMO_DELLA_FOTOGRAFIA))
                    percorso = Path(corta) / f"pagina{numero:02d}.jpg"
                    immagine.save(percorso, "JPEG", quality=80)
            except (OSError, KeyError):
                continue
            allegati.append(percorso)
            nomi[chiave] = f"l'immagine allegata numero {len(allegati)}"
        if not allegati:
            raise RuntimeError("NOTGO di sistema: nessuna fotografia della demo da mandare al product manager")
        istruzioni = (FILE_DELLE_ISTRUZIONI.read_text(encoding="utf-8-sig")
                      .replace("Apri con lo strumento Read le fotografie di tutte le pagine.", "Le fotografie di tutte le pagine sono allegate.")
                      .replace("{computer}", nomi.get("computer", "non disponibile")).replace("{telefono}", nomi.get("telefono", "non disponibile"))
                      .replace("{altrePagine}", "\n".join(f"- {chiave.replace('|', ' sul ')}: {nome}" for chiave, nome in nomi.items() if "|" in chiave) or "- nessuna")
                      .replace("{frasi}", "\n".join(frasi)))
        giudizio = chiediAFreeLLM(istruzioni, allegati, 330, valida=lambda r: isinstance(r.get("punti"), dict))
    return esitoDelGiudizio(giudizio)


def giudizioEsteticoAI(sito, fotografie, recensioni):
    regole = json.loads(FILE_DELLE_REGOLE.read_text(encoding="utf-8-sig"))
    ospiti = " ".join(" ".join((voce.get("testo") or "").split()) for voce in recensioni)
    frasi = []
    testoVisto = Path(fotografie["computer"]).with_suffix(".txt")
    righe = (testoVisto.read_text(encoding="utf-8", errors="ignore").splitlines() if testoVisto.is_file()
             else frasiItalianeDellePagine(sito))
    for frase in (" ".join(riga.split()) for riga in righe):
        if not frase:
            continue
        if frase not in frasi and not (len(frase) >= 25 and frase in ospiti):
            frasi.append(frase)
    return giudizioDaiModelliGratuiti(fotografie, frasi[:int(regole["frasiMassime"])])

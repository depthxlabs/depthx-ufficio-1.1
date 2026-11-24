"""Passo 4.1, prima della scelta: le categorie precise delle foto scaricate nel passo 3.6.

Il motore dà alle foto categorie larghe ("struttura", "prodotti", "altro") che non sono quelle che chiedono le aree dei
contratti dei template ("esterno della struttura", "camere", "ristorante"...): senza questo passo quasi tutte le aree
restavano vuote e la demo spoglia (8/11/2026). Le miniature delle foto scaricate vanno in una cartella dal percorso corto
e Claude sul server (claude -p, una sola chiamata per cliente, al minimo) guarda ogni foto e le dà una categoria di
_05_RegoleDelleCategoriePreciseDelleFoto.json, con le istruzioni di _06_IstruzioniPerLeCategoriePreciseDelleFoto.md.
Nella stessa chiamata Claude dà a ogni foto anche il voto di bellezza da 1 a 10 e il riquadro del soggetto (Michele,
8/11/2026): il voto sceglie la foto migliore di ogni area, il soggetto guida i tagli. Le miniature sono girate nel verso
giusto, come le foto che poi si tagliano, così il riquadro corrisponde.
Restituisce le foto in ordine con la categoria precisa ("scartare" diventa "altro", che nelle aree non entra mai), con
"voto" e "soggetto" ([sinistra, alto, destra, basso] da 0 a 1) quando Claude li ha dati.
Se Claude non risponde, le foto restano con la categoria del motore.
Il giudizio di ogni foto si salva in _08_GiudiziGiaDatiAlleFoto, con l'identità della foto su Drive: al giro dopo la stessa
foto ha lo stesso giudizio e a Claude vanno solo le foto mai viste, così la scelta delle foto non cambia da un giro
all'altro (Michele, 9/11/2026).
Pitstop 9 (Michele, 12/11/2026, task #614): nelle istruzioni (_06) un bagno è tale solo se si vedono wc, doccia, vasca o bidet;
un lavello con il piano di lavoro è una cucina (sotto "Le camere" compariva una cucina presa per un bagno). Copia: .copiaPrimaVelocita.
"""

import json
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

from PIL import Image, ImageOps

CARTELLA = Path(__file__).absolute().parent
FILE_DELLE_REGOLE = CARTELLA / "_05_RegoleDelleCategoriePreciseDelleFoto.json"
FILE_DELLE_ISTRUZIONI = CARTELLA / "_06_IstruzioniPerLeCategoriePreciseDelleFoto.md"
PROGRAMMA_DI_CLAUDE = Path.home() / ".local" / "bin" / "claude.exe"
# il giudizio dato a ogni foto (categoria, voto, soggetto), un file per foto con l'identità della foto su Drive
# dal 9/11/2026 le categorie nuove (cucina, soggiorno, terrazze): i giudizi con le categorie di prima non valgono più
CARTELLA_DEI_GIUDIZI = CARTELLA / "_09_GiudiziGiaDatiAlleFotoConLeCategorieDel9Novembre"


def giudizioGiaDato(idFoto):
    file = CARTELLA_DEI_GIUDIZI / f"{re.sub(r'[^A-Za-z0-9_-]', '_', str(idFoto))}.json"
    try:
        return json.loads(file.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def salvaIlGiudizio(idFoto, giudizio):
    CARTELLA_DEI_GIUDIZI.mkdir(exist_ok=True)
    file = CARTELLA_DEI_GIUDIZI / f"{re.sub(r'[^A-Za-z0-9_-]', '_', str(idFoto))}.json"
    file.write_text(json.dumps(giudizio, ensure_ascii=False), encoding="utf-8")


def categoriePreciseDelleFoto(fotoInOrdine, fotoScaricate):
    # la stessa foto riceve sempre lo stesso giudizio: si chiede a Claude solo per le foto mai viste (Michele, 9/11/2026)
    giaDati = {voce["id"]: giudizioGiaDato(voce["id"]) for voce in fotoInOrdine if voce.get("id") in fotoScaricate}
    giaDati = {idFoto: giudizio for idFoto, giudizio in giaDati.items() if giudizio}
    nuovi = categorieDaClaude([voce for voce in fotoInOrdine if voce.get("id") not in giaDati], fotoScaricate)
    for idFoto, giudizio in nuovi.items():
        salvaIlGiudizio(idFoto, giudizio)
    precise = {**giaDati, **nuovi}
    # foto e sezione coincidono (Michele, 9/11/2026): una foto senza il giudizio di Claude non entra in nessuna area
    return [{**voce, "categoriaDelMotore": voce.get("categoria"), **precise[voce["id"]]}
            if voce.get("id") in precise else {**voce, "categoriaDelMotore": voce.get("categoria"), "categoria": "altro"}
            for voce in fotoInOrdine]


FOTO_PER_CHIAMATA = 8


def categorieDaiModelliGratuiti(istruzioni, nomi, cartella):
    """Le categorie da FreeLLMAPI, 8 miniature per chiamata. Il dizionario nome -> giudizio, o None se un gruppo non risponde."""
    from _03_CicloDiProduzionePerOgniCliente._05_PersonalizzazioneDelTemplateConLidentitàDelCliente._08_TestiPerOgniCliente._04_CompletaLaFraseConIFattiVeriDelCliente._07_FattiProvatiDalMaterialeDelCliente import chiediAFreeLLM
    risultato = {}
    for inizio in range(0, len(nomi), FOTO_PER_CHIAMATA):
        gruppo = nomi[inizio:inizio + FOTO_PER_CHIAMATA]
        testo = re.sub(r"Le foto di una struttura ricettiva sono in questa cartella:[^\n]*",
                       "Le foto di una struttura ricettiva sono allegate, nell'ordine: " + ", ".join(gruppo) + ".", istruzioni)
        testo = testo.replace("Apri ogni foto con lo strumento Read.", "Guarda ogni foto allegata.")
        testo += "\n\nRispondi con un oggetto JSON che ha come chiavi esattamente questi nomi: " + ", ".join(gruppo) + "."
        risposta = chiediAFreeLLM(testo, [cartella / nome for nome in gruppo], 120)
        if not isinstance(risposta, dict):
            return None
        risultato.update({nome: giudizio for nome, giudizio in risposta.items() if nome in gruppo})
    return risultato


def categorieDaClaude(fotoInOrdine, fotoScaricate):
    regole = json.loads(FILE_DELLE_REGOLE.read_text(encoding="utf-8-sig"))
    programma = shutil.which("claude") or (str(PROGRAMMA_DI_CLAUDE) if PROGRAMMA_DI_CLAUDE.is_file() else "")
    scaricate = [voce for voce in fotoInOrdine if voce.get("id") in fotoScaricate]
    if not scaricate:
        return {}
    lato = int(regole["latoMassimoDellaMiniatura"])
    with tempfile.TemporaryDirectory(prefix="dxfoto_", ignore_cleanup_errors=True) as corta:
        nomi = {}
        for numero, voce in enumerate(scaricate, 1):
            nome = f"f{numero:02d}.jpg"
            try:
                with Image.open(fotoScaricate[voce["id"]]) as immagine:
                    immagine = ImageOps.exif_transpose(immagine).convert("RGB")
                    immagine.thumbnail((lato, lato))
                    immagine.save(Path(corta) / nome, "JPEG", quality=82)
            except OSError:
                continue
            nomi[nome] = voce["id"]
        istruzioni = FILE_DELLE_ISTRUZIONI.read_text(encoding="utf-8-sig").replace("{elenco}", ", ".join(nomi))
        # prima i modelli gratuiti di FreeLLMAPI: le miniature vanno allegate, 8 per chiamata, con i loro nomi nell'ordine
        categorie = categorieDaiModelliGratuiti(istruzioni, list(nomi), Path(corta))
        if categorie is None and programma:
            try:
                esito = subprocess.run([programma, "-p", "--model", regole["modello"], "--allowedTools", "Read",
                                        "--max-turns", str(regole["turniMassimi"]), "--output-format", "json"],
                                       input=istruzioni, capture_output=True, text=True, encoding="utf-8", errors="ignore", cwd=corta,
                                       timeout=int(regole["secondiMassimi"]), creationflags=subprocess.CREATE_NO_WINDOW)
                risposta = json.loads(esito.stdout).get("result", "")
                categorie = json.loads(re.search(r"\{.*\}", risposta, re.S).group(0))
            except (ValueError, AttributeError, subprocess.TimeoutExpired):
                categorie = None
        if not categorie:
            # nessun modello ha risposto: è un errore di sistema, non un cliente senza foto. Senza questo controllo tutte le foto
            # restavano "altro" e il cliente veniva escluso per materiale insufficiente (24/11/2026, prima prova su GitHub)
            raise RuntimeError("riconoscimento delle foto non riuscito: nessun modello ha risposto")
    ammesse = set(regole["categorie"])
    precise = {}
    for nome, giudizio in categorie.items():
        if nome not in nomi:
            continue
        giudizio = giudizio if isinstance(giudizio, dict) else {"categoria": giudizio}
        categoria = giudizio.get("categoria")
        precisa = {"categoria": categoria if categoria in ammesse else "altro"}
        try:
            precisa["voto"] = max(1.0, min(10.0, float(giudizio["voto"])))
        except (KeyError, TypeError, ValueError):
            pass
        precisa["scritte"] = giudizio.get("scritte") is True
        soggetto = giudizio.get("soggetto")
        try:
            sinistra, alto, destra, basso = [max(0.0, min(100.0, float(valore))) / 100 for valore in soggetto]
            if destra - sinistra >= 0.05 and basso - alto >= 0.05:
                precisa["soggetto"] = [sinistra, alto, destra, basso]
        except (TypeError, ValueError):
            pass
        precise[nomi[nome]] = precisa
    return precise

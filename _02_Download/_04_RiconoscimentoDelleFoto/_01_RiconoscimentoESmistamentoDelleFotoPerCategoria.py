"""Riconoscimento delle foto: scarto delle foto piccole, sfocate o doppie e classificazione di tutte le foto valide.

Le misure (lato, nitidezza, firma per i doppioni) e una miniatura temporanea si fanno al momento dello scaricamento.
La classificazione usa la vista di Claude (claude -p) su mosaici numerati, come la fabbrica dei siti.
Leggero sui token (Michele, 4/11/2026): piano Claude Max, sonnet con sforzo basso, un prompt di sistema di una riga al posto di quello
di Claude Code e un solo strumento, quello che legge l'immagine. I token di ogni mosaico vanno in
_05_RegistroEStatoDelMotore/tokenDelRiconoscimentoDelleFoto.jsonl.
Attesi: tutte le foto valide. Scaricati: le foto che hanno ricevuto categoria e voto. Un mosaico senza risposta
valida si riprova; le foto che restano senza categoria vanno nel motivo.
"""

import sys

sys.dont_write_bytecode = True

import json
import os
import re
import shutil
import subprocess
import time

import _02_PercorsiChiaviEFunzioniComuni as comune
from _04_ContestoDelClienteEConteggioDeiPassi import NOME_FILE_FOTO_VALIDE, Passo

LATO_CORTO_MINIMO = 600
NITIDEZZA_MINIMA = 45
VISTE_INSIEME = 3
SISTEMA = "Guardi le immagini con lo strumento Read e rispondi solo con un array JSON valido, senza altro testo."
FILE_DEI_TOKEN = os.path.join(comune.CARTELLA_DEL_REGISTRO, "tokenDelRiconoscimentoDelleFoto.jsonl")


def scriviToken(idCliente, token, esito):
    try:
        with open(FILE_DEI_TOKEN, "a", encoding="utf-8") as file:
            file.write(json.dumps({"ora": comune.adesso(), "idCliente": idCliente, "token": token, "esito": esito}) + "\n")
    except OSError:
        pass


def rispostaETokenDellaBusta(uscita):
    """Con --output-format json claude restituisce una busta: il testo della risposta e i token usati."""
    try:
        busta = json.loads(uscita or "{}")
    except ValueError:
        return uscita, 0
    uso = busta.get("usage") or {}
    return busta.get("result") or "", sum(int(uso.get(k) or 0) for k in ("input_tokens", "cache_creation_input_tokens", "cache_read_input_tokens", "output_tokens"))
LATO_DELLA_CASELLA = 400
# le 12 categorie dell'ospitalità decise da Michele (task 466, 4/11/2026)
CATEGORIE = ("esterno della struttura", "esterni senza struttura", "camere", "bagni", "piscina", "ristorante", "colazione", "prodotti",
             "persone", "locandine", "logo", "altro")
DOMANDA_DEL_MOSAICO = (
    "Guarda l'immagine {mosaico}: è un mosaico con {quante} foto di {nome} ({tipo}), ognuna con il suo numero nel riquadro giallo. "
    "Per ogni foto rispondi SOLO con un array JSON di oggetti con queste chiavi: "
    "\"n\" il numero; "
    "\"categoria\" una tra \"esterno della struttura\" (l'edificio o la struttura fotografati da fuori), "
    "\"esterni senza struttura\" (giardino, vista, paesaggio, territorio, senza l'edificio), \"camere\", \"bagni\", \"piscina\", "
    "\"ristorante\" (sala, tavoli, piatti serviti), \"colazione\", \"prodotti\" ({prodotti}), "
    "\"persone\" (persone in posa, ritratti, gruppi, staff), \"locandine\" (volantini, grafiche, foto con scritte sopra, annunci, menù con prezzi), "
    "\"logo\" (solo il marchio), \"altro\"; "
    "\"qualita\" voto da 1 a 10 come foto professionale per il sito: basso se sgranata, sfocata, mossa, buia, storta o con scritte sopra. "
    "Nessun altro testo."
)


def programmaClaude():
    trovato = shutil.which("claude")
    if trovato:
        return trovato
    nellaCartellaUtente = os.path.join(os.path.expanduser("~"), ".local", "bin", "claude.exe")
    return nellaCartellaUtente if os.path.isfile(nellaCartellaUtente) else None


def leggiRispostaJson(testo):
    for trovato in re.finditer(r"\[[\s\S]*?\](?=\s*$|\s*```)", testo or ""):
        try:
            return json.loads(trovato.group(0))
        except ValueError:
            continue
    trovato = re.search(r"\[[\s\S]*\]", testo or "")
    if trovato:
        try:
            return json.loads(trovato.group(0))
        except ValueError:
            return None
    return None


def creaMosaico(miniature, destinazione):
    from PIL import Image, ImageDraw, ImageFont

    colonne = 3
    righe = (len(miniature) + colonne - 1) // colonne
    mosaico = Image.new("RGB", (colonne * LATO_DELLA_CASELLA, righe * LATO_DELLA_CASELLA), "white")
    disegno = ImageDraw.Draw(mosaico)
    try:
        carattere = ImageFont.truetype("arial.ttf", 44)
    except OSError:
        carattere = ImageFont.load_default()
    for numero, percorso in enumerate(miniature, start=1):
        with Image.open(percorso) as miniatura:
            miniatura = miniatura.convert("RGB")
            x, y = ((numero - 1) % colonne) * LATO_DELLA_CASELLA, ((numero - 1) // colonne) * LATO_DELLA_CASELLA
            mosaico.paste(miniatura, (x + 4 + (LATO_DELLA_CASELLA - 8 - miniatura.width) // 2, y + 4 + (LATO_DELLA_CASELLA - 8 - miniatura.height) // 2))
        disegno.rectangle((x, y, x + 62, y + 54), fill="#ffd400")
        disegno.text((x + 10, y + 4), str(numero), fill="black", font=carattere)
    mosaico.save(destinazione, quality=86)


def miniaturaDellaFoto(contesto, chiave, voce):
    """Percorso della miniatura; in ripresa la foto si rilegge da Drive e si misura di nuovo."""
    percorso = os.path.join(contesto.miniature, comune.nomeDiFilePulito(chiave, 120) + ".jpg")
    if os.path.isfile(percorso) and voce["misure"].get("firma"):
        return percorso
    provvisorio = os.path.join(contesto.temporanea, "_ripresa_foto")
    contesto.destinazione.scaricaFile(voce["id"], provvisorio)
    try:
        voce["misure"].update(comune.verificaFile(provvisorio, "immagine"))
        voce["misure"].update(contesto._misureDellaFoto(provvisorio, chiave))
    finally:
        os.remove(provvisorio)
    return percorso


# Il riconoscimento sulla macchina, senza Claude: il modello di immagini OpenCLIP ViT-B-32 con lo strato di decisione addestrato
# sulle risposte già date da Claude (_02_StratoDiDecisioneAddestrato.json). Il voto di qualità viene da nitidezza e grandezza.
FILE_DELLO_STRATO = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_02_StratoDiDecisioneAddestrato.json")
_MODELLO = {}


def modelloSullaMacchina():
    if not _MODELLO:
        import open_clip
        import torch
        torch.set_num_threads(2)   # il processore resta libero per gli altri lavoratori
        modello, _, prepara = open_clip.create_model_and_transforms("ViT-B-32", pretrained="laion2b_s34b_b79k")
        modello.eval()
        with open(FILE_DELLO_STRATO, encoding="utf-8") as file:
            strato = json.load(file)
        _MODELLO.update(modello=modello, prepara=prepara, torch=torch, categorie=strato["categorie"],
                        pesi=torch.tensor(strato["pesi"]), scarti=torch.tensor(strato["scarti"]))
    return _MODELLO


def categorieSullaMacchina(miniature):
    from PIL import Image
    m, categorie = modelloSullaMacchina(), []
    for inizio in range(0, len(miniature), 16):
        immagini = m["torch"].stack([m["prepara"](Image.open(p).convert("RGB")) for p in miniature[inizio:inizio + 16]])
        with m["torch"].no_grad():
            v = m["modello"].encode_image(immagini)
            v = v / v.norm(dim=-1, keepdim=True)
            punteggi = v @ m["pesi"].T + m["scarti"]
        categorie += [m["categorie"][i] for i in punteggi.argmax(dim=-1).tolist()]
    return categorie


def votoDiQualita(riga, massimo):
    """Da 1 a 10: nitidezza e lato corto rispetto alla foto migliore del cliente."""
    valore = (riga.get("nitidezza") or 0) * min(riga.get("larghezza") or 0, riga.get("altezza") or 0)
    return max(1, min(10, round(10 * valore / massimo))) if massimo else 5


def esegui(contesto):
    passo = Passo("Riconoscimento delle foto")
    if comune.regola("riconoscimentoSullaMacchina") and os.path.isfile(FILE_DELLO_STRATO):
        return eseguiSullaMacchina(contesto, passo)
    if not programmaClaude():
        raise comune.ChiaveMancante("Il programma claude non è installato: il riconoscimento delle foto non si fa.")
    valide, scartate, firmeViste = [], [], {}
    for chiave, voce in contesto.stato["elementi"].items():
        if not voce.get("foto"):
            continue
        try:
            miniatura = miniaturaDellaFoto(contesto, chiave, voce)
        except Exception as errore:
            scartate.append({"chiave": chiave, "nome": voce["nome"], "motivo": "non leggibile: " + comune.messaggioSicuro(type(errore).__name__)})
            continue
        misure = voce["misure"]
        riga = {"chiave": chiave, "id": voce["id"], "nome": voce["nome"], "fonte": voce["passo"], "larghezza": misure.get("larghezza"),
                "altezza": misure.get("altezza"), "nitidezza": misure.get("nitidezza"), "miniatura": miniatura}
        if min(misure.get("larghezza") or 0, misure.get("altezza") or 0) < LATO_CORTO_MINIMO:
            scartate.append({**riga, "motivo": "piccola"})
        elif (misure.get("nitidezza") or 0) < NITIDEZZA_MINIMA:
            scartate.append({**riga, "motivo": "sfocata"})
        elif misure.get("firma") in firmeViste:
            scartate.append({**riga, "motivo": "doppione di " + firmeViste[misure["firma"]]})
        else:
            firmeViste[misure.get("firma")] = voce["nome"]
            valide.append(riga)
    passo.attesi = len(valide)
    perMosaico = int(comune.regola("fotoPerMosaicoDelRiconoscimento"))
    secondiMassimi = int(comune.regola("secondiMassimiDelRiconoscimento"))
    cartellaMosaici = os.path.join(contesto.temporanea, "_mosaici")
    os.makedirs(cartellaMosaici, exist_ok=True)
    daFare = [valide[inizio:inizio + perMosaico] for inizio in range(0, len(valide), perMosaico)]
    for ripetizione in range(int(comune.regola("ripetizioniPerMetodo"))):
        if not daFare:
            break
        inCorso, ancora = [], []
        for numeroGruppo, gruppo in enumerate(daFare):
            mosaico = os.path.join(cartellaMosaici, f"mosaico_{ripetizione}_{numeroGruppo:04d}.jpg")
            creaMosaico([riga["miniatura"] for riga in gruppo], mosaico)
            domanda = DOMANDA_DEL_MOSAICO.format(mosaico=mosaico, quante=len(gruppo), nome=contesto.cliente.get("nome", ""),
                                                 tipo=contesto.industria.get("tipoDiAttivita", ""), prodotti=contesto.industria.get("descrizioneDeiProdotti", ""))
            while len([voce for voce in inCorso if voce[0].poll() is None]) >= VISTE_INSIEME:
                time.sleep(0.5)
            comando = [programmaClaude(), "-p", domanda, "--tools", "Read", "--allowedTools", "Read", "--system-prompt", SISTEMA, "--effort", "low",
                       "--output-format", "json", "--setting-sources", "local", "--strict-mcp-config",
                       "--no-session-persistence", "--model", str(comune.regola("modelloDelRiconoscimento"))]
            processo = subprocess.Popen(comando, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, stdin=subprocess.DEVNULL, text=True, encoding="utf-8",
                                        errors="ignore", cwd=cartellaMosaici, creationflags=comune.PRIORITA_BASSA | comune.SENZA_FINESTRA)
            inCorso.append((processo, gruppo, time.time()))
        for processo, gruppo, inizio in inCorso:
            try:
                uscita, _ = processo.communicate(timeout=max(5, secondiMassimi - (time.time() - inizio)))
            except subprocess.TimeoutExpired:
                processo.kill()
                processo.communicate()
                ancora.append(gruppo)
                continue
            uscita, token = rispostaETokenDellaBusta(uscita)
            risposta = leggiRispostaJson(uscita)
            scriviToken(contesto.idCliente, token, "GO" if isinstance(risposta, list) else "NOTGO")
            assegnate = set()
            for voce in risposta if isinstance(risposta, list) else []:
                try:
                    riga = gruppo[int(voce["n"]) - 1]
                    riga["categoria"] = voce.get("categoria") if voce.get("categoria") in CATEGORIE else "altro"
                    riga["qualita"] = max(1, min(10, int(voce.get("qualita") or 1)))
                    assegnate.add(id(riga))
                except (KeyError, ValueError, TypeError, IndexError):
                    continue
            mancanti = [riga for riga in gruppo if id(riga) not in assegnate]
            if mancanti:
                ancora.append(mancanti)
        daFare = ancora
        if daFare:
            time.sleep(comune.regola("secondiDiAttesaTraLeRipetizioni")[min(ripetizione, 2)])
    shutil.rmtree(cartellaMosaici, ignore_errors=True)
    for gruppo in daFare:
        for riga in gruppo:
            passo.irraggiungibili.append({"elemento": riga["nome"], "motivo": "la vista di Claude non ha dato categoria e voto dopo le ripetizioni"})
    passo.scaricati = len([riga for riga in valide if riga.get("categoria")])
    for riga in valide + scartate:
        riga.pop("miniatura", None)
    conteggio = {categoria: len([riga for riga in valide if riga.get("categoria") == categoria]) for categoria in CATEGORIE}
    ordinate = sorted(valide, key=lambda riga: (-(riga.get("qualita") or 0), -(riga.get("nitidezza") or 0)))
    contesto.scriviJson("foto", "_01_RiconoscimentoDelleFoto.json", {"idCliente": contesto.idCliente, "categorie": conteggio, "valide": ordinate, "scartate": scartate})
    contesto.scriviJson("resto", NOME_FILE_FOTO_VALIDE, ordinate)
    contesto.stato["fotoValide"], contesto.stato["fotoScartate"], contesto.stato["categorie"] = len(valide), len(scartate), conteggio
    passo.dettagli = {"fotoRaccolte": len(valide) + len(scartate), "valide": len(valide), "scartate": len(scartate), "categorie": conteggio}
    return [passo]


def eseguiSullaMacchina(contesto, passo):
    """Lo stesso passo, senza Claude: stesso scarto delle foto piccole, sfocate o doppie, stessi file di risultato."""
    valide, scartate, firmeViste = [], [], {}
    for chiave, voce in contesto.stato["elementi"].items():
        if not voce.get("foto"):
            continue
        try:
            miniatura = miniaturaDellaFoto(contesto, chiave, voce)
        except Exception as errore:
            scartate.append({"chiave": chiave, "nome": voce["nome"], "motivo": "non leggibile: " + comune.messaggioSicuro(type(errore).__name__)})
            continue
        misure = voce["misure"]
        riga = {"chiave": chiave, "id": voce["id"], "nome": voce["nome"], "fonte": voce["passo"], "larghezza": misure.get("larghezza"),
                "altezza": misure.get("altezza"), "nitidezza": misure.get("nitidezza"), "miniatura": miniatura}
        if min(misure.get("larghezza") or 0, misure.get("altezza") or 0) < LATO_CORTO_MINIMO:
            scartate.append({**riga, "motivo": "piccola"})
        elif (misure.get("nitidezza") or 0) < NITIDEZZA_MINIMA:
            scartate.append({**riga, "motivo": "sfocata"})
        elif misure.get("firma") in firmeViste:
            scartate.append({**riga, "motivo": "doppione di " + firmeViste[misure["firma"]]})
        else:
            firmeViste[misure.get("firma")] = voce["nome"]
            valide.append(riga)
    passo.attesi = len(valide)
    leggibili = [riga for riga in valide if os.path.isfile(riga["miniatura"])]
    for riga, categoria in zip(leggibili, categorieSullaMacchina([riga["miniatura"] for riga in leggibili]) if leggibili else []):
        riga["categoria"] = categoria if categoria in CATEGORIE else "altro"
    massimo = max([(r.get("nitidezza") or 0) * min(r.get("larghezza") or 0, r.get("altezza") or 0) for r in valide] or [0])
    for riga in valide:
        riga["qualita"] = votoDiQualita(riga, massimo)
        if not riga.get("categoria"):
            passo.irraggiungibili.append({"elemento": riga["nome"], "motivo": "miniatura non leggibile per il riconoscimento sulla macchina"})
    passo.scaricati = len([riga for riga in valide if riga.get("categoria")])
    for riga in valide + scartate:
        riga.pop("miniatura", None)
    conteggio = {categoria: len([riga for riga in valide if riga.get("categoria") == categoria]) for categoria in CATEGORIE}
    ordinate = sorted(valide, key=lambda riga: (-(riga.get("qualita") or 0), -(riga.get("nitidezza") or 0)))
    contesto.scriviJson("foto", "_01_RiconoscimentoDelleFoto.json", {"idCliente": contesto.idCliente, "categorie": conteggio, "valide": ordinate,
                                                                    "scartate": scartate, "metodo": "sulla macchina, senza Claude"})
    contesto.scriviJson("resto", NOME_FILE_FOTO_VALIDE, ordinate)
    contesto.stato["fotoValide"], contesto.stato["fotoScartate"], contesto.stato["categorie"] = len(valide), len(scartate), conteggio
    passo.dettagli = {"fotoRaccolte": len(valide) + len(scartate), "valide": len(valide), "scartate": len(scartate), "categorie": conteggio,
                      "metodo": "sulla macchina, senza Claude"}
    return [passo]

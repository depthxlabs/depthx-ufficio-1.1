"""Rapporto di unicità: i settori in cui il cliente ha qualcosa di caratteristico, detto dai fatti del suo materiale.

Esempio: "ambiente: location immersa nel verde", "cocktail: drink con le erbe dell'orto". I settori li sceglie il modello,
da 3 a 8, con nomi brevi (Michele, 4/11/2026): così servono meno token di una lista fissa da scorrere tutta.
Legge da Drive quello che il motore ha già scaricato (recensioni, scheda Google, dati del CRM, testi del sito,
Instagram, YouTube), lo scrive in un unico testo corto con la fonte di ogni pezzo e chiede a Claude una frase per settore.
Ultra conservativo sui token: abbonamento Claude Max, modello sonnet con sforzo basso, nessuno strumento, un prompt di
sistema di una riga al posto di quello di Claude Code, circa 10.000 caratteri di materiale e una risposta corta.
Regola: niente inventato. Ogni settore ha una citazione copiata parola per parola dal materiale; il codice la cerca nel
materiale vero e scarta il settore se non la trova. Ogni chiamata scrive token, inizio e fine in
_05_RegistroEStatoDelMotore/tokenDelRapportoDiUnicita.jsonl, che il Centro Gestione mostra.
Il rapporto va in _01_RaccoltaMateriale/_10_IlRestoDeiDati/_05_RapportoDiUnicita.json: lo usano la fabbrica e l'invio.
"""

import sys

sys.dont_write_bytecode = True

import json
import os
import re
import subprocess
import time
import unicodedata

import _02_PercorsiChiaviEFunzioniComuni as comune
from _04_ContestoDelClienteEConteggioDeiPassi import NOME_FILE_DATI_CRM, Passo

NOME_DEL_PASSO = "Rapporto di unicità"
NOME_FILE_DEL_RAPPORTO = "_05_RapportoDiUnicita.json"
FORMATO = "settori"  # il formato del rapporto dal 4/11/2026: un rapporto di un formato vecchio si rifà
FILE_DEI_TOKEN = os.path.join(comune.CARTELLA_DEL_REGISTRO, "tokenDelRapportoDiUnicita.jsonl")
CARATTERI_MASSIMI = {"recensioni": 6500, "sito": 1500, "instagram": 800, "youtube": 400, "scheda": 600, "crm": 500}
CARATTERI_DI_UNA_RECENSIONE = 350
SISTEMA = "Rispondi solo con un oggetto JSON valido, in italiano, senza altro testo."
LUNGHEZZA_MINIMA_DI_UNA_CITAZIONE = 12

DOMANDA = (
    "Materiale vero di {nome} ({tipo}); ogni riga inizia con la fonte tra [ ]. Scegli da 3 a 8 settori in cui questa struttura ha qualcosa "
    "di caratteristico e concreto (nome del settore di 1-3 parole, per esempio ambiente, colazione, cocktail). Per ognuno una frase di massimo 8 parole "
    "e una citazione copiata parola per parola dal materiale (5-20 parole). Niente inventato, niente di generico. "
    "JSON: {{\"sintesi\":\"1 frase\",\"settori\":{{\"nome del settore\":{{\"frase\":\"...\",\"citazione\":\"...\"}}}}}}\n\n{materiale}"
)


def normalizza(testo):
    testo = unicodedata.normalize("NFKC", str(testo or "")).lower()
    testo = re.sub(r"[\"'«»“”‘’`´]", "", testo)
    return re.sub(r"\s+", " ", re.sub(r"[^\w\s]", " ", testo)).strip()


def pezzo(fonte, testo):
    testo = re.sub(r"\s+", " ", str(testo or "")).strip()
    return f"[{fonte}] {testo}" if testo else ""


def limita(righe, massimo):
    fuori, lunghezza = [], 0
    for riga in righe:
        if not riga:
            continue
        if lunghezza + len(riga) > massimo:
            # l'ultimo pezzo entra tagliato, così una pagina lunga non lascia fuori tutto il sito
            if massimo - lunghezza > 200:
                fuori.append(riga[:massimo - lunghezza])
            break
        fuori.append(riga)
        lunghezza += len(riga) + 1
    return fuori


def materialeDelCliente(contesto):
    """Il testo con tutto il materiale, una fonte per pezzo, e quante fonti di ogni tipo sono state lette."""
    leggi = lambda chiave, nome: contesto.destinazione.leggiJson(contesto.cartelle[chiave], nome) or {}
    parti, conteggio = [], {}
    crm = leggi("resto", NOME_FILE_DATI_CRM)
    parti += limita([pezzo("CRM " + chiave, valore) for chiave, valore in crm.items() if isinstance(valore, (str, int, float)) and str(valore).strip()],
                    CARATTERI_MASSIMI["crm"])
    scheda = leggi("scheda", "_02_SchedaGoogle.json")
    if scheda:
        parti += limita([pezzo("scheda Google " + chiave, json.dumps(valore, ensure_ascii=False) if isinstance(valore, (dict, list)) else valore)
                         for chiave, valore in scheda.items() if valore not in ("", None, [], {})], CARATTERI_MASSIMI["scheda"])
    recensioni = [voce for voce in leggi("recensioni", "_01_RecensioniGoogle.json").get("recensioni", []) if (voce.get("testo") or "").strip()]
    conteggio["recensioni"] = len(recensioni)
    utili = sorted(recensioni, key=lambda voce: -len(voce["testo"]))
    parti += limita([pezzo(f"recensione {numero} · {voce.get('autore') or 'ospite'}", voce["testo"][:CARATTERI_DI_UNA_RECENSIONE])
                     for numero, voce in enumerate(utili, start=1)], CARATTERI_MASSIMI["recensioni"])
    pagine = leggi("sito", "_01_PagineDelSito.json").get("pagine", [])
    conteggio["pagineDelSito"] = len(pagine)
    parti += limita([pezzo(f"sito {voce.get('url', '')}", " · ".join(filter(None, [voce.get("titolo"), voce.get("descrizione"), voce.get("testo")])))
                     for voce in pagine], CARATTERI_MASSIMI["sito"])
    instagram = leggi("instagram", "_01_ProfiloInstagram.json")
    datiInstagram = instagram.get("dati") or {}
    post = [voce for voce in instagram.get("post", []) if (voce.get("caption") or "").strip()]
    conteggio["postInstagram"] = len(post)
    parti += limita([pezzo("Instagram profilo", datiInstagram.get("biography"))] +
                    [pezzo(f"Instagram post {voce.get('timestamp', '')[:10]}", voce["caption"]) for voce in post], CARATTERI_MASSIMI["instagram"])
    youtube = leggi("youtube", "_01_CanaleEVideo.json")
    video = youtube.get("video", [])
    conteggio["videoYoutube"] = len(video)
    # canale e video come li dà YouTube Data API: titolo e descrizione dentro snippet
    parti += limita([pezzo("YouTube canale", ((youtube.get("canale") or {}).get("snippet") or {}).get("description"))] +
                    [pezzo(f"YouTube video {(voce.get('snippet') or {}).get('title', '')}", (voce.get("snippet") or {}).get("description")) for voce in video],
                    CARATTERI_MASSIMI["youtube"])
    return "\n".join(parti), conteggio


def leggiOggettoJson(testo):
    trovato = re.search(r"\{[\s\S]*\}", testo or "")
    if not trovato:
        return None
    try:
        return json.loads(trovato.group(0))
    except ValueError:
        return None


def scriviToken(**campi):
    """Una riga per inizio e fine di ogni chiamata: il Centro Gestione ne ricava se l'agente lavora e quanti token ha usato."""
    try:
        with open(FILE_DEI_TOKEN, "a", encoding="utf-8") as file:
            file.write(json.dumps({"ora": comune.adesso(), "pid": os.getpid(), **campi}, ensure_ascii=False) + "\n")
    except OSError:
        pass


def chiediIlRapporto(contesto, materiale):
    """Solo i modelli gratuiti di FreeLLMAPI sul server (dal 25/11/2026), con le ripetizioni delle regole del motore."""
    domanda = DOMANDA.format(materiale=materiale, nome=contesto.cliente.get("nome", ""), tipo=contesto.industria.get("tipoDiAttivita", "struttura ricettiva"))
    for ripetizione in range(int(comune.regola("ripetizioniPerMetodo"))):
        comune.battito()
        scriviToken(tipo="inizio", idCliente=contesto.idCliente, modello="FreeLLMAPI")
        rapporto = leggiOggettoJson(comune.chiediAFreeLLM(domanda, SISTEMA) or "")
        if isinstance(rapporto, dict) and isinstance(rapporto.get("settori"), dict):
            scriviToken(tipo="fine", idCliente=contesto.idCliente, token=0, esito="GO", modello="FreeLLMAPI")
            return rapporto, "", 0
        scriviToken(tipo="fine", idCliente=contesto.idCliente, token=0, esito="NOTGO", modello="FreeLLMAPI", motivo="nessun rapporto valido")
        time.sleep(comune.regola("secondiDiAttesaTraLeRipetizioni")[min(ripetizione, 2)])
    return None, "i modelli gratuiti non hanno dato un rapporto valido", 0


def provaValida(prova, corpo):
    citazione = normalizza((prova or {}).get("citazione"))
    return len(citazione) >= LUNGHEZZA_MINIMA_DI_UNA_CITAZIONE and citazione in corpo


def verifica(rapporto, materiale):
    """Tiene solo i settori con la citazione trovata parola per parola nel materiale."""
    corpo = normalizza(materiale)
    tenuti, scartati = {}, []
    for nome, voce in (rapporto.get("settori") or {}).items():
        if str(nome).strip() and isinstance(voce, dict) and (voce.get("frase") or "").strip() and provaValida(voce, corpo):
            tenuti[str(nome).strip().lower()] = {"frase": voce["frase"].strip(), "citazione": voce["citazione"].strip()}
        else:
            scartati.append(nome)
    rapporto["settori"] = tenuti
    return rapporto, scartati


def esegui(contesto):
    passo = Passo(NOME_DEL_PASSO)
    materiale, conteggio = materialeDelCliente(contesto)
    if not any(conteggio.values()):
        passo.piattaforma = "nessuna recensione con testo e nessun testo di sito, Instagram o YouTube: il rapporto si basa solo sui dati del CRM"
    passo.attesi = 1
    rapporto, motivo, token = chiediIlRapporto(contesto, materiale)
    if not rapporto:
        passo.irraggiungibili.append({"elemento": NOME_FILE_DEL_RAPPORTO, "motivo": motivo})
        return [passo]
    rapporto, scartati = verifica(rapporto, materiale)
    if not rapporto["settori"]:
        if not passo.piattaforma:
            passo.limite = "nessun settore con una citazione trovata parola per parola nel materiale"
            return [passo]
        # senza recensioni e senza testi il rapporto resta vuoto: limite della piattaforma, il passo è GO con il motivo
        passo.attesi = 0
    rapporto = {"idCliente": contesto.idCliente, "nome": contesto.cliente.get("nome", ""), "formato": FORMATO, "scritto": comune.adesso(),
                "sintesi": rapporto.get("sintesi", ""), "settori": rapporto["settori"], "materialeLetto": conteggio,
                "settoriScartatiPerchéSenzaProva": scartati, "tokenUsati": token}
    contesto.scriviJson("resto", NOME_FILE_DEL_RAPPORTO, rapporto)
    passo.scaricati = passo.attesi
    passo.dettagli = {"formato": FORMATO, "settori": {settore: voce["frase"] for settore, voce in rapporto["settori"].items()},
                      "sintesi": rapporto["sintesi"], "settoriScartati": len(scartati), "token": token, "materialeLetto": conteggio}
    contesto.stato["unicita"] = {"settori": len(rapporto["settori"])}
    return [passo]

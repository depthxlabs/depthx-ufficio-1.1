"""Motore unico di download del materiale clienti della Linea 1.2.

Dal 2 novembre 2026 legge i CRM nuovi (cartella Drive "_01_CRM Linea 1.2", configurazione _02_LetturaDalCRM/_03_ColonneEImpostazioniDelCrm.json):
ogni foglio (tipo, categoria, regione) è una "industria" del motore con un numero a tre cifre; solo le regioni della configurazione.
Il vecchio CRM a 20 industrie (_01_Industrie.json) non si usa più.
Modi:
  --coordinatore [--industrie 001,002] [--rifai]   tutti i fogli delle regioni scelte, 2 insieme (regola industrieInsieme), riprende da dove era
  --lavoratore --industria NNN [--clienti ID,ID] [--rifai]   un foglio, avviato dal coordinatore
  --collaudo CARTELLA --clienti ID,ID             collaudo su alcuni clienti con destinazione sul disco (solo senza Drive)
  --consenso                                      consenso di Michele a Google Drive nel browser
  --stato                                         riepilogo leggibile del registro
"""

import os
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))  # il modulo comune aggiunge le cartelle degli altri passi

import _02_PercorsiChiaviEFunzioniComuni as comune  # percorsi brevi prima delle altre librerie

import argparse
import datetime
import importlib.util
import json
import re
import subprocess
import time
import traceback
import uuid

import _03_RegistroDegliEventiEDelloStato as registro
import _01_CaricamentoNellaCartellaDelClienteSuDrive as destinazioni
import _02_ClientiDalCrmASezioni as crmNuovi
from _04_ContestoDelClienteEConteggioDeiPassi import NOME_FILE_DATI_CRM, NOME_FILE_RIEPILOGO, Contesto

FILE_DEL_PID = os.path.join(comune.CARTELLA_DEL_REGISTRO, "motore.pid")
CARTELLA_DELLE_USCITE = os.path.join(comune.CARTELLA_DEL_REGISTRO, "uscite")
CODICE_CONSENSO = 3
CODICE_CHIAVE = 2
FONTI_INSIEME = [("_01_DownloadDelSitoAttuale", "sito"), ("_01_DownloadDaInstagram", "instagram")]  # YouTube no: la fabbrica non usa i video
FONTI_DOPO = ["_01_RiconoscimentoESmistamentoDelleFotoPerCategoria", "_01_RapportoDiUnicitaDalleRecensioniEDalMateriale"]
# dal 4/11/2026 (Michele) Facebook e TikTok non si scaricano più: non contano neanche per il cliente senza materiale
CAMPI_DEI_SOCIAL = ("sito", "instagram", "youtube")
PASSI_DELLE_FONTI = {
    "Google Maps": ["Google Maps foto", "Google Maps recensioni"],
    "_01_DownloadDelSitoAttuale": ["Sito attuale pagine", "Sito attuale immagini", "Sito attuale file"],
    "_01_DownloadDaInstagram": ["Instagram post", "Instagram reel", "Instagram storie in evidenza"],
    "_01_DownloadDaYoutube": ["YouTube video"],
    "_01_RiconoscimentoESmistamentoDelleFotoPerCategoria": ["Riconoscimento delle foto"],
    "_01_RapportoDiUnicitaDalleRecensioniEDalMateriale": ["Rapporto di unicità"],
}


def processoVivo(pid):
    if not pid:
        return False
    risultato = subprocess.run(["tasklist", "/FI", f"PID eq {pid}", "/NH"], capture_output=True, text=True, creationflags=comune.SENZA_FINESTRA)
    return str(pid) in risultato.stdout


# Lavoro su un cliente.


SOLO_MAPS = {"attivo": False}


def lavoraCliente(cliente, voceIndustria, destinazione, rifai):
    idCliente = cliente["idCliente"]
    registro.evento("inizio_cliente", industria=voceIndustria["cartellaDrive"], idCliente=idCliente, nome=cliente.get("nome"))
    comune.dalVivo(idCliente, "preparo la cartella su Drive", nome=cliente.get("nome", ""))
    contesto = Contesto(cliente, voceIndustria, destinazione)
    try:
        contesto.preparaCartelle()
        contesto.caricaStato(rifai)
        contesto.scriviJson("resto", NOME_FILE_DATI_CRM, {chiave: valore for chiave, valore in cliente.items()})
        esiti = {}

        def chiudi(passi):
            for passo in passi:
                if passo.dettagli.get("nelCrm") is False:
                    passo.dettagli["nota"] = "fonte non presente nel CRM: nessun elemento da scaricare"
                esiti[passo.nome] = (contesto.chiudiPasso(passo), passo.motivo())

        # dal 9/11/2026 (Michele): Google Maps, sito, Instagram e YouTube insieme, ognuno con il suo tempo massimo; poi il
        # riconoscimento delle foto e il rapporto di unicità, che leggono quello che è arrivato. Nessun cliente si salta più:
        # con poco materiale prende quello che ha e, se lo scarica, è GO.
        # Google Maps si legge con il Chrome condiviso dell'account del motore: scheda, foto della galleria e recensioni
        import _01_DownloadDiSchedaFotoERecensioniDaGoogleMaps as maps
        from concurrent.futures import ThreadPoolExecutor

        def fonte(modulo, nome, chiaveDelTempo):
            contesto.filo.scadenza = comune.scadenzaDellaFonte(chiaveDelTempo)
            try:
                return eseguiFonte(contesto, modulo, nome)
            finally:
                contesto.filo.scadenza = None

        insieme = [(maps, "Google Maps", "Google Maps")] + [(importlib.import_module(nomeModulo), nomeModulo, tempo) for nomeModulo, tempo in FONTI_INSIEME]
        # modalita veloci (Michele, 10/11/2026), attive solo con le variabili d'ambiente del lavoro che le chiede:
        # MOTORE_RECENSIONI_VELOCI=1 rifà solo le recensioni di Maps; MOTORE_SENZA_MAPS=1 salta Maps e ne tiene l'esito
        veloci, senzaMaps = os.environ.get("MOTORE_RECENSIONI_VELOCI") == "1", os.environ.get("MOTORE_SENZA_MAPS") == "1"
        if veloci or senzaMaps:
            tenuti = (("Google Maps foto", "Riconoscimento delle foto") if veloci else ("Google Maps foto", "Google Maps recensioni"))
            precedenti = ((comune.leggiJson(os.path.join(comune.CARTELLA_DEL_REGISTRO, "stato.json"), {}) or {}).get("clienti", {})
                          .get(idCliente, {}).get("passi", {}))
            for nomePasso in tenuti:
                if nomePasso in precedenti:
                    esiti[nomePasso] = (precedenti[nomePasso].get("esito", "GO"), precedenti[nomePasso].get("motivo", ""))
            if senzaMaps:
                insieme = insieme[1:]
        if SOLO_MAPS["attivo"]:
            # solo Google Maps: gli altri passi tengono l'esito già scritto nello stato del motore
            insieme = insieme[:1]
            precedenti = ((comune.leggiJson(os.path.join(comune.CARTELLA_DEL_REGISTRO, "stato.json"), {}) or {}).get("clienti", {})
                          .get(idCliente, {}).get("passi", {}))
            for nomePasso, voce in precedenti.items():
                if not nomePasso.startswith("Google Maps") and nomePasso not in ("Riconoscimento delle foto", "Rapporto di unicità"):
                    esiti[nomePasso] = (voce.get("esito", "GO"), voce.get("motivo", ""))
        with ThreadPoolExecutor(max_workers=len(insieme), thread_name_prefix="fonte") as fili:
            futuri = [fili.submit(fonte, modulo, nome, tempo) for modulo, nome, tempo in insieme]
            risultati = [futuro.result() for futuro in futuri]
        for passi, _ in risultati:
            chiudi(passi)
        for nomeModulo in ([] if SENZA_CLAUDE else FONTI_DOPO):
            if veloci and nomeModulo == "_01_RiconoscimentoESmistamentoDelleFotoPerCategoria":
                continue  # le foto non cambiano: il riconoscimento già fatto resta
            passi, _ = eseguiFonte(contesto, importlib.import_module(nomeModulo), nomeModulo)
            chiudi(passi)
        nonGo = [f"{nome}: {motivo}" for nome, (esito, motivo) in esiti.items() if esito != "GO"]
        esito = "NOTGO" if any(e == "NOTGO" for e, _ in esiti.values()) else "GO"  # dal 9/11/2026 solo GO o NOTGO
        # il cliente senza il materiale che serve al pacchetto è ESCLUSO, non NOTGO
        if esito == "GO" and contesto.stato.get("materialeInsufficiente"):
            esito = "ESCLUSO"
            nonGo.insert(0, contesto.stato["materialeInsufficiente"])
        if esito == "GO" and SENZA_CLAUDE:
            esito = "DA RICONOSCERE"  # scaricato su GitHub: diventa GO sul server dopo riconoscimento e unicità
        # i limiti della piattaforma restano scritti nel motivo anche quando il cliente è GO
        nonGo += [f"{nome}: {motivo}" for nome, (e, motivo) in esiti.items() if e == "GO" and motivo]
        concludi(contesto, esito, " | ".join(nonGo), esiti)
        comune.dalVivo(idCliente, "concluso", esito=esito)
        return esito
    finally:
        contesto.chiudiCaricamenti()
        comune.svuotaCartella(contesto.temporanea)


def eseguiFonte(contesto, modulo, nome):
    """Esegue una fonte; un errore imprevisto diventa un passo NOTGO con il motivo, e il cliente continua."""
    from _04_ContestoDelClienteEConteggioDeiPassi import Passo

    try:
        try:
            risultato = modulo.esegui(contesto)
        except comune.ChromeRiavviato:
            # il Chrome condiviso era bloccato ed è stato chiuso: la stessa fonte si ripete una volta con il Chrome riacceso
            registro.evento("errore", idCliente=contesto.idCliente, passo=nome, dettaglio="Chrome condiviso riavviato, la fonte si ripete")
            risultato = modulo.esegui(contesto)
        except Exception as errore:
            # un timeout della pagina (Google Maps lenta, un pulsante che non risponde) è un intoppo del momento: la fonte si ripete una volta
            if type(errore).__name__ != "TimeoutError":
                raise
            registro.evento("errore", idCliente=contesto.idCliente, passo=nome, dettaglio="timeout della pagina, la fonte si ripete")
            risultato = modulo.esegui(contesto)
    except (comune.ChiaveMancante, comune.ConsensoDriveMancante):
        raise
    except Exception as errore:
        motivo = ("" if type(errore).__name__ in ("LimiteMeta", "TettoPlaces") else "errore imprevisto: ") + comune.messaggioSicuro(f"{type(errore).__name__}: {errore}")
        registro.evento("errore", idCliente=contesto.idCliente, passo=nome, dettaglio=comune.messaggioSicuro(traceback.format_exc(limit=4)))
        passi = []
        for nomePasso in PASSI_DELLE_FONTI.get(nome, [nome]):
            passo = Passo(nomePasso)
            passo.limite = motivo
            passi.append(passo)
        return passi, None
    if isinstance(risultato, tuple):
        return risultato
    return risultato, None


def concludi(contesto, esito, motivo, esiti):
    contesto.stato.update({"esito": esito, "motivo": motivo, "concluso": comune.adesso()})
    contesto.salvaStato()
    riepilogo = {"idCliente": contesto.idCliente, "nome": contesto.cliente.get("nome", ""), "industria": contesto.industria["cartellaDrive"],
                 "esito": esito, "motivo": motivo, "iniziato": contesto.stato.get("iniziato"), "concluso": contesto.stato["concluso"],
                 "passi": contesto.stato.get("passi", {}), "fotoValide": contesto.stato.get("fotoValide"), "categorie": contesto.stato.get("categorie")}
    contesto.scriviJson("resto", NOME_FILE_RIEPILOGO, riepilogo)
    if esito == "GO" and not isinstance(contesto.destinazione, destinazioni.DestinazioneDiCollaudo):
        # dal 22/11/2026 (Michele): la bolla del cliente con tutti i dettagli del materiale si scrive subito, a download chiuso
        import _03_BollaDelClienteDopoIlDownload as bolla
        nota = bolla.bollaDopoIlDownload(contesto, riepilogo)
        if nota:
            registro.evento("errore", idCliente=contesto.idCliente, passo="Bolla", dettaglio=nota)
    registro.evento("fine_cliente", industria=contesto.industria["cartellaDrive"], idCliente=contesto.idCliente, esito=esito, motivo=motivo,
                    cartellaDrive=contesto.destinazione.collegamento(contesto.idCartellaCliente))


# Lavoratore: una industria.


def lavoratore(argomenti):
    voceIndustria = comune.industria(argomenti.industria)
    nome = voceIndustria["cartellaDrive"]
    comune.GIRO = int(argomenti.giro or 2)
    if not argomenti.collaudo:
        comune.FILE_DEL_BATTITO = comune.percorsoDelBattito(chiaveDelBattito(voceIndustria["numero"], argomenti.parte))
        comune.battito()
    try:
        clienti = crmNuovi.leggiClientiDelFoglio(voceIndustria)
    except Exception as errore:
        registro.evento("fine_industria", industria=nome, stato="fermo: CRM non leggibile", riepilogo={"motivo": comune.messaggioSicuro(errore)})
        return CODICE_CHIAVE
    if argomenti.clienti:
        scelti = {voce.strip().upper() for voce in argomenti.clienti.split(",")}
        clienti = [cliente for cliente in clienti if cliente["idCliente"].upper() in scelti]
    if argomenti.collaudo:
        destinazione = destinazioni.DestinazioneDiCollaudo(argomenti.collaudo)
    else:
        try:
            destinazione = destinazioni.DestinazioneDrive()
        except comune.ConsensoDriveMancante as errore:
            registro.evento("fine_industria", industria=nome, stato="in attesa del consenso Google Drive", riepilogo={"motivo": str(errore)})
            return CODICE_CONSENSO
    stato = registro.leggiStato().get("clienti", {})
    # primo giro: i clienti mai chiusi; secondo giro: anche i PARZIALE, da completare
    chiusi = ESITI_CHIUSI
    # un cliente su cui il lavoratore si è già fermato oltre il limite in questo giro non si riprende nello stesso giro
    daFare = [cliente for cliente in clienti if argomenti.rifai or argomenti.collaudo or (stato.get(cliente["idCliente"], {}).get("esito") not in chiusi
                                                                                         and (stato.get(cliente["idCliente"], {}).get("blocchi", 0) < comune.GIRO
                                                                                              or cliente["idCliente"] in (argomenti.clienti or "")))]
    registro.evento("avvio_industria", industria=nome, clienti=len(clienti), daFare=len(daFare), giro=comune.GIRO)
    conteggio = {"GO": 0, "NOTGO": 0, "SALTATO": 0, "giaFatti": len(clienti) - len(daFare)}
    for cliente in daFare:
        try:
            esito = lavoraCliente(cliente, voceIndustria, destinazione, argomenti.rifai)
            conteggio[esito] = conteggio.get(esito, 0) + 1
        except comune.ConsensoDriveMancante as errore:
            registro.evento("fine_cliente", industria=nome, idCliente=cliente["idCliente"], esito="INTERROTTO", motivo=str(errore))
            registro.evento("fine_industria", industria=nome, stato="in attesa del consenso Google Drive", riepilogo=conteggio)
            return CODICE_CONSENSO
        except comune.ChiaveMancante as errore:
            registro.evento("fine_cliente", industria=nome, idCliente=cliente["idCliente"], esito="INTERROTTO", motivo=str(errore))
            registro.evento("fine_industria", industria=nome, stato="fermo: chiave mancante", riepilogo={"motivo": str(errore), **conteggio})
            return CODICE_CHIAVE
        except Exception as errore:
            conteggio["NOTGO"] += 1
            registro.evento("fine_cliente", industria=nome, idCliente=cliente["idCliente"], esito="NOTGO",
                            motivo="errore imprevisto: " + comune.messaggioSicuro(f"{type(errore).__name__}: {errore}"))
            registro.evento("errore", idCliente=cliente["idCliente"], dettaglio=comune.messaggioSicuro(traceback.format_exc(limit=5)))
    registro.evento("fine_industria", industria=nome, stato="conclusa", riepilogo=conteggio)
    return 0


def soloRapportoDiUnicita(argomenti):
    """Il rapporto di unicità sui clienti già scaricati: legge il loro materiale da Drive, scrive il rapporto e il suo passo.

    Lo stato del cliente su Drive si tiene com'è (elementi, passi ed esito): si aggiunge soltanto il passo del rapporto.
    """
    import _01_RapportoDiUnicitaDalleRecensioniEDalMateriale as unicita
    from _04_ContestoDelClienteEConteggioDeiPassi import NOME_FILE_DI_STATO

    voceIndustria = comune.industria(argomenti.industria)
    clienti = crmNuovi.leggiClientiDelFoglio(voceIndustria)
    if argomenti.clienti:
        scelti = {voce.strip().upper() for voce in argomenti.clienti.split(",")}
        clienti = [cliente for cliente in clienti if cliente["idCliente"].upper() in scelti]
    destinazione = destinazioni.DestinazioneDrive()
    scaricati = registro.leggiStato().get("clienti", {})
    for cliente in clienti:
        voce = scaricati.get(cliente["idCliente"], {})
        # un rapporto GO già scritto non si rifà: meno token sull'abbonamento
        if voce.get("esito") not in ("GO", "PARZIALE", "NOTGO", "DA RICONOSCERE") or ((voce.get("passi", {}).get("Rapporto di unicità") or {}).get("esito") == "GO"
                                                                     and ((voce.get("passi", {}).get("Rapporto di unicità") or {}).get("dettagli") or {}).get("formato") == "settori"):
            continue
        contesto = Contesto(cliente, voceIndustria, destinazione)
        try:
            contesto.preparaCartelle()
            contesto.stato = destinazione.leggiJson(contesto.cartelle["resto"], NOME_FILE_DI_STATO) or {"elementi": {}}
            contesto.stato.setdefault("passi", {})
            passi, _ = eseguiFonte(contesto, unicita, "_01_RapportoDiUnicitaDalleRecensioniEDalMateriale")
            for passo in passi:
                print(cliente["idCliente"], passo.nome, contesto.chiudiPasso(passo), passo.motivo())
        finally:
            contesto.chiudiCaricamenti()
            comune.svuotaCartella(contesto.temporanea)
    return 0


def soloRiconoscimentoDelleFoto(argomenti):
    """Il riconoscimento delle foto rifatto con le categorie di oggi sui clienti già scaricati (Michele, 10/11/2026).

    Non scarica niente: legge le foto del cliente da Drive, scrive il nuovo riconoscimento e il suo passo. Lo stato del
    cliente su Drive si tiene com'è (elementi, altri passi ed esito).
    """
    import _01_RiconoscimentoESmistamentoDelleFotoPerCategoria as riconoscimento
    from _04_ContestoDelClienteEConteggioDeiPassi import NOME_FILE_DI_STATO

    voceIndustria = comune.industria(argomenti.industria)
    clienti = crmNuovi.leggiClientiDelFoglio(voceIndustria)
    if argomenti.clienti:
        scelti = {voce.strip().upper() for voce in argomenti.clienti.split(",")}
        clienti = [cliente for cliente in clienti if cliente["idCliente"].upper() in scelti]
    destinazione = destinazioni.DestinazioneDrive()
    for cliente in clienti:
        contesto = Contesto(cliente, voceIndustria, destinazione)
        try:
            contesto.preparaCartelle()
            contesto.stato = destinazione.leggiJson(contesto.cartelle["resto"], NOME_FILE_DI_STATO) or {"elementi": {}}
            contesto.stato.setdefault("passi", {})
            passi, _ = eseguiFonte(contesto, riconoscimento, "_01_RiconoscimentoESmistamentoDelleFotoPerCategoria")
            for passo in passi:
                print(cliente["idCliente"], passo.nome, contesto.chiudiPasso(passo), passo.motivo(), flush=True)
            contesto.salvaStato()
        except Exception as errore:
            print(cliente["idCliente"], "NOTGO", comune.messaggioSicuro(f"{type(errore).__name__}: {errore}"), flush=True)
        finally:
            contesto.chiudiCaricamenti()
            comune.svuotaCartella(contesto.temporanea)
    return 0


# Coordinatore: un foglio del CRM alla volta, in ordine, con più lavoratori insieme sullo stesso foglio.


def chiaveDelBattito(numero, parte):
    """Un battito per lavoratore: il foglio, e la parte quando un foglio è diviso tra più lavoratori."""
    return f"{numero}_{parte}" if parte and parte != "0" else numero


# Blocco di download (deciso da Michele il 4/11/2026): un blocco è un foglio del CRM. Il motore scarica un foglio intero alla volta,
# nell'ordine del CRM (sezione, tipo, categoria, regione); i clienti da fare del foglio si dividono in parti da pochi clienti, così più
# lavoratori lavorano insieme sullo stesso foglio. Finito un foglio passa al successivo; il foglio in corso è scritto nel file del blocco,
# che il Centro Gestione legge.
FILE_DEL_BLOCCO = comune.FILE_DEL_BLOCCO_DI_DOWNLOAD
CLIENTI_PER_PARTE = 3
PASSATE = 3  # passate sui blocchi: la prima scarica, le altre recuperano i NOTGO (9/11/2026)
# le date di inserimento nel CRM dei clienti trovati dalla ricerca, scritte dal server della ricerca: l'ordine cronologico del download
FILE_DEI_CONTATTI_SCRITTI = r"C:\_02_DepthXSoftware\_01_CentroGestioneDepthX\V1.0(161126_1124)\_01_StrumentiDiLavoroPerIlServer\_03_MemoriaDatiDelCentroGestione\_25_RicercaClientiLinea11\_01_ContattiScrittiNelCrm.json"
ESITI_CHIUSI = ("GO", "ESCLUSO", "DA RICONOSCERE", "IN CODA SU GITHUB")  # escluso per materiale insufficiente; scaricato su GitHub in attesa del riconoscimento sul server
# su GitHub (dal 23/11/2026) il riconoscimento delle foto e il rapporto di unicità con Claude si fanno sul server, dopo il download
SENZA_CLAUDE = os.environ.get("MOTORE_SENZA_CLAUDE") == "1"  # dal 9/11/2026: i SALTATO si rifanno e diventano GO; i vecchi PARZIALE hanno già più dei tetti nuovi


def clientiDelFoglio(voceIndustria, soloIniziati=False):
    """Tutti i clienti del foglio, in ordine di CRM, e quelli ancora da chiudere (non GO e non saltati)."""
    clienti = [cliente["idCliente"] for cliente in crmNuovi.leggiClientiDelFoglio(voceIndustria)]
    stato = registro.leggiStato().get("clienti", {})
    # un cliente fermato due volte oltre il limite (blocchi >= 2) non si riprende più: va controllato (9/11/2026)
    if soloIniziati:
        # passata di chiusura (Michele, 9/11/2026): i clienti già iniziati e non GO, anche quelli fermati più volte
        return clienti, [idCliente for idCliente in clienti if idCliente in stato and stato[idCliente].get("esito") not in ESITI_CHIUSI]
    return clienti, [idCliente for idCliente in clienti if stato.get(idCliente, {}).get("esito") not in ESITI_CHIUSI
                     and int(stato.get(idCliente, {}).get("blocchi", 0) or 0) < 2]


def scriviIlBlocco(voceIndustria, clienti):
    comune.scriviJsonSulDisco(FILE_DEL_BLOCCO, {
        "descrizione": "Blocco di download in corso: un blocco è un foglio del CRM (deciso da Michele il 4/11/2026). Il motore scarica il foglio intero, "
                       "poi passa al foglio successivo nell'ordine del CRM.",
        "numero": int(voceIndustria["numero"]), "foglio": voceIndustria["cartellaDrive"], "nome": voceIndustria["nome"], "creato": comune.adesso(),
        "clienti": clienti, "percorsi": {idCliente: voceIndustria["cartellaDrive"] for idCliente in clienti}})


def driveDisponibile():
    try:
        destinazioni.credenzialiDrive()
        return True
    except comune.ConsensoDriveMancante:
        return False


def oreSenzaBattito(numero):
    """Ore passate dall'ultimo battito del lavoratore dell'industria."""
    try:
        return (time.time() - os.path.getmtime(comune.percorsoDelBattito(numero))) / 3600
    except OSError:
        return 0


def chiudiLavoratore(processo, fileUscita):
    """Chiude il lavoratore con tutti i suoi processi (Chrome compreso)."""
    subprocess.run(["taskkill", "/PID", str(processo.pid), "/T", "/F"], capture_output=True, creationflags=comune.SENZA_FINESTRA)
    try:
        processo.wait(timeout=60)
    except subprocess.TimeoutExpired:
        pass
    fileUscita.close()


CLIENTI_DELLE_PARTI = {}  # "numero:parte" -> ID dei clienti della parte, quando il foglio è diviso


def clientiInCorso(numero, parte="0"):
    """idCliente -> voce dello stato, per i clienti IN CORSO dell'industria (della sola parte, quando il foglio è diviso)."""
    nome = comune.industria(numero)["cartellaDrive"]
    soli = set(CLIENTI_DELLE_PARTI.get(f"{numero}:{parte}") or [])
    return {idCliente: cliente for idCliente, cliente in registro.leggiStato().get("clienti", {}).items()
            if cliente.get("industria") == nome and cliente.get("esito") == "IN CORSO" and (not soli or idCliente in soli)}


def oreSulCliente(numero, parte="0"):
    """Ore passate dall'inizio del cliente IN CORSO dell'industria (0 se nessuno)."""
    ore = 0
    for cliente in clientiInCorso(numero, parte).values():
        try:
            iniziato = datetime.datetime.fromisoformat(cliente.get("iniziato") or "")
        except ValueError:
            continue
        ore = max(ore, (datetime.datetime.now(iniziato.tzinfo) - iniziato).total_seconds() / 3600)
    return ore


def fermaClienteTroppoLungo(voce, processo, fileUscita, ore):
    """Il cliente oltre il tempo massimo del suo giro si chiude PARZIALE e il lavoratore riparte dal cliente seguente.

    Primo giro: si completa nel secondo giro. Secondo giro: PARZIALE definitivo con il materiale già scaricato, mai ripreso
    (blocchi = 2). Prima del 9/11/2026 il secondo giro lo riprendeva subito, all'infinito: C_S_HOT_0040 per 54 ore."""
    numero, giro, parte = (voce.split(":") + ["0"])[:3]
    chiudiLavoratore(processo, fileUscita)
    nome = comune.industria(numero)["cartellaDrive"]
    massimo = comune.regola("oreMassimePerClienteNelPrimoGiro" if giro == "1" else "oreMassimePerClienteNelSecondoGiro")
    lunghi = clientiInCorso(numero, parte)
    for idCliente, cliente in lunghi.items():
        blocchi = max(int(cliente.get("blocchi", 0)) + 1, int(giro))
        registro.evento("fine_cliente", industria=nome, idCliente=idCliente, esito="NOTGO", blocchi=max(blocchi, 2),
                        motivo=f"oltre {massimo} ore sul cliente nonostante il tempo massimo di ogni fonte: va controllato")
    registro.evento("errore", industria=numero, dettaglio=f"cliente {', '.join(lunghi) or '?'} oltre {massimo} ore nel giro {giro} ({ore:.1f} ore): "
                                                          "chiuso NOTGO, il lavoratore riparte dal cliente seguente")


def fermaLavoratoreBloccato(voce, processo, fileUscita, ore):
    """Chiude il lavoratore fermo con tutti i suoi processi (Chrome compreso) e segna il cliente su cui si era fermato.

    Primo blocco del cliente: PARZIALE, si riprende nel secondo giro. Secondo blocco: NOTGO con il motivo.
    """
    numero, giro, parte = (voce.split(":") + ["0"])[:3]
    chiudiLavoratore(processo, fileUscita)
    nome = comune.industria(numero)["cartellaDrive"]
    bloccati = []
    for idCliente, cliente in clientiInCorso(numero, parte).items():
        blocchi = int(cliente.get("blocchi", 0)) + 1
        esito = "NOTGO"  # dal 9/11/2026 solo GO o NOTGO: al primo blocco si riprende una volta (blocchi < 2)
        registro.evento("fine_cliente", industria=nome, idCliente=idCliente, esito=esito, blocchi=blocchi,
                        motivo=f"lavoratore fermo da oltre {int(comune.regola('oreSenzaBattitoPrimaDelRiavvio'))} ore su questo cliente: "
                               + ("si riprende nel secondo giro" if esito == "PARZIALE" else "fermo anche nel secondo giro, va controllato"))
        bloccati.append(idCliente)
    registro.evento("errore", industria=numero, dettaglio=f"lavoratore del giro {giro} senza battito da {ore:.1f} ore: chiuso e riavviato"
                                                          + (f", cliente {', '.join(bloccati)} rimandato" if bloccati else ""))


def coordinatore(argomenti):
    os.makedirs(CARTELLA_DELLE_USCITE, exist_ok=True)
    precedente = comune.leggiJson(FILE_DEL_PID, {}) or {}
    if processoVivo(precedente.get("pid")) and precedente.get("pid") != os.getpid():
        print(f"Il motore è già acceso (processo {precedente.get('pid')}).")
        return 1
    comune.scriviJsonSulDisco(FILE_DEL_PID, {"pid": os.getpid(), "avviato": comune.adesso()})
    # i blocchi veri del CRM, letti da Drive attraverso il Centro Gestione (Michele, 9/11/2026)
    registro.evento("ripresa", motivo=f"blocchi del CRM letti: {comune.aggiornaIBlocchiDelCrm()}")
    for nome in os.listdir(comune.CARTELLA_TEMPORANEA) if os.path.isdir(comune.CARTELLA_TEMPORANEA) else []:
        if re.match(r"^(C_S_|S\d_[A-Z]{3}_[A-Z]{3}_\d)", nome):  # solo le cartelle temporanee dei clienti rimaste da un arresto, mai quelle del collaudo
            comune.svuotaCartella(os.path.join(comune.CARTELLA_TEMPORANEA, nome))
    comune.chiudiChromeDeiSiti()  # un Chrome dei siti rimasto da un arresto
    insieme = int(argomenti.insieme or comune.regola("industrieInsieme"))
    try:
        if argomenti.industrie or argomenti.tutto:
            numeri = [comune.industria(voce.strip())["numero"] for voce in argomenti.industrie.split(",")] if argomenti.industrie else [voce["numero"] for voce in comune.INDUSTRIE]
            eseguiIFogli(argomenti, numeri, {}, insieme)
            return 0
        # un blocco è un foglio: i fogli in ordine di CRM, uno alla volta, saltando quelli già chiusi.
        # Dal 9/11/2026 (Michele) finite le passate sui blocchi, il motore ripassa da solo sui NOTGO (per esempio Instagram
        # in pausa per il limite di Meta), al massimo PASSATE volte, dopo la fine della pausa di Instagram.
        for passata in range(0, PASSATE + 1):
            lavorato = False
            if passata > 1:
                import _01_DownloadDaInstagram as instagram
                attesa = instagram.pausaMetaFinoA() - time.time()
                if attesa > 0:
                    registro.evento("attesa", motivo=f"passata {passata}: aspetto la fine della pausa di Instagram ({int(attesa // 60)} minuti)")
                    time.sleep(attesa)
                registro.evento("ripresa", motivo=f"passata di recupero {passata} sui clienti NOTGO")
            # tutti i fogli con clienti da fare insieme, nell'ordine del CRM: i lavoratori restano sempre pieni anche quando un foglio ne ha pochi
            parti, primo = {}, None
            # le sezioni tenute da parte (regola sezioniDaNonScaricare): i loro fogli non si scaricano
            daParte = [sezione for sezione in (comune.regola("sezioniDaNonScaricare") or []) if sezione]
            for voce in comune.INDUSTRIE:
                if any(re.search(rf"(^|[^A-Z0-9]){sezione}_", str(voce.get("cartellaDrive", ""))) for sezione in daParte):
                    continue
                try:
                    tutti, daFare = clientiDelFoglio(voce, soloIniziati=passata == 0)
                except Exception as errore:
                    registro.evento("errore", industria=voce["cartellaDrive"], dettaglio="foglio del CRM non leggibile: " + comune.messaggioSicuro(errore))
                    continue
                if not daFare:
                    continue
                primo = primo or (voce, tutti)
                parti[voce["numero"]] = [daFare[inizio:inizio + CLIENTI_PER_PARTE] for inizio in range(0, len(daFare), CLIENTI_PER_PARTE)]
            if parti:
                lavorato = True
                scriviIlBlocco(*primo)
                if not eseguiIFogli(argomenti, list(parti), parti, insieme):
                    return 0
            if not lavorato and passata > 0:
                break
        return 0
    finally:
        comune.chiudiChromeDeiSiti()
        if (comune.leggiJson(FILE_DEL_PID, {}) or {}).get("pid") == os.getpid():
            os.remove(FILE_DEL_PID)


def eseguiIFogli(argomenti, numeri, parti, insieme):
    """Lavoratori sui fogli indicati (le parti, quando un foglio è diviso), fino alla fine dei due giri. False se il motore è fermato."""
    CLIENTI_DELLE_PARTI.clear()
    for numero, gruppi in parti.items():
        for i, ids in enumerate(gruppi, start=1):
            CLIENTI_DELLE_PARTI[f"{numero}:{i}"] = ids
    if not argomenti.collaudo and driveDisponibile():
        # cartelle tipo/categoria/regione create una volta qui, così due lavoratori non creano la stessa cartella insieme
        try:
            destinazione = destinazioni.DestinazioneDrive()
            for numero in numeri:
                destinazione.cartellaDellIndustria(dict(comune.industria(numero)))
        except Exception as errore:
            registro.evento("errore", industria="coordinatore", dettaglio="cartelle dei fogli su Drive: " + comune.messaggioSicuro(errore))
    idEsecuzione = uuid.uuid4().hex[:12]
    registro.evento("avvio_esecuzione", idEsecuzione=idEsecuzione, industrie=numeri, industrieInsieme=insieme, rifai=bool(argomenti.rifai))
    # deciso da Michele il 29/10/2026: prima il giro 1 di tutte le industrie (si chiudono i clienti piccoli), poi il giro 2 (i PARZIALE)
    giri = ["2"]  # dal 9/11/2026 (Michele) un solo giro, con i tetti fissi delle regole
    daAvviare = [f"{numero}:{giro}:{i}" for giro in giri for numero in numeri for i in range(1, len(parti[numero]) + 1)] if parti \
        else [f"{numero}:{giro}:0" for giro in giri for numero in numeri]
    # ordine cronologico su tutti i fogli insieme (Michele): prima i clienti inseriti da più tempo nel CRM.
    # La data è quella scritta dal server della ricerca; i clienti senza data sono di prima della ricerca automatica e vanno per primi.
    if parti:
        inseriti = {voce.get("id"): voce.get("quando", "") for voce in (comune.leggiJson(FILE_DEI_CONTATTI_SCRITTI, {}) or {}).values() if isinstance(voce, dict) and voce.get("id")}
        posizione = {voce: k for k, voce in enumerate(daAvviare)}
        daAvviare.sort(key=lambda voce: (inseriti.get((CLIENTI_DELLE_PARTI.get(voce.split(":")[0] + ":" + voce.split(":")[2]) or [""])[0], ""), posizione[voce]))
    accesi, riavvii, esiti = {}, {}, {}
    attesaConsenso = False
    ultimoControlloDelTempo = 0
    try:
        while daAvviare or accesi:
            for numero, (processo, fileUscita) in list(accesi.items()):
                codice = processo.poll()
                if codice is None:
                    ore = oreSenzaBattito(chiaveDelBattito(numero.split(":")[0], (numero.split(":") + ["0"])[2]))
                    if ore >= float(comune.regola("oreSenzaBattitoPrimaDelRiavvio")):
                        # deciso da Michele il 30/10/2026: un lavoratore fermo da più di 3 ore si riavvia da solo
                        fermaLavoratoreBloccato(numero, processo, fileUscita, ore)
                        del accesi[numero]
                        daAvviare.insert(0, numero)
                    elif time.time() - ultimoControlloDelTempo >= 60:
                        # deciso da Michele il 30/10/2026: nel primo giro nessun cliente oltre 2 ore, il resto nel secondo giro;
                        # dal 9/11/2026 anche il secondo giro ha il suo limite. Il giro è il secondo campo della voce
                        # (numero:giro:parte), non l'ultimo: prima si leggeva la parte e il secondo giro girava all'infinito.
                        _, giroDellaVoce, parteDellaVoce = (numero.split(":") + ["0", "0"])[:3]
                        ore = oreSulCliente(numero.split(":")[0], parteDellaVoce)
                        limite = "oreMassimePerClienteNelPrimoGiro" if giroDellaVoce == "1" else "oreMassimePerClienteNelSecondoGiro"
                        if ore >= float(comune.regola(limite)):
                            fermaClienteTroppoLungo(numero, processo, fileUscita, ore)
                            del accesi[numero]
                            daAvviare.insert(0, numero)
                    continue
                fileUscita.close()
                del accesi[numero]
                if codice == CODICE_CONSENSO:
                    daAvviare.insert(0, numero)
                    attesaConsenso = True
                elif codice == 0 or codice == CODICE_CHIAVE:
                    esiti[numero] = codice
                else:
                    riavvii[numero] = riavvii.get(numero, 0) + 1
                    if riavvii[numero] <= 3:
                        registro.evento("errore", industria=numero, dettaglio=f"lavoratore uscito con codice {codice}: riavvio {riavvii[numero]} di 3")
                        daAvviare.insert(0, numero)
                    else:
                        esiti[numero] = codice
            if time.time() - ultimoControlloDelTempo >= 60:
                ultimoControlloDelTempo = time.time()
            if attesaConsenso or (daAvviare and not argomenti.collaudo and not driveDisponibile()):
                if not accesi:
                    registro.evento("attesa", motivo="token di Google Drive scaduto o revocato: il motore aspetta il consenso dato con _08_ComandiDelMotore/_02_ConsensoGoogleDriveDelMotore.cmd")
                    while not driveDisponibile():
                        time.sleep(int(comune.regola("secondiTraUnControlloEAltroDelConsensoDrive")))
                    registro.evento("ripresa", motivo="consenso Google Drive presente")
                    attesaConsenso = False
                else:
                    time.sleep(10)
                    continue
            while daAvviare and len(accesi) < insieme:
                # mai due lavoratori sulla stessa parte: il giro 2 di una parte aspetta la fine del suo giro 1
                inLavoro = {(voce.split(":") + ["0"])[0] + ":" + (voce.split(":") + ["0"])[2] for voce in accesi}
                libera = next((voce for voce in daAvviare if (voce.split(":") + ["0"])[0] + ":" + (voce.split(":") + ["0"])[2] not in inLavoro), None)
                if not libera:
                    break
                daAvviare.remove(libera)
                numero, giro, parte = (libera.split(":") + ["0"])[:3]
                chiave = chiaveDelBattito(numero, parte)
                fileUscita = open(os.path.join(CARTELLA_DELLE_USCITE, f"industria_{chiave}.log"), "a", encoding="utf-8")
                comune.FILE_DEL_BATTITO = comune.percorsoDelBattito(chiave)
                comune.battito()  # il conteggio delle ore parte dall'avvio del lavoratore
                comune.FILE_DEL_BATTITO = ""
                comando = [comune.PYTHON_DEL_MOTORE, "-B", os.path.abspath(__file__), "--lavoratore", "--industria", numero, "--giro", giro] + (["--rifai"] if argomenti.rifai else [])
                if parte != "0":
                    comando += ["--parte", parte, "--clienti", ",".join(CLIENTI_DELLE_PARTI[f"{numero}:{parte}"])]
                accesi[libera] = (subprocess.Popen(comando, stdout=fileUscita, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL,
                                                   creationflags=comune.PRIORITA_BASSA | comune.SENZA_FINESTRA), fileUscita)
            time.sleep(5)
        registro.evento("fine_esecuzione", idEsecuzione=idEsecuzione, stato="concluso", esitiDelleIndustrie=esiti)
        return True
    except KeyboardInterrupt:
        registro.evento("fine_esecuzione", idEsecuzione=idEsecuzione, stato="fermato", motivo="interruzione")
        return False


def collaudo(argomenti):
    """Collaudo su alcuni clienti: un cliente dopo l'altro, destinazione sul disco, registro separato da quello vero."""
    cartellaDelRegistro = os.path.join(argomenti.collaudo, "_RegistroDelCollaudo")
    os.makedirs(cartellaDelRegistro, exist_ok=True)
    registro.FILE_DEL_REGISTRO = os.path.join(cartellaDelRegistro, "registro.jsonl")
    registro.FILE_DELLO_STATO = os.path.join(cartellaDelRegistro, "stato.json")
    registro.evento("avvio_esecuzione", idEsecuzione="collaudo_" + uuid.uuid4().hex[:8], industrie=["collaudo"], industrieInsieme=1, collaudo=argomenti.collaudo)
    for idCliente in argomenti.clienti.split(","):
        idCliente = idCliente.strip()
        numero = crmNuovi.trovaFoglioDelCliente(idCliente)
        if not numero:
            print("Cliente non trovato nei CRM:", idCliente)
            continue
        argomenti.industria = numero
        argomenti.clienti = idCliente
        lavoratore(argomenti)
    registro.evento("fine_esecuzione", idEsecuzione="collaudo", stato="concluso")
    return 0


def stampaStato():
    stato = registro.leggiStato()
    print(json.dumps(stato.get("motore", {}), ensure_ascii=False, indent=1))
    for nome, voce in sorted(stato.get("industrie", {}).items()):
        print(nome, voce.get("stato"), voce.get("riepilogo") or "")
    conteggio = {}
    for voce in stato.get("clienti", {}).values():
        conteggio[voce.get("esito")] = conteggio.get(voce.get("esito"), 0) + 1
    print("Clienti:", conteggio)
    return 0


def main():
    parametri = argparse.ArgumentParser(description="Motore unico di download del materiale clienti, Linea 1.2")
    parametri.add_argument("--coordinatore", action="store_true")
    parametri.add_argument("--lavoratore", action="store_true")
    parametri.add_argument("--consenso", action="store_true")
    parametri.add_argument("--stato", action="store_true")
    parametri.add_argument("--fermato", action="store_true")
    parametri.add_argument("--industria")
    parametri.add_argument("--industrie")
    parametri.add_argument("--clienti")
    parametri.add_argument("--insieme")
    parametri.add_argument("--rifai", action="store_true")
    parametri.add_argument("--soloMaps", action="store_true")  # solo Google Maps, gli altri passi restano (Michele, 9/11/2026)
    parametri.add_argument("--collaudo")
    parametri.add_argument("--giro")
    parametri.add_argument("--parte")  # parte del foglio quando il blocco divide un foglio tra più lavoratori
    parametri.add_argument("--unicita", action="store_true")  # solo il rapporto di unicità sui clienti già scaricati di --industria
    parametri.add_argument("--tutto", action="store_true")
    parametri.add_argument("--soloFoto", action="store_true")  # solo il riconoscimento delle foto sui clienti già scaricati di --industria (Michele, 10/11/2026)  # tutti i fogli delle regioni scelte, senza il blocco
    argomenti = parametri.parse_args()
    SOLO_MAPS["attivo"] = argomenti.soloMaps
    if argomenti.consenso:
        print("1. Aprire questo link sul Mac o sul telefono e dare il consenso con depthxlabs@gmail.com:\n")
        print(destinazioni.linkDiConsenso() + "\n")
        print("2. Alla fine il browser va su una pagina 127.0.0.1 che non si apre: copiare tutto il link dalla barra e incollarlo qui sotto, poi Invio.\n")
        try:
            incollato = input("Link: ")
            account = destinazioni.incollaConsenso(incollato)
        except comune.ChiaveMancante as errore:
            print("NOTGO: " + str(errore))
            return CODICE_CHIAVE
        registro.evento("consenso_drive", motivo=f"consenso a Google Drive salvato per {account}: il motore in attesa riparte entro 5 minuti")
        print(f"GO: consenso salvato per {account}. Il motore in attesa riparte entro 5 minuti.")
        return 0
    if argomenti.stato:
        return stampaStato()
    if argomenti.fermato:
        stato = registro.leggiStato()
        for nome, voce in stato.get("industrie", {}).items():
            if voce.get("stato") == "in corso":
                registro.evento("fine_industria", industria=nome, stato="fermata con _02_FermaIlMotore.cmd")
        for idCliente, voce in stato.get("clienti", {}).items():
            if voce.get("esito") == "IN CORSO":
                registro.evento("fine_cliente", industria=voce.get("industria"), idCliente=idCliente, esito="INTERROTTO", motivo="motore fermato con _02_FermaIlMotore.cmd: riprende alla prossima accensione")
        registro.evento("fine_esecuzione", stato="fermato", motivo="fermato con _02_FermaIlMotore.cmd")
        if os.path.exists(FILE_DEL_PID):
            os.remove(FILE_DEL_PID)
        return 0
    if argomenti.collaudo and argomenti.clienti and not argomenti.lavoratore:
        return collaudo(argomenti)
    if argomenti.soloFoto and argomenti.industria:
        return soloRiconoscimentoDelleFoto(argomenti)
    if argomenti.unicita and argomenti.industria:
        return soloRapportoDiUnicita(argomenti)
    if argomenti.lavoratore and argomenti.industria:
        return lavoratore(argomenti)
    if argomenti.coordinatore:
        return coordinatore(argomenti)
    parametri.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())

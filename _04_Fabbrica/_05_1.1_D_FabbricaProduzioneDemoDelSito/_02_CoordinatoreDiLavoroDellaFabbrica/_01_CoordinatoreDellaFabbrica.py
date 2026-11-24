"""Il coordinatore della fabbrica: un foreach sul singolo cliente, senza logiche di business (direttiva di Michele).

Prende la lista dei clienti divisa a blocchi (_02_ClientiDivisiABlocchi.py), un blocco alla volta dal primo. Per ogni
cliente chiama in ordine i manager del ciclo di produzione (_03_CicloDiProduzionePerOgniCliente), solo i manager, e ogni
manager chiama i passaggi della sua cartella. All'ultimo passo il cliente è finito e caricato, e si riparte con il cliente
successivo dal primo passo. Quando i blocchi sono finiti aspetta i clienti nuovi del motore: finché la fabbrica è accesa
funziona così. La ferma _01_StrumentiDellaFabbrica/_02_ComandoDiStopDalCentroGestione.

Più fabbriche insieme (task #582, _01_StrumentiDellaFabbrica/_07_UnaSolaFabbricaAccesa): al massimo fabbricheInsieme delle
regole del coordinatore; un'accensione in più esce subito, due fabbriche non lavorano mai lo stesso cliente e il Worker delle
demo si pubblica una fabbrica alla volta.
Un cliente con la demo già pronta per l'invio non si rilavora. Nessun cliente resta fermo (Michele, 8/11/2026): se il
collaudo (passo 7) o il product manager (passo 8) danno NOTGO, la correzione del product manager (passo 8.4) corregge la demo, che
si ripubblica e si ricontrolla, fino ai giri di _08_ApprovazioneProductManager/_04_CorrezioneAutomaticaDellaDemo/_01_RegoleDellaCorrezione.json. Un
cliente che resta fermo, per un errore o perché i giri sono finiti, ha la causa nel registro e si riprova al giro
successivo della lista.

La bolla (Michele, 11/11/2026, task #570, #571, #572, #573, _04_BollaDelCliente.py): ogni cliente ha la sua bolla su Drive, nata
con il passo 0. Prima di ogni passo il coordinatore controlla la bolla (GO e file presenti nel banco di lavoro del cliente,
_02_SitoDelClienteInCorso/<idCliente>), dopo ogni passo la aggiorna. Un cliente senza bolla non si lavora. Il risultato di
ogni passo GO dall'1 al 5 si salva nel banco: alla riaccensione si riparte dal primo passo senza risultato GO; la pubblicazione, il collaudo,
il product manager e le correzioni (7, 8, 8.4) si rifanno sempre dopo la pubblicazione. Dopo l'esportazione (passo 9) il banco
del cliente si svuota. Le regole del coordinatore sono in _03_RegoleDelCoordinatore.json.
Avvio: _01_StrumentiDellaFabbrica/_01_ComandoDiAvvioDalCentroGestione/_01_AvviaLaFabbrica.cmd [--blocchi 004 005]
"""

import argparse
import json
import sys
import time
import traceback
from pathlib import Path

sys.dont_write_bytecode = True
# Nessuna finestra sul desktop del server (Michele, 11/11/2026: "schede vuote che si creano"): la fabbrica gira senza console e
# ogni programma che lancia (wrangler, rclone, node, Chrome) aprirebbe una finestra sua; qui ogni processo figlio parte nascosto.
import subprocess  # noqa: E402
if sys.platform == "win32":
    _avvioOriginale = subprocess.Popen.__init__

    def _avvioSenzaFinestra(self, *argomenti, **opzioni):
        if not opzioni.get("creationflags"):
            opzioni["creationflags"] = subprocess.CREATE_NO_WINDOW
        _avvioOriginale(self, *argomenti, **opzioni)
    subprocess.Popen.__init__ = _avvioSenzaFinestra
FABBRICA = Path(__file__).absolute().parents[1]
sys.path.insert(0, str(FABBRICA))
sys.path.insert(0, str(Path(__file__).absolute().parent))

from _01_StrumentiDellaFabbrica._04_RegistroLogDellaFabbrica._00_RegistroDellaFabbrica import (  # noqa: E402
    clientiGiaLavorati, registraErrore, registraEvento)
from _01_StrumentiDellaFabbrica._07_UnaSolaFabbricaAccesa._01_UnaSolaFabbricaAccesa import clienteLibero, unaSolaFabbricaAccesa  # noqa: E402
from _02_ClientiDivisiABlocchi import clientiDivisiABlocchi  # noqa: E402
from _03_CicloDiProduzionePerOgniCliente._01_LetturaDellaSezioneDelTipoDiClienteDalCRM._00_LetturaDellaSezioneDelTipoDiClienteDalCRMManager import \
    letturaDellaSezioneDelTipoDiClienteDalCRMManager  # noqa: E402
from _03_CicloDiProduzionePerOgniCliente._02_SceltaDelTemplatePerTipoDiBusinessDelCliente._00_SceltaDelTemplatePerTipoDiBusinessDelClienteManager import \
    sceltaDelTemplatePerTipoDiBusinessDelClienteManager  # noqa: E402
from _03_CicloDiProduzionePerOgniCliente._03_DownloadDelMaterialeDelClienteDaDrive._00_DownloadDelMaterialeDelClienteDaDriveManager import \
    downloadDelMaterialeDelClienteDaDriveManager  # noqa: E402
from _03_CicloDiProduzionePerOgniCliente._04_MiglioramentoDelleFotoEsistentiDelCliente._00_MiglioramentoDelleFotoEsistentiDelClienteManager import \
    miglioramentoDelleFotoEsistentiDelClienteManager  # noqa: E402
from _03_CicloDiProduzionePerOgniCliente._05_PersonalizzazioneDelTemplateConLidentitàDelCliente._00_PersonalizzazioneDelTemplateConLidentitàDelClienteManager import \
    personalizzazioneDelTemplateConLidentitàDelClienteManager  # noqa: E402
from _03_CicloDiProduzionePerOgniCliente._06_PubblicazioneSuDepthxlabsDemo._00_PubblicazioneSuDepthxlabsDemoManager import \
    pubblicazioneSuDepthxlabsDemoManager  # noqa: E402
from _03_CicloDiProduzionePerOgniCliente._07_CollaudoBasicoDellaDemo._00_CollaudoBasicoDellaDemoManager import \
    collaudoBasicoDellaDemoManager  # noqa: E402
from _03_CicloDiProduzionePerOgniCliente._08_ApprovazioneProductManager._00_ApprovazioneProductManagerManager import \
    approvazioneProductManagerManager  # noqa: E402
from _03_CicloDiProduzionePerOgniCliente._09_EsportazioneSuDrive._00_EsportazioneSuDriveManager import \
    esportazioneSuDriveManager  # noqa: E402
from _03_CicloDiProduzionePerOgniCliente._08_ApprovazioneProductManager._04_CorrezioneAutomaticaDellaDemo._00_CorrezioneAutomaticaDellaDemoManager import \
    correzioneAutomaticaDellaDemoManager  # noqa: E402
from _03_CicloDiProduzionePerOgniCliente._09_EsportazioneSuDrive._03_SchedaPerLApprovazione._00_SchedaPerLApprovazioneManager import \
    schedaPerLApprovazioneManager  # noqa: E402

from _04_BollaDelCliente import (BollaNonValida, aggiornaLaBolla, attendiLaBolla, controllaLaBolla, creaLaBollaIniziale, leggiLaBolla,  # noqa: E402
                                 passoSalvato, regole, salvaIlPasso)
from _03_CicloDiProduzionePerOgniCliente._01_LetturaDellaSezioneDelTipoDiClienteDalCRM._01_AccediAllaCartellaDelClienteSuGDrive._01_AccediAllaCartellaDelClienteSuGDrive import \
    accediAllaCartellaDelClienteSuGDrive  # noqa: E402
from _03_CicloDiProduzionePerOgniCliente._02_SceltaDelTemplatePerTipoDiBusinessDelCliente._02_CreazioneCopiaDelTemplateOriginalePerIlClienteInCorso._01_CreazioneCopiaDelTemplatePerIlCliente import \
    CARTELLA_DEI_CLIENTI_IN_CORSO, togliLaCartella  # noqa: E402

from _01_StrumentiDellaFabbrica._08_TracciamentoDelleAzioni._01_TracciamentoDelleAzioni import strumenta  # noqa: E402

FILE_DELLA_CORREZIONE = (FABBRICA / "_03_CicloDiProduzionePerOgniCliente" / "_08_ApprovazioneProductManager" / "_04_CorrezioneAutomaticaDellaDemo"
                         / "_01_RegoleDellaCorrezione.json")


class ClienteFermato(Exception):
    pass


def passo(idCliente, nome, chiamata, fermaSeNotgo=True):
    try:
        risultato = chiamata()
    except Exception as errore:
        registraErrore(idCliente, nome, traceback.format_exc())
        registraEvento("passo", idCliente=idCliente, passo=nome, esito="NOTGO", motivo=str(errore)[:300], dettagli=None)
        raise ClienteFermato(f"{nome}: {errore}")
    esito = risultato.get("esito", "GO") if isinstance(risultato, dict) else "GO"
    registraEvento("passo", idCliente=idCliente, passo=nome, esito=esito, motivo="", dettagli=risultato)
    if esito == "NOTGO" and fermaSeNotgo:
        raise ClienteFermato(f"{nome}: NOTGO")
    return risultato


class Bolla:
    """La bolla del cliente durante il ciclo: controlla prima di ogni passo, aggiorna dopo, salva i risultati per la ripresa."""

    def __init__(self, idCliente):
        self.idCliente = idCliente
        self.idDrive = accediAllaCartellaDelClienteSuGDrive(idCliente)["idDrive"]
        self.banco = CARTELLA_DEI_CLIENTI_IN_CORSO / idCliente
        try:
            try:
                self.bolla = leggiLaBolla(idCliente, self.idDrive)
            except BollaNonValida as errore:
                # Michele, 13/11/2026: la bolla mancante si crea al passo 0 e il cliente parte (solo se il file manca davvero)
                if "bolla assente" not in str(errore):
                    raise
                self.bolla = creaLaBollaIniziale(idCliente, self.idDrive)
                registraEvento("passo", idCliente=idCliente, passo="0 Bolla", esito="GO", motivo="bolla creata: mancava su Drive", dettagli=None)
        except BollaNonValida as errore:
            registraEvento("passo", idCliente=idCliente, passo="0 Bolla", esito="NOTGO", motivo=str(errore), dettagli=None)
            raise ClienteFermato(str(errore))

    def aggiorna(self, numero, esito, motivo="", fileProdotto=None):
        try:
            self.bolla = aggiornaLaBolla(self.bolla, self.idDrive, numero, esito, motivo, fileProdotto)
        except Exception as errore:
            raise ClienteFermato(f"bolla del passo {numero} non aggiornata: {errore}")

    def attendi(self):
        """Pitstop 1 (task #605): la bolla si spedisce a Drive in un filo a parte; a fine cliente si aspetta che l'ultima sia su
        Drive, riletta e uguale."""
        try:
            attendiLaBolla(self.bolla, self.idDrive)
        except Exception as errore:
            registraEvento("passo", idCliente=self.idCliente, passo="0 Bolla", esito="NOTGO", motivo=f"bolla non confermata su Drive: {errore}"[:300], dettagli=None)
            raise ClienteFermato(f"bolla non confermata su Drive: {errore}")

    def esegui(self, numero, nome, chiamata):
        """Passi dall'1 al 5: se il risultato GO è salvato nel banco e la bolla lo elenca, si riprende da lì."""
        relativo = f"_passi/{numero}.json"
        salvato = passoSalvato(self.banco, numero) if relativo in (self.bolla.get("fileProdotti") or []) else None
        if salvato is not None:
            registraEvento("passo", idCliente=self.idCliente, passo=nome, esito="GO", motivo="ripreso dal banco di lavoro", dettagli=None)
            return salvato
        # il passo si rifà: i risultati di questo passo e dei successivi non valgono più
        self.bolla["fileProdotti"] = [f for f in self.bolla.get("fileProdotti") or []
                                      if not (f.startswith("_passi/") and float(f[7:-5]) >= numero)]
        for vecchio in (self.banco / "_passi").glob("*.json") if (self.banco / "_passi").is_dir() else []:
            if float(vecchio.stem) >= numero:
                vecchio.unlink()
        try:
            if self.bolla.get("esito") != "GO" and float(self.bolla.get("passo") or 0) < numero:
                raise BollaNonValida(f"{self.idCliente}: la bolla non è GO (passo {self.bolla.get('passo')}: {self.bolla.get('motivo')})")
            controllaLaBolla({**self.bolla, "esito": "GO"}, self.banco)
        except BollaNonValida as errore:
            raise ClienteFermato(str(errore))
        try:
            risultato = passo(self.idCliente, nome, chiamata)
        except ClienteFermato as fermato:
            self.aggiorna(numero, esitoDelFermo(fermato), str(fermato))
            raise
        try:
            prodotto = salvaIlPasso(self.banco, numero, risultato)
        except (TypeError, ValueError):
            prodotto = None  # un risultato che non si scrive in JSON: alla ripresa il passo si rifà
        self.aggiorna(numero, "GO", "", prodotto)
        return risultato


def esitoDelFermo(fermato):
    """NOTGO solo quando qualcosa che deve funzionare non funziona; il cliente senza materiale sufficiente è ESCLUSO."""
    return "ESCLUSO" if "materiale insufficiente" in str(fermato).lower() else "NOTGO"


def datiMancantiDellaDemo(copia):
    """Quello che il cliente non ha dato e che nessuna correzione può inventare: oggi la galleria di foto (Advanced, voce 10)."""
    radice = Path(copia["sito"])
    home = radice / "index.html"
    codice = home.read_text(encoding="utf-8-sig", errors="ignore") if home.is_file() else ""
    if (radice / "galleria.html").is_file() or 'class="galleria"' in codice:
        return []
    return ["troppo poche foto per la galleria"]


def cicloSulCliente(idCliente):
    b = Bolla(idCliente)
    try:
        return lavoraIlCliente(b, idCliente)
    finally:
        b.attendi()  # l'ultima bolla su Drive prima di passare al cliente successivo, anche se il cliente si è fermato


def lavoraIlCliente(b, idCliente):
    if b.bolla.get("passo") == 9 and b.bolla.get("esito") == "GO":
        registraEvento("passo", idCliente=idCliente, passo="0 Bolla", esito="GO", motivo="demo già esportata: il cliente non si rilavora",
                       dettagli=None)
        return ""
    scheda = b.esegui(1, "1 Lettura dal CRM", lambda: letturaDellaSezioneDelTipoDiClienteDalCRMManager(idCliente))
    registraEvento("inizio_cliente", idCliente=idCliente, nome=scheda.get("nome", ""), template=scheda.get("tipo", ""))
    copia = b.esegui(2, "2 Scelta e copia del template", lambda: sceltaDelTemplatePerTipoDiBusinessDelClienteManager(scheda))
    materiale = b.esegui(3, "3 Materiale da Drive", lambda: downloadDelMaterialeDelClienteDaDriveManager(scheda, copia))
    foto = b.esegui(4, "4 Foto migliorate", lambda: miglioramentoDelleFotoEsistentiDelClienteManager(copia, materiale))
    identita = b.esegui(5, "5 Identità del cliente",
                        lambda: personalizzazioneDelTemplateConLidentitàDelClienteManager(scheda, copia, materiale, foto))
    # dati mancanti (Michele, 12/11/2026): senza foto per la galleria la demo non supera mai il collaudo e la correzione non
    # può aggiungere foto. Il cliente si ferma subito, senza i giri di correzione, e resta tra gli esclusi per materiale.
    mancanti = datiMancantiDellaDemo(copia)
    if mancanti:
        motivo = "materiale insufficiente: dati mancanti, " + ", ".join(mancanti)
        b.aggiorna(5, "ESCLUSO", motivo)
        raise ClienteFermato(motivo)
    # la pubblicazione si rifà sempre, anche alla ripresa: online va sempre il sito com'è nel banco, comprese le correzioni
    # del giro prima (11/11/2026). Dal banco si riprendono solo i passi dall'1 al 5.
    try:
        pubblicazione = passo(idCliente, "6 Pubblicazione su depthxlabs.com/demo", lambda: pubblicazioneSuDepthxlabsDemoManager(scheda, copia))
    except ClienteFermato as fermato:
        b.aggiorna(6, "NOTGO", str(fermato))
        raise
    b.aggiorna(6, "GO")
    giri = int(json.loads(FILE_DELLA_CORREZIONE.read_text(encoding="utf-8-sig"))["giriMassimi"])
    storia = []
    for giro in range(giri + 1):
        collaudo = passo(idCliente, "7 Collaudo basico", lambda: collaudoBasicoDellaDemoManager(copia, materiale, foto),
                         fermaSeNotgo=False)
        b.aggiorna(7, collaudo["esito"], "" if collaudo["esito"] == "GO" else "collaudo da correggere")
        approvazione = None
        if collaudo["esito"] == "GO":
            approvazione = passo(idCliente, "8 Approvazione del product manager",
                                 lambda: approvazioneProductManagerManager(copia, materiale), fermaSeNotgo=False)
            b.aggiorna(8, approvazione["esito"], "" if approvazione["esito"] == "GO" else "product manager da correggere")
            if approvazione["esito"] == "GO":
                break
        if giro == giri:
            # il motivo scritto: i controlli che la demo non supera ancora (Michele, 9/11/2026)
            restano = [f"collaudo, {nome}: {voce}" for nome, voci in (collaudo.get("controlli") or {}).items() for voce in voci or []]
            restano += [f"product manager: {voce}" for voci in ((approvazione or {}).get("note") or {}).values() for voce in voci or []]
            motivo = f"dopo {giri} correzioni non supera ancora: " + " | ".join(restano)[:900]
            b.aggiorna(8 if approvazione else 7, "NOTGO", motivo)
            raise ClienteFermato(motivo)
        storia.append(passo(idCliente, f"8.4 Correzione del product manager, giro {giro + 1}",
                            lambda: correzioneAutomaticaDellaDemoManager(copia, collaudo, approvazione, identita, storia)))
        b.aggiorna(8.4, "GO", f"correzione, giro {giro + 1}")
        pubblicazione = passo(idCliente, "6 Pubblicazione su depthxlabs.com/demo, dopo la correzione",
                              lambda: pubblicazioneSuDepthxlabsDemoManager(scheda, copia))
        b.aggiorna(6, "GO", f"ripubblicata dopo la correzione, giro {giro + 1}")
    try:
        passo(idCliente, "9 Esportazione su Drive",
              lambda: esportazioneSuDriveManager(copia, pubblicazione, collaudo, approvazione, identita["testi"].get("prove", {})))
    except ClienteFermato as fermato:
        b.aggiorna(9, "NOTGO", str(fermato))
        raise
    b.aggiorna(9, "GO")
    # la demo entra nella pagina Approvazione del Centro Gestione con le sue schermate (Michele, 11/11/2026)
    passo(idCliente, "9.3 Scheda per l'approvazione", lambda: schedaPerLApprovazioneManager(scheda, copia, pubblicazione["link"]))
    # il banco di lavoro del cliente si svuota dopo l'esportazione (task #571)
    if b.banco.is_dir():
        togliLaCartella(b.banco)
    return pubblicazione["link"]


def coordinatore(soloQuestiBlocchi):
    registraEvento("fabbrica", stato="accesa", blocchi=list(soloQuestiBlocchi))
    while True:
        lavorati = clientiGiaLavorati()
        pronti = 0
        for blocco, clienti in clientiDivisiABlocchi(soloQuestiBlocchi):
            for idCliente in clienti:
                if idCliente in lavorati:
                    continue
                # con più fabbriche accese (task #582) un cliente lo lavora una fabbrica sola: se è già preso si passa al successivo
                with clienteLibero(idCliente) as libero:
                    if not libero:
                        continue
                    registraEvento("blocco", blocco=blocco, idCliente=idCliente)
                    try:
                        link = cicloSulCliente(idCliente)
                        registraEvento("fine_cliente", idCliente=idCliente, esito="PRONTA PER L'INVIO", motivo="", link=link)
                        pronti += 1
                    except ClienteFermato as fermato:
                        registraEvento("fine_cliente", idCliente=idCliente, esito=esitoDelFermo(fermato), motivo=str(fermato)[:1000], link="")
                    lavorati.add(idCliente)
        if not pronti:
            time.sleep(float(regole()["minutiDiAttesaDeiClientiNuovi"]) * 60)


# il tracciamento di ogni azione della fabbrica (Michele, 11/11/2026): _04_LogDiOgniSezione/<sezione>/<anno>/<mese>/<giorno>
strumenta()


if __name__ == "__main__":
    argomenti = argparse.ArgumentParser(description="Coordinatore della fabbrica dei siti demo")
    argomenti.add_argument("--blocchi", nargs="*", default=[], help="solo questi blocchi del CRM, per esempio 004 005")
    argomenti.add_argument("--cliente", default="", help="un solo cliente da cima a fondo, poi la fabbrica si chiude (le macchine di GitHub)")
    scelti = argomenti.parse_args()
    if scelti.cliente:
        registraEvento("blocco", blocco="github", idCliente=scelti.cliente)
        try:
            link = cicloSulCliente(scelti.cliente)
            registraEvento("fine_cliente", idCliente=scelti.cliente, esito="PRONTA PER L'INVIO", motivo="", link=link)
        except ClienteFermato as fermato:
            registraEvento("fine_cliente", idCliente=scelti.cliente, esito=esitoDelFermo(fermato), motivo=str(fermato)[:1000], link="")
        sys.exit(0)
    blocchi = tuple(voce for gruppo in scelti.blocchi for voce in gruppo.split(",") if voce)
    if not unaSolaFabbricaAccesa():
        registraEvento("fabbrica", stato="già accese tutte le fabbriche delle regole: questa accensione in più si ferma")
        sys.exit(0)
    coordinatore(blocchi)

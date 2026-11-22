"""Lavoro su un cliente: cartelle su Drive, regola del 100% per ogni passo, scaricamento verificato.

Regola del 100%: per ogni passo il motore conta gli elementi che esistono (attesi) e quelli scaricati,
verificati e caricati su Drive (scaricati). Il passo è GO soltanto se i due numeri coincidono,
nessun elemento è rimasto irraggiungibile e la fonte non ha un limite che nasconde altri elementi.
Ogni elemento si riprova con più metodi e più ripetizioni con attesa; alla fine del passo c'è
un giro di recupero. Ogni elemento che resta fuori ha il suo motivo preciso nel registro.
"""

import sys

sys.dont_write_bytecode = True

import datetime
import io
import os
import threading
import time
from concurrent.futures import ThreadPoolExecutor

import _02_PercorsiChiaviEFunzioniComuni as comune
import _03_RegistroDegliEventiEDelloStato as registro

CARTELLA_DELLA_RACCOLTA = "_01_RaccoltaMateriale"
CARTELLA_DELLA_PRODUZIONE = "_02_ProduzioneDelSitoDemo"
CARTELLE_DELLA_PRODUZIONE = ["_01_LogoDelCliente", "_02_ContenutiCreatiDaDepthxPerIlCliente", "_03_JsonDiLavoro", "_04_DemoDelSito", "_05_CollaudoDelSito"]
CARTELLA_DELLA_VENDITA = "_03_InvioEProcessoDiVendita"
SOTTOCARTELLE = {
    "scheda": "_01_SchedaDiGoogle",
    "fotoMaps": "_02_FotoDaGoogleMaps",
    "recensioni": "_03_RecensioniDaGoogleMaps",
    "sito": "_04_AttualeSitoWeb",
    "instagram": "_05_Instagram",
    "facebook": "_06_Facebook",
    "youtube": "_07_Youtube",
    "tiktok": "_08_TikTok",
    "foto": "_09_RiconoscimentoDelleFoto",
    "resto": "_10_IlRestoDeiDati",
}
NOME_FILE_DATI_CRM = "_01_DatiDalCrm.json"
NOME_FILE_DI_STATO = "_02_StatoDellaRaccolta.json"
NOME_FILE_FOTO_VALIDE = "_03_FotoValide.json"
NOME_FILE_RIEPILOGO = "_04_RiepilogoDelLavoro.json"
LATO_DELLA_MINIATURA = 400
ESTENSIONI_DEI_FORMATI = {"JPEG": ".jpg", "MPO": ".jpg", "PNG": ".png", "WEBP": ".webp", "GIF": ".gif", "AVIF": ".avif", "HEIF": ".heic",
                          "ICO": ".ico", "BMP": ".bmp", "TIFF": ".tif", "SVG": ".svg"}
MASSIMO_IRRAGGIUNGIBILI_NEL_REGISTRO = 60
CARTELLE_DEI_CLIENTI = comune.leggiJson(comune.FILE_DELLE_CARTELLE_DEI_CLIENTI, {}) or {}


class Passo:
    """Conteggio di un passo: attesi, scaricati, irraggiungibili con motivo, limite della fonte.

    limite: qualcosa da sistemare (scheda non verificata, CRM sbagliato, errore): il passo è NOTGO.
    piattaforma: un limite della piattaforma (Google Maps senza accesso, Facebook senza accesso, storie Instagram): il motore ha
    scaricato tutto quello che la piattaforma espone, il passo è GO e il limite resta scritto nel motivo (deciso da Michele il 29/10/2026).
    """

    def __init__(self, nome):
        self.nome = nome
        self.attesi = 0
        self.scaricati = 0
        self.irraggiungibili = []
        self.limite = ""
        self.piattaforma = ""
        self.parziale = ""  # primo giro: il passo si è fermato al tetto e si completa nel secondo giro
        self.dettagli = {}
        self.daRecuperare = []

    def esito(self):
        if self.limite:
            return "NOTGO"
        # dal 9/11/2026 (Michele) non esistono più i PARZIALE: un tetto o un tempo raggiunto è GO, scritto nel motivo
        # irraggiungibili dopo le ripetizioni e il giro di recupero: NOTGO solo se non è arrivato niente
        if self.irraggiungibili and not self.scaricati:
            return "NOTGO"
        if self.scaricati != self.attesi and not self.piattaforma and not self.irraggiungibili:
            return "NOTGO"
        return "GO"

    def motivo(self):
        parti = []
        if self.limite:
            parti.append(self.limite)
        if self.piattaforma:
            parti.append("limite della piattaforma: " + self.piattaforma)
        if self.parziale:
            parti.append(self.parziale)
        if self.irraggiungibili:
            parti.append(f"{len(self.irraggiungibili)} elementi irraggiungibili")
        if self.scaricati != self.attesi and not self.irraggiungibili:
            parti.append(f"scaricati {self.scaricati} su {self.attesi}")
        return "; ".join(parti)


class Contesto:
    """Tutto quello che serve alle fonti per lavorare su un cliente."""

    def __init__(self, cliente, voceIndustria, destinazione):
        self.cliente = cliente
        self.industria = voceIndustria
        self.destinazione = destinazione
        self.idCliente = cliente["idCliente"]
        self.temporanea = comune.cartellaTemporaneaDelCliente(self.idCliente)
        self.miniature = os.path.join(self.temporanea, "_miniature")
        os.makedirs(self.miniature, exist_ok=True)
        self.cartelle = {}
        self.stato = {}
        self.idCartellaCliente = ""
        self.ultimoSalvataggio = 0
        # caricamenti su Drive in parallelo: la fonte continua a scaricare mentre i file salgono; il blocco protegge stato e conteggi
        fili = int(comune.regola("caricamentiInParalleloSuDrive"))
        self.blocco = threading.RLock()
        self.caricamenti = ThreadPoolExecutor(max_workers=fili, thread_name_prefix="caricamentoSuDrive")
        self.postiInCoda = threading.BoundedSemaphore(4 * fili)  # al massimo 4 file in attesa per filo nella cartella temporanea
        self.caricamentiInCorso = []
        self.erroreDelCaricamento = None
        self.numeroDelCaricamento = 0
        self.filo = threading.local()  # giro di recupero di una fonte: vale solo per il suo filo (fonti in parallelo dal 9/11/2026)

    # Cartelle su Drive.

    def preparaCartelle(self):
        # la cartella del cliente creata il 4/11/2026 (_05_CartelleDeiClienti.json) si usa sempre: mai una seconda cartella dello stesso cliente
        nota = CARTELLE_DEI_CLIENTI.get(self.idCliente) or {}
        if nota.get("idDrive") and hasattr(self.destinazione, "cartellaValida") and self.destinazione.cartellaValida(nota["idDrive"]):
            self.idCartellaCliente = nota["idDrive"]
        else:
            idIndustria = self.destinazione.cartellaDellIndustria(self.industria)
            nome = f"_{self.idCliente}_{comune.nomeSenzaSpazi(self.cliente.get('nome'))}"
            self.idCartellaCliente = self.destinazione.cartella(nome, idIndustria)
        idRaccolta = self.destinazione.cartella(CARTELLA_DELLA_RACCOLTA, self.idCartellaCliente)
        idProduzione = self.destinazione.cartella(CARTELLA_DELLA_PRODUZIONE, self.idCartellaCliente)
        for nomeCartella in CARTELLE_DELLA_PRODUZIONE:
            self.destinazione.cartella(nomeCartella, idProduzione)
        self.destinazione.cartella(CARTELLA_DELLA_VENDITA, self.idCartellaCliente)
        for chiave, nomeCartella in SOTTOCARTELLE.items():
            self.cartelle[chiave] = self.destinazione.cartella(nomeCartella, idRaccolta)

    def caricaStato(self, rifai):
        letto = self.destinazione.leggiJson(self.cartelle["resto"], NOME_FILE_DI_STATO) or {}
        if letto.get("motore") != "motore unico":
            letto = {}
        # Gli elementi già caricati e verificati si tengono sempre (stessa chiave, stesso nome su Drive, nessun doppione);
        # passi ed esito ripartono da capo quando il cliente era concluso o si rifà.
        elementi = letto.get("elementi", {})
        if rifai or letto.get("concluso") or not letto:
            letto = {"motore": "motore unico", "idCliente": self.idCliente, "industria": self.industria["cartellaDrive"],
                     "iniziato": comune.adesso(), "passi": {}}
        letto["elementi"] = elementi
        self.stato = letto

    def salvaStato(self, subito=True):
        with self.blocco:
            if not subito and time.time() - self.ultimoSalvataggio < 60:
                return
            self.stato["aggiornato"] = comune.adesso()
            self.destinazione.scriviJson(self.cartelle["resto"], NOME_FILE_DI_STATO, self.stato, self.temporanea)
            self.ultimoSalvataggio = time.time()

    def scriviJson(self, chiave, nome, oggetto):
        return self.destinazione.scriviJson(self.cartelle[chiave], nome, oggetto, self.temporanea)

    # Scaricamento verificato di un elemento.

    def scadenzaDi(self, passo):
        """Tempo massimo della fonte: quello del passo, oppure quello del filo della fonte (fonti in parallelo dal 9/11/2026)."""
        return getattr(passo, "scadenza", None) or getattr(self.filo, "scadenza", None)

    def giaCaricato(self, chiaveElemento):
        voce = self.stato["elementi"].get(chiaveElemento)
        if not voce:
            return None
        presenti = self.destinazione.elenco(self.cartelle[voce["cartella"]])
        file = presenti.get(voce["nome"])
        if file and file.get("md5") == voce["md5"]:
            return voce
        return None

    def scaricaElemento(self, passo, chiaveCartella, chiaveElemento, nomeBase, genere, metodi, foto=False, descrizione=None):
        """Scarica un elemento provando i metodi in ordine, ognuno con ripetizioni e attese.

        metodi: lista di (nomeDelMetodo, funzione(percorsoTemporaneo) -> tipoMime o estensione).
        Aggiorna il passo: scaricati +1 oppure elemento da recuperare con il motivo.
        """
        comune.battito()
        if self.erroreDelCaricamento:
            raise self.erroreDelCaricamento
        if self.giaCaricato(chiaveElemento):
            with self.blocco:
                passo.scaricati += 1
            return True
        if comune.scaduta(self.scadenzaDi(passo)):
            # tempo massimo della fonte (Michele, 9/11/2026): si tiene quello che è arrivato e la fonte è GO
            with self.blocco:
                passo.piattaforma = passo.piattaforma or "tempo massimo della fonte raggiunto: tenuto quello che è arrivato"
            return False
        motivi = []
        attese = list(comune.regola("secondiDiAttesaTraLeRipetizioni"))
        for nomeMetodo, funzione in metodi:
            ultimo = ""
            for ripetizione in range(int(comune.regola("ripetizioniPerMetodo"))):
                provvisorio = os.path.join(self.temporanea, comune.nomeDiFilePulito(chiaveElemento, 80) + ".part")
                try:
                    if os.path.exists(provvisorio):
                        os.remove(provvisorio)
                    tipo = funzione(provvisorio) or ""
                    misure = comune.verificaFile(provvisorio, genere)
                    estensione = self._estensione(genere, tipo, misure)
                    nome = nomeBase + estensione
                    md5 = comune.impronta(provvisorio)
                    if foto and genere == "immagine" and misure.get("formato") != "SVG":
                        misure.update(self._misureDellaFoto(provvisorio, chiaveElemento))
                    voce = {"cartella": chiaveCartella, "nome": nome, "id": "", "md5": md5, "passo": passo.nome,
                            "foto": bool(foto and misure.get("formato") != "SVG"), "misure": misure,
                            "descrizione": descrizione or {}, "metodo": nomeMetodo}
                    if getattr(self.filo, "inRecupero", False):
                        # giro di recupero: un file alla volta, così l'esito dell'elemento si conosce subito
                        voce["id"] = self.destinazione.caricaFile(self.cartelle[chiaveCartella], provvisorio, nome, md5)
                        with self.blocco:
                            self.stato["elementi"][chiaveElemento] = voce
                            passo.scaricati += 1
                        self.salvaStato(subito=False)
                        return True
                    with self.blocco:
                        self.numeroDelCaricamento += 1
                        inCoda = f"{provvisorio[:-5]}.{self.numeroDelCaricamento}.inCaricamento"
                    comune.sostituisciFile(provvisorio, inCoda)
                    with self.blocco:
                        self.stato["elementi"][chiaveElemento] = voce
                    self.postiInCoda.acquire()
                    with self.blocco:
                        self.caricamentiInCorso.append(self.caricamenti.submit(
                        self._caricaInParallelo, passo, chiaveCartella, chiaveElemento, inCoda, voce,
                        (passo, chiaveCartella, chiaveElemento, nomeBase, genere, metodi, foto, descrizione)))
                    return True
                except (comune.ChiaveMancante, comune.ConsensoDriveMancante):
                    raise
                except comune.ElementoNonScaricabile as errore:
                    ultimo = str(errore)
                    if errore.definitivo:
                        break
                except Exception as errore:
                    ultimo = f"{type(errore).__name__}: {comune.messaggioSicuro(errore)}"
                finally:
                    if os.path.exists(provvisorio):
                        try:
                            os.remove(provvisorio)
                        except OSError:
                            pass
                if ripetizione < len(attese):
                    time.sleep(attese[ripetizione])
            motivi.append(f"{nomeMetodo}: {ultimo}")
        passo.daRecuperare.append({"elemento": chiaveElemento, "motivo": " | ".join(motivi),
                                   "argomenti": (passo, chiaveCartella, chiaveElemento, nomeBase, genere, metodi, foto, descrizione)})
        return False

    def _caricaInParallelo(self, passo, chiaveCartella, chiaveElemento, percorso, voce, argomenti):
        """Un filo di caricamento: carica e verifica MD5 e dimensione; se non riesce l'elemento va al giro di recupero."""
        try:
            idFile = self.destinazione.caricaFile(self.cartelle[chiaveCartella], percorso, voce["nome"], voce["md5"])
            with self.blocco:
                voce["id"] = idFile
                passo.scaricati += 1
            self.salvaStato(subito=False)
        except (comune.ChiaveMancante, comune.ConsensoDriveMancante) as errore:
            with self.blocco:
                if self.stato["elementi"].get(chiaveElemento) is voce:
                    del self.stato["elementi"][chiaveElemento]
                self.erroreDelCaricamento = self.erroreDelCaricamento or errore
        except Exception as errore:
            with self.blocco:
                if self.stato["elementi"].get(chiaveElemento) is voce:
                    del self.stato["elementi"][chiaveElemento]
                passo.daRecuperare.append({"elemento": chiaveElemento, "argomenti": argomenti,
                                           "motivo": f"caricamento su Drive: {type(errore).__name__}: {comune.messaggioSicuro(errore)}"})
        finally:
            try:
                os.remove(percorso)
            except OSError:
                pass
            self.postiInCoda.release()

    def attendiCaricamenti(self):
        """Aspetta che tutti i file in coda siano su Drive e verificati, prima di contare o chiudere un passo."""
        while True:
            comune.battito()
            with self.blocco:
                if not self.caricamentiInCorso:
                    break
                prossimo = self.caricamentiInCorso.pop(0)
            prossimo.result()
        if self.erroreDelCaricamento:
            raise self.erroreDelCaricamento

    def chiudiCaricamenti(self):
        """Fine del cliente: i caricamenti ancora in corso finiscono, poi i fili si chiudono."""
        self.caricamenti.shutdown(wait=True, cancel_futures=True)

    def giroDiRecupero(self, passo):
        """Riprova gli elementi non scaricati dopo un'attesa; quelli che restano fuori diventano irraggiungibili con il motivo."""
        self.attendiCaricamenti()
        if passo.daRecuperare and not comune.scaduta(self.scadenzaDi(passo)):
            time.sleep(int(comune.regola("secondiPrimaDelGiroDiRecupero")))
            daRiprovare, passo.daRecuperare = passo.daRecuperare, []
            self.filo.inRecupero = True
            try:
                for voce in daRiprovare:
                    if not self.scaricaElemento(*voce["argomenti"]):
                        ultimo = passo.daRecuperare.pop() if passo.daRecuperare else {"motivo": "tempo massimo della fonte raggiunto"}
                        passo.irraggiungibili.append({"elemento": voce["elemento"], "motivo": ultimo["motivo"]})
            finally:
                self.filo.inRecupero = False
        self.salvaStato()

    def _estensione(self, genere, tipo, misure):
        if genere == "immagine":
            return ESTENSIONI_DEI_FORMATI.get(misure.get("formato", ""), comune.estensioneDalTipo(tipo, ".jpg"))
        if genere == "video":
            return tipo if str(tipo).startswith(".") else ".mp4"
        if genere == "pdf":
            return ".pdf"
        if genere == "html":
            return ".html"
        if genere == "json":
            return ".json"
        return tipo if str(tipo).startswith(".") else comune.estensioneDalTipo(tipo)

    def _misureDellaFoto(self, percorso, chiaveElemento):
        """Nitidezza, impronta per i doppioni e miniatura temporanea per il riconoscimento."""
        from PIL import Image, ImageFilter, ImageOps, ImageStat

        with Image.open(percorso) as originale:
            originale.draft("RGB", (1280, 1280))
            immagine = ImageOps.exif_transpose(originale).convert("RGB")
        ridotta = immagine.copy()
        ridotta.thumbnail((640, 640), Image.LANCZOS)
        grigio = ridotta.convert("L")
        laplaciano = grigio.filter(ImageFilter.Kernel((3, 3), [0, 1, 0, 1, -4, 1, 0, 1, 0], scale=1, offset=128))
        nitidezza = ImageStat.Stat(laplaciano).var[0]
        piccola = grigio.resize((9, 8), Image.LANCZOS)
        punti = list(piccola.getdata())
        firma = "".join("1" if punti[riga * 9 + colonna] > punti[riga * 9 + colonna + 1] else "0" for riga in range(8) for colonna in range(8))
        miniatura = ImageOps.contain(immagine, (LATO_DELLA_MINIATURA - 8, LATO_DELLA_MINIATURA - 8), Image.LANCZOS)
        miniatura.save(os.path.join(self.miniature, comune.nomeDiFilePulito(chiaveElemento, 120) + ".jpg"), quality=85)
        return {"nitidezza": round(nitidezza, 1), "firma": firma}

    # Registro.

    def chiudiPasso(self, passo):
        self.attendiCaricamenti()
        esito = passo.esito()
        irraggiungibili = passo.irraggiungibili[:MASSIMO_IRRAGGIUNGIBILI_NEL_REGISTRO]
        self.stato["passi"][passo.nome] = {"esito": esito, "attesi": passo.attesi, "scaricati": passo.scaricati, "motivo": passo.motivo(),
                                          "irraggiungibili": passo.irraggiungibili, "dettagli": passo.dettagli, "ora": comune.adesso()}
        self.salvaStato()
        registro.evento("passo", industria=self.industria["cartellaDrive"], idCliente=self.idCliente, passo=passo.nome, esito=esito,
                        attesi=passo.attesi, scaricati=passo.scaricati, motivo=passo.motivo(), irraggiungibili=irraggiungibili or None,
                        irraggiungibiliTotali=len(passo.irraggiungibili) or None, dettagli=passo.dettagli or None)
        return esito

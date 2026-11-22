"""La bolla del cliente scritta dal motore appena il download è chiuso (Michele, 22/11/2026).

La bolla è il file della fabbrica _02_ProduzioneDelSitoDemo/_03_JsonDiLavoro/_00_Bolla.json nella cartella del cliente su Drive.
Il motore scrive solo la sezione "materiale", con tutti i dettagli di quello che ha scaricato; il resto della bolla (passo, esito,
file prodotti) è della fabbrica e non si tocca. Se la bolla non c'è, il motore la crea come la fabbrica: passo 0, GO, nessun file prodotto.
Si usa anche da sola per rifare la bolla di tutti i clienti già scaricati: materialeDalRiepilogo() legge il riepilogo del lavoro su Drive.
"""

import sys

sys.dont_write_bytecode = True

import datetime
import json
import subprocess

RCLONE = r"C:\_02_DepthXSoftware\_02_RCloneDepthX\rclone.exe"
LETTURA = (r"C:\_02_DepthXSoftware\_02_RCloneDepthX\rclone.conf", "gdrive")
SCRITTURA = (r"C:\_02_DepthXSoftware\_02_RCloneDepthX\rclone_scrittura.conf", "gdrivescrittura")
BOLLA = "_02_ProduzioneDelSitoDemo/_03_JsonDiLavoro/_00_Bolla.json"
RIEPILOGO = "_01_RaccoltaMateriale/_10_IlRestoDeiDati/_04_RiepilogoDelLavoro.json"
TIPI = {"HOT": "Hotel", "BEB": "B&B", "AGR": "Agriturismo", "CAV": "Casa vacanze"}


def rclone(scrittura, idDrive, *argomenti, ingresso=None):
    configurazione, remoto = SCRITTURA if scrittura else LETTURA
    return subprocess.run([RCLONE, *argomenti[:-1], f"{remoto}:{argomenti[-1]}", "--drive-root-folder-id", idDrive, "--config", configurazione],
                          input=ingresso, capture_output=True, encoding="utf-8", errors="ignore", timeout=180,
                          creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))


def leggi(idDrive, percorso):
    esito = rclone(False, idDrive, "cat", percorso)
    if esito.returncode != 0 or not esito.stdout.strip():
        return None
    try:
        return json.loads(esito.stdout.lstrip("\ufeff"))
    except ValueError:
        return None


def scaricati(passi, nome):
    return int((passi.get(nome) or {}).get("scaricati") or 0)


def materialeDalRiepilogo(riepilogo, scheda=None):
    """Tutti i dettagli del materiale del cliente, dal riepilogo del lavoro del motore."""
    passi = riepilogo.get("passi") or {}
    categorie = riepilogo.get("categorie") or {}
    conta = lambda *nomi: sum(int(categorie.get(n) or 0) for n in nomi)
    recensioni = passi.get("Google Maps recensioni") or {}
    return {
        "esitoDelDownload": riepilogo.get("esito", ""), "motivoDelDownload": str(riepilogo.get("motivo") or "")[:600],
        "scaricatoIl": riepilogo.get("concluso", ""),
        "recensioniConTesto": scaricati(passi, "Google Maps recensioni"),
        "recensioniSuGoogle": int(((recensioni.get("dettagli") or {}).get("recensioniTotaliDellaScheda")) or 0),
        "fotoValide": int(riepilogo.get("fotoValide") or 0),
        "fotoPerFonte": {"googleMaps": scaricati(passi, "Google Maps foto"), "sito": scaricati(passi, "Sito attuale immagini"),
                         "instagram": scaricati(passi, "Instagram post") + scaricati(passi, "Instagram reel"), "youtube": scaricati(passi, "YouTube video")},
        "fotoPerCategoria": categorie,
        "fotoEsterno": conta("esterno della struttura", "esterni senza struttura") > 0,
        "fotoCamere": conta("camere") > 0,
        "fotoBagni": conta("bagni") > 0,
        "fotoPiscina": conta("piscina") > 0,
        "fotoRistorante": conta("ristorante", "colazione") > 0,
        "paginePerSito": scaricati(passi, "Sito attuale pagine"),
        "rapportoDiUnicita": (passi.get("Rapporto di unicità") or {}).get("esito") == "GO",
        "esitoPerPasso": {nome: (voce or {}).get("esito", "") for nome, voce in passi.items()},
    }


def scriviLaBolla(idCliente, idDrive, nome, materiale):
    """Aggiorna la sezione materiale della bolla su Drive, o crea la bolla se manca. Restituisce la bolla scritta."""
    bolla = leggi(idDrive, BOLLA)
    if bolla is not None and bolla.get("idCliente") not in (None, idCliente):
        raise ValueError(f"{idCliente}: la bolla su Drive è di un altro cliente ({bolla.get('idCliente')})")
    if bolla is None:
        bolla = {"idCliente": idCliente, "NomeAziendaCliente": nome, "tipoCliente": TIPI.get(idCliente.split("_")[1], ""),
                 "PacchettoSitoInBaseAlMaterialeEsistenteDelCliente": "", "versione": 1, "passo": 0, "esito": "GO",
                 "motivo": "bolla creata dal motore di download a download chiuso",
                 "ora": datetime.datetime.now().astimezone().isoformat(timespec="seconds"), "materiale": {}, "home": "", "fileProdotti": []}
    bolla["materiale"] = {**(bolla.get("materiale") or {}), **materiale}
    esito = rclone(True, idDrive, "rcat", BOLLA, ingresso=json.dumps(bolla, ensure_ascii=False, indent=2))
    if esito.returncode != 0:
        raise RuntimeError(f"{idCliente}: bolla non scritta su Drive: " + (esito.stderr or esito.stdout).strip()[-300:])
    return bolla


def bollaDopoIlDownload(contesto, riepilogo):
    """Chiamata dal motore a fine cliente: scrive la bolla con il materiale appena scaricato. Un errore non ferma il motore."""
    try:
        scriviLaBolla(contesto.idCliente, contesto.idCartellaCliente, contesto.cliente.get("nome", ""), materialeDalRiepilogo(riepilogo))
        return ""
    except Exception as errore:
        return f"bolla non scritta: {type(errore).__name__}: {errore}"[:300]

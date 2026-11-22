"""Fonte YouTube: tutti i video interi del canale scritto nel CRM.

Elenco completo dalla YouTube Data API ufficiale (playlist dei caricamenti). Video scaricati con yt-dlp
(con il motore JavaScript node, senza il quale YouTube risponde "video non disponibile"), fino a 1080p.
Attesi: tutti i video della playlist dei caricamenti. Un video privato o rimosso resta nel motivo.
"""

import sys

sys.dont_write_bytecode = True

import re

import _02_PercorsiChiaviEFunzioniComuni as comune
from _04_ContestoDelClienteEConteggioDeiPassi import Passo
from _01_ScaricamentoDiUnVideoConYtDlp import scaricaConYtDlp

VIDEO_PER_CHIAMATA = 50
LINGUE_DEL_TESTO_PARLATO = ["it", "en"]


def canaleDallaPagina(collegamento):
    try:
        risposta = comune.sessioneWeb().get(collegamento, timeout=(20, 40))
    except Exception:
        return ""
    trovato = re.search(r'<link rel="canonical" href="https://www\.youtube\.com/channel/(UC[0-9A-Za-z_\-]{20,})"', risposta.text) or re.search(r'"externalId":"(UC[0-9A-Za-z_\-]{20,})"', risposta.text)
    return trovato.group(1) if trovato else ""


def canaleDalCrm(servizio, valore):
    valore = (valore or "").strip()
    trovato = re.search(r"youtube\.com/channel/(UC[0-9A-Za-z_\-]{20,})", valore)
    if trovato:
        return trovato.group(1)
    trovato = re.search(r"youtube\.com/@([^/?#\s]+)", valore)
    if trovato:
        risposta = servizio.channels().list(part="id", forHandle="@" + trovato.group(1)).execute()
        return risposta["items"][0]["id"] if risposta.get("items") else ""
    trovato = re.search(r"youtube\.com/user/([^/?#\s]+)", valore)
    if trovato:
        risposta = servizio.channels().list(part="id", forUsername=trovato.group(1)).execute()
        return risposta["items"][0]["id"] if risposta.get("items") else ""
    trovato = re.search(r"(?:youtube\.com/(?:watch\?(?:.*&)?v=|shorts/|embed/)|youtu\.be/)([0-9A-Za-z_\-]{11})", valore)
    if trovato:
        risposta = servizio.videos().list(part="snippet", id=trovato.group(1)).execute()
        return risposta["items"][0]["snippet"]["channelId"] if risposta.get("items") else ""
    trovato = re.search(r"https?://(?:www\.|m\.)?youtube\.com/(?!(?:watch|results|playlist|feed|embed|shorts)\b)(?:c/)?[^/?#\s]+", valore)
    if trovato:
        return canaleDallaPagina(trovato.group(0))
    return ""


def testoParlato(idVideo):
    try:
        from youtube_transcript_api import YouTubeTranscriptApi

        return YouTubeTranscriptApi().fetch(idVideo, languages=LINGUE_DEL_TESTO_PARLATO).to_raw_data()
    except Exception:
        return []


def esegui(contesto):
    passo = Passo("YouTube video")
    valore = contesto.cliente.get("youtube")
    if not valore or not re.search(r"youtube\.com|youtu\.be", valore):
        passo.dettagli = {"nelCrm": False}
        return [passo]
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError

    chiave = comune.leggiChiaveTesto("youtube", r"AIza[0-9A-Za-z_\-]{30,}")
    servizio = build("youtube", "v3", developerKey=chiave, cache_discovery=False)
    try:
        idCanale = canaleDalCrm(servizio, valore)
        if not idCanale:
            passo.limite = "il collegamento YouTube del CRM non porta a un canale"
            return [passo]
        canale = servizio.channels().list(part="snippet,statistics,contentDetails,brandingSettings", id=idCanale).execute()["items"][0]
        caricamenti = canale["contentDetails"]["relatedPlaylists"]["uploads"]
        idVideo, pagina = [], None
        while True:
            risposta = servizio.playlistItems().list(part="contentDetails", playlistId=caricamenti, maxResults=VIDEO_PER_CHIAMATA, pageToken=pagina).execute()
            idVideo.extend(voce["contentDetails"]["videoId"] for voce in risposta.get("items", []))
            pagina = risposta.get("nextPageToken")
            if not pagina:
                break
        idVideo = list(dict.fromkeys(idVideo))
        video = []
        for inizio in range(0, len(idVideo), VIDEO_PER_CHIAMATA):
            gruppo = idVideo[inizio:inizio + VIDEO_PER_CHIAMATA]
            video.extend(servizio.videos().list(part="snippet,contentDetails,statistics,status", id=",".join(gruppo)).execute().get("items", []))
    except HttpError as errore:
        codice = errore.resp.status if errore.resp is not None else 0
        if codice in (400, 403):
            raise comune.ChiaveMancante("La chiave _02_ChiaveAPIYoutube.md non è accettata o la quota del giorno è finita.") from None
        raise RuntimeError(f"YouTube Data API: risposta {codice}") from None
    contesto.scriviJson("youtube", "_01_CanaleEVideo.json", {"canale": canale, "video": video})
    passo.attesi = len(idVideo)
    leggibili = {voce["id"]: voce for voce in video}
    testi = {}
    for numero, identificativo in enumerate(idVideo, start=1):
        if identificativo not in leggibili:
            passo.irraggiungibili.append({"elemento": identificativo, "motivo": "video nella playlist dei caricamenti ma privato o rimosso (la YouTube Data API non lo restituisce)"})
            continue
        voce = leggibili[identificativo]
        contesto.scaricaElemento(passo, "youtube", f"youtube:{identificativo}", f"youtube_{numero:03d}_{identificativo}", "video",
                                 [("yt-dlp", lambda percorso, url=f"https://www.youtube.com/watch?v={identificativo}": scaricaConYtDlp(url, percorso))],
                                 descrizione={"titolo": voce["snippet"].get("title", ""), "pubblicato": voce["snippet"].get("publishedAt", "")})
        righe = testoParlato(identificativo)
        if righe:
            testi[identificativo] = {"titolo": voce["snippet"].get("title", ""), "testo": " ".join(riga.get("text", "") for riga in righe), "righe": righe}
    contesto.giroDiRecupero(passo)
    contesto.scriviJson("youtube", "_02_TestiParlati.json", testi)
    passo.dettagli = {"videoDichiaratiDalCanale": (canale.get("statistics") or {}).get("videoCount"), "videoNellaPlaylistDeiCaricamenti": len(idVideo)}
    return [passo]

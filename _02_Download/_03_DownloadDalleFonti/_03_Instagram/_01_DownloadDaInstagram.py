"""Fonte Instagram: post, reel e storie in evidenza del profilo scritto nel CRM.

Elenco completo dei post con la Graph API ufficiale di Meta (Business Discovery, account @depthxmedia come porta).
Attesi: ogni foto e ogni video di ogni post elencato (gli album contano ogni elemento).
Primo metodo: il collegamento media_url della Graph API. Secondo metodo per i video senza media_url
(per esempio i reel con musica protetta): yt-dlp sulla pagina pubblica del post.
Le storie in evidenza non sono esposte dalla Graph API per i profili di altre attività e si leggono
solo con un accesso a Instagram, che il motore non ha: il passo lo dice nel motivo.
"""

import sys

sys.dont_write_bytecode = True

import os
import re
import time

import _02_PercorsiChiaviEFunzioniComuni as comune
from _04_ContestoDelClienteEConteggioDeiPassi import Passo
from _01_ScaricamentoDiUnVideoConYtDlp import scaricaConYtDlp

VERSIONE_GRAPH = "v23.0"
URL_GRAPH = f"https://graph.facebook.com/{VERSIONE_GRAPH}"
POST_PER_PAGINA = 50
CAMPI_DEI_POST = "id,caption,media_type,media_product_type,media_url,thumbnail_url,permalink,timestamp,like_count,comments_count,children{id,media_type,media_url,thumbnail_url}"
CAMPI_DEL_PROFILO = "id,username,name,biography,website,followers_count,follows_count,media_count,profile_picture_url"
NOMI_NON_PROFILI = {"p", "reel", "reels", "explore", "stories", "tv", "accounts"}


SECONDI_DI_ATTESA_DELLA_RETE = [10, 30, 60]  # solo per la rete che non risponde
# dal 9/11/2026 (Michele): quando Meta risponde con il limite di chiamate il motore non aspetta. Instagram va in pausa per tutti
# i lavoratori fino all'ora scritta in questo file, il cliente chiude le altre fonti e resta NOTGO con il motivo; si riprende
# da solo nella passata successiva del coordinatore, con gli elementi già caricati che non si riscaricano.
FILE_DELLA_PAUSA_META = os.path.join(comune.CARTELLA_DEL_REGISTRO, "pausaInstagramMeta.json")


def pausaMetaFinoA():
    return float((comune.leggiJson(FILE_DELLA_PAUSA_META, {}) or {}).get("fino", 0))


def mettiInPausaMeta(motivo):
    fino = time.time() + 60 * float(comune.regola("minutiDiPausaDiInstagramDopoIlLimiteMeta"))
    comune.scriviJsonSulDisco(FILE_DELLA_PAUSA_META, {"fino": fino, "motivo": motivo, "scritto": comune.adesso()})


class ProfiloNonLeggibile(Exception):
    pass


class LimiteMeta(Exception):
    pass


def nomeDelProfilo(valore):
    valore = (valore or "").strip()
    trovato = re.search(r"(?:^|//|\.)instagram\.com/([A-Za-z0-9._]+)", valore)
    if trovato and trovato.group(1).lower() not in NOMI_NON_PROFILI:
        return trovato.group(1)
    return ""


def chiamaGraph(token, percorso, parametri):
    import requests

    ultimo = "rete non raggiungibile"
    if time.time() < pausaMetaFinoA():
        raise LimiteMeta("Instagram in pausa per il limite di chiamate di Meta: si riprende nella passata successiva")
    for giro, attesa in enumerate(SECONDI_DI_ATTESA_DELLA_RETE):
        try:
            risposta = comune.sessioneWeb().get(f"{URL_GRAPH}/{percorso}", params=parametri, headers={"Authorization": f"Bearer {token}"}, timeout=(20, 90))
        except (requests.ConnectionError, requests.Timeout):
            time.sleep(min(attesa, 120))
            continue
        try:
            corpo = risposta.json()
        except ValueError:
            corpo = {}
        errore = corpo.get("error") if isinstance(corpo, dict) else None
        if not errore and risposta.status_code < 400:
            return corpo
        errore = errore or {}
        codice, sottocodice = errore.get("code"), errore.get("error_subcode")
        if codice == 190:
            raise comune.ChiaveMancante("Il token _04_TokenAccessoMetaDevelopers.md non è valido o è scaduto.")
        if codice == 110 or sottocodice == 2207013 or "cannot be found" in str(errore.get("message", "")).lower():
            raise ProfiloNonLeggibile("profilo personale o inesistente")
        if codice in (4, 17, 32, 613) or risposta.status_code in comune.CODICI_DA_RIPETERE:
            ultimo = f"limite di chiamate della Graph API di Meta raggiunto (errore {codice}: {comune.messaggioSicuro(errore.get('message', ''))[:120]})"
            mettiInPausaMeta(ultimo)
            raise LimiteMeta(ultimo + ": Instagram in pausa, si riprende nella passata successiva")
        raise RuntimeError(f"Graph API: errore {codice} {sottocodice or ''} {comune.messaggioSicuro(errore.get('message', ''))[:160]}".strip())
    raise LimiteMeta(f"{ultimo}: si riprende nella passata successiva")


def nostroAccountInstagram(token):
    pagine = chiamaGraph(token, "me/accounts", {"fields": "instagram_business_account{id,username}", "limit": 100})
    for pagina in pagine.get("data", []):
        account = pagina.get("instagram_business_account")
        if account and account.get("id"):
            return account["id"]
    raise comune.ChiaveMancante("Il token Meta non è collegato a un account Instagram professionale: Business Discovery non funziona.")


def esegui(contesto):
    passoPost, passoReel, passoStorie = Passo("Instagram post"), Passo("Instagram reel"), Passo("Instagram storie in evidenza")
    profilo = nomeDelProfilo(contesto.cliente.get("instagram"))
    if not profilo:
        for passo in (passoPost, passoReel, passoStorie):
            passo.dettagli = {"nelCrm": False}
        return [passoPost, passoReel, passoStorie]
    token = comune.leggiChiaveTesto("meta", r"EA[A-Za-z0-9]{40,}")
    nostroId = nostroAccountInstagram(token)
    post, visti, datiDelProfilo, cursore = [], set(), {}, ""
    massimi = int(comune.regola("postInstagramMassimi"))
    try:
        while True:
            pagina = f".after({cursore})" if cursore else ""
            campi = f"business_discovery.username({profilo}){{{CAMPI_DEL_PROFILO},media{pagina}.limit({POST_PER_PAGINA}){{{CAMPI_DEI_POST}}}}}"
            risposta = chiamaGraph(token, nostroId, {"fields": campi}).get("business_discovery", {})
            if not datiDelProfilo:
                datiDelProfilo = {chiave: valore for chiave, valore in risposta.items() if chiave != "media"}
            media = risposta.get("media", {})
            for voce in media.get("data", []):
                if voce.get("id") not in visti:
                    visti.add(voce.get("id"))
                    post.append(voce)
            cursore = (media.get("paging", {}).get("cursors", {}) or {}).get("after", "")
            # i 100 post più recenti (Michele, 9/11/2026): nessuna chiamata in più a Meta oltre il tetto
            if not cursore or not media.get("data") or len(post) >= massimi:
                break
    except ProfiloNonLeggibile:
        motivo = (f"il profilo @{profilo} è personale o non esiste: la Graph API (Business Discovery) legge solo profili professionali "
                  "e il motore non ha un accesso a Instagram")
        contesto.scriviJson("instagram", "_01_ProfiloInstagram.json", {"profilo": profilo, "leggibile": False, "motivo": motivo})
        for passo in (passoPost, passoReel, passoStorie):
            passo.piattaforma = motivo
        return [passoPost, passoReel, passoStorie]
    # la Graph API dà i post dal più recente: si tengono i primi 100 ed è GO (Michele, 9/11/2026)
    if len(post) >= massimi:
        post = post[:massimi]
        for passo in (passoPost, passoReel):
            passo.piattaforma = f"scaricati i {massimi} post più recenti (regola postInstagramMassimi)"
    contesto.scriviJson("instagram", "_01_ProfiloInstagram.json", {"profilo": profilo, "leggibile": True, "dati": datiDelProfilo, "post": post})
    if datiDelProfilo.get("profile_picture_url"):
        passoPost.attesi += 1
        contesto.scaricaElemento(passoPost, "instagram", f"instagram:profilo:{profilo}", "immagine_del_profilo", "immagine",
                                 [("Graph API", lambda percorso: comune.scaricaInFile(datiDelProfilo["profile_picture_url"], percorso))])
    for numero, voce in enumerate(post, start=1):
        reel = voce.get("media_product_type") == "REELS"
        passo = passoReel if reel else passoPost
        elementi = (voce.get("children") or {}).get("data") if voce.get("media_type") == "CAROUSEL_ALBUM" else [voce]
        if not elementi:
            elementi = [voce]
        for parte, elemento in enumerate(elementi, start=1):
            video = elemento.get("media_type") == "VIDEO"
            passo.attesi += 1
            nomeBase = f"{'reel' if reel else 'post'}_{numero:04d}_{parte:02d}_{elemento.get('id', '')}"
            metodi = []
            if elemento.get("media_url"):
                metodi.append(("Graph API media_url", lambda percorso, sorgente=elemento["media_url"], video=video: (comune.scaricaInFile(sorgente, percorso) and (".mp4" if video else "image/jpeg"))))
            if video and voce.get("permalink"):
                indice = parte if len(elementi) > 1 else None
                metodi.append(("yt-dlp sulla pagina pubblica del post", lambda percorso, url=voce["permalink"], indice=indice: scaricaVideoDelPost(url, indice, percorso)))
            if not metodi:
                passo.irraggiungibili.append({"elemento": nomeBase, "motivo": "la Graph API non dà il collegamento di questa foto e non c'è un secondo metodo senza accesso"})
                continue
            descrizione = {"permalink": voce.get("permalink", ""), "data": voce.get("timestamp", ""), "didascalia": (voce.get("caption") or "")[:1000],
                           "miPiace": voce.get("like_count"), "commenti": voce.get("comments_count")}
            contesto.scaricaElemento(passo, "instagram", f"instagram:{voce.get('id')}:{parte}", nomeBase, "video" if video else "immagine", metodi,
                                     foto=not video, descrizione=descrizione)
    contesto.giroDiRecupero(passoPost)
    contesto.giroDiRecupero(passoReel)
    dichiarati = datiDelProfilo.get("media_count")
    for passo in (passoPost, passoReel):
        passo.dettagli = {"postDichiaratiDalProfilo": dichiarati, "postElencatiDallaGraphApi": len(post)}
    passoStorie.piattaforma = ("le storie in evidenza dei profili di altre attività non sono esposte dalla Graph API di Meta e si leggono "
                          "solo con un accesso a Instagram: il motore non ha un accesso")
    return [passoPost, passoReel, passoStorie]


def scaricaVideoDelPost(url, indice, percorso):
    """yt-dlp sulla pagina pubblica del post; per gli album prende l'elemento indicato."""
    if indice:
        import glob
        import os

        radice = percorso[:-5] if percorso.endswith(".part") else percorso
        codice, uscita, errori = comune.eseguiYtDlp(["-q", "--playlist-items", str(indice), "-f", "b", "-o", radice + ".%(ext)s", url])
        prodotti = [voce for voce in glob.glob(glob.escape(radice) + ".*") if not voce.endswith((".part", ".ytdl")) and voce != percorso]
        if codice != 0 or not prodotti:
            raise comune.ElementoNonScaricabile("yt-dlp: " + comune.ultimoErrore(errori))
        scelto = max(prodotti, key=os.path.getsize)
        os.replace(scelto, percorso)
        return os.path.splitext(scelto)[1]
    return scaricaConYtDlp(url, percorso)

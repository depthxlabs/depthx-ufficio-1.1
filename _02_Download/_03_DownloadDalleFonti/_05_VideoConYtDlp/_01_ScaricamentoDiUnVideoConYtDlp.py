"""Scaricamento di un video con yt-dlp, usato dalle fonti sito, Instagram, Facebook, YouTube e TikTok."""

import sys

sys.dont_write_bytecode = True

import _02_PercorsiChiaviEFunzioniComuni as comune


def scaricaConYtDlp(url, percorso):
    """Scarica un video con yt-dlp nel percorso temporaneo indicato. Restituisce l'estensione."""
    import glob
    import os

    radice = percorso[:-5] if percorso.endswith(".part") else percorso
    altezza = int(comune.regola("altezzaMassimaDeiVideo"))
    codice, uscita, errori = comune.eseguiYtDlp(["-q", "--no-playlist", "-f", f"bv*[height<={altezza}]+ba/b[height<={altezza}]/bv*+ba/b",
                                                 "--merge-output-format", "mp4", "-o", radice + ".%(ext)s", url])
    prodotti = [voce for voce in glob.glob(glob.escape(radice) + ".*") if not voce.endswith((".part", ".ytdl")) and voce != percorso]
    if codice != 0 or not prodotti:
        for voce in prodotti:
            os.remove(voce)
        raise comune.ElementoNonScaricabile("yt-dlp: " + comune.ultimoErrore(errori))
    scelto = max(prodotti, key=os.path.getsize)
    os.replace(scelto, percorso)
    for voce in prodotti:
        if voce != scelto and os.path.exists(voce):
            os.remove(voce)
    return os.path.splitext(scelto)[1]

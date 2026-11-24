"""Passo 7.9: nelle recensioni nessun nome di chi le ha scritte; la firma è "un ospite di {nomestruttura}".

Il nome di chi ha scritto ogni recensione del materiale (passo 3.3) non deve comparire nelle frasi visibili; se nella
pagina c'è il testo di una recensione, c'è anche la firma "un ospite di". Il nome conta solo come parole intere e con almeno
3 lettere (Michele, 8/11/2026): prima "Ema" scattava dentro "sistema" e "T M" dentro "great meal", e la demo restava ferma.
Restituisce l'elenco dei problemi trovati.
"""

import re

from .._02_ControlloCheNonCiSiaNessunaParolaVietata._02_FrasiVisibiliDelSito import frasiVisibiliDelSito

CHIAVI_DEL_NOME = ("autore", "nome", "nomeAutore", "author", "name")
LETTERE_MINIME_DEL_NOME = 3


def nomiDegliOspitiNelSito(sito, recensioni):
    testo = " ".join(" \n ".join(frasiVisibiliDelSito(sito)).split())
    minuscole = testo.lower()
    problemi = []
    for voce in recensioni:
        nome = next((str(voce[chiave]).strip() for chiave in CHIAVI_DEL_NOME if voce.get(chiave)), "")
        # il nome si cerca con la maiuscola iniziale, come si scrive un nome: "Sardo" è un nome, "pecorino sardo" no
        intero = r"(?<![\wà-ÿ])" + r"\s+".join(re.escape(parola[:1].upper() + parola[1:].lower()) for parola in nome.split()) + r"(?![\wà-ÿ])"
        if len(re.findall(r"[^\W\d_]", nome)) >= LETTERE_MINIME_DEL_NOME and re.search(intero, testo):
            problemi.append(f"compare il nome di chi ha scritto una recensione: \"{nome}\"")
    testi = [" ".join((voce.get("testo") or "").split()).lower()[:60] for voce in recensioni]
    if any(testo and testo in minuscole for testo in testi) and "un ospite di" not in minuscole:
        problemi.append("ci sono recensioni senza la firma \"un ospite di\"")
    return problemi

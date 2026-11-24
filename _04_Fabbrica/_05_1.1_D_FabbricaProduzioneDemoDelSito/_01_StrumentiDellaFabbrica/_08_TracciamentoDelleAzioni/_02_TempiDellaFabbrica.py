"""I tempi della fabbrica, letti dai registri delle sezioni (Michele, 11/11/2026): il cronometro del pitstop.

Uso: python _02_TempiDellaFabbrica.py [giorno AAAA-MM-GG] [idCliente]
Per ogni cliente del giorno: la durata di ogni manager dei passi (le azioni di primo livello sotto il ciclo del cliente) e le
azioni più lente di tutto il giro, con i millisecondi e il numero di ripetizioni.
"""

import datetime
import sqlite3
import sys
from pathlib import Path

CARTELLA_DEI_LOG = Path(__file__).absolute().parents[2] / "_04_LogDiOgniSezione"
LENTE = 25


def registriDelGiorno(giorno):
    return sorted(CARTELLA_DEI_LOG.glob(f"*/{giorno:%Y}/{giorno:%m}/{giorno:%d}/_01_AzioniDelGiorno.sqlite"))


def leggi(giorno, soloCliente=""):
    righe = []
    for file in registriDelGiorno(giorno):
        with sqlite3.connect(f"file:{file}?mode=ro", uri=True, timeout=10) as db:
            righe += db.execute("SELECT idAzione, padre, profondita, idCliente, sezione, azione, inizio, millisecondi, esito, ripetizioni "
                                "FROM azioni WHERE (? = '' OR idCliente = ?)", (soloCliente, soloCliente)).fetchall()
    return righe


def tempi(giorno, soloCliente=""):
    righe = leggi(giorno, soloCliente)
    perId = {r[0]: r for r in righe}
    cicli = [r for r in righe if r[5] == "cicloSulCliente"]
    for ciclo in sorted(cicli, key=lambda r: r[6]):
        figli = sorted((r for r in righe if r[1] == ciclo[0] or (r[1] in perId and perId[r[1]][1] == ciclo[0] and perId[r[1]][5] == "passo")),
                       key=lambda r: r[6])
        print(f"\n== {ciclo[3]}  inizio {ciclo[6][11:19]}  totale {(ciclo[7] or 0) / 1000:.1f} s  {ciclo[8]}")
        for r in figli:
            if r[5] in ("passo", "esegui"):
                continue
            print(f"   {(r[7] or 0) / 1000:8.1f} s  {r[5]}  {r[8]}")
        sotto = [r for r in righe if r[3] == ciclo[3] and r[6] >= ciclo[6] and r[7]]
        print("   le più lente:")
        for r in sorted(sotto, key=lambda r: -(r[7] or 0))[:LENTE]:
            print(f"      {(r[7] or 0) / 1000:8.2f} s  x{r[9] or 1:<4} {r[4][4:]:<55.55} {r[5]}")


if __name__ == "__main__":
    giorno = datetime.date.fromisoformat(sys.argv[1]) if len(sys.argv) > 1 and sys.argv[1] else datetime.date.today()
    tempi(giorno, sys.argv[2] if len(sys.argv) > 2 else "")

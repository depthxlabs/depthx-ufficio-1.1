"""Registro del motore: un evento per riga in _03_Registro/registro.jsonl e lo stato attuale in _03_Registro/stato.json.

Più processi scrivono insieme: ogni scrittura passa da un blocco su _03_Registro/blocco.lock.
Il formato è descritto in _00_LeggimiDelMotore.md.
"""

import sys

sys.dont_write_bytecode = True

import json
import msvcrt
import os
import time

import _02_PercorsiChiaviEFunzioniComuni as comune

FILE_DEL_REGISTRO = os.path.join(comune.CARTELLA_DEL_REGISTRO, "registro.jsonl")
FILE_DELLO_STATO = os.path.join(comune.CARTELLA_DEL_REGISTRO, "stato.json")
FILE_DEL_BLOCCO = os.path.join(comune.CARTELLA_DEL_REGISTRO, "blocco.lock")


class _Blocco:
    """Blocco esclusivo tra processi su un file, con attesa."""

    def __enter__(self):
        os.makedirs(comune.CARTELLA_DEL_REGISTRO, exist_ok=True)
        self.file = open(FILE_DEL_BLOCCO, "a+b")
        for giro in range(600):
            try:
                self.file.seek(0)
                msvcrt.locking(self.file.fileno(), msvcrt.LK_NBLCK, 1)
                return self
            except OSError:
                time.sleep(0.1)
        raise TimeoutError("registro occupato da oltre 60 secondi")

    def __exit__(self, *dettagli):
        try:
            self.file.seek(0)
            msvcrt.locking(self.file.fileno(), msvcrt.LK_UNLCK, 1)
        finally:
            self.file.close()


def _statoVuoto():
    return {"motore": {"stato": "mai avviato"}, "industrie": {}, "clienti": {}}


def leggiStato():
    return comune.leggiJson(FILE_DELLO_STATO, None) or _statoVuoto()


def evento(tipo, **campi):
    """Aggiunge una riga al registro e aggiorna lo stato. Restituisce l'evento scritto."""
    voce = {"ora": comune.adesso(), "tipo": tipo, "pid": os.getpid()}
    voce.update({chiave: valore for chiave, valore in campi.items() if valore is not None})
    riga = json.dumps(voce, ensure_ascii=False)
    with _Blocco():
        with open(FILE_DEL_REGISTRO, "a", encoding="utf-8") as file:
            file.write(riga + "\n")
        stato = leggiStato()
        _aggiornaStato(stato, voce)
        stato["aggiornato"] = voce["ora"]
        comune.scriviJsonSulDisco(FILE_DELLO_STATO, stato)
    comune.battito()
    return voce


def riportaEvento(voce):
    """Un evento già scritto altrove (il lavoro su GitHub): si aggiunge al registro con la sua ora e aggiorna lo stato."""
    with _Blocco():
        with open(FILE_DEL_REGISTRO, "a", encoding="utf-8") as file:
            file.write(json.dumps(voce, ensure_ascii=False) + "\n")
        stato = leggiStato()
        _aggiornaStato(stato, voce)
        stato["aggiornato"] = voce.get("ora", comune.adesso())
        comune.scriviJsonSulDisco(FILE_DELLO_STATO, stato)


def _aggiornaStato(stato, voce):
    tipo = voce["tipo"]
    motore = stato.setdefault("motore", {})
    if tipo == "avvio_esecuzione":
        motore.update({"stato": "in corso", "idEsecuzione": voce.get("idEsecuzione"), "avviato": voce["ora"], "pid": voce["pid"],
                       "industrieInsieme": voce.get("industrieInsieme"), "industrie": voce.get("industrie"), "concluso": None, "motivo": ""})
    elif tipo == "fine_esecuzione":
        motore.update({"stato": voce.get("stato", "concluso"), "concluso": voce["ora"], "motivo": voce.get("motivo", "")})
    elif tipo == "attesa":
        motore.update({"stato": "in attesa", "motivo": voce.get("motivo", "")})
    elif tipo == "ripresa":
        motore.update({"stato": "in corso", "motivo": ""})
    elif tipo in ("avvio_industria", "fine_industria"):
        industrie = stato.setdefault("industrie", {})
        voceIndustria = industrie.setdefault(voce["industria"], {})
        if tipo == "avvio_industria":
            voceIndustria.update({"stato": "in corso", "avviata": voce["ora"], "clienti": voce.get("clienti"), "pid": voce["pid"]})
        else:
            voceIndustria.update({"stato": voce.get("stato", "conclusa"), "conclusa": voce["ora"], "riepilogo": voce.get("riepilogo")})
    elif tipo in ("inizio_cliente", "passo", "fine_cliente"):
        clienti = stato.setdefault("clienti", {})
        cliente = clienti.setdefault(voce["idCliente"], {"passi": {}})
        cliente["industria"] = voce.get("industria", cliente.get("industria"))
        cliente["nome"] = voce.get("nome", cliente.get("nome"))
        if tipo == "inizio_cliente":
            cliente.update({"esito": "IN CORSO", "motivo": "", "iniziato": voce["ora"], "concluso": None, "passi": {}})
        elif tipo == "passo":
            cliente["passi"][voce["passo"]] = {chiave: voce.get(chiave) for chiave in ("esito", "attesi", "scaricati", "motivo", "irraggiungibili", "dettagli", "ora")}
        else:
            cliente.update({"esito": voce.get("esito"), "motivo": voce.get("motivo", ""), "concluso": voce["ora"], "cartellaDrive": voce.get("cartellaDrive")})
            if voce.get("blocchi"):
                cliente["blocchi"] = voce["blocchi"]  # volte in cui il lavoratore si è fermato oltre il limite su questo cliente

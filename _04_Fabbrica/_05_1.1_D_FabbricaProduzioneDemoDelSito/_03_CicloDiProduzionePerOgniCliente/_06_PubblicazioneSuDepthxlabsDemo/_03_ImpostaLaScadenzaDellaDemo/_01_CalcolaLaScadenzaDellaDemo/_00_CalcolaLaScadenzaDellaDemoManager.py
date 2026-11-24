"""Manager del passo 6.3.1: la scheda della demo con la data di scadenza."""

from ._02_CalcolaLaScadenzaDellaDemo import calcolaLaScadenzaDellaDemo


def calcolaLaScadenzaDellaDemoManager(idCliente, schedaPrecedente):
    return calcolaLaScadenzaDellaDemo(idCliente, schedaPrecedente)

"""Manager del passo 6.1: il nome della demo per il link depthxlabs.com/demo/<nome>/."""

from ._01_NomeDellaDemo import nomeDellaDemo


def preparaNomeDellaDemoPerIlLinkManager(schedaDelCliente):
    return nomeDellaDemo(schedaDelCliente)

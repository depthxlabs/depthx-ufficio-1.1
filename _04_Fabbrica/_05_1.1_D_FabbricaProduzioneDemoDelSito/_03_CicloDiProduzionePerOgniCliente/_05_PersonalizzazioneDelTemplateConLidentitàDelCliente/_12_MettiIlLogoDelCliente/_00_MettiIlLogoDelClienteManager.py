"""Manager del passo 5.12: il logo del cliente, se è usabile."""

from ._01_MettiIlLogoDelCliente import mettiIlLogoDelCliente


def mettiIlLogoDelClienteManager(sito, fotoInOrdine, fotoScaricate):
    return mettiIlLogoDelCliente(sito, fotoInOrdine, fotoScaricate)

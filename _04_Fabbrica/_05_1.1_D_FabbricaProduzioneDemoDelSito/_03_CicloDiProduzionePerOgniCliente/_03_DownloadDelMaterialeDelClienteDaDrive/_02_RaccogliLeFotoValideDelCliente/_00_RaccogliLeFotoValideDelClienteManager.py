"""Manager del passo 3.2: le foto valide del cliente, in ordine di qualità."""

from ._01_RaccogliLeFotoValideDelCliente import raccogliLeFotoValideDelCliente
from ._02_FotoInOrdineDiQualita import fotoInOrdineDiQualita


def raccogliLeFotoValideDelClienteManager(cartellaDiLavoro):
    return fotoInOrdineDiQualita(raccogliLeFotoValideDelCliente(cartellaDiLavoro))

"""Manager del passo 2.2: la copia del template originale per il cliente in corso."""

from ._01_CreazioneCopiaDelTemplatePerIlCliente import creazioneCopiaDelTemplatePerIlCliente


def creazioneCopiaDelTemplateOriginalePerIlClienteInCorsoManager(idCliente, cartellaDelTemplate):
    return creazioneCopiaDelTemplatePerIlCliente(idCliente, cartellaDelTemplate)

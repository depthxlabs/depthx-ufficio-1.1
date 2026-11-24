"""Manager del passo 7.13: il logo del cliente compare quando si apre la home."""

from ._01_LogoMancanteNellaHome import logoMancanteNellaHome


def controlloDelLogoNellaHomeManager(sito):
    return logoMancanteNellaHome(sito)

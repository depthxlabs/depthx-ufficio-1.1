"""Manager del passo 7.11: il link alle recensioni porta alla pagina delle recensioni Google, mai a Google Maps."""

from ._01_LinkDelleRecensioniVersoMaps import linkDelleRecensioniVersoMaps


def controlloCheIlLinkDelleRecensioniPortiAGoogleManager(sito):
    return linkDelleRecensioniVersoMaps(sito)

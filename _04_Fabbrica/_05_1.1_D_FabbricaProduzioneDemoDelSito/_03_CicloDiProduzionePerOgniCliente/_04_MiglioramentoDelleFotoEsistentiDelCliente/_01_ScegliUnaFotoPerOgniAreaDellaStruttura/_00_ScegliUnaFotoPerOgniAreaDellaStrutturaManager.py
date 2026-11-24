"""Manager del passo 4.1: una foto per ogni area della struttura del template.

Prima le foto scaricate prendono la categoria precisa che chiedono i contratti (_07_CategoriePreciseDelleFoto.py),
poi si sceglie una foto per ogni area.
"""

from ._04_ScegliUnaFotoPerOgniAreaDellaStruttura import scegliUnaFotoPerOgniAreaDellaStruttura
from ._07_CategoriePreciseDelleFoto import categoriePreciseDelleFoto


def scegliUnaFotoPerOgniAreaDellaStrutturaManager(contratto, fotoInOrdine, fotoScaricate):
    return scegliUnaFotoPerOgniAreaDellaStruttura(contratto, categoriePreciseDelleFoto(fotoInOrdine, fotoScaricate),
                                                  fotoScaricate)

"""Manager del passo 4: il miglioramento delle foto esistenti del cliente.

Riceve la copia del template del passo 2.2 (sito e contratto) e il materiale del passo 3 (foto in ordine e foto scaricate).
Per ogni area della struttura e per ogni sua forma (Michele, 8/11/2026): la foto di quella forma (passo 4.1), raddrizzata,
tagliata intorno al soggetto, ingrandita se è piccola, con contrasto, colore e luci sistemati, poi salvata nel sito con la
nitidezza data a ogni misura dopo il rimpicciolimento (passo 4.9, che usa il 4.8).
"""

from ._01_ScegliUnaFotoPerOgniAreaDellaStruttura._00_ScegliUnaFotoPerOgniAreaDellaStrutturaManager import scegliUnaFotoPerOgniAreaDellaStrutturaManager
from ._02_RaddrizzaLaFoto._00_RaddrizzaLaFotoManager import raddrizzaLaFotoManager
from ._03_TrovaIlCentroDelSoggettoDellaFoto._00_TrovaIlCentroDelSoggettoDellaFotoManager import \
    trovaIlCentroDelSoggettoDellaFotoManager
from ._04_TagliaLaFotoInSediciNoniENoveSedicesimi._00_TagliaLaFotoInSediciNoniENoveSedicesimiManager import \
    tagliaLaFotoInSediciNoniENoveSedicesimiManager
from ._05_IngrandisciLeFotoPiccole._00_IngrandisciLeFotoPiccoleManager import ingrandisciLeFotoPiccoleManager
from ._06_RendiContrastoEColoreReali._00_RendiContrastoEColoreRealiManager import rendiContrastoEColoreRealiManager
from ._07_SistemaLeLuciBruciate._00_SistemaLeLuciBruciateManager import sistemaLeLuciBruciateManager
from ._09_SalvaLaFotoInJpegNelSitoDelCliente._00_SalvaLaFotoInJpegNelSitoDelClienteManager import \
    salvaLaFotoInJpegNelSitoDelClienteManager


def miglioramentoDiUnaFoto(copiaDelTemplate, idArea, forma, perQuesta):
    immagine = raddrizzaLaFotoManager(perQuesta["percorso"])
    centro = trovaIlCentroDelSoggettoDellaFotoManager(immagine, perQuesta["foto"].get("soggetto"))
    taglio = tagliaLaFotoInSediciNoniENoveSedicesimiManager(immagine, centro, [forma])[forma]
    taglio = ingrandisciLeFotoPiccoleManager(taglio, bool(perQuesta["foto"].get("scritte")), idArea)
    taglio = rendiContrastoEColoreRealiManager(taglio)
    taglio = sistemaLeLuciBruciateManager(taglio)
    return salvaLaFotoInJpegNelSitoDelClienteManager(taglio, copiaDelTemplate["sito"], idArea, forma)


def miglioramentoDelleFotoEsistentiDelClienteManager(copiaDelTemplate, materiale):
    # Pitstop (Michele, 11/11/2026): le foto delle aree si lavorano in parallelo (il modello e le librerie delle immagini
    # lasciano lavorare gli altri fili), con il tracciamento di ogni foto nella stessa azione del passo
    import contextvars
    from concurrent.futures import ThreadPoolExecutor
    scelte = scegliUnaFotoPerOgniAreaDellaStrutturaManager(copiaDelTemplate["contratto"], materiale["foto"], materiale["fotoScaricate"])
    lavori = [(idArea, forma, scelta["perForma"][forma]) for idArea, scelta in scelte.items() for forma in scelta["forme"]]
    with ThreadPoolExecutor(max_workers=4) as fili:
        futuri = [fili.submit(contextvars.copy_context().run, miglioramentoDiUnaFoto, copiaDelTemplate, idArea, forma, perQuesta)
                  for idArea, forma, perQuesta in lavori]
        risultati = [futuro.result() for futuro in futuri]
    fotoSalvate = {idArea: {} for idArea in scelte}
    for (idArea, forma, _), nome in zip(lavori, risultati):
        fotoSalvate[idArea][forma] = nome
    return {"idCliente": materiale["idCliente"], "scelte": scelte, "fotoSalvate": fotoSalvate}

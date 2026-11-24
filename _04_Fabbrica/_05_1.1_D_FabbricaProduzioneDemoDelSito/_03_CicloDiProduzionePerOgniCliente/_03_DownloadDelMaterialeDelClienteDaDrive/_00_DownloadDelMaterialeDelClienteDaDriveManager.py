"""Manager del passo 3: il download del materiale del cliente da Drive.

Riceve la scheda del cliente del passo 1 (con idDrive) e la copia del template del passo 2.2 (con cartellaDelClienteInCorso).
Pitstop 8 (Michele, 12/11/2026, task #613): i file JSON del materiale si leggono da Drive in una sola lettura
(_07_LeggiIFileDelMaterialeInUnaSolaLettura.py), nello stesso momento in cui si controlla la cartella di lavoro, e si
scaricano solo le foto che servono alle aree del contratto del template (passo 3.6). Copia di prima: .copiaPrimaVelocita.
"""

import contextvars
from concurrent.futures import ThreadPoolExecutor

from ._01_TrovaLaCartellaDiLavoroDelClienteSuDrive._00_TrovaLaCartellaDiLavoroDelClienteSuDriveManager import \
    trovaLaCartellaDiLavoroDelClienteSuDriveManager
from ._01_TrovaLaCartellaDiLavoroDelClienteSuDrive._01_TrovaLaCartellaDiLavoroDelClienteSuDrive import RACCOLTA
from ._02_RaccogliLeFotoValideDelCliente._00_RaccogliLeFotoValideDelClienteManager import \
    raccogliLeFotoValideDelClienteManager
from ._03_RaccogliLeRecensioniMigliori._00_RaccogliLeRecensioniMiglioriManager import \
    raccogliLeRecensioniMiglioriManager
from ._04_RicavaLeLingueDelSitoGiaEsistente._00_RicavaLeLingueDelSitoGiaEsistenteManager import \
    ricavaLeLingueDelSitoGiaEsistenteManager
from ._05_RaccogliIdatiUniciDelClienteInCorso._00_RaccogliIdatiUniciDelClienteInCorsoManager import \
    raccogliIdatiUniciDelClienteInCorsoManager
from ._06_ScaricaLeFotoMiglioriDelClienteInCorsoDaDrive._00_ScaricaLeFotoMiglioriDelClienteInCorsoDaDriveManager import \
    scaricaLeFotoMiglioriDelClienteInCorsoDaDriveManager
from ._07_LeggiIFileDelMaterialeInUnaSolaLettura import leggiIFileDelMaterialeInUnaSolaLettura


def downloadDelMaterialeDelClienteDaDriveManager(schedaDelCliente, copiaDelTemplate):
    """Per la massima velocità (Michele, 8/11/2026) le letture da Drive che non dipendono l'una dall'altra vanno insieme:
    le recensioni (3.3), le lingue (3.4) e i dati (3.5) mentre si scelgono e si scaricano le foto (3.2 e 3.6)."""
    with ThreadPoolExecutor(max_workers=1) as aParte:  # pitstop 8: la lettura unica dei JSON parte subito
        inLettura = aParte.submit(contextvars.copy_context().run, leggiIFileDelMaterialeInUnaSolaLettura,
                                  {"idDrive": schedaDelCliente["idDrive"], "raccolta": RACCOLTA})
        cartellaDiLavoro = trovaLaCartellaDiLavoroDelClienteSuDriveManager(schedaDelCliente["idDrive"])
        letti = inLettura.result()
    lavoro = {**cartellaDiLavoro, "letti": letti} if letti is not None else cartellaDiLavoro
    with ThreadPoolExecutor(max_workers=3) as insieme:
        inRecensioni = insieme.submit(raccogliLeRecensioniMiglioriManager, lavoro)
        inLingue = insieme.submit(ricavaLeLingueDelSitoGiaEsistenteManager, lavoro)
        inDati = insieme.submit(raccogliIdatiUniciDelClienteInCorsoManager, lavoro)
        foto = raccogliLeFotoValideDelClienteManager(lavoro)
        fotoScaricate = scaricaLeFotoMiglioriDelClienteInCorsoDaDriveManager(foto, copiaDelTemplate["cartellaDelClienteInCorso"],
                                                                             copiaDelTemplate.get("contratto"))
        recensioni, sitoGiaEsistente, datiUnici = inRecensioni.result(), inLingue.result(), inDati.result()
    return {"idCliente": schedaDelCliente["idCliente"], "cartellaDiLavoro": cartellaDiLavoro, "foto": foto,
            "recensioni": recensioni, "sitoGiaEsistente": sitoGiaEsistente, "datiUnici": datiUnici,
            "fotoScaricate": fotoScaricate}

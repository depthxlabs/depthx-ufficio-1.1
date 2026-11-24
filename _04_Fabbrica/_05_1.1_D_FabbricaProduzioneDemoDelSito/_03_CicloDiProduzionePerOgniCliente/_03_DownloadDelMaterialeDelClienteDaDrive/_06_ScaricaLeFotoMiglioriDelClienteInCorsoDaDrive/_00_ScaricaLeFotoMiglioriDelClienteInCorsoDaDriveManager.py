"""Manager del passo 3.6: le foto migliori del cliente in corso, scaricate da Drive.
Pitstop 8 (Michele, 12/11/2026, task #613): con il contratto del template si scaricano solo le foto che servono alle sue aree.
Copia di prima: .copiaPrimaVelocita.
"""

from ._02_ScaricaLeFotoMiglioriDelClienteInCorsoDaDrive import scaricaLeFotoMiglioriDelClienteInCorsoDaDrive


def scaricaLeFotoMiglioriDelClienteInCorsoDaDriveManager(fotoInOrdine, cartellaDelClienteInCorso, contratto=None):
    return scaricaLeFotoMiglioriDelClienteInCorsoDaDrive(fotoInOrdine, cartellaDelClienteInCorso, contratto)

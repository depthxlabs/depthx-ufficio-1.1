"""Manager del passo 1.2: la verifica che il motore di download abbia scaricato il materiale del cliente."""

from ._01_StatoDelClienteScaricato import statoDelClienteScaricato
from ._02_ElencoDeiClientiScaricatiDalMotore import elencoDeiClientiScaricatiDalMotore


def verificaCheIlMotoreDiDownloadAbbiaScaricatoIlMaterialeDelClienteManager(idCliente):
    statoNelMotore = statoDelClienteScaricato(idCliente)
    if idCliente not in elencoDeiClientiScaricatiDalMotore():
        raise RuntimeError(f"{idCliente}: il cliente non è nell'elenco dei clienti scaricati dal motore")
    return statoNelMotore

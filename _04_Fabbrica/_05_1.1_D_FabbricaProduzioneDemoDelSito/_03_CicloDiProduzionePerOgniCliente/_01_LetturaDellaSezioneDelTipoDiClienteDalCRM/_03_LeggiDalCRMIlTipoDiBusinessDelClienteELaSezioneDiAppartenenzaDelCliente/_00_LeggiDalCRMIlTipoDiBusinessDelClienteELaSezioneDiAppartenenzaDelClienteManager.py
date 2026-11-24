"""Manager del passo 1.3: il tipo di business del cliente e la sezione del CRM a cui appartiene."""

from ._01_TipoESezioneDelCliente import tipoESezioneDelCliente


def leggiDalCRMIlTipoDiBusinessDelClienteELaSezioneDiAppartenenzaDelClienteManager(idCliente, cartellaSuDrive, statoNelMotore):
    return tipoESezioneDelCliente(idCliente, cartellaSuDrive, statoNelMotore)

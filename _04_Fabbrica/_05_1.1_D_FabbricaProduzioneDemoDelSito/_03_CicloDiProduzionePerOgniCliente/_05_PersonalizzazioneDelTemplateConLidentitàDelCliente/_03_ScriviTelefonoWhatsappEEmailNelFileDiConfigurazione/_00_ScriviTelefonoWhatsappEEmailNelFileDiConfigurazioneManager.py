"""Manager del passo 5.3: telefono, WhatsApp ed email nel file di configurazione."""

from ._02_ScriviTelefonoWhatsappEEmailNelFileDiConfigurazione import scriviTelefonoWhatsappEEmailNelFileDiConfigurazione, \
    togliIlWhatsappDalFileDiConfigurazione


def scriviTelefonoWhatsappEEmailNelFileDiConfigurazioneManager(sito, datiUnici):
    return scriviTelefonoWhatsappEEmailNelFileDiConfigurazione(sito, datiUnici)

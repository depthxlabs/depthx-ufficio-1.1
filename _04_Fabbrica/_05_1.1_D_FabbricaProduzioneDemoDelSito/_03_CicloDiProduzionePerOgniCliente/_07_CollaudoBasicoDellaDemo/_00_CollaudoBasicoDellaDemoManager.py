"""Manager del passo 7: il collaudo basico della demo, le cose tecniche.

Riceve la copia del template del passo 2.2 (sito e contratto), il materiale del passo 3 (dati del CRM e recensioni) e le
foto migliorate del passo 4 (le foto salvate nel sito). Il collaudo guarda solo il codice che riceve il visitatore, senza
i commenti. GO solo se passano tutti i controlli, altrimenti NOTGO con la causa di ogni controllo non passato.
"""

from ._01_ControlloCheNessunaParolaDelTemplateSiaRimasta._00_ControlloCheNessunaParolaDelTemplateSiaRimastaManager import \
    controlloCheNessunaParolaDelTemplateSiaRimastaManager
from ._02_ControlloCheNonCiSiaNessunaParolaVietata._00_ControlloCheNonCiSiaNessunaParolaVietataManager import \
    controlloCheNonCiSiaNessunaParolaVietataManager
from ._03_ControlloCheTuttiIFileChiamatiEsistono._00_ControlloCheTuttiIFileChiamatiEsistonoManager import \
    controlloCheTuttiIFileChiamatiEsistonoManager
from ._04_ControlloCheGliScriptSianoValidi._00_ControlloCheGliScriptSianoValidiManager import \
    controlloCheGliScriptSianoValidiManager
from ._05_ControlloDellaConfigurazioneDelleScenePresenti._00_ControlloDellaConfigurazioneDelleScenePresentiManager import \
    controlloDellaConfigurazioneDelleScenePresentiManager
from ._06_ControlloDelContattoTelefonicoPresente._00_ControlloDelContattoTelefonicoPresenteManager import \
    controlloDelContattoTelefonicoPresenteManager
from ._07_ControlloCheOgniFraseSiaDelCopywritingApprovato._00_ControlloCheOgniFraseSiaDelCopywritingApprovatoManager import \
    controlloCheOgniFraseSiaDelCopywritingApprovatoManager
from ._08_ControlloCheLaStrutturaParliConIlNoiEChiamiLOspiteConIlVoi._00_ControlloCheLaStrutturaParliConIlNoiEChiamiLOspiteConIlVoiManager import \
    controlloCheLaStrutturaParliConIlNoiEChiamiLOspiteConIlVoiManager
from ._09_ControlloCheLeRecensioniNonAbbianoIlNomeDiChiLeHaScritte._00_ControlloCheLeRecensioniNonAbbianoIlNomeDiChiLeHaScritteManager import \
    controlloCheLeRecensioniNonAbbianoIlNomeDiChiLeHaScritteManager
from ._10_ControlloCheNelSitoNonCiSianoVotoENumeroDelleRecensioni._00_ControlloCheNelSitoNonCiSianoVotoENumeroDelleRecensioniManager import \
    controlloCheNelSitoNonCiSianoVotoENumeroDelleRecensioniManager
from ._11_ControlloCheIlLinkDelleRecensioniPortiAGoogle._00_ControlloCheIlLinkDelleRecensioniPortiAGoogleManager import \
    controlloCheIlLinkDelleRecensioniPortiAGoogleManager
from ._12_ControlloDellIconaInOgniPagina._00_ControlloDellIconaInOgniPaginaManager import controlloDellIconaInOgniPaginaManager
from ._13_ControlloDelLogoNellaHome._00_ControlloDelLogoNellaHomeManager import controlloDelLogoNellaHomeManager
from ._14_ControlloDellaListaAdvanced._00_ControlloDellaListaAdvancedManager import controlloDellaListaAdvancedManager


def collaudoBasicoDellaDemoManager(copiaDelTemplate, materiale, fotoMigliorate):
    sito, contratto = copiaDelTemplate["sito"], copiaDelTemplate["contratto"]
    crm, recensioni = materiale["datiUnici"]["crm"], materiale.get("recensioni") or []
    controlli = {
        "paroleDelTemplate": controlloCheNessunaParolaDelTemplateSiaRimastaManager(sito, contratto),
        "paroleVietate": controlloCheNonCiSiaNessunaParolaVietataManager(sito, recensioni),
        "fileChiamati": controlloCheTuttiIFileChiamatiEsistonoManager(sito, fotoMigliorate["fotoSalvate"]),
        "script": controlloCheGliScriptSianoValidiManager(sito),
        "configurazioneDelleScene": controlloDellaConfigurazioneDelleScenePresentiManager(sito),
        "telefono": controlloDelContattoTelefonicoPresenteManager(sito, crm),
        "copywritingApprovato": controlloCheOgniFraseSiaDelCopywritingApprovatoManager(sito, recensioni),
        "noiEVoi": controlloCheLaStrutturaParliConIlNoiEChiamiLOspiteConIlVoiManager(sito, recensioni),
        "nomiDegliOspiti": controlloCheLeRecensioniNonAbbianoIlNomeDiChiLeHaScritteManager(sito, recensioni),
        "votoENumeroDelleRecensioni": controlloCheNelSitoNonCiSianoVotoENumeroDelleRecensioniManager(sito),
        "linkDelleRecensioni": controlloCheIlLinkDelleRecensioniPortiAGoogleManager(sito),
        "icona": controlloDellIconaInOgniPaginaManager(sito),
        "logoNellaHome": controlloDelLogoNellaHomeManager(sito),
        "listaAdvanced": controlloDellaListaAdvancedManager(sito),
    }
    return {"idCliente": materiale["idCliente"], "esito": "NOTGO" if any(controlli.values()) else "GO",
            "controlli": controlli}

"""Manager del passo 5: la personalizzazione del template con l'identità del cliente.

Riceve la scheda del cliente del passo 1, la copia del template del passo 2.2, il materiale del passo 3 e le foto
migliorate del passo 4. Scrive i dati veri nel file di configurazione, sceglie le pagine della lista Advanced (passo 5.15),
scrive i testi e le recensioni nelle pagine, poi colore, logo e icona del cliente; alla fine toglie le pagine rimaste senza
materiale (passo 5.15).
"""

from ._01_ScriviIlNomeDelClienteNelFileDiConfigurazione._00_ScriviIlNomeDelClienteNelFileDiConfigurazioneManager import \
    scriviIlNomeDelClienteNelFileDiConfigurazioneManager
from ._02_ScriviPosizioneEMappaNelFileDiConfigurazione._00_ScriviPosizioneEMappaNelFileDiConfigurazioneManager import \
    scriviPosizioneEMappaNelFileDiConfigurazioneManager
from ._03_ScriviTelefonoWhatsappEEmailNelFileDiConfigurazione._00_ScriviTelefonoWhatsappEEmailNelFileDiConfigurazioneManager import \
    scriviTelefonoWhatsappEEmailNelFileDiConfigurazioneManager, togliIlWhatsappDalFileDiConfigurazione
from ._04_ScriviFacebookEInstagramNelFileDiConfigurazione._00_ScriviFacebookEInstagramNelFileDiConfigurazioneManager import \
    scriviFacebookEInstagramNelFileDiConfigurazioneManager
from ._05_ScriviIlLinkDelleRecensioniNelFileDiConfigurazione._00_ScriviIlLinkDelleRecensioniNelFileDiConfigurazioneManager import \
    scriviIlLinkDelleRecensioniNelFileDiConfigurazioneManager
from ._06_ScriviLeLingueDellaDemoNelFileDiConfigurazione._00_ScriviLeLingueDellaDemoNelFileDiConfigurazioneManager import \
    scriviLeLingueDellaDemoNelFileDiConfigurazioneManager
from ._07_ScriviLeAreeDellaStrutturaNelFileDiConfigurazione._00_ScriviLeAreeDellaStrutturaNelFileDiConfigurazioneManager import \
    scriviLeAreeDellaStrutturaNelFileDiConfigurazioneManager
from ._08_TestiPerOgniCliente._00_TestiPerOgniClienteManager import testiPerOgniClienteManager
from ._09_ScriviLeRecensioniMiglioriNellaPagina._00_ScriviLeRecensioniMiglioriNellaPaginaManager import \
    scriviLeRecensioniMiglioriNellaPaginaManager
from ._10_TrovaIlColoreDelCliente._00_TrovaIlColoreDelClienteManager import trovaIlColoreDelClienteManager
from ._11_ColoraIlSitoConIlColoreDelCliente._00_ColoraIlSitoConIlColoreDelClienteManager import \
    coloraIlSitoConIlColoreDelClienteManager
from ._12_MettiIlLogoDelCliente._00_MettiIlLogoDelClienteManager import mettiIlLogoDelClienteManager
from ._13_ScriviIlNomeComeLogoSeIlLogoManca._00_ScriviIlNomeComeLogoSeIlLogoMancaManager import \
    scriviIlNomeComeLogoSeIlLogoMancaManager
from ._14_CreaLIconaDelSito._00_CreaLIconaDelSitoManager import creaLIconaDelSitoManager
from ._15_LePagineDallaListaAdvanced._00_LePagineDallaListaAdvancedManager import     primaSezioneRiccaManager, scegliLePagineDallaListaAdvancedManager, togliLePagineVuoteManager


def personalizzazioneDelTemplateConLidentitàDelClienteManager(schedaDelCliente, copiaDelTemplate, materiale, fotoMigliorate):
    sito, datiUnici = copiaDelTemplate["sito"], materiale["datiUnici"]
    nome = scriviIlNomeDelClienteNelFileDiConfigurazioneManager(sito, datiUnici)
    posizione = scriviPosizioneEMappaNelFileDiConfigurazioneManager(sito, datiUnici)
    contatti = scriviTelefonoWhatsappEEmailNelFileDiConfigurazioneManager(sito, datiUnici)
    social = scriviFacebookEInstagramNelFileDiConfigurazioneManager(sito, datiUnici)
    recensioniGoogle = scriviIlLinkDelleRecensioniNelFileDiConfigurazioneManager(sito, datiUnici)
    lingue = scriviLeLingueDellaDemoNelFileDiConfigurazioneManager(sito, schedaDelCliente, materiale["sitoGiaEsistente"])
    aree = scriviLeAreeDellaStrutturaNelFileDiConfigurazioneManager(sito, copiaDelTemplate["contratto"], fotoMigliorate["fotoSalvate"])
    # le pagine della lista Advanced (Michele, 11/11/2026): prima dei testi, così i testi si scrivono solo nelle pagine che nascono
    pagine = scegliLePagineDallaListaAdvancedManager(sito, copiaDelTemplate["contratto"], aree)
    testi = testiPerOgniClienteManager(sito, datiUnici, schedaDelCliente, materiale["recensioni"],
                                      {scena for scena, conFoto in aree.items() if conFoto})
    if contatti["whatsapp"] and not testi["fatti"].get("whatsapp"):
        togliIlWhatsappDalFileDiConfigurazione(sito)
        contatti["whatsapp"] = ""
    recensioniScritte = scriviLeRecensioniMiglioriNellaPaginaManager(sito, materiale["recensioni"])
    identitaCompletata = completaIFattiDellIdentita(sito, testi["fatti"])
    colore = trovaIlColoreDelClienteManager(materiale["foto"], materiale["fotoScaricate"], fotoMigliorate["scelte"])
    colori = coloraIlSitoConIlColoreDelClienteManager(sito, colore["tinta"])
    logo = mettiIlLogoDelClienteManager(sito, materiale["foto"], materiale["fotoScaricate"])
    nomeComeLogo = scriviIlNomeComeLogoSeIlLogoMancaManager(sito, logo)
    icona = creaLIconaDelSitoManager(sito, nome["nome"], colore["tinta"], logo)
    pagine["primaSezioneSalita"] = primaSezioneRiccaManager(sito)
    # Michele, 11/11/2026: la regola "una pagina senza materiale non nasce" è tolta; ogni sezione ha una frase che vale con i
    # dati del CRM, così nessuna pagina resta vuota
    return {"idCliente": schedaDelCliente["idCliente"], "nome": nome, "posizione": posizione, "contatti": contatti,
            "social": social, "recensioniGoogle": recensioniGoogle, "lingue": lingue, "aree": aree, "testi": testi,
            "recensioniScritte": recensioniScritte, "colore": colore, "colori": colori, "logo": logo,
            "nomeComeLogo": nomeComeLogo, "icona": icona, "identitaCompletata": identitaCompletata, "pagine": pagine}


# Siti atomici (Michele, 9/11/2026): un segnaposto dell'identità rimasto nella pagina (per esempio la firma "un ospite di
# {nomestruttura}" dell'Hotel, che è in un elemento diverso) si completa sempre con il fatto vero, e la frase completata conta
# come verificata, perché dice solo chi è e dove sta la struttura. Gli altri segnaposto restano ai passi che li gestiscono.
FATTI_SEMPRE_VERI = ("nomestruttura", "nomeBreve", "comune", "provincia", "regione")


def completaIFattiDellIdentita(sito, fatti):
    import html
    import json
    import re
    from pathlib import Path
    valori = {chiave: str(fatti.get(chiave)).strip() for chiave in FATTI_SEMPRE_VERI if str(fatti.get(chiave) or "").strip()}
    if not valori:
        return []
    segnaposto = re.compile(r"\{(" + "|".join(valori) + r")\}")
    completate = []
    for pagina in Path(sito).glob("*.html"):
        codice = pagina.read_text(encoding="utf-8-sig")
        for testo in re.findall(r">([^<>]*\{(?:" + "|".join(valori) + r")\}[^<>]*)<", codice):
            if not re.search(r"\{(?!(?:" + "|".join(valori) + r")\})\w+\}", testo):
                completate.append(" ".join(html.unescape(segnaposto.sub(lambda m: valori[m.group(1)], testo)).split()))
        nuovo = segnaposto.sub(lambda m: html.escape(valori[m.group(1)], quote=True), codice)
        if nuovo != codice:
            pagina.write_text(nuovo, encoding="utf-8")
    file = Path(sito).parent / "frasiVerificate.json"
    if completate and file.is_file():
        verificate = json.loads(file.read_text(encoding="utf-8"))
        file.write_text(json.dumps(verificate + [f for f in completate if f not in verificate], ensure_ascii=False, indent=1), encoding="utf-8")
    return completate

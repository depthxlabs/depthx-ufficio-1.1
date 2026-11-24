"""Passo 5.9: le recensioni migliori del cliente (passo 3.3) nella pagina, al posto dei segnaposto del template.

{recensioneInEvidenza}, {testoDellaRecensione} e {testoRecensione1} prendono la recensione migliore, {recensione2},
{recensione3}, {testoRecensione2}...{testoRecensione6} le successive (6 nel pacchetto Advanced, Michele 11/11/2026). Il testo si riporta intero, non si tocca e non si commenta
(si tolgono solo le emoji e le virgolette attorno; le recensioni tagliate con i tre puntini vanno dopo le altre); mai il nome di chi l'ha scritta (la firma del
template è "un ospite di {nomestruttura}"). Le parole vietate valgono per i testi di DepthX, non per le parole degli ospiti:
una recensione entra anche se ne contiene una (Michele, 8/11/2026). Se mancano recensioni, il riquadro della recensione
rimasta senza testo esce intero, con la sua firma; una sezione delle recensioni senza nessuna recensione esce intera.
"""

import html
import re
from pathlib import Path

from ..._03_DownloadDelMaterialeDelClienteDaDrive._03_RaccogliLeRecensioniMigliori._02_RaccogliLeRecensioniMigliori import testoPulito
from .._08_TestiPerOgniCliente._07_DueOTreFrasiPerOgniSezione._01_DueOTreFrasiPerOgniSezione import togliLaSezione

SEZIONE = re.compile(r"<section\b([^>]*)>(.*?)</section\s*>", re.S | re.I)
SEGNAPOSTO = re.compile(r"\{(?:recensioneInEvidenza|testoDellaRecensione|recensione[23]|testoRecensione[1-6])\}")


def togliLaRecensioneVuota(codice, segnaposto):
    """Una recensione che manca esce con tutto il suo riquadro (figura, citazione, scheda), firma compresa: mai una firma
    "un ospite di..." senza il testo (Michele, 8/11/2026). Se il riquadro non c'è, esce solo l'elemento del segnaposto."""
    for tag in ("figure", "article", "li", "blockquote"):
        dentro = r"(?:(?!</?" + tag + r"\b).)*?"  # senza uscire dal riquadro e senza entrare in un altro
        riquadro = re.compile(r"<" + tag + r"\b[^>]*>" + dentro + r"\{" + segnaposto + r"\}" + dentro + r"</" + tag + r"\s*>", re.S | re.I)
        if riquadro.search(codice):
            return riquadro.sub("", codice, count=1)
    return re.sub(r"<([a-zA-Z0-9]+)(?:\s[^>]*)?>[^<]*\{" + segnaposto + r"\}[^<]*</\1\s*>", "", codice)


POSIZIONE_DEL_SEGNAPOSTO = {"recensioneInEvidenza": 0, "testoDellaRecensione": 0, "recensione2": 1, "recensione3": 2,
                           "testoRecensione1": 0, "testoRecensione2": 1, "testoRecensione3": 2,
                           # pacchetto Advanced (Michele, 11/11/2026): 6 recensioni Google nel sito
                           "testoRecensione4": 3, "testoRecensione5": 4, "testoRecensione6": 5}


CHIAVI_DEL_NOME = ("autore", "nome", "nomeAutore", "author", "name")


def nomiDegliAutori(recensioni):
    """I nomi di chi ha scritto le recensioni, come li cerca il collaudo 7.9: parole intere, almeno 3 lettere."""
    nomi = []
    for voce in recensioni:
        nome = next((str(voce[chiave]).strip() for chiave in CHIAVI_DEL_NOME if voce.get(chiave)), "")
        if len(re.findall(r"[^\W\d_]", nome)) >= 3:
            nomi.append(re.compile(r"(?<![\wà-ÿ])" + r"\s+".join(re.escape(p[:1].upper() + p[1:].lower()) for p in nome.split()) + r"(?![\wà-ÿ])"))
    return nomi


def scriviLeRecensioniMiglioriNellaPagina(sito, recensioni):
    # le stelle vere di ogni recensione accanto al suo testo (Michele, 11/11/2026): mai un voto inventato
    voci = [(testoPulito(voce.get("testo")), voce.get("voto")) for voce in recensioni]
    voci = [voce for voce in voci if voce[0]]
    # il testo non si tocca: entrano solo le recensioni che non nominano nessuno degli autori (un ospite che ringrazia
    # "Paolo e Raffaella" fa comparire nel sito il nome di chi ha scritto un'altra recensione, e il collaudo 7.9 ferma la demo)
    nomi = nomiDegliAutori(recensioni)
    voci = [voce for voce in voci if not any(nome.search(" ".join(voce[0].split())) for nome in nomi)]
    voci.sort(key=lambda voce: voce[0].endswith(("…", "...")))
    testi = [testo for testo, _ in voci]
    stelle = ["★" * max(1, min(5, round(float(voto)))) if voto else "" for _, voto in voci]
    scritte = 0
    for pagina in Path(sito).glob("*.html"):
        codice = pagina.read_text(encoding="utf-8-sig")
        conRecensioni = [s.group(1) for s in SEZIONE.finditer(codice) if SEGNAPOSTO.search(s.group(0))]
        for segnaposto, posizione in POSIZIONE_DEL_SEGNAPOSTO.items():
            if "{" + segnaposto + "}" not in codice:
                continue
            if posizione < len(testi):
                codice = codice.replace("{" + segnaposto + "}", html.escape(testi[posizione], quote=True))
                numero = re.search(r"\d$", segnaposto)
                if numero:
                    codice = codice.replace("{stelleRecensione" + numero.group(0) + "}", stelle[posizione])
                scritte += 1
            else:
                codice = togliLaRecensioneVuota(codice, segnaposto)
        # una sezione delle recensioni rimasta senza nessuna recensione esce intera, con i link del menu (Michele, 8/11/2026)
        for sezione in list(SEZIONE.finditer(codice)):
            if sezione.group(1) in conRecensioni and not re.search(r"<blockquote\b", sezione.group(0)):  # una foto da sola non è una recensione
                codice, _ = togliLaSezione(codice, sezione)
        codice = re.sub(r'<span class="stelle"[^>]*>\{stelleRecensione\d\}</span>', "", codice)  # senza voto, niente stelle
        pagina.write_text(codice, encoding="utf-8")
    return scritte

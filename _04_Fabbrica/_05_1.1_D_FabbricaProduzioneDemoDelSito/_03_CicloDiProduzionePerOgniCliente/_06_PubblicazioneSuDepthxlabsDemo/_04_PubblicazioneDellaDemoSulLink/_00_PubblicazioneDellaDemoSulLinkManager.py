"""Manager del passo 6.4: la demo online sul suo link depthxlabs.com/demo/<nome>/.

Prima escono le demo scadute (dalla cartella di pubblicazione e da R2), poi la demo si carica su R2, poi si controlla che tutte
le pagine della demo siano online, non solo la prima (Michele, 11/11/2026, task #578).
R2 (12/11/2026): le risorse statiche del Worker avevano raggiunto il limite di file del piano gratuito (errore 10304). Ora il
Worker delle demo legge i file dal bucket R2 "depthx-demo" e non si ripubblica più: ogni demo carica solo i suoi file
(_13_PubblicazioneSuR2). Le fabbriche non si aspettano più a vicenda: il blocco "una pubblicazione alla volta" resta solo per
togliere le demo scadute. Se R2 non risponde, il passo dà NOTGO con il motivo (niente wrangler deploy).
"""

from _01_StrumentiDellaFabbrica._07_UnaSolaFabbricaAccesa._01_UnaSolaFabbricaAccesa import unaPubblicazioneAllaVolta

from ._04_TogliLeDemoScaduteDallaCartellaDiPubblicazione import togliLeDemoScaduteDallaCartellaDiPubblicazione
from ._06_LinkDellaDemo import linkDellaDemo
from ._07_ControlloCheTutteLePagineSianoOnline import controlloCheTutteLePagineSianoOnline
from ._13_PubblicazioneSuR2 import pubblicazioneDellaDemoSuR2


def pubblicazioneDellaDemoSulLinkManager(nome):
    with unaPubblicazioneAllaVolta():
        demoScaduteTolte = togliLeDemoScaduteDallaCartellaDiPubblicazione(tranne=nome)
    versione = pubblicazioneDellaDemoSuR2(nome)["versione"]
    link = linkDellaDemo(nome)
    pagineOnline = controlloCheTutteLePagineSianoOnline(nome, link)
    return {"link": link, "versione": versione, "demoScaduteTolte": demoScaduteTolte, "pagineOnline": pagineOnline}

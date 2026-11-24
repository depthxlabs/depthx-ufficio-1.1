"""Le demo scadute escono dalla cartella di pubblicazione e da R2, così restano solo le demo ancora valide.

La scadenza si legge dal registro delle demo su Cloudflare: dall'etichetta della chiave (scritta dal passo 6.3), oppure dalla
scheda per le demo pubblicate prima delle etichette. La scheda resta su Cloudflare: il link di una demo scaduta mostra la pagina
"anteprima non più disponibile" e le aperture restano per il Centro Gestione. Una cartella senza scheda non si tocca.
Restituisce i nomi delle demo tolte. Pitstop 4 (task #609, 12/11/2026): il registro si legge con le API di Cloudflare.
R2 (12/11/2026): i file della demo scaduta escono prima da R2, poi dalla cartella; se R2 non risponde la cartella resta e si
riprova alla pubblicazione dopo (il Worker mostra comunque "anteprima non più disponibile"). La demo che si sta pubblicando
(tranne) non si tocca.
"""

import datetime
from pathlib import Path

from .._02_CopiaNellaCartellaDiPubblicazione._01_CopiaNellaCartellaDiPubblicazione import CARTELLA_DI_PUBBLICAZIONE, \
    togliLaCartella
from ._03_SchedaDellaDemoSuCloudflare import schedaDellaDemoSuCloudflare
from ._09_ApiDiCloudflare import chiaviDelRegistro
from ._13_PubblicazioneSuR2 import togliLaDemoDaR2


def togliLeDemoScaduteDallaCartellaDiPubblicazione(cartella=CARTELLA_DI_PUBBLICAZIONE, tranne=None):
    # la pulizia delle scadute si fa al massimo una volta all'ora: l'elenco del registro ha una quota giornaliera su Cloudflare
    segno = Path(cartella).parent / "_03_UltimaPuliziaDelleScadute.txt"
    try:
        if segno.exists() and datetime.datetime.now().timestamp() - segno.stat().st_mtime < 3600:
            return []
        segno.write_text(datetime.datetime.now().isoformat(timespec="seconds"), encoding="utf-8")
        etichette = {voce["name"][5:]: voce.get("metadata") or {} for voce in chiaviDelRegistro("demo:")}
    except Exception as errore:
        # senza l'elenco la pulizia si salta: la pubblicazione della demo nuova continua
        print(f"pulizia delle demo scadute saltata, registro delle demo non letto da Cloudflare: {str(errore)[:200]}")
        return []
    ora = datetime.datetime.now(datetime.timezone.utc)
    tolte = []
    for demo in sorted(Path(cartella).iterdir()):
        if not demo.is_dir() or demo.name.startswith(".") or demo.name not in etichette or demo.name == tranne:
            continue
        scadenza = etichette[demo.name].get("scadenza") or (schedaDellaDemoSuCloudflare(demo.name) or {}).get("scadenza")
        if scadenza and datetime.datetime.fromisoformat(scadenza.replace("Z", "+00:00")) <= ora:
            try:
                togliLaDemoDaR2(demo.name)
            except Exception as errore:
                print(str(errore)[:400])
                continue
            togliLaCartella(demo)
            tolte.append(demo.name)
    return tolte

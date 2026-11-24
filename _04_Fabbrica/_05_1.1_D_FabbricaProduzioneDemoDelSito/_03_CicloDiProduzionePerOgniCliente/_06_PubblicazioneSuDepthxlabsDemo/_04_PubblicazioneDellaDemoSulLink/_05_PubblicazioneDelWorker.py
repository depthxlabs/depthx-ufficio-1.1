"""Il Worker delle demo NON si ripubblica più a ogni demo (R2, 12/11/2026).

Il Worker (_01_PercorsoDelleDemoSuCloudflare) è il piccolo programma di Cloudflare che risponde a depthxlabs.com/demo/...: legge
la scheda della demo (se è scaduta mostra "anteprima non più disponibile"), registra le aperture dopo l'invio e serve i file del
sito del cliente dal bucket R2 "depthx-demo". Le demo si pubblicano caricando i loro file su R2 (_13_PubblicazioneSuR2).
Ripubblicarlo con wrangler deploy e le risorse statiche riempirebbe di nuovo il limite di file del piano gratuito (errore 10304):
per questo qui non si fa più. La copia di prima è _05_PubblicazioneDelWorker.py.copiaPrimaR2.
"""


def pubblicazioneDelWorker(*opzioni):
    raise RuntimeError("il Worker delle demo non si ripubblica più a ogni demo: la demo si carica su R2 (_13_PubblicazioneSuR2)")

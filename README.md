# DepthX Linea 1.1, Ricerca clienti

Motore di ricerca dei clienti dell'ospitalità (Hotel, B&B, Agriturismi, Case Vacanze) su GitHub Actions.

- La ricerca parte dal Centro Gestione: tipi, città di partenza, raggio, obiettivo di contatti.
- Ogni giro il piano dà fino a 20 coppie tipo e comune ai motori, che lavorano tutti insieme.
- Ogni motore cerca su Google Maps, controlla il sito e tiene solo chi ha un'email pubblica.
- Sezione decisa dal controllo del sito: S3 datato, S2 debole, S4 di qualità.
- Il giro successivo parte appena finisce il precedente, fino all'obiettivo.
- I contatti vanno nel repository privato depthx-dati-1.1; il Centro Gestione li scrive nel CRM su disco.

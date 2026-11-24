# Motore di download del materiale clienti, Linea 1.1 Outbound Websites (aggiornato il 4/11/2026)

Il motore legge i clienti dal CRM, scarica il loro materiale pubblico, riconosce le foto, scrive il rapporto di unicità
e carica tutto su Google Drive, nella cartella di ogni cliente. Le regole complete sono nelle skill:
`C:\Users\Administrator\.claude\skills\_03_Business\_01_ClaudeInDepthXLabs\_01_Linea1_ProductionDepartement\_01_Linea_1.1_OUTBOUND_WEBSITES\_01_1.1_A_GestioneAcquisizioneMaterialeClienti\_02_1.1_A_MotoreGestioneAcquisizioneMaterialeClienti`

## Le cartelle, una per passo

| Cartella | Cosa contiene |
|---|---|
| `_01_StrumentiDelMotore` | Ambiente Python, chiavi, regole numeriche, coordinatore, registro, file temporanei, profilo Chrome dell'account dedicato, comandi |
| `_02_LetturaDalCRM` | Lettura dei 140 fogli del CRM, colonne, blocco in corso |
| `_03_DownloadDalleFonti` | Google Maps (dal Chrome dell'account dedicato), sito attuale, Instagram, YouTube, video con yt-dlp |
| `_04_RiconoscimentoDelleFoto` | 12 categorie, voto, scarti di foto piccole, sfocate e doppie |
| `_05_RapportoDiUnicita` | I settori in cui il cliente ha qualcosa di caratteristico, con le citazioni verificate (sonnet, piano Claude Max) |
| `_06_CaricamentoSuDrive` | Caricamento verificato con MD5 e dimensione, 8 file insieme, elenco delle cartelle dei clienti |

Facebook e TikTok non si scaricano più (Michele, 4/11/2026).

## Come lavora
- **Un blocco è un foglio del CRM:** il motore scarica il foglio intero, poi passa al successivo nell'ordine del CRM, saltando i fogli già chiusi. Il blocco in corso è in `_02_LetturaDalCRM\_05_BloccoDiDownloadInCorso.json`.
- **In parallelo:** i clienti da fare del foglio si dividono in parti da 3, fino a 6 lavoratori insieme; due giri (il secondo completa i Parziali).
- **Riprende sempre da dove era:** i clienti GO e Saltati non si rifanno.

## Comandi
Da `_01_StrumentiDelMotore`:
- **Avvio:** `_01_AmbientePythonDelMotore\Scripts\python.exe -B _04_CoordinatoreDelMotore\_01_CoordinatoreELavoratoriDelMotore.py --coordinatore`
  - `--industrie 004,005`: solo i fogli indicati; `--tutto`: tutti i fogli insieme;
  - `--unicita --industria NNN`: solo il rapporto di unicità sui clienti già scaricati del foglio.
- **Arresto:** il pulsante "Ferma il motore" del Centro Gestione, oppure `_08_ComandiDelMotore\_01_ArrestoDelMotore.cmd`.
- **Consenso Google Drive** (account depthxlabs): `_08_ComandiDelMotore\_02_ConsensoGoogleDriveDelMotore.cmd`.
- **Accesso di Michele all'account dedicato a Maps:** `_08_ComandiDelMotore\_03_AperturaDelProfiloChromePerLAccessoDiMichele.bat`, a motore fermo.
- L'avvio automatico con l'inizio dell'invio si costruisce insieme alla parte dell'invio.

## Registro
In `_05_RegistroEStatoDelMotore`: `registro.jsonl` (un evento per riga), `stato.json` (la fotografia di adesso, letta dal Centro Gestione),
`tokenDelRapportoDiUnicita.jsonl` (token di ogni chiamata a sonnet), battiti, uscite dei lavoratori e `motore.pid`.

## Dove va il materiale
Google Drive di depthxlabs, `_01_Area_1B_CartelleDeiClientiCompleteProntePerIniziareLaProduzione / sezione / tipo / _C_S_ID_NomeCliente`,
con `_01_RaccoltaMateriale` (da `_01_SchedaDiGoogle` a `_10_IlRestoDeiDati`), `_02_ProduzioneDelSitoDemo` e `_03_InvioEProcessoDiVendita`.

## Backup
Il backup del codice lo fa Michele nella cartella Drive `_01_StrumentiDelMotore` (id 1Dpsty805a6IU3VOpdSzIV7AIjrqEXGTZ), senza l'ambiente Python
e senza il profilo Chrome: si ricreano con `_09_ElencoDelleLibrerieDelMotore.txt` e `_10_ComeRifareIlProfiloChrome.md`.

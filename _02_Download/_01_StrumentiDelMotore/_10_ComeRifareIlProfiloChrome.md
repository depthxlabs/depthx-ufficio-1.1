# Come rifare l'ambiente Python e il profilo Chrome del motore

Il backup su Drive non contiene due cartelle di `_01_StrumentiDelMotore`, per scelta di Michele (4/11/2026):

| Cartella | Perché non è nel backup | Come si rifà |
|---|---|---|
| `_01_AmbientePythonDelMotore` | 7.600 file di librerie, si ricreano uguali | punto 1 |
| `_07_ProfiloChromeDellAccountDelMotore` | contiene la sessione attiva dell'account Google dedicato: chi ha i file entra nell'account senza password | punto 2 |

## 1. Ambiente Python

Serve Python 3.14 installato sul server (la versione esatta è nella prima riga di `_09_ElencoDelleLibrerieDelMotore.txt`).
Da `_01_StrumentiDelMotore`:

```
py -3.14 -m venv _01_AmbientePythonDelMotore
_01_AmbientePythonDelMotore\Scripts\python.exe -m pip install -r _09_ElencoDelleLibrerieDelMotore.txt
```

Il motore usa il Chrome installato sul server (Google Chrome), non un browser di Playwright: non serve scaricarne altri.

## 2. Profilo Chrome dell'account dedicato

1. Il motore deve essere fermo (`_08_ComandiDelMotore\_01_ArrestoDelMotore.cmd`).
2. Michele apre `_08_ComandiDelMotore\_03_AperturaDelProfiloChromePerLAccessoDiMichele.bat`: si apre un Chrome nuovo con la cartella `_07_ProfiloChromeDellAccountDelMotore`.
3. Michele fa l'accesso all'account Google dedicato con le sue mani, poi chiude Chrome.
4. Il motore ritrova l'accesso alla prossima accensione e legge Google Maps senza la vista limitata.

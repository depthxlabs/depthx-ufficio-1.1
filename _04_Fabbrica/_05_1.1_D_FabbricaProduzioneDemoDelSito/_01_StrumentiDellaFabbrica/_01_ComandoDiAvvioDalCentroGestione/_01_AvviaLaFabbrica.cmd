@echo off
rem Avvio della fabbrica dei siti demo dal Centro Gestione: tutti i clienti scaricati, in ordine di foglio, saltando quelli gia in approvazione.
rem Ambiente Python della fabbrica, nessuna finestra; messaggi ed errori vanno nel registro del giorno (_04_RegistroLogDellaFabbrica).
rem Piu fabbriche insieme (task #582): si accende una fabbrica in piu solo se quelle accese sono meno di fabbricheInsieme
rem (_02_CoordinatoreDiLavoroDellaFabbrica\_03_RegoleDelCoordinatore.json). Il coordinatore lo controlla anche da solo.
rem Ogni fabbrica sono due processi (il lanciatore dell'ambiente e il Python vero): si conta solo il Python vero (11/11/2026).
set "FABBRICA=%~dp0..\.."
set "PYTHONIOENCODING=utf-8"
powershell -NoProfile -Command "$r = Get-Content -Raw -Encoding UTF8 '%FABBRICA%\_02_CoordinatoreDiLavoroDellaFabbrica\_03_RegoleDelCoordinatore.json' | ConvertFrom-Json; $n = [Math]::Max(1, [int]$r.fabbricheInsieme); if (@(Get-CimInstance Win32_Process | Where-Object { $_.Name -like 'python*' -and $_.CommandLine -like '*_01_CoordinatoreDellaFabbrica.py*' -and $_.ExecutablePath -notlike '*_03_AmbientePythonDellaFabbrica*' }).Count -ge $n) { exit 1 } else { exit 0 }"
if errorlevel 1 (
  "%FABBRICA%\_01_StrumentiDellaFabbrica\_03_AmbientePythonDellaFabbrica\Scripts\python.exe" -B -c "import sys; sys.path.insert(0, r'%FABBRICA%'); from _01_StrumentiDellaFabbrica._04_RegistroLogDellaFabbrica._00_RegistroDellaFabbrica import registraEvento; registraEvento('fabbrica', stato='già accese tutte le fabbriche delle regole: il comando di avvio non ne lancia un\'altra')"
  echo fabbriche gia accese tutte: nessuna accensione in piu
  exit /b 0
)
cd /d "%FABBRICA%\_02_CoordinatoreDiLavoroDellaFabbrica"
start "" /b "%FABBRICA%\_01_StrumentiDellaFabbrica\_03_AmbientePythonDellaFabbrica\Scripts\pythonw.exe" -B _01_CoordinatoreDellaFabbrica.py --blocchi %*
echo fabbrica accesa

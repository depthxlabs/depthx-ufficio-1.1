@echo off
chcp 65001 >nul
rem Ferma il motore: coordinatore, lavoratori e processi figli (Chrome, yt-dlp, ffmpeg, claude). Lo usa il pulsante "Ferma il motore" del Centro Gestione.
rem Scrive l'arresto nel registro. Alla prossima accensione il motore riprende da dove era.
powershell -NoProfile -ExecutionPolicy Bypass -Command "$p = @(Get-CimInstance Win32_Process | Where-Object { $_.Name -like 'python*.exe' -and $_.CommandLine -like '*_01_CoordinatoreELavoratoriDelMotore.py*' -and $_.CommandLine -notlike '*--fermato*' }); foreach ($x in $p) { taskkill /PID $x.ProcessId /T /F 2>$null | Out-Null }; Write-Host ('Processi del motore fermati: ' + $p.Count)"
"%~dp0..\_01_AmbientePythonDelMotore\Scripts\python.exe" -B "%~dp0..\_04_CoordinatoreDelMotore\_01_CoordinatoreELavoratoriDelMotore.py" --fermato
echo Motore fermo.

@echo off
rem Stop della fabbrica dal Centro Gestione: ferma solo i processi Python del coordinatore della fabbrica (il motore di download non si tocca).
powershell -NoProfile -Command "$p = @(Get-CimInstance Win32_Process | Where-Object { $_.Name -like 'python*' -and $_.CommandLine -like '*_01_CoordinatoreDellaFabbrica.py*' }); $p | ForEach-Object { Stop-Process -Id $_.ProcessId -Force }; Write-Output ('processi della fabbrica fermati: ' + $p.Count)"

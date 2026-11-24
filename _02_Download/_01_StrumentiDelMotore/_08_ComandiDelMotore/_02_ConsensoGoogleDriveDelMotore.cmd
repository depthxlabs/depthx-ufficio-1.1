@echo off
chcp 65001 >nul
rem Serve solo se Google chiede di rifare il consenso a Drive del motore (account depthxlabs@gmail.com).
rem 1. Il comando mostra un link: si apre sul Mac o sul telefono e si da' il consenso.
rem 2. Il browser finisce su una pagina 127.0.0.1 che non si apre: si copia tutto il link dalla barra e si incolla qui.
rem Il token si salva in _02_ChiaviDiAccessoAServiziDiTerzeParti\_06_TokenGoogleDrive.json. Code e token non si mostrano e non vanno nel registro.
"%~dp0..\_01_AmbientePythonDelMotore\Scripts\python.exe" -B "%~dp0..\_04_CoordinatoreDelMotore\_01_CoordinatoreELavoratoriDelMotore.py" --consenso
pause

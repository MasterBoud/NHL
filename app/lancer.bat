@echo off
title Scores NHL
rem Double-cliquer pour lancer l'app Scores NHL.
cd /d "%~dp0"

set "PY="
where py >nul 2>nul && set "PY=py"
if not defined PY where python >nul 2>nul && set "PY=python"
if not defined PY (
  echo Python est introuvable. Installez-le depuis https://www.python.org/downloads/
  echo en cochant "Add python.exe to PATH", puis relancez ce fichier.
  pause
  exit /b 1
)

echo Demarrage de Scores NHL sur http://127.0.0.1:8000
echo Fermez cette fenetre pour arreter l'app.
rem Ouvre le navigateur apres 2 secondes, le temps que le serveur demarre.
start "" /b cmd /c "timeout /t 2 /nobreak >nul & start http://127.0.0.1:8000"
%PY% -m nhl_score
pause

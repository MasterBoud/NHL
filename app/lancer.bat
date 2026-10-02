@echo off
title Scores NHL
rem Double-cliquer pour lancer l'app Scores NHL.
cd /d "%~dp0"
rem Si ce fichier a ete copie ailleurs (ex. sur le Bureau), retrouver le dossier de l'app.
if not exist "nhl_score\__main__.py" (
  for /d %%D in ("%USERPROFILE%\Desktop\nhl-app\*") do if exist "%%D\app\nhl_score\__main__.py" cd /d "%%D\app"
)
if not exist "nhl_score\__main__.py" (
  echo Dossier de l'app introuvable.
  echo Placez lancer.bat dans le dossier "app" qui contient "nhl_score",
  echo ou creez un raccourci vers lui au lieu de le copier.
  pause
  exit /b 1
)

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
%PY% -m nhl_score --open
pause

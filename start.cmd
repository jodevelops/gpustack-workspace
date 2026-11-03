@echo off
setlocal
cd /d "%~dp0"

if not exist "%~dp0desktop.pyw" (
    echo Paket unvollstaendig. Bitte das vollstaendige Repository-ZIP entpacken.
    pause
    exit /b 1
)

if exist "%~dp0.venv\Scripts\python.exe" (
    "%~dp0.venv\Scripts\python.exe" "%~dp0desktop.pyw" %*
    goto finished
)

where python >nul 2>&1
if not errorlevel 1 (
    python "%~dp0desktop.pyw" %*
    goto finished
)

where py >nul 2>&1
if not errorlevel 1 (
    py -3 "%~dp0desktop.pyw" %*
    goto finished
)

echo Python 3.11 oder neuer wurde nicht gefunden. Bitte die Einrichtung in README.md pruefen.
pause
exit /b 1

:finished
set "WORKROOM_EXIT_CODE=%ERRORLEVEL%"
if not "%WORKROOM_EXIT_CODE%"=="0" pause
exit /b %WORKROOM_EXIT_CODE%

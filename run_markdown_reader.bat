@echo off
REM Launcher for Markdown Reader.
REM Activates the local virtual environment (.venv) and starts the app.
REM Any arguments passed to this script (e.g. a .md file path) are forwarded to main.py.

setlocal

REM Resolve the directory this script lives in (project root).
set "APP_DIR=%~dp0"
set "APP_DIR=%APP_DIR:~0,-1%"

cd /d "%APP_DIR%"

REM Prefer pythonw.exe from the venv so no console window is shown.
set "VENV_PYW=%APP_DIR%\.venv\Scripts\pythonw.exe"
set "VENV_PY=%APP_DIR%\.venv\Scripts\python.exe"

if exist "%VENV_PYW%" (
    start "" "%VENV_PYW%" "%APP_DIR%\main.py" %*
    goto :eof
)

if exist "%VENV_PY%" (
    "%VENV_PY%" "%APP_DIR%\main.py" %*
    goto :eof
)

echo Virtual environment not found at "%APP_DIR%\.venv".
echo Please create it and install requirements first:
echo     python -m venv .venv
echo     .\.venv\Scripts\Activate.ps1
echo     pip install -r requirements.txt
pause
endlocal

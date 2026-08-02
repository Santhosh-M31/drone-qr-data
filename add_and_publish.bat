@echo off
setlocal

cd /d "%~dp0"

where python >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found in PATH.
    echo Please install Python 3 and make sure it is added to your PATH.
    pause
    exit /b 1
)

python "%~dp0add_and_publish.py"

endlocal

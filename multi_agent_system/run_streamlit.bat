@echo off
REM ============================================================================
REM Multi-Agent Orchestration Learning Lab - Windows Launcher
REM ============================================================================
REM This batch file launches the Streamlit educational UI.
REM
REM Usage: Double-click this file or run from command prompt
REM ============================================================================

echo.
echo ============================================================
echo   Multi-Agent Orchestration Learning Lab
echo ============================================================
echo.

REM Get the directory of this batch file
set SCRIPT_DIR=%~dp0
set VENV_DIR=%SCRIPT_DIR%..\venv

REM Check if virtual environment exists
if not exist "%VENV_DIR%\Scripts\python.exe" (
    echo ERROR: Virtual environment not found at %VENV_DIR%
    echo.
    echo Please create the virtual environment first:
    echo   cd %SCRIPT_DIR%..
    echo   python -m venv venv
    echo   venv\Scripts\pip.exe install -r multi_agent_system\requirements.txt
    echo.
    pause
    exit /b 1
)

REM Check if streamlit is installed
if not exist "%VENV_DIR%\Scripts\streamlit.exe" (
    echo Streamlit not found. Installing...
    "%VENV_DIR%\Scripts\pip.exe" install streamlit
)

echo Starting Streamlit server...
echo.
echo The app will open in your default browser.
echo Press Ctrl+C to stop the server.
echo.
echo ============================================================
echo.

REM Change to the multi_agent_system directory
cd /d "%SCRIPT_DIR%"

REM Run streamlit
"%VENV_DIR%\Scripts\streamlit.exe" run streamlit_app\app.py

pause

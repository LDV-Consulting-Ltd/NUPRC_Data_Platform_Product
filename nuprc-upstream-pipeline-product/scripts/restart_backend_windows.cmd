@echo off
REM Batch script to restart the FastAPI backend
echo Restarting FastAPI backend...

REM Navigate to project root
cd /d "%~dp0\.."

REM Kill any existing uvicorn processes
echo Stopping existing backend processes...
for /f "tokens=2" %%a in ('tasklist /FI "IMAGENAME eq python.exe" /FO LIST ^| findstr /I "PID"') do (
    wmic process where "ProcessId=%%a" get CommandLine 2>nul | findstr /I "uvicorn app.main" >nul
    if !errorlevel! equ 0 (
        taskkill /F /PID %%a >nul 2>&1
    )
)
timeout /t 2 /nobreak >nul
echo Stopped existing processes

REM Navigate to backend directory
cd backend

REM Activate virtual environment and start
if exist ".venv\Scripts\activate.bat" (
    call .venv\Scripts\activate.bat
) else (
    echo Creating virtual environment...
    python -m venv .venv
    call .venv\Scripts\activate.bat
    python -m pip install --upgrade pip
    pip install -r requirements.txt
)

REM Start the backend
echo Starting FastAPI backend on http://0.0.0.0:8000...
echo Press Ctrl+C to stop
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

pause

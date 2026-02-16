# PowerShell script to restart the FastAPI backend
Write-Host "Restarting FastAPI backend..." -ForegroundColor Cyan

# Navigate to project root
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Split-Path -Parent $scriptPath
Set-Location $projectRoot

# Kill any existing processes on ports 8000 and 8001
$ports = @(8000, 8001)
foreach ($portNum in $ports) {
    Write-Host "Checking port $portNum..." -ForegroundColor Yellow
    try {
        $portInfo = netstat -ano | findstr ":$portNum" | findstr LISTENING
        if ($portInfo) {
            $pid = ($portInfo -split '\s+')[-1]
            if ($pid) {
                Write-Host "Found process $pid on port $portNum, attempting to stop..." -ForegroundColor Yellow
                taskkill /F /PID $pid 2>&1 | Out-Null
                if ($LASTEXITCODE -eq 0) {
                    Write-Host "Stopped process $pid on port $portNum" -ForegroundColor Green
                    Start-Sleep -Seconds 1
                } else {
                    Write-Host "Could not stop process $pid. You may need to run as Administrator." -ForegroundColor Yellow
                }
            }
        }
    } catch {
        Write-Host "Error checking port $portNum : $_" -ForegroundColor Yellow
    }
}

# Also try to kill any Python processes that might be uvicorn
Write-Host "Checking for Python processes..." -ForegroundColor Yellow
$pythonProcs = Get-Process -Name "python" -ErrorAction SilentlyContinue | Where-Object {
    try {
        $cmdLine = (Get-CimInstance Win32_Process -Filter "ProcessId = $($_.Id)").CommandLine
        $cmdLine -like "*uvicorn*" -or $cmdLine -like "*app.main*"
    } catch {
        $false
    }
}
if ($pythonProcs) {
    $pythonProcs | ForEach-Object {
        Write-Host "Stopping Python process $($_.Id)..." -ForegroundColor Yellow
        Stop-Process -Id $_.Id -Force -ErrorAction SilentlyContinue
    }
    Start-Sleep -Seconds 2
}

# Navigate to backend directory
Set-Location "$projectRoot\backend"

# Activate virtual environment
if (Test-Path ".\.venv") {
    & .\.venv\Scripts\Activate.ps1
} else {
    Write-Host "Creating virtual environment..." -ForegroundColor Yellow
    python -m venv .venv
    & .\.venv\Scripts\Activate.ps1
    python -m pip install --upgrade pip
    pip install -r requirements.txt
}

# Start the backend
Write-Host "Starting FastAPI backend on http://0.0.0.0:8001..." -ForegroundColor Green
Write-Host "Press Ctrl+C to stop" -ForegroundColor Gray
python -m uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload

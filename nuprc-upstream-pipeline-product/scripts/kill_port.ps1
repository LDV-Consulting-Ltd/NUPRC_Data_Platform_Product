# PowerShell script to kill process on a specific port
param(
    [Parameter(Mandatory=$true)]
    [int]$Port
)

Write-Host "Finding process on port $Port..." -ForegroundColor Cyan

$portInfo = netstat -ano | findstr ":$Port" | findstr LISTENING
if ($portInfo) {
    $pid = ($portInfo -split '\s+')[-1]
    if ($pid) {
        Write-Host "Found process $pid on port $Port" -ForegroundColor Yellow
        Write-Host "Attempting to stop process..." -ForegroundColor Yellow
        
        try {
            taskkill /F /PID $pid 2>&1 | Out-Null
            if ($LASTEXITCODE -eq 0) {
                Write-Host "Successfully stopped process $pid" -ForegroundColor Green
                Start-Sleep -Seconds 1
            } else {
                Write-Host "Failed to stop process. You may need to run PowerShell as Administrator." -ForegroundColor Red
                Write-Host "Or manually stop it from Task Manager (Process ID: $pid)" -ForegroundColor Yellow
                exit 1
            }
        } catch {
            Write-Host "Error stopping process: $_" -ForegroundColor Red
            exit 1
        }
    }
} else {
    Write-Host "No process found listening on port $Port" -ForegroundColor Green
}

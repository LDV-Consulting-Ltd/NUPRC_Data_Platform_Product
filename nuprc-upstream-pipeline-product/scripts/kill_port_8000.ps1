# Quick script to kill process on port 8000
Write-Host "Finding process on port 8000..." -ForegroundColor Cyan

$port = netstat -ano | findstr :8000 | findstr LISTENING
if ($port) {
    $processId = ($port -split '\s+')[-1]
    if ($processId) {
        Write-Host "Found process $processId on port 8000" -ForegroundColor Yellow
        Write-Host "Attempting to stop process..." -ForegroundColor Yellow
        taskkill /F /PID $processId
        if ($LASTEXITCODE -eq 0) {
            Write-Host "Successfully stopped process $processId" -ForegroundColor Green
        } else {
            Write-Host "Failed to stop process. You may need to run PowerShell as Administrator." -ForegroundColor Red
            Write-Host "Or manually stop it from Task Manager (Process ID: $processId)" -ForegroundColor Yellow
        }
    }
} else {
    Write-Host "No process found listening on port 8000" -ForegroundColor Green
}

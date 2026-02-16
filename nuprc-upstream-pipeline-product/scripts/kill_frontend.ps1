# PowerShell script to kill Next.js frontend process
Write-Host "Finding Next.js process on port 3000..." -ForegroundColor Cyan

$portInfo = netstat -ano | findstr ":3000" | findstr LISTENING
if ($portInfo) {
    $pid = ($portInfo -split '\s+')[-1]
    if ($pid) {
        Write-Host "Found process $pid on port 3000" -ForegroundColor Yellow
        Write-Host "Attempting to stop process..." -ForegroundColor Yellow
        
        try {
            taskkill /F /PID $pid 2>&1 | Out-Null
            if ($LASTEXITCODE -eq 0) {
                Write-Host "Successfully stopped process $pid" -ForegroundColor Green
                Start-Sleep -Seconds 2
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
    Write-Host "No process found listening on port 3000" -ForegroundColor Green
}

# Also try to kill any node processes that might be Next.js
Write-Host "Checking for Node.js processes..." -ForegroundColor Yellow
$nodeProcs = Get-Process -Name "node" -ErrorAction SilentlyContinue
if ($nodeProcs) {
    Write-Host "Found $($nodeProcs.Count) Node.js process(es)" -ForegroundColor Yellow
    $nodeProcs | ForEach-Object {
        try {
            $cmdLine = (Get-CimInstance Win32_Process -Filter "ProcessId = $($_.Id)").CommandLine
            if ($cmdLine -like "*next*" -or $cmdLine -like "*npm*") {
                Write-Host "Stopping Node process $($_.Id)..." -ForegroundColor Yellow
                Stop-Process -Id $_.Id -Force -ErrorAction SilentlyContinue
            }
        } catch {
            # Ignore errors
        }
    }
    Start-Sleep -Seconds 2
}

Write-Host "Done! You can now start the frontend with: npm run dev" -ForegroundColor Green

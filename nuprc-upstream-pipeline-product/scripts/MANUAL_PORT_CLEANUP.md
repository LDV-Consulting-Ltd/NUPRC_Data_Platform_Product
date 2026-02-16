# Manual Port Cleanup Instructions

If you're getting "port already in use" errors, here's how to manually clean up:

## Option 1: Use Task Manager (Easiest)

1. Press `Ctrl + Shift + Esc` to open Task Manager
2. Go to the **Details** tab
3. Find processes with these PIDs (from the error or netstat):
   - PID 38784 (port 8001)
   - PID 46036 (port 8000)
4. Right-click on the process → **End Task**

## Option 2: Use PowerShell as Administrator

1. Right-click on PowerShell → **Run as Administrator**
2. Run these commands:

```powershell
# Kill process on port 8001
taskkill /F /PID 38784

# Kill process on port 8000
taskkill /F /PID 46036

# Or find and kill all processes on these ports:
netstat -ano | findstr :8001
netstat -ano | findstr :8000
# Then use taskkill /F /PID <PID> for each process found
```

## Option 3: Use the Kill Port Script

From project root:
```powershell
.\scripts\kill_port.ps1 -Port 8001
.\scripts\kill_port.ps1 -Port 8000
```

## Option 4: Find All Python/Uvicorn Processes

```powershell
# Find all Python processes
Get-Process python | Select-Object Id, ProcessName

# Kill a specific one
Stop-Process -Id <PID> -Force
```

## After Cleaning Up

Once you've killed the processes, restart the backend:
```powershell
cd backend
.venv\Scripts\Activate.ps1
python -m uvicorn app.main:app --host 0.0.0.0 --port 8001
```

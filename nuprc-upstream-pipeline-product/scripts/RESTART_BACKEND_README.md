# Backend Restart Scripts

## Quick Restart

### Windows (PowerShell) - Recommended
```powershell
.\scripts\restart_backend_windows.ps1
```

### Windows (Command Prompt)
```cmd
.\scripts\restart_backend_windows.cmd
```

### Linux/Mac
```bash
chmod +x scripts/restart_backend.sh
./scripts/restart_backend.sh
```

## What the Scripts Do

1. **Stop existing backend processes** - Kills any running uvicorn/python processes
2. **Navigate to backend directory** - Changes to the `backend` folder
3. **Activate virtual environment** - Creates `.venv` if it doesn't exist
4. **Start FastAPI backend** - Runs `uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload`

## Manual Restart

If you prefer to restart manually:

### Windows PowerShell
```powershell
cd backend
# Kill existing process (if running)
Get-Process python | Where-Object {$_.CommandLine -like "*uvicorn*"} | Stop-Process -Force
# Start backend
.\.venv\Scripts\Activate.ps1
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Windows CMD
```cmd
cd backend
taskkill /F /IM python.exe /FI "WINDOWTITLE eq uvicorn*"
.venv\Scripts\activate.bat
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Linux/Mac
```bash
cd backend
pkill -f "uvicorn app.main:app"
source .venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

## Backend URL

After restarting, the backend will be available at:
- **Local**: http://localhost:8000
- **Network**: http://0.0.0.0:8000
- **API Docs**: http://localhost:8000/docs

## Troubleshooting

### Port Already in Use
If port 8000 is already in use:
```powershell
# Find process using port 8000
netstat -ano | findstr :8000
# Kill the process (replace PID with actual process ID)
taskkill /F /PID <PID>
```

### Virtual Environment Issues
If the virtual environment is corrupted:
```powershell
cd backend
Remove-Item -Recurse -Force .venv
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

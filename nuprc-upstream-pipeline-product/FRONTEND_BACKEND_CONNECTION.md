# Frontend-Backend Connection Guide

## Current Configuration

- **Frontend Port**: 3000 (Next.js default)
- **Backend Port**: 8000
- **Connection Method**: Next.js rewrites (server-side proxy)

## How It Works

1. Frontend makes requests to `/api/backend/*`
2. Next.js rewrites these to `http://127.0.0.1:8000/*`
3. Backend responds through the proxy

## Troubleshooting Steps

### Step 1: Verify Backend is Running

Open in browser:
- `http://localhost:8000/health/summary`
- Should return: `{"ok": true, "status": "green"}`

If this fails, your backend isn't running. Start it:
```powershell
cd backend
.venv\Scripts\Activate.ps1
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Step 2: Verify Frontend is Running

Open in browser:
- `http://localhost:3000`
- Should show the NUPRC platform interface

If this fails, start it:
```powershell
cd frontend
npm run dev
```

### Step 3: Test Connection

Visit the test page:
- `http://localhost:3000/test-connection`
- Click "Test Connection" button
- This will test:
  1. Direct backend connection
  2. Through Next.js rewrite
  3. Pipeline endpoints

### Step 4: Check Browser Console

1. Open browser DevTools (F12)
2. Go to "Network" tab
3. Try clicking a button
4. Look for failed requests
5. Check the error message

### Step 5: Check Backend Logs

When you click a button, watch the backend terminal:
- You should see the request come in
- Check for any error messages
- Look for the full traceback

## Common Issues

### Issue: "Backend POST failed: 500 Internal Server Error"

**Causes:**
1. Backend code has errors (check backend logs)
2. Database connection issues
3. Missing dependencies

**Fix:**
- Check backend terminal for error messages
- Restart backend after code changes
- Verify database is running

### Issue: "Network Error" or "Failed to fetch"

**Causes:**
1. Backend not running
2. Wrong port (frontend looking for 8000, backend on 8000)
3. CORS issues (should be fixed now)

**Fix:**
- Verify backend is running on port 8000
- Restart frontend after config changes
- Check `next.config.js` has correct port

### Issue: Frontend shows old data

**Causes:**
1. Next.js cache
2. Browser cache

**Fix:**
- Restart Next.js dev server
- Hard refresh browser (Ctrl+Shift+R)
- Clear browser cache

## Quick Fixes

### Restart Everything

```powershell
# Terminal 1: Backend
cd backend
.venv\Scripts\Activate.ps1
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Terminal 2: Frontend
cd frontend
npm run dev
```

### Verify Ports

```powershell
# Check what's using port 8000
netstat -ano | findstr :8000

# Check what's using port 3000
netstat -ano | findstr :3000
```

### Test Direct Connection

```powershell
# Test backend directly
curl http://localhost:8000/health/summary

# Test through Next.js (if frontend is running)
curl http://localhost:3000/api/backend/health/summary
```

## Environment Variables

You can override the backend URL with an environment variable:

Create `frontend/.env.local`:
```
BACKEND_URL=http://127.0.0.1:8000
```

Then restart the frontend.

# Test Backend Connection

## If you see NOTHING in backend terminal:

The endpoint might not be getting called. Let's test step by step:

### Step 1: Test if Backend is Running

Open in browser:
```
http://localhost:8001/health/summary
```

Should return: `{"ok": true, "status": "green"}`

### Step 2: Test Pipeline Endpoint Directly

**Option A: Use the test script**
```powershell
cd backend
python test_endpoint.py
```

**Option B: Use curl**
```powershell
curl -X POST "http://localhost:8001/pipeline/run?source_ids=oil_production_status"
```

**Option C: Use browser/Postman**
- Method: POST
- URL: `http://localhost:8001/pipeline/run?source_ids=oil_production_status`
- Should see response with run_id

### Step 3: Check Browser Network Tab

1. Open browser DevTools (F12)
2. Go to Network tab
3. Click "Run Oil Production" button
4. Look for request to `/api/backend/pipeline/run`
5. Check:
   - Status code (should be 200)
   - Request URL (should include source_ids)
   - Response body

### Step 4: Check Frontend Console

Open browser console (F12 → Console tab):
- Look for any errors
- Look for the request being made

### Step 5: Verify Next.js Rewrite

The frontend uses `/api/backend/*` which Next.js rewrites to `http://127.0.0.1:8001/*`

Test the rewrite:
```
http://localhost:3000/api/backend/health/summary
```

Should return the same as `http://localhost:8001/health/summary`

## Most Likely Issues:

1. **Frontend not connecting** - Check browser console for errors
2. **Next.js rewrite not working** - Restart frontend
3. **Backend not running** - Check if it's actually running on port 8001
4. **CORS blocking** - Should be fixed now, but check browser console

## Quick Test:

Run this in a new terminal while backend is running:
```powershell
python backend/test_endpoint.py
```

This will show if the endpoint works when called directly.

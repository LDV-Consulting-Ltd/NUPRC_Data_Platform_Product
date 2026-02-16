# Backend restart (Windows)

## If uvicorn crashes with `watchfiles` / `RustNotify` / `PanicException`

The file watcher used by `--reload` can crash on Windows (e.g. long or OneDrive paths). Use either:

- **Run without reload** (no auto-restart on code changes):
  ```powershell
  python -m uvicorn app.main:app --port 8001
  ```
- **Or force polling so reload still works:**
  ```powershell
  $env:WATCHFILES_FORCE_POLLING = "1"
  python -m uvicorn app.main:app --reload --port 8001
  ```

---

## From `nuprc-upstream-pipeline-product` (repo root)

You are already in the repo root. Do **not** `cd nuprc-upstream-pipeline-product` again.

1. **Go into backend and use its venv:**
   ```powershell
   cd backend
   .\.venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   python -m uvicorn app.main:app --port 8001
   ```
   If the watcher has been fixed or you set `WATCHFILES_FORCE_POLLING=1`, you can add `--reload`.

2. **Or use your existing venv (e.g. Product-level `.venv`):**
   ```powershell
   cd backend
   pip install -r requirements.txt
   python -m uvicorn app.main:app --port 8001
   ```
   Make sure the venv is activated first (`& "path/to/.venv/Scripts/Activate.ps1"`).

## From `NUPRC data platform Product` (parent of repo)

```powershell
cd "nuprc-upstream-pipeline-product\backend"
pip install -r requirements.txt
python -m uvicorn app.main:app --port 8001
```

Use the same Python/venv that has `uvicorn` and the backend dependencies installed.

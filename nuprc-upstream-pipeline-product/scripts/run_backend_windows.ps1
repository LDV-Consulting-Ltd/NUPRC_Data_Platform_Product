cd $PSScriptRoot\..
cd .\backend

if (!(Test-Path .\.venv)) { python -m venv .venv }
.\.venv\Scripts\Activate.ps1

python -m pip install --upgrade pip
pip install -r requirements.txt

python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

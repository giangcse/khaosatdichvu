@echo off
setlocal

REM Configure environment
set FLASK_CONFIG=ProductionConfig
set HOST=0.0.0.0
set PORT=8000
set THREADS=8
set CONN_LIMIT=200

REM Create venv if not exists (optional)
if not exist .venv (
  python -m venv .venv
)

call .venv\Scripts\activate.bat
python -m pip install --upgrade pip >NUL 2>&1
pip install -r requirements.txt

echo Starting production server on %HOST%:%PORT% ...
python run_waitress.py

endlocal


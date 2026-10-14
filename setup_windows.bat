@echo off
setlocal EnableExtensions
cd /d "%~dp0"
title ResumeMatch setup
echo.
echo ================================================
echo   ResumeMatch - one-time setup (Windows)
echo ================================================
echo.

rem ---- 1. Python 3.10 - 3.13 (3.14 is too new for some packages) ----
set "PY="
for %%V in (3.12 3.11 3.13 3.10) do (
  if not defined PY (
    py -%%V -c "import sys" >nul 2>&1 && set "PY=py -%%V"
  )
)
if not defined PY (
  python -c "import sys; raise SystemExit(0 if (3,10) <= sys.version_info[:2] <= (3,13) else 1)" >nul 2>&1 && set "PY=python"
)
if not defined PY (
  echo [!] Python 3.10 - 3.13 was not found.
  echo     Install it, then run this file again:
  echo        winget install -e --id Python.Python.3.12
  pause
  exit /b 1
)
echo [ok] Python: %PY%

rem ---- 2. Node.js 18+ ----
where node >nul 2>&1
if errorlevel 1 (
  echo [!] Node.js was not found. Install it, then run this file again:
  echo        winget install -e --id OpenJS.NodeJS.LTS
  pause
  exit /b 1
)
for /f "delims=" %%N in ('node -v') do echo [ok] Node.js %%N

rem ---- 3. Backend: virtual environment + packages ----
cd resume_scorer
if not exist .venv (
  echo Creating virtual environment...
  %PY% -m venv .venv || (echo [!] Could not create venv & pause & exit /b 1)
)
call .venv\Scripts\activate.bat
python -m pip install --upgrade pip
echo Installing CPU-only PyTorch (smaller download)...
python -m pip install torch --index-url https://download.pytorch.org/whl/cpu || (echo [!] torch install failed & pause & exit /b 1)
echo Installing backend packages...
python -m pip install -r requirements.txt -r requirements-dev.txt || (echo [!] pip install failed & pause & exit /b 1)
if not exist .env copy .env.example .env >nul

echo Downloading the two local AI models (one time, about 220 MB)...
python -c "from sentence_transformers import SentenceTransformer as S; S('all-MiniLM-L6-v2'); S('BAAI/bge-small-en-v1.5'); print('models ready')" && (echo ok> .models_ready)

echo Running the test suite...
python -m pytest -q
call deactivate
cd ..

rem ---- 4. Frontend ----
cd frontend
if not exist .env.local (> .env.local echo NEXT_PUBLIC_API_URL=http://localhost:8000)
call npm install || (echo [!] npm install failed & pause & exit /b 1)
call npm run build || (echo [!] frontend build failed & pause & exit /b 1)
cd ..

echo.
echo ================================================
echo   Setup complete. Double-click start_windows.bat
echo ================================================
pause

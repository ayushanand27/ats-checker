@echo off
setlocal EnableExtensions
cd /d "%~dp0"
if not exist resume_scorer\.venv (
  echo Run setup_windows.bat first.
  pause
  exit /b 1
)
if not exist frontend\.next\BUILD_ID (
  echo Building the frontend once...
  pushd frontend & call npm run build & popd
)

rem Work offline once the models are cached, so the demo never waits on the network
if exist resume_scorer\.models_ready set "HF_HUB_OFFLINE=1"

start "ResumeMatch API (port 8000)" cmd /k "cd /d %~dp0resume_scorer && call .venv\Scripts\activate.bat && python -m uvicorn api.main:app --port 8000"
start "ResumeMatch Web (port 3000)" cmd /k "cd /d %~dp0frontend && npm run start"

echo Waiting for the servers to start...
set /a TRIES=0
:wait
timeout /t 2 >nul
set /a TRIES+=1
curl.exe -s http://localhost:8000/api/health >nul 2>&1 && goto ready
if %TRIES% lss 40 goto wait
echo [!] API did not start - check the "ResumeMatch API" window for errors.
pause
exit /b 1

:ready
echo Warming up the AI models (first analysis loads them)...
curl.exe -s -o nul -X POST http://localhost:8000/api/analyze -F "resume=@demo\resume_strong_riya.pdf" -F "jd_text=<demo\jd_data_analyst.txt"
start "" http://localhost:3000/analyze
echo.
echo ResumeMatch is running:  http://localhost:3000/analyze
echo API docs:                http://localhost:8000/docs
echo Demo files:              %~dp0demo
echo Close the two server windows to stop.

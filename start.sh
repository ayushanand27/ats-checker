#!/usr/bin/env bash
# Start API (port 8000) and web app (port 3000). Ctrl+C stops both.
set -euo pipefail
cd "$(dirname "$0")"
[ -f resume_scorer/.models_ready ] && export HF_HUB_OFFLINE=1
(cd resume_scorer && source .venv/bin/activate && python -m uvicorn api.main:app --port 8000) &
API=$!
(cd frontend && npm run start) &
WEB=$!
trap 'kill $API $WEB 2>/dev/null' EXIT
until curl -s localhost:8000/api/health >/dev/null; do sleep 2; done
curl -s -o /dev/null -X POST localhost:8000/api/analyze -F "resume=@demo/resume_strong_riya.pdf" -F "jd_text=<demo/jd_data_analyst.txt"
echo "ResumeMatch is running: http://localhost:3000/analyze"
wait

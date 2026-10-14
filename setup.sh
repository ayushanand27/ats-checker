#!/usr/bin/env bash
# One-time setup for macOS / Linux
set -euo pipefail
cd "$(dirname "$0")"
PY=$(command -v python3.12 || command -v python3.11 || command -v python3.13 || command -v python3)
echo "Using $($PY --version)"
cd resume_scorer
[ -d .venv ] || "$PY" -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install torch --index-url https://download.pytorch.org/whl/cpu
pip install -r requirements.txt -r requirements-dev.txt
[ -f .env ] || cp .env.example .env
python -c "from sentence_transformers import SentenceTransformer as S; S('all-MiniLM-L6-v2'); S('BAAI/bge-small-en-v1.5'); print('models ready')" && echo ok > .models_ready
python -m pytest -q
deactivate
cd ../frontend
[ -f .env.local ] || echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > .env.local
npm install
npm run build
echo "Setup complete. Run ./start.sh"

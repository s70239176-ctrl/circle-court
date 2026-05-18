#!/usr/bin/env bash
set -euo pipefail

ROOT="$(pwd)"

echo "Setting up Circle Court Codespace at $ROOT"

if [[ ! -f .env && -f .env.example ]]; then
  cp .env.example .env
fi

if [[ ! -f backend/.env ]]; then
  cat > backend/.env <<'ENV'
API_KEY=dev-circle-court-key
DATABASE_URL=postgresql+asyncpg://circle:circle@postgres:5432/circlecourt
REDIS_URL=redis://redis:6379/0
CORS_ORIGINS=["http://localhost:5173","http://localhost:8000"]
LLM_MODEL_LEADER=gpt-4o
LLM_VALIDATOR_MODELS=gpt-4o-mini,claude-3-5-sonnet-20241022,groq/llama-3.1-70b-versatile
EMBEDDINGS_PROVIDER=hash
CIRCLE_SIMULATION_MODE=true
WEB3_SIMULATION_MODE=true
CHAIN_ID=11155111
ENV
fi

python -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -r backend/requirements.txt
.venv/bin/python -m compileall backend/app

cd frontend
npm install --no-audit --no-fund
npm run build
cd "$ROOT"

echo ""
echo "Codespace ready."
echo "Backend:  cd backend && ../.venv/bin/python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"
echo "Frontend: cd frontend && npm run dev -- --host 0.0.0.0"

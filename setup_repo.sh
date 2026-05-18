#!/usr/bin/env bash
set -euo pipefail

SKIP_FRONTEND=0
SKIP_BACKEND=0
SEED=0
DOCKER=0

for arg in "$@"; do
  case "$arg" in
    --skip-frontend) SKIP_FRONTEND=1 ;;
    --skip-backend) SKIP_BACKEND=1 ;;
    --seed) SEED=1 ;;
    --docker) DOCKER=1 ;;
    *) echo "Unknown option: $arg" >&2; exit 1 ;;
  esac
done

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"

step() {
  printf '\n==> %s\n' "$1"
}

echo "Circle Court repo setup"
echo "Root: $ROOT"

if [[ ! -f .env && -f .env.example ]]; then
  step "Creating .env from .env.example"
  cp .env.example .env
fi

if [[ ! -f backend/.env && -f .env ]]; then
  step "Creating backend/.env from root .env"
  cp .env backend/.env
fi

if [[ "$DOCKER" -eq 1 ]]; then
  step "Starting Docker Compose stack"
  docker compose up --build
  exit $?
fi

if [[ "$SKIP_BACKEND" -eq 0 ]]; then
  step "Setting up Python backend"
  python -m venv .venv
  .venv/bin/python -m pip install --upgrade pip
  .venv/bin/python -m pip install -r backend/requirements.txt
  .venv/bin/python -m compileall backend/app

  if [[ "$SEED" -eq 1 ]]; then
    step "Seeding example contracts and disputes"
    (cd backend && ../.venv/bin/python -m app.seed.seed)
  fi
fi

if [[ "$SKIP_FRONTEND" -eq 0 ]]; then
  step "Setting up React frontend"
  (cd frontend && npm install --no-audit --no-fund && npm run build)
fi

step "Setup complete"
echo "Backend dev server:"
echo "  .venv/bin/python -m uvicorn app.main:app --reload --app-dir backend"
echo "Frontend dev server:"
echo "  cd frontend && npm run dev"
echo "Docker stack:"
echo "  ./setup_repo.sh --docker"

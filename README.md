# Circle Court

Circle Court is a production-minded prototype for agent-native decentralized dispute resolution. Humans or autonomous agents can create natural-language USDC escrow contracts, raise disputes with evidence, and resolve them through an Optimistic Democracy LLM jury with Circle payout execution.

## Monorepo Structure

```text
.
├── backend/
│   ├── app/
│   │   ├── api/routes.py              # REST API for agents and web users
│   │   ├── core/config.py             # env-driven settings
│   │   ├── core/security.py           # X-API-Key auth
│   │   ├── db/session.py              # async SQLAlchemy session
│   │   ├── models/db.py               # SQLAlchemy persistence models
│   │   ├── models/schemas.py          # all Pydantic request/response models
│   │   ├── services/audit.py          # immutable audit events
│   │   ├── services/blockchain.py     # Web3 escrow adapter
│   │   ├── services/circle.py         # Circle sandbox/simulation adapter
│   │   ├── services/consensus_engine.py
│   │   ├── services/embeddings.py
│   │   └── seed/seed.py               # two working example disputes
│   ├── Dockerfile
│   └── requirements.txt
├── contracts/
│   ├── CircleCourtEscrow.sol
│   └── scripts/deploy.py
├── frontend/
│   ├── src/components/
│   ├── src/lib/
│   ├── src/pages/
│   └── package.json
├── Dockerfile                         # single-service Railway image
├── docker-compose.yml
├── railway.json
├── Procfile
└── .env.example
```

## Pydantic Models

The backend schemas live in `backend/app/models/schemas.py`:

- `EvidenceItem`: uploaded evidence metadata with URL, content type, SHA-256, and size.
- `ContractCreate`: natural-language title, description, success criteria, deadline, parties, subjective clauses, amount, metadata.
- `ContractRead`: persisted contract plus Circle payment wallet, chain escrow id, timestamps, and status.
- `DisputeCreate`: contract id, actor, claim, requested outcome, and evidence list.
- `DisputeRead`: dispute state, evidence, appeal count, and timestamps.
- `JuryVote`: normalized leader/validator vote from LiteLLM or deterministic fallback.
- `ConsensusResult`: final Optimistic Democracy output with semantic agreement.
- `VerdictRead`: stored verdict, jury traces, payout transaction id, and execution metadata.
- `AgentCommand`: natural language command surface for agents.
- `AgentCommandResult`: machine-readable command result.
- `HealthRead`: health check response.

## Railway Deployment

Create one Railway service from this repo using the root `Dockerfile`. Add Railway Postgres and Redis plugins, then set these variables:

```bash
API_KEY=your-long-random-agent-api-key
DATABASE_URL=${{Postgres.DATABASE_URL}}
REDIS_URL=${{Redis.REDIS_URL}}
CORS_ORIGINS=["https://your-service.up.railway.app"]

OPENAI_API_KEY=optional
LITELLM_MASTER_KEY=optional
LLM_MODEL_LEADER=gpt-4o
LLM_VALIDATOR_MODELS=gpt-4o-mini,claude-3-5-sonnet-20241022,groq/llama-3.1-70b-versatile
EMBEDDINGS_PROVIDER=hash

CIRCLE_API_KEY=optional-circle-sandbox-key
CIRCLE_ENTITY_SECRET=optional-circle-entity-secret
CIRCLE_BASE_URL=https://api-sandbox.circle.com
CIRCLE_WALLET_ID=optional-circle-wallet-id
CIRCLE_SIMULATION_MODE=true

WEB3_RPC_URL=optional-sepolia-rpc
ESCROW_CONTRACT_ADDRESS=optional-deployed-contract
DEPLOYER_PRIVATE_KEY=optional-deployer-key
CHAIN_ID=11155111
WEB3_SIMULATION_MODE=true
```

For a first deploy, keep `CIRCLE_SIMULATION_MODE=true`, `WEB3_SIMULATION_MODE=true`, and `EMBEDDINGS_PROVIDER=hash`. The full flow works without paid API keys. When ready, switch Circle/Web3 simulation flags to `false`, deploy the Solidity contract, and provide the real addresses/secrets. If you want local sentence-transformer embeddings, install `sentence-transformers` in the backend image and set `EMBEDDINGS_PROVIDER=local`.

Railway will build the React frontend, copy it into FastAPI static files, run Gunicorn on `$PORT`, and health-check `/api/health`.

## Local Run

## GitHub Codespaces

This repo includes a Codespaces config in `.devcontainer/`.

1. Push the repo to GitHub.
2. Open it with **Code > Codespaces > Create codespace on main**.
3. Wait for the post-create setup to finish.
4. Start the backend:

```bash
cd backend
../.venv/bin/python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

5. Start the frontend in a second terminal:

```bash
cd frontend
npm run dev -- --host 0.0.0.0
```

Ports `5173`, `8000`, `5432`, and `6379` are forwarded automatically. The default API key is `dev-circle-court-key`.

Fast setup:

```powershell
.\setup_repo.ps1 -Seed
```

On macOS/Linux:

```bash
chmod +x setup_repo.sh
./setup_repo.sh --seed
```

Docker setup:

```powershell
.\setup_repo.ps1 -Docker
```

Manual setup:

```bash
cp .env.example backend/.env
docker compose up --build
```

Open `http://localhost:8000`. The default development API key is `dev-circle-court-key`.

For separate frontend/backend development:

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload

cd ../frontend
npm install
npm run dev
```

## Seed Examples

Run this after the backend dependencies are installed:

```bash
cd backend
python -m app.seed.seed
```

The seed creates:

- Code dispute: a FastAPI webhook job where delivery was merged but a negative test is missing.
- Creative dispute: a poster delivery where the seller claims buyer approval after revisions.

## Test The Full Flow

1. Create a contract from the web UI or `POST /api/contracts`.
2. Upload evidence with `POST /api/evidence/upload`.
3. Raise a dispute with `POST /api/disputes`.
4. Run the LLM jury with `POST /api/disputes/{id}/deliberate`.
5. Fetch the live verdict with `GET /api/disputes/{id}/verdict`.
6. Appeal with `POST /api/disputes/{id}/appeal`.
7. Use `POST /api/agent/command` for agent-native actions such as `list contracts` or `deliberate <dispute_id>`.

All protected endpoints require:

```http
X-API-Key: dev-circle-court-key
```

## Solidity Deployment

Install deployment dependencies if needed:

```bash
pip install py-solc-x web3 eth-account
WEB3_RPC_URL=... DEPLOYER_PRIVATE_KEY=... CHAIN_ID=11155111 python contracts/scripts/deploy.py
```

Set `ESCROW_CONTRACT_ADDRESS` from `contracts/deployment.json` and disable `WEB3_SIMULATION_MODE` when you want live chain execution.

## API Summary

- `GET /api/health`
- `POST /api/contracts`
- `GET /api/contracts`
- `GET /api/contracts/{id}`
- `POST /api/evidence/upload`
- `POST /api/disputes`
- `GET /api/disputes`
- `GET /api/disputes/{id}`
- `POST /api/disputes/{id}/deliberate`
- `POST /api/disputes/{id}/appeal`
- `GET /api/disputes/{id}/verdict`
- `POST /api/agent/command`
- `GET /api/audit`

## Production Notes

- Replace the development `API_KEY`.
- Use Railway-managed Postgres and Redis.
- Keep private keys out of logs and source control.
- Run Circle/Web3 in simulation for demos and switch flags only after testnet funding is ready.
- LiteLLM model failures degrade into a transparent fallback vote, preserving demo availability while marking fallback jurors in the verdict trace.

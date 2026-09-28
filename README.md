# BioVerse AI

BioVerse AI is a visual-first biology exploration platform built around source-grounded scientific data. This repository is currently at **Milestone 1**: the application scaffold only. Search, scientific adapters, AI explanations, and visual explorers are intentionally not implemented yet.

## Prerequisites

- Docker with Docker Compose, or
- Python 3.12+, Node.js 20+, npm, and a PostgreSQL 16+ server

## Start the complete stack

No environment file is required for local defaults. To customize ports or credentials, copy `.env.example` to `.env` and edit only local values.

```powershell
docker compose up --build
```

Then open:

- Frontend: <http://localhost:3000>
- Backend readiness: <http://localhost:8000/health>

Stop the stack while retaining the local database volume:

```powershell
docker compose down
```

## Split local development

Start PostgreSQL:

```powershell
docker compose up -d database
```

In one terminal, start the backend:

```powershell
Set-Location backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
$env:DATABASE_URL = "postgresql+psycopg://bioverse:bioverse_dev@localhost:5433/bioverse"
python -m uvicorn app.main:app --reload
```

In a second terminal, start the frontend:

```powershell
Set-Location frontend
npm install
npm run dev
```

## Validation

Backend:

```powershell
Set-Location backend
python -m ruff check .
python -m mypy app tests
python -m pytest
```

Frontend:

```powershell
Set-Location frontend
npm run lint
npm run typecheck
npm test -- --run
npm run build
```

Container configuration and smoke test:

```powershell
docker compose config
docker compose build
docker compose up -d --wait
Invoke-RestMethod http://localhost:8000/health
Invoke-WebRequest http://localhost:3000
docker compose down
```

## Safety boundary

BioVerse is an educational and research exploration tool, not a diagnostic or treatment system. Future biological facts must come from the approved structured sources defined in `AGENTS.md` and `BIOVERSE_MASTER_SPEC.md`; the application must never fill missing biology from model memory.

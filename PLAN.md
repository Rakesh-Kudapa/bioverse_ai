# BioVerse AI - Implementation Plan

## Current Milestone
**Milestone 1 - Repository scaffold**

## Scope
Create the local development and validation foundation only:

- a strict TypeScript Next.js frontend with a premium dark landing page and inert search shell;
- a typed FastAPI backend with a PostgreSQL-backed readiness endpoint;
- PostgreSQL, backend, and frontend services orchestrated by Docker Compose;
- reproducible environment templates, local startup documentation, tests, linting, and type checks;
- baseline architecture and decision records limited to choices already frozen by the master specification.

Out of scope: scientific source adapters, normalized biological records, search behavior, AI, 2D/3D viewers, relationship graphs, demo fixtures, and domain claims.

## Workspace Inspection

- The initial workspace contains only `AGENTS.md`, `BIOVERSE_MASTER_SPEC.md`, and `PLAN.md`.
- No implementation files conflict with the target structure.
- The workspace is not currently a Git repository.
- Available tools: Python 3.12, Node.js 24/npm 11, and Docker Compose v5.

## Files Expected to Change

- Root: `PLAN.md`, `README.md`, `.env.example`, `.gitignore`, `docker-compose.yml`
- Backend: `backend/Dockerfile`, `backend/pyproject.toml`, `backend/app/**`, `backend/tests/**`
- Frontend: `frontend/Dockerfile`, `frontend/package.json`, lockfile and configuration files, `frontend/app/**`, `frontend/tests/**`
- Documentation: `docs/ARCHITECTURE.md`, `docs/DECISIONS.md`

## Implementation Steps

- [x] Add environment templates and ignore rules without committing secrets.
- [x] Scaffold FastAPI with typed configuration, async SQLAlchemy connectivity, and structured `/health` responses.
- [x] Add backend tests for healthy and unavailable database states plus Ruff and mypy configuration.
- [x] Scaffold a strict Next.js App Router frontend with Tailwind CSS and an accessible, non-functional search shell containing no biological claims.
- [x] Add frontend component testing, ESLint, typecheck, and production build commands.
- [x] Add container images and Docker Compose services with dependency health checks.
- [x] Document exact local/container startup and validation commands.
- [x] Record only frozen architecture decisions and the Milestone 1 service boundaries.
- [x] Run every validation command below and repair all failures.

## Validation Commands

- `python -m pip install -e ".[dev]"` (from `backend/`)
- `python -m ruff check .` (from `backend/`)
- `python -m mypy app tests` (from `backend/`)
- `python -m pytest` (from `backend/`)
- `npm install` (from `frontend/`)
- `npm run lint` (from `frontend/`)
- `npm run typecheck` (from `frontend/`)
- `npm test -- --run` (from `frontend/`)
- `npm run build` (from `frontend/`)
- `docker compose config`
- `docker compose build`
- `docker compose up -d --wait`
- `Invoke-RestMethod http://localhost:8000/health`
- `Invoke-WebRequest http://localhost:3000`
- `docker compose down`

## Acceptance Criteria

- [x] `docker compose up --build` starts PostgreSQL, backend, and frontend from one command.
- [x] `GET /health` returns HTTP 200 and structured service/database status when PostgreSQL is ready.
- [x] The frontend loads the BioVerse landing page with an accessible search shell and no fake biological data.
- [x] Database configuration is environment-driven and no secret is committed.
- [x] Backend tests pass.
- [x] Backend lint and type checks pass.
- [x] Frontend tests, lint, and type checks pass.
- [x] Frontend production build passes.
- [x] `README.md` contains exact local and Docker startup commands.
- [x] `docs/ARCHITECTURE.md` matches the master specification without inventing future decisions.
- [x] No Milestone 2+ capability is implemented.

## Decisions / Deviations

- Use async SQLAlchemy with the `psycopg` driver so the readiness endpoint verifies real database connectivity without blocking the FastAPI event loop.
- Use the Next.js App Router and strict TypeScript, consistent with the target frontend stack.
- Use Vitest with React Testing Library for the Milestone 1 frontend smoke test.
- Treat `/health` as a readiness endpoint: return `200` when the service and database are ready and `503` with the same structured schema when the database is unavailable.
- Publish PostgreSQL on host port `5433` by default while retaining port `5432` inside Compose, avoiding conflicts with conventional host PostgreSQL installations.
- No deviations from the frozen product scope or source policy.

## Stop Rule
Do not start Milestone 2 until every acceptance criterion above is satisfied or a blocker is explicitly reported.

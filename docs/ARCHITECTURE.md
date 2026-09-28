# BioVerse AI Architecture

## Milestone 1 system boundary

The current repository establishes three independently deployable services:

```text
Browser
  |
  v
Next.js frontend :3000

FastAPI backend :8000
  |
  v
PostgreSQL :5432 (container; host development port :5433)
```

The Milestone 1 landing page does not call the backend. It is a visual product shell with disabled search controls. The only backend route is `GET /health`, which performs a real database readiness query. Docker Compose starts PostgreSQL first, then the backend after PostgreSQL is healthy, and finally the frontend after the backend is healthy.

## Frontend

- Next.js App Router with React and strict TypeScript.
- Tailwind CSS is available for later feature work; the current landing experience uses a small global design layer.
- The frontend image uses Next.js standalone output and runs as a non-root user.
- No scientific API, biological record, graph, AI, or structure-viewer code exists in this milestone.

Future server-fetch logic and visual components will remain separate as required by the master specification. Their design is intentionally deferred to their owning milestones.

## Backend

- FastAPI owns HTTP validation and serialization.
- Pydantic settings load environment-driven configuration.
- Async SQLAlchemy owns database engine and connectivity concerns.
- Pydantic response models define the current HTTP boundary.
- Application logs use newline-delimited JSON.

The package layout begins the specified separation between API routes, core infrastructure, and schemas. Service, adapter, normalized domain, repository, cache, and AI packages will be introduced only when a milestone requires real behavior in those layers.

## Database

PostgreSQL is the normal local/deployment database. Credentials and the SQLAlchemy URL come from environment variables. Docker Compose provides development-only defaults so the stack can start without committing a `.env` file. The database is published on host port `5433` by default to avoid colliding with conventional host PostgreSQL installations; services use port `5432` inside Compose. Persistent local data is stored in the named `bioverse_postgres_data` volume.

No tables or migrations are created in Milestone 1 because no persisted domain model has been approved for implementation yet.

## Health contract

`GET /health` is a readiness endpoint:

- HTTP `200` and `status: ready` when the API can execute `SELECT 1` against PostgreSQL.
- HTTP `503` and `status: degraded` when PostgreSQL is unavailable.

Both outcomes use the same typed response shape and report component state without exposing credentials or connection details.

## Future architecture (frozen, not implemented)

The master specification reserves backend adapters for PubChem, RCSB PDB, and Open Targets; normalized entity and provenance models; repositories and demo caches; grounded explanation services; and frontend 3D/graph adapters. Browser code must not call scientific sources directly. These boundaries are documented here only to preserve the frozen architecture—not as implemented capability.

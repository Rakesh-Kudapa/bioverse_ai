# BioVerse AI Decision Log

This log records frozen product decisions and the minimal implementation choices required by Milestone 1. It does not authorize work from later milestones.

## Frozen product and architecture decisions

1. The product is named BioVerse AI.
2. Visual-first exploration takes priority over broad feature count.
3. PubChem, RCSB PDB, and Open Targets are the initial approved scientific sources.
4. AI may interpret and explain retrieved facts but is never a source of biological facts.
5. The application uses a Next.js/TypeScript frontend and FastAPI/Python backend.
6. PostgreSQL is the normal deployment database; local alternatives must preserve the database abstraction.
7. External scientific APIs remain behind backend adapters.
8. Provenance and demo/offline resilience are mandatory product concerns.
9. Docking, efficacy prediction, clinical recommendations, and autonomous multi-agent behavior are outside the MVP.
10. Work proceeds one tested milestone at a time.

## Milestone 1 implementation decisions

### D-001: Async PostgreSQL connectivity

**Status:** Accepted for Milestone 1  
**Decision:** Use SQLAlchemy 2.x with the async `psycopg` driver.  
**Reason:** This matches the frozen backend stack and permits a non-blocking readiness query while leaving persistence details for later milestones.

### D-002: Readiness behavior

**Status:** Accepted for Milestone 1  
**Decision:** `/health` returns HTTP 200 only when PostgreSQL is reachable, otherwise it returns a typed HTTP 503 response.  
**Reason:** The endpoint is specified as suitable for readiness checks, and Compose must not start dependent services before the backend is operational.

### D-003: Frontend foundation

**Status:** Accepted for Milestone 1  
**Decision:** Use the Next.js App Router, strict TypeScript, Tailwind CSS, ESLint, and Vitest with React Testing Library.  
**Reason:** These choices implement the frozen frontend stack and required validation surface without selecting any future visualization architecture.

### D-004: Search is a disabled shell

**Status:** Accepted for Milestone 1  
**Decision:** Render an accessible but disabled search input and clearly label it as coming soon.  
**Reason:** Search behavior belongs to later source-integration milestones; an inert shell satisfies the landing-page scope without showing fabricated data.


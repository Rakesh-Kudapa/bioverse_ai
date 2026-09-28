# BioVerse AI - Codex Repository Instructions

## Mission
Build **BioVerse AI**, a visual-first, scientifically grounded biology exploration platform for a hackathon. The product lets non-specialists and specialists explore real relationships between drugs, compounds, proteins, genes, diseases, structures, and later variants/pathways through interactive 2D/3D visualizations and grounded AI explanations.

## Non-negotiable product rule
**AI must never invent biological facts.**
All factual biological claims shown to users must originate from approved structured scientific sources (initially PubChem, RCSB PDB, Open Targets). AI may interpret user intent, summarize supplied facts, change explanation level, and generate narrative transitions, but it must not fabricate targets, structures, disease associations, molecular properties, residues, variants, pathways, citations, or experimental conclusions.

If required source data is unavailable, return an explicit unavailable/insufficient-data state. Never fill missing biology from model memory.

## Required workflow for Codex
1. Read this `AGENTS.md` and `BIOVERSE_MASTER_SPEC.md` before changing code.
2. Read `PLAN.md` if present and work only on the current milestone unless explicitly asked otherwise.
3. Before implementation, inspect the existing repository and preserve working code.
4. Implement in small, testable milestones.
5. After each milestone, run all relevant validation commands and fix failures before continuing.
6. Do not silently change architecture, source policy, entity schemas, API contracts, or MVP scope. Record proposed changes in `docs/DECISIONS.md` and ask for approval when the change is material.
7. Prefer deterministic adapters, validators, schemas, and typed interfaces over prompt-only logic.
8. Keep external scientific APIs behind backend adapters. The browser must not depend directly on PubChem, RCSB, or Open Targets.
9. Do not expose API keys or secrets to the frontend.
10. Every external request needs timeout, retry/backoff where sensible, typed error handling, logging, and cache/fallback behavior.
11. The application must support a demo/offline-cache mode for preselected demo journeys.
12. Never implement clinical diagnosis, treatment recommendation, drug efficacy prediction, molecular docking, or claims that BioVerse predicts biological truth.

## Product principles
- Visual first: 3D structure/graph is central, not decorative.
- Simple first: a non-life-science judge should understand the screen in <30 seconds.
- Scientific depth on demand: simple and scientific explanation modes.
- Traceable: every displayed fact records its source database and external identifier when possible.
- Progressive disclosure: avoid dumping specialist terminology on the first screen.
- Reliable demo: pre-cache tested demo entities and structures.
- Responsive: expensive queries should not block the whole UI; show staged progress and clear failures.

## Initial approved sources
### PubChem PUG REST
Use for compounds, CIDs, 2D/3D records, molecular properties, and similar compounds.
Official docs: https://pubchem.ncbi.nlm.nih.gov/docs/pug-rest

### RCSB PDB APIs
Use for experimentally determined/computed structure search and metadata; render compatible structure data in the frontend.
Official docs: https://www.rcsb.org/docs/programmatic-access/web-apis-overview

### Open Targets Platform API
Use for target-disease associations and drug/target/disease relationships exposed by the platform.
Official API: https://api.platform.opentargets.org/

Do not add a new biological source without updating source normalization, provenance, tests, and documentation.

## Target stack
### Frontend
- Next.js + TypeScript
- React
- Tailwind CSS
- Framer Motion for controlled transitions
- Mol* and/or 3Dmol.js for molecular/protein visualization, chosen per use case
- Cytoscape.js for biological relationship graphs

### Backend
- Python 3.12+
- FastAPI
- Pydantic v2
- httpx
- SQLAlchemy 2.x
- PostgreSQL for normal deployment
- SQLite may be used for local zero-config developer mode if the repository keeps the DB abstraction clean

### Infrastructure
- Docker + Docker Compose
- `.env.example`
- structured logging
- pytest
- frontend unit/component tests and a small E2E smoke suite

## Domain model
Normalized entity types:
- `compound`
- `drug`
- `gene`
- `protein`
- `disease`
- `structure`
- later: `variant`, `pathway`

Core relationship types:
- `TARGETS`
- `ENCODES`
- `ASSOCIATED_WITH`
- `HAS_STRUCTURE`
- `SIMILAR_TO`
- `HAS_LIGAND`
- later: `HAS_VARIANT`, `IN_PATHWAY`

Every normalized entity/edge must include provenance.

## Grounded AI contract
AI inputs should consist of:
- user request
- resolved intent/entity identifiers
- structured facts retrieved by adapters
- permitted presentation instructions

AI outputs must be structured where possible and must not create facts not present in context.

Explanation service must support at least:
- `beginner`
- `student`
- `scientific`

If fact context is empty or incomplete, the explanation must say so.

## MVP scope - must work before optional features
1. Global search for compound/drug, protein/gene, disease.
2. Compound page: 2D structure, interactive 3D molecule, key properties, similar compounds.
3. Protein page: basic metadata + interactive 3D structure with representation controls.
4. Disease page: target associations as an interactive graph.
5. Cross-navigation: compound/drug -> target/protein; protein -> disease; disease -> target.
6. Grounded AI explanation in beginner and scientific modes.
7. Provenance visible for key facts.
8. Offline/demo cache for known demo journeys.
9. Polished loading, empty, unavailable, and API-error states.

## Not MVP
Do not implement until MVP acceptance criteria pass:
- mutation mapping
- pathway exploration
- docking
- de novo molecule generation
- efficacy prediction
- clinical recommendations
- autonomous multi-agent framework
- arbitrary knowledge graph ingestion
- user accounts unless specifically requested

## Required demo journeys
Keep these working throughout development and add fixtures/cache for them:
1. Aspirin -> compound 3D -> target/protein -> protein 3D -> explanation.
2. Breast cancer -> target network -> ERBB2/HER2 -> structure -> related drug context.
3. Ibuprofen -> compound 3D -> similar compounds -> comparison/explanation.

If a specific relationship is not supported by the approved source data, replace the demo entity with a source-supported one and document the change rather than fabricating it.

## Repository structure target
```text
bioverse-ai/
  AGENTS.md
  BIOVERSE_MASTER_SPEC.md
  PLAN.md
  README.md
  .env.example
  docker-compose.yml
  docs/
    ARCHITECTURE.md
    DECISIONS.md
    DATA_PROVENANCE.md
    DEMO_RUNBOOK.md
  backend/
    app/
      main.py
      api/
      adapters/
      core/
      models/
      schemas/
      services/
      repositories/
      cache/
    tests/
    pyproject.toml
  frontend/
    app/
    components/
    features/
    lib/
    types/
    tests/
    package.json
  demo_data/
    manifests/
    compounds/
    structures/
    relationships/
```

## API conventions
- All app APIs under `/api/v1`.
- Use stable response envelopes where appropriate.
- Use typed error codes, not only free-text messages.
- Include provenance in domain responses.
- External raw payloads must not leak directly into UI contracts.
- Prefer server-side caching for public scientific data.

Initial endpoints:
- `GET /health`
- `GET /api/v1/search?q=`
- `GET /api/v1/compounds/{id}`
- `GET /api/v1/compounds/{id}/similar`
- `GET /api/v1/proteins/{id}`
- `GET /api/v1/proteins/{id}/structures`
- `GET /api/v1/diseases/{id}`
- `GET /api/v1/network/{entity_type}/{id}`
- `POST /api/v1/explain`
- optional after MVP: `POST /api/v1/story`

## Data provenance requirements
At minimum keep:
- `source_name`
- `source_record_id`
- `source_url` or reconstructable URL metadata
- `retrieved_at`
- `field_path` or source category when feasible

For an AI explanation, keep the set of source facts/IDs that were supplied to the model so the UI can expose "Based on" provenance.

## Testing rules
- Adapter tests must mock external APIs and include known fixture payloads.
- Add contract tests for normalized entity schemas.
- Add tests proving AI explanation cannot receive unsourced free-form biology.
- Add demo-journey smoke tests.
- Add fallback-cache tests.
- Never make CI depend on live scientific APIs.
- Live integration tests may exist behind an explicit marker/environment flag.

## UI quality bar
- Dark, premium scientific-exploration aesthetic.
- One dominant visual per screen.
- Avoid generic dashboard card overload.
- Keep labels understandable to non-specialists.
- Smooth but restrained animation.
- 3D viewer should be usable: rotate, zoom, reset, representation toggle, ligand focus where source data supports it.
- Mobile responsiveness is desirable but desktop demo quality is higher priority.

## Performance targets for demo
- Cached demo search result visible in <1 second on a typical local laptop.
- Cached 3D structure begins rendering in ~2 seconds where practical.
- Live API operations show meaningful progress/fallback states rather than appearing frozen.

## Security and safety
- No secrets committed.
- Validate and sanitize query inputs.
- Apply outbound request allowlists to approved scientific hosts where practical.
- Set size/time limits for fetched structure files.
- Do not render arbitrary HTML from external sources.
- Do not present BioVerse as medical advice or a diagnostic system.

## Stop conditions
Stop and report rather than guessing when:
- source APIs contradict the required data model in a material way;
- a demo story cannot be supported with real source data;
- an API requires licensing/credentials incompatible with the project;
- a requested feature would make unsupported scientific/clinical claims;
- tests reveal that normalization loses provenance.

## Definition of done for a milestone
A milestone is complete only when:
1. code is implemented;
2. relevant tests pass;
3. lint/type checks pass;
4. acceptance criteria in `PLAN.md` pass;
5. docs are updated if behavior/contracts changed;
6. no known regression breaks the three demo journeys.

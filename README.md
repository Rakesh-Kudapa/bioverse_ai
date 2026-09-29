# BioVerse AI

BioVerse AI is a visual-first biology exploration platform built around source-grounded scientific data. **Milestone 4** adds a production-built Next.js explorer for real PubChem compounds and experimental RCSB protein structures. PubChem SDF coordinates render with 3Dmol.js, RCSB mmCIF coordinates render with Mol*, and every browser data request passes through BioVerse-owned API paths. Open Targets, disease graphs, and AI explanations remain intentionally deferred.

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
- Search explorer: <http://localhost:3000/explore?q=aspirin>
- Aspirin explorer: <http://localhost:3000/compound/2244>
- EGFR structure results: <http://localhost:3000/protein/EGFR>
- RCSB structure explorer: <http://localhost:3000/structure/1M17>
- Backend readiness: <http://localhost:8000/health>
- Compound search: <http://localhost:8000/api/v1/compounds/search?q=aspirin>
- Protein search: <http://localhost:8000/api/v1/proteins/search?q=EGFR>
- Structure detail: <http://localhost:8000/api/v1/structures/1M17>

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

The frontend server proxies `/bioverse-api/api/v1/**` to `BIOVERSE_API_BASE_URL` (default `http://localhost:8000`). Browser code never calls PubChem or RCSB directly. In Compose, the server-only destination is `http://backend:8000`.

## Visual explorer

- `/explore?q={term}` runs the existing deterministic compound and protein searches and separates results by entity/source type.
- `/compound/{cid}` displays normalized PubChem properties, backend-proxied 2D PNG, interactive SDF with ball-and-stick/stick/sphere controls, and field provenance.
- `/protein/{query}` displays refresh-safe experimental RCSB polymer-entity results without describing source order as biological importance.
- `/structure/{pdb_id}` displays source metadata, nullable resolution, polymer/chains, ligands, an interactive backend-proxied mmCIF structure, and provenance.

Viewer modules load only on the relevant detail route. 3Dmol models and Mol* plugins are cleared/disposed when records change or components unmount. Missing conformers, resolution, ligands, records, files, and temporary source failures retain useful metadata and show explicit controlled states.

## Validation

Backend:

```powershell
Set-Location backend
python -m ruff check .
python -m mypy app tests
python -m pytest -m "not live"
```

An opt-in integration suite verifies the current PubChem contract and requires network access:

```powershell
Set-Location backend
$env:RUN_LIVE_PUBCHEM_TESTS = "1"
python -m pytest -m live tests/integration/test_pubchem_live.py
```

The RCSB live suite is independently opt-in:

```powershell
Set-Location backend
$env:RUN_LIVE_RCSB_TESTS = "1"
python -m pytest -m live tests/integration/test_rcsb_live.py
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
Invoke-RestMethod "http://localhost:8000/api/v1/compounds/search?q=aspirin"
Invoke-WebRequest http://localhost:3000/compound/2244
Invoke-WebRequest http://localhost:3000/protein/EGFR
Invoke-WebRequest http://localhost:3000/structure/1M17
docker compose down
```

## Compound API

All scientific-source calls occur in the backend. Responses contain normalized BioVerse models and field-level PubChem provenance; raw PubChem payloads are never exposed as application contracts.

- `GET /api/v1/compounds/search?q={name}` resolves a name and returns normalized matches.
- `GET /api/v1/compounds/{cid}` returns one normalized compound.
- `GET /api/v1/compounds/{cid}/similar?threshold=90&limit=10` returns PubChem 2D similarity results.
- `GET /api/v1/compounds/{cid}/structure/2d` proxies a source-derived PNG.
- `GET /api/v1/compounds/{cid}/structure/3d` proxies a source-derived SDF when PubChem reports a conformer.

Unknown searches return an empty result set. Unknown CIDs, missing 3D conformers, upstream timeouts, throttling, unavailability, and invalid payloads use stable typed error envelopes. Successful source records are cached in-process for a bounded TTL; failures are not cached.

## Protein and structure API

RCSB Search results are restricted to experimental protein polymer entities. User query text is never promoted into a gene or protein fact; names, gene symbols, chains, entity descriptions, methods, resolution, dates, ligands, assemblies, and identifiers come from validated RCSB responses.

- `GET /api/v1/proteins/search?q={term}` returns normalized RCSB polymer entities and associated structure summaries.
- `GET /api/v1/structures/{pdb_id}` returns normalized entry, polymer, chain, ligand, and assembly metadata.
- `GET /api/v1/structures/{pdb_id}/ligands` returns source-reported non-polymer entities; ligand-free entries return an empty list.
- `GET /api/v1/structures/{pdb_id}/file` proxies the unmodified PDBx/mmCIF file with size and content-type checks.

Missing resolution is valid and remains null, including for the tested solution-NMR entry `1D3Z`. The backend does not rank structures, infer ligand function, modify coordinates, or cross-link ligands to PubChem.

## Safety boundary

BioVerse is an educational and research exploration tool, not a diagnostic or treatment system. Future biological facts must come from the approved structured sources defined in `AGENTS.md` and `BIOVERSE_MASTER_SPEC.md`; the application must never fill missing biology from model memory.

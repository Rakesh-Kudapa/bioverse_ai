# BioVerse AI - Implementation Plan

## Current Milestone

**Milestone 4 - Visual Compound and Protein Explorer**

Milestones 1 through 3 are complete. This user-approved milestone combines the compound visualization and protein visualization work that the older `BIOVERSE_MASTER_SPEC.md` roadmap split across separate milestones. The master specification remains unchanged for auditability; the sequencing decision is recorded in `docs/DECISIONS.md`.

Stop after Milestone 4. Do not implement Open Targets, disease search/graphs, AI explanations, natural-language biological reasoning, mutations, pathways, docking, predictions, or any Milestone 5 capability.

## Objective

Build the first interactive BioVerse scientific explorer over the existing normalized PubChem and RCSB contracts:

```text
Browser
  -> Next.js routes and reusable explorer components
  -> same-origin /bioverse-api route proxy
  -> existing FastAPI /api/v1 endpoints
  -> existing PubChem and RCSB services/adapters
  -> approved source data only
```

The biological structure is the visual centerpiece. The frontend renders backend-supplied facts and coordinates without creating, correcting, ranking, or interpreting biological evidence.

## Governing Constraints

- The browser calls only BioVerse-owned paths; it never calls PubChem or RCSB directly.
- All scientific text, metadata, identifiers, images, and coordinates originate in existing backend responses.
- Viewer rendering is visualization, not a biological claim.
- Missing nullable values display explicit unavailable language, never invented defaults.
- RCSB result order is not labeled as biological relevance or importance.
- Ligands are displayed as source-reported non-polymer entities without therapeutic, functional, affinity, or mechanistic claims.
- Viewer code is client-only, lazy-loaded, lifecycle-safe, and isolated behind local components.
- Scientific API response types remain separate from viewer-library types.
- No backend scientific model, adapter, or normalization behavior should change.
- Desktop demo quality is primary; narrow screens must remain usable without overflow.
- Automated component tests mock viewers and do not require WebGL.

## Existing Repository Review

- The frontend currently contains a single App Router landing page, global stylesheet, and one component test.
- The landing search is disabled and no API client, routes, domain types, or viewer wrappers exist.
- The old public API-base variable pointed browsers at the backend. A narrow same-origin Next.js route proxy keeps the browser contract stable while Docker provides a server-only backend destination at runtime.
- Compound search returns full `CompoundEntity` results. Detail, 2D PNG, 3D SDF, and similarity endpoints already exist.
- Protein search returns RCSB polymer entities with associated structure summaries. Structure detail, ligand list, and mmCIF endpoints already exist.
- Typed backend failures use `{ error: { code, message, source, retryable } }`.
- Existing backend caches remain the source of download reuse; frontend requests use cancellation and stable component lifecycles.
- The current worktree contains validated uncommitted Milestone 2/3 work and must be preserved.

## Dependency Decisions

- `3dmol@2.5.5`: small-molecule SDF rendering, mouse/touch rotate and zoom, local reset and representation controls.
- `molstar@5.12.0`: macromolecular mmCIF rendering with an official plugin/viewer lifecycle and camera controls.
- Next.js uses its supported webpack mode because the default Turbopack build misorders Mol*'s circular ESM initialization at browser runtime.
- No animation, state-management, query, component-kit, or icon package is needed. CSS transitions and native React state are sufficient.
- Viewer libraries are dynamically imported only on detail pages.

## Routes

- `/`: upgraded landing page with functional deterministic search entry.
- `/explore?q={query}`: combined compound and experimental protein search with explicitly separated result types.
- `/compound/{cid}`: compound detail, PubChem 2D image, interactive 3D molecule or source-unavailable state, properties, and provenance.
- `/protein/{query}`: refresh-safe RCSB protein/structure search results for a deterministic query.
- `/structure/{pdb_id}`: structure metadata, Mol* viewer, ligand controls/data, and provenance.

## Frontend Component Architecture

```text
frontend/
  app/
    page.tsx
    explore/page.tsx
    compound/[cid]/page.tsx
    protein/[query]/page.tsx
    structure/[pdbId]/page.tsx
  components/
    shell/              brand header, footer
    search/             search form, grouped results
    compound/           compound explorer and properties
    protein/            protein results and structure metadata
    molecular-viewer/   3Dmol wrapper and controls
    protein-viewer/     Mol* wrapper and controls
    provenance/         reusable source panel
    states/             loading, empty, error, unavailable
  lib/
    api.ts              centralized typed client and binary helpers
    format.ts           presentation-only formatting
  types/
    bioverse.ts         exact backend-facing TypeScript contracts
```

Route files remain thin and delegate interactive behavior to feature components. Viewers expose small local control interfaces rather than leaking third-party objects into scientific components.

## API Client Contract

- Default browser prefix: `/bioverse-api`.
- Next.js route-proxy destination: server-only `BIOVERSE_API_BASE_URL`, defaulting to `http://localhost:8000`.
- Docker frontend destination: `http://backend:8000`.
- Typed JSON methods cover compound search/detail, protein search, and structure detail.
- Binary endpoint helpers provide only same-origin BioVerse URLs for PNG, SDF, and mmCIF.
- Non-2xx JSON failures normalize to a local `BioVerseApiError` with backend code, retryability, and safe message.
- Requests accept `AbortSignal`; search/detail components cancel stale work on unmount or query changes.

## Visualization Design

### Compound 2D

- Use the existing BioVerse PNG endpoint in a dimensionally stable image frame.
- Supply descriptive alt text using the backend compound name/CID.
- Handle image loading and failure independently from compound metadata.

### Compound 3D

- Fetch SDF through the BioVerse endpoint, then pass its text to lazily imported 3Dmol.js.
- Default to ball-and-stick; offer stick and sphere controls.
- Expose reset view; library mouse/touch controls provide rotate and zoom.
- Clear models, render state, resize observer, and viewer reference on replacement/unmount.
- If `has_3d_conformer` is false or the endpoint returns `STRUCTURE_NOT_AVAILABLE`, keep the rest of the explorer usable.

### Protein structure

- Lazily import Mol* only on `/structure/{pdb_id}`.
- Load mmCIF exclusively from `/bioverse-api/api/v1/structures/{pdb_id}/file`.
- Use a cartoon-oriented default preset and expose reset camera.
- Dispose the Mol* plugin on structure replacement/unmount and guard late async initialization.
- Display all ligand facts outside WebGL. When reliable against Mol* APIs, `Show ligand` selects/focuses the source component ID; failure remains a controlled viewer notice and does not change metadata.

## Loading, Empty, and Error States

- Search: `Searching BioVerse...` plus grouped skeletons.
- Compound: metadata skeleton, separate `Loading 2D structure...` and `Loading molecular structure...` states.
- Protein: `Searching experimental protein structures...`.
- Mol*: `Loading protein coordinates...`.
- Empty compound/protein results remain distinct.
- Missing compound properties render `Not reported` only where useful; optional rows may be progressively disclosed.
- Missing 3D, missing resolution, no ligand, source unavailable, structure unavailable, and malformed viewer data have explicit non-technical states.
- Backend error codes map to controlled user language; stack traces are never rendered.

## Accessibility and Responsive Behavior

- Semantic form, navigation, headings, lists, buttons, details, and source links.
- Visible keyboard focus and minimum practical control sizes.
- Viewer controls carry labels; metadata duplicates essential visual information.
- Status changes use appropriate live regions without fabricated percentages.
- Desktop uses metadata/viewer/provenance columns; tablet/mobile stack the viewer first without horizontal overflow.
- Motion is restrained and disabled under `prefers-reduced-motion`.

## Files Expected to Change

- Root/docs: `PLAN.md`, `README.md`, `docker-compose.yml`, `docs/ARCHITECTURE.md`, `docs/DECISIONS.md`
- Frontend configuration: `package.json`, `package-lock.json`, `next.config.ts`
- Frontend routes, components, library code, domain types, tests, and `app/globals.css`
- Backend code is not expected to change.

## Implementation Steps

- [x] Add only the selected Mol* and 3Dmol.js dependencies.
- [x] Add same-origin BioVerse API route proxy and Docker server-side backend destination.
- [x] Define strict TypeScript contracts for compound, protein, structure, ligand, provenance, and typed failures.
- [x] Implement centralized abortable API client and safe binary endpoint builders.
- [x] Build shared application shell, search form, scientific states, provenance panel, and formatting helpers.
- [x] Replace the disabled landing shell with a functional, grounded entry experience.
- [x] Implement grouped deterministic compound/protein search at `/explore` and refresh-safe protein result routing.
- [x] Implement compound detail, progressive properties, 2D image, and provenance UI.
- [x] Implement lazy 3Dmol SDF viewer with representation/reset controls and complete cleanup.
- [x] Implement structure detail metadata, nullable resolution, chains/entities, ligand/no-ligand states, and provenance.
- [x] Implement lazy Mol* mmCIF viewer with reset, controlled load failures, and complete disposal.
- [x] Add source-supported ligand display and reliable Mol* focus/highlight where supported.
- [x] Add responsive premium visual styling and reduced-motion/focus behavior.
- [x] Add component tests covering every required search/entity/missing/error/provenance state with mocked viewers.
- [x] Update README and architecture/decision documentation without changing stable source provenance policy.
- [x] Run and repair all backend, frontend, live-source, Docker, and live UI validation gates.

## Validation Commands

Backend, from `backend/`:

- `python -m ruff check .`
- `python -m mypy app tests`
- `python -m pytest -m "not live"`
- `$env:RUN_LIVE_PUBCHEM_TESTS="1"; python -m pytest -m live tests/integration/test_pubchem_live.py`
- `$env:RUN_LIVE_RCSB_TESTS="1"; python -m pytest -m live tests/integration/test_rcsb_live.py`

Frontend, from `frontend/`:

- `npm install`
- `npm run lint`
- `npm run typecheck`
- `npm test -- --run`
- `npm run build`

Containers and UI smoke checks, from the repository root:

- `docker compose config`
- `docker compose build`
- `docker compose up -d --wait`
- validate `GET /health`
- open and exercise Dockerized `/`, `/explore`, `/compound/2244`, `/protein/EGFR`, `/structure/1M17`, and `/structure/1D3Z`
- confirm browser requests target only BioVerse paths
- confirm aspirin, ibuprofen, caffeine, EGFR, 1M17/AQ4, and 1D3Z states
- `docker compose down`
- `git diff --check`
- `git status --short --untracked-files=all`

## Acceptance Criteria

- [x] Compound search is usable from the frontend.
- [x] Aspirin can be opened in a compound explorer.
- [x] PubChem properties display correctly.
- [x] PubChem 2D structure displays through BioVerse.
- [x] PubChem 3D SDF renders interactively.
- [x] Missing 3D data is handled gracefully.
- [x] Protein/RCSB search is usable from the frontend.
- [x] EGFR search returns RCSB-backed structure results.
- [x] A structure can be selected.
- [x] 1M17 renders in Mol* from backend-delivered mmCIF.
- [x] Experimental method displays correctly.
- [x] Resolution displays correctly.
- [x] Missing resolution displays correctly.
- [x] Ligands display where present.
- [x] 1M17 AQ4 ligand metadata is accessible.
- [x] 1D3Z displays the correct no-ligand and missing-resolution states.
- [x] Scientific provenance is visible.
- [x] Frontend never directly calls PubChem.
- [x] Frontend never directly calls RCSB.
- [x] No scientific data is fabricated.
- [x] Viewer instances dispose correctly.
- [x] Loading, error, empty, and unavailable states are polished.
- [x] Existing backend tests remain green.
- [x] Frontend lint passes.
- [x] TypeScript passes.
- [x] Vitest passes.
- [x] Next.js production build passes.
- [x] Docker stack remains healthy.
- [x] Live UI smoke tests pass.
- [x] No Milestone 5 functionality is implemented.

## Decisions / Deviations

- Follow the latest explicit request: call the combined compound/protein visualization work Milestone 4, while retaining the older master roadmap unchanged.
- Use 3Dmol.js for small PubChem SDF structures and Mol* for RCSB mmCIF macromolecules; each library is used for its intended structure scale.
- Use a narrow same-origin Next.js route proxy rather than enabling broad backend CORS or exposing Docker-only backend hostnames to browser code. A runtime proxy is required because a build-time rewrite would freeze the wrong hostname into the standalone Docker image.
- Use Next.js webpack mode for Mol* compatibility; Turbopack compiled successfully but produced a browser-time `ArrayEncoding` initialization failure from Mol*'s circular ESM graph.
- Use query-specific protein routes because the existing source-grounded backend supports protein search but does not expose an invented canonical protein record endpoint.
- Treat Mol* ligand focus as a visualization convenience keyed only by the source component ID; ligand metadata remains authoritative even if WebGL focus is unavailable.
- Do not add a client state library or UI framework for this bounded explorer.

## Stop Rule

Stop after every acceptance criterion is satisfied or a blocker is explicitly reported. Do not begin Milestone 5 without explicit approval.

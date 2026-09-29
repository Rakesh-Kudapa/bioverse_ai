# BioVerse AI Architecture

## Milestone 4 system boundary

```text
Browser :3000
  |
  |-- Next.js pages and reusable explorer components
  |     |-- deterministic compound/protein search
  |     |-- normalized metadata and provenance UI
  |     |-- lazy 3Dmol.js SDF viewer
  |     +-- lazy Mol* mmCIF plugin
  |
  +-- GET /bioverse-api/api/v1/** (same origin)
          |
          +-- Next.js runtime route proxy
                  |
                  +-- FastAPI :8000
                         |-- CompoundService -> cache -> PubChemAdapter -> PubChem
                         |-- ProteinService  -> cache --+
                         +-- StructureService -> cache -+-> RcsbAdapter -> RCSB

FastAPI -> PostgreSQL :5432 (container; host :5433) for readiness
```

Open Targets, disease data, biological graphs, AI explanations, and later milestone features remain outside this boundary.

## Frontend routes

- `/` is a functional landing/search entry with links to known source-grounded examples.
- `/explore?q={query}` runs compound and protein searches independently and groups results by source/entity type.
- `/compound/{cid}` renders normalized PubChem facts, 2D PNG, optional 3D SDF, and provenance.
- `/protein/{query}` reruns the deterministic RCSB polymer-entity search, preserving deep links and refresh behavior.
- `/structure/{pdb_id}` renders normalized entry/polymer/chain/ligand facts, mmCIF, and provenance.

Route components are thin. Client feature components own cancellation and state transitions; viewer wrappers own WebGL/library lifecycles.

## Browser/API boundary

Browser code uses a single typed client in `frontend/lib/api.ts`. Its only base path is `/bioverse-api`, and its builders accept fixed BioVerse API operations rather than arbitrary external URLs.

The catch-all Next.js GET route accepts only paths beginning with `api/v1`, forwards only the `Accept` header, copies only content type/disposition/cache headers, and returns a typed safe 503 when the backend is unreachable. It reads `BIOVERSE_API_BASE_URL` on the server. Compose supplies `http://backend:8000`; split local development defaults to `http://localhost:8000`.

The proxy serves JSON, PubChem PNG/SDF, and RCSB mmCIF without exposing PubChem or RCSB hosts to frontend code. Existing backend adapters remain the only components that contact scientific sources.

## Type and scientific-data ownership

`frontend/types/bioverse.ts` mirrors the existing BioVerse API contracts for compounds, RCSB polymer entities, structures, chains, ligands, assemblies, provenance, and typed errors. Nullable values remain explicit. Viewer-library objects never enter those contracts.

The UI performs presentation-only formatting:

- source strings and identifiers remain unchanged;
- missing resolution displays `Not reported` rather than zero;
- empty ligand collections display an explicit source-reported absence state;
- RCSB result ordering is not labeled as scientific ranking;
- visual selection of a ligand adds no therapeutic or mechanistic meaning.

## Compound visualization

The compound explorer requests metadata first. The 2D panel uses the BioVerse PNG route with fixed dimensions, loading state, descriptive alt text, and an independent unavailable state.

3Dmol.js is dynamically imported only when a compound has a source-reported 3D conformer. The component fetches SDF from the same-origin BioVerse route, displays ball-and-stick by default, and offers stick, sphere, and reset controls. Pointer/touch interaction supplies rotation and zoom.

An `AbortController` cancels stale SDF requests. A resize observer resizes the canvas. Cleanup disconnects the observer, clears 3Dmol state, removes canvas children, and releases references.

## Protein visualization

Mol* is dynamically imported only on structure pages. BioVerse uses the documented lower-level plugin UI rather than the prebuilt Viewer app, so optional MP4/server integrations are not bundled.

Next.js runs through its supported webpack mode. The default Turbopack production build compiled Mol* but misordered a circular ESM initialization at runtime; webpack preserves the library's required module order.

The plugin:

- downloads only the same-origin BioVerse mmCIF URL;
- parses the response as mmCIF;
- applies the default macromolecular representation with chain coloring;
- disables remote state, volume streaming, optional extensions, and unrelated controls;
- exposes camera reset;
- selects and focuses a ligand by the backend-reported `label_comp_id` when requested.

All ligand metadata remains visible outside WebGL. Plugin disposal and resize-observer cleanup run on structure replacement, navigation, and unmount. Late asynchronous initialization checks component activity before retaining a plugin.

## Search and error behavior

The combined explorer starts existing compound and protein searches concurrently. `Promise.allSettled` keeps one source's results usable if the other source fails. Search requests and detail requests use `AbortSignal`.

Backend error envelopes normalize to a local `BioVerseApiError`. Pages display controlled states for empty search, unknown entity, unavailable source, absent 3D conformer, structure-file failure, missing resolution, and no ligand. Raw payloads, upstream HTML, and stack traces are never rendered.

## Rendering, performance, and accessibility

- Viewer libraries are excluded from landing/search bundles and loaded only on detail pages.
- Backend caches continue to avoid repeat scientific downloads; the frontend does not add a conflicting scientific cache.
- Desktop uses metadata, dominant viewer, and provenance columns. Tablet/mobile layouts stack without canvas overflow.
- Search forms, links, buttons, details, headings, and statuses are semantic and keyboard accessible.
- Viewer controls have text labels, scientific metadata is available without WebGL, and reduced-motion preferences disable decorative motion.

## Backend and persistence

Milestone 4 does not modify backend adapters, normalization, caching, Pydantic contracts, database behavior, or scientific provenance policy. `GET /health` continues to perform PostgreSQL readiness. Scientific records remain in bounded process-local caches; persistent demo packs remain later work.

## Deferred architecture

Open Targets, disease search, disease/target graphs, Cytoscape, cross-domain relationship navigation, persistent offline demo packs, AI explanations, mutations, pathways, docking, prediction, and cinematic story mode remain unimplemented.

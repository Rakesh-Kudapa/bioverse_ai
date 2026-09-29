# BioVerse AI Decision Log

This log records frozen product decisions and implementation choices through the user-directed RCSB backend milestone. It does not authorize work from later milestones.

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

## Milestone 2 implementation decisions

### D-005: BioVerse-owned PubChem contract

**Status:** Accepted for Milestone 2

**Decision:** Keep raw PUG REST schemas private to `PubChemAdapter` and return immutable normalized `CompoundEntity` models with field-level provenance.

**Reason:** External payload changes must not leak into API or UI contracts, and every displayed scientific value must remain traceable.

### D-006: Versioned compound endpoints

**Status:** Accepted for Milestone 2

**Decision:** Expose compound functionality under `/api/v1/compounds`, including backend-proxied PNG and SDF structure resources. Unknown name searches return an empty list; unknown CID detail requests return a typed 404.

**Reason:** This follows the repository-wide API convention, keeps browsers away from scientific APIs, and distinguishes a valid empty search from an absent requested record.

### D-007: Bounded process-local cache

**Status:** Accepted for Milestone 2

**Decision:** Cache successful normalized lookups and structures in a bounded async TTL/LRU cache. Preserve original retrieval metadata and never cache errors.

**Reason:** This reduces repeat source traffic and improves demo responsiveness without prematurely introducing Redis or a persistence schema. Persistent offline demo packs are still required in a later milestone.

### D-008: PubChem structure availability

**Status:** Accepted for Milestone 2

**Decision:** Advertise 3D only when PubChem's `ConformerCount3D` is greater than zero. Fetch 2D as PNG and 3D as SDF through fixed-host adapter requests with configured byte limits.

**Reason:** Structure availability must be source-derived, and bounded proxying provides a stable frontend contract without inventing geometry.

### D-009: Similar-compound semantics

**Status:** Accepted for Milestone 2

**Decision:** Use PubChem `fastsimilarity_2d`, exclude the input CID from results, and expose validated threshold and limit metadata.

**Reason:** Similarity is a PubChem-derived operation, not an application prediction, and explicit parameters make the result interpretable and testable.

## Milestone 3 RCSB implementation decisions

### D-010: User-directed milestone sequence

**Status:** Accepted for Milestone 3

**Decision:** Implement the RCSB protein/structure backend as Milestone 3 and continue deferring both compound and protein visualization. Leave `BIOVERSE_MASTER_SPEC.md` unchanged.

**Reason:** The newer explicit implementation request reorders the older roadmap numbering without changing the approved source policy or architecture. Recording the deviation preserves auditability.

### D-011: Search returns real polymer entities

**Status:** Accepted for Milestone 3

**Decision:** Search experimental content with RCSB Search API `return_type=polymer_entity`, restricted to source-reported protein polymer entities. Normalize each returned RCSB entity rather than treating an arbitrary entry or query string as a protein fact.

**Reason:** Polymer-entity identifiers provide a conservative structural protein representation with explicit parent PDB entries, chains, descriptions, and source references.

### D-012: Selected GraphQL hierarchy

**Status:** Accepted for Milestone 3

**Decision:** Use RCSB Data GraphQL queries with explicit field selections for protein search enrichment and structure detail. Keep GraphQL response schemas private to `RcsbAdapter`.

**Reason:** One bounded query can traverse entry, polymer, chain, non-polymer, and assembly hierarchy without exposing giant REST/mmCIF payloads or requiring many per-entity calls.

### D-013: Resolution and experimental methods

**Status:** Accepted for Milestone 3

**Decision:** Preserve every source-reported experimental method. Normalize the first value of RCSB `resolution_combined` to nullable `resolution_angstroms`, documenting the mechanical mapping. Absence is valid and creates no error or quality judgment.

**Reason:** Experimental methods have different resolution semantics; notably the tested solution-NMR entry `1D3Z` has no reported combined resolution.

### D-014: Non-polymer entities are ligands without inferred meaning

**Status:** Accepted for Milestone 3

**Decision:** Normalize RCSB non-polymer entities as ligand records with chemical component and chain/asym context. Do not infer binding function, affinity, mechanism, or PubChem relationships.

**Reason:** RCSB supplies the structural occurrence and identifiers, but those facts alone do not support mechanistic claims or cross-source identity assumptions.

### D-015: Proxied PDBx/mmCIF files

**Status:** Accepted for Milestone 3

**Decision:** Proxy uncompressed source mmCIF from the fixed RCSB download host, accept the documented `application/octet-stream` and live `chemical/x-cif` types, enforce a byte limit, and return `chemical/x-mmcif` to BioVerse clients.

**Reason:** mmCIF supports current and extended PDB records and future Mol* rendering. Proxying retains the fixed-host security boundary and a stable application contract without modifying coordinates.

## Milestone 4 visual explorer decisions

### D-016: User-directed combined visualization milestone

**Status:** Accepted for Milestone 4

**Decision:** Implement both compound and protein visualization in the user-named Milestone 4, while leaving the older master-spec roadmap unchanged for auditability.

**Reason:** The latest explicit milestone contract combines the previously separate UI phases and authorizes no disease or AI work.

### D-017: Separate viewers by scientific structure scale

**Status:** Accepted for Milestone 4

**Decision:** Use 3Dmol.js 2.5.5 for PubChem SDF small molecules and Mol* 5.12.0 for RCSB mmCIF macromolecular structures. Wrap both behind local client components and lazy route-level loading.

**Reason:** 3Dmol.js supplies a compact SDF workflow and simple representations; Mol* supplies robust mmCIF/macromolecular rendering and structure selection. Using each for its intended scale avoids forcing one large framework across both cases.

### D-018: Runtime same-origin frontend proxy

**Status:** Accepted for Milestone 4

**Decision:** Browser code calls only `/bioverse-api/api/v1/**`. A narrow Next.js route handler forwards GET requests to the server-only `BIOVERSE_API_BASE_URL`; Compose sets this to `http://backend:8000`.

**Reason:** This keeps browser traffic on BioVerse-owned paths, avoids broad backend CORS, and resolves the Docker backend at runtime. A Next.js rewrite was rejected because its destination is captured during the standalone image build.

### D-019: Mol* plugin UI without optional app extensions

**Status:** Accepted for Milestone 4

**Decision:** Create a minimal `PluginUIContext` using Mol*'s documented plugin APIs rather than importing the prebuilt Viewer app. Disable remote state, volume streaming, optional extensions, and unrelated controls.

**Reason:** The prebuilt Viewer app statically imported the optional MP4 exporter and its Node-only encoder into the browser bundle. The lower-level plugin keeps mmCIF parsing, interaction, camera reset, ligand focus, and disposal while producing a valid Next.js browser build and preventing unintended external integrations.

### D-020: Viewer lifecycle and ligand semantics

**Status:** Accepted for Milestone 4

**Decision:** Abort small-molecule downloads, disconnect resize observers, clear 3Dmol state, and dispose Mol* plugins on replacement/unmount. Ligand focus uses only the RCSB-reported chemical component ID; the textual metadata remains authoritative if focus cannot be rendered.

**Reason:** Explicit ownership prevents stale requests and WebGL leaks. Component-ID focus is a visual selection, not an inferred biological, therapeutic, or mechanistic claim.

### D-021: Webpack for Mol* module compatibility

**Status:** Accepted for Milestone 4

**Decision:** Run Next.js development and production builds with the supported `--webpack` option.

**Reason:** Next.js 16 Turbopack compiled Mol* but evaluated its circular ESM graph out of order in the browser, leaving `ArrayEncoding` undefined during module initialization. Webpack preserves Mol*'s module initialization semantics and produces a working viewer without source patches or scientific-data changes.

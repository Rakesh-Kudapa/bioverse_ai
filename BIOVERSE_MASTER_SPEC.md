# BioVerse AI - Master Product, Architecture & Implementation Specification

**Version:** 1.0  
**Purpose:** Primary implementation contract for OpenAI Codex in VS Code  
**Project:** BioVerse AI  
**Team concept:** CatalystX  

---

## 1. Executive Summary

BioVerse AI is a visual-first biology exploration application designed to make molecular and biomedical knowledge understandable to non-specialists without sacrificing scientific traceability.

Users can search for a drug/compound, protein/gene, or disease and interactively move through real biological relationships such as:

`Disease -> Gene/Target -> Protein -> Structure -> Drug/Compound`

The experience should feel closer to exploring a scientific universe than reading a database page. Its distinguishing elements are interactive 3D molecular/protein structures, relationship graphs, source-grounded biological facts, and AI explanations at different levels of complexity.

### Core promise
> Explore real biology visually, with AI explaining only what verified scientific sources provide.

### Primary hackathon objective
Create an application that a judge without deep life-science expertise can understand in under 30 seconds, while still demonstrating serious technical and biological engineering.

---

## 2. Problem Statement

Life-science information is fragmented across specialist databases and often presented using identifiers, tables, and terminology that are difficult for non-specialists to interpret. Even when high-quality molecular, protein-structure, disease-association, and compound data are publicly available, connecting these data into an understandable biological story requires domain knowledge and manual navigation across multiple tools.

BioVerse AI addresses this by creating a unified visual exploration layer across trusted scientific data sources. Users can start from an intuitive concept such as a drug or disease and visually navigate to related molecules, targets, proteins, structures, and associations while receiving grounded explanations appropriate to their knowledge level.

---

## 3. Goals

### G1 - Immediate comprehensibility
A non-biologist should understand what the app does from the landing page and first demo interaction.

### G2 - Visual wow factor
3D structures and biological relationship graphs should be core to the interaction, not secondary decorations.

### G3 - Scientific grounding
Factual biology comes from approved databases, not model memory.

### G4 - Explainability
Users can switch between beginner and scientific explanations without changing the underlying facts.

### G5 - Cross-domain navigation
The user can move between compounds/drugs, proteins/genes, diseases, structures, and related entities.

### G6 - Reliable hackathon demo
The application must continue to demonstrate its key journeys if venue internet access is slow or unavailable.

---

## 4. Non-Goals

The first release must NOT attempt to:
- diagnose disease;
- recommend treatment;
- predict whether a drug will work for a patient;
- perform molecular docking as a scientific claim engine;
- generate new drugs;
- claim mutation pathogenicity from model inference;
- replace PubChem, PDB, Open Targets, UniProt, or professional bioinformatics tools;
- function as an unrestricted scientific chatbot;
- build a fully autonomous multi-agent system.

---

## 5. Product Principles

1. **Real data before AI.** Retrieve and normalize scientific facts first; explain second.
2. **No invented biology.** Missing information stays missing.
3. **Visual before textual.** The dominant experience is structure/graph exploration.
4. **Simple surface, deep drill-down.** Beginner-friendly labels first, specialist detail on demand.
5. **Every fact knows its source.** Provenance is a first-class field.
6. **Deterministic core, AI at the edges.** Search adapters, normalization, schemas, validators, graph building, and provenance are deterministic.
7. **Demo resilience.** Cache all planned demo journeys.

---

## 6. Target Users

### 6.1 Curious learner
Wants to understand what a drug, protein, or disease is without specialist vocabulary.

### 6.2 Life-science student
Needs visual structure and relationships alongside more scientific terminology.

### 6.3 Developer / hackathon judge
Needs to see that the application is more than an LLM wrapper: multiple scientific APIs, normalization, 3D rendering, knowledge graph construction, caching, provenance, and controlled AI.

### 6.4 Scientist / technical reviewer
Needs traceability to source identifiers and confidence that the model is not inventing scientific data.

---

## 7. Core User Journeys

### Journey A - Compound exploration
1. User searches `Aspirin`.
2. Search resolves to a PubChem compound and normalized BioVerse entity.
3. App displays:
   - compound name and identifiers;
   - 2D representation;
   - interactive 3D conformer if available;
   - selected molecular properties;
   - source provenance.
4. User opens `Similar compounds`.
5. Backend performs/caches source-supported similarity retrieval.
6. User selects another compound to compare visually.
7. AI explains the currently displayed facts in beginner/scientific mode.

### Journey B - Protein/structure exploration
1. User searches a protein/gene such as `EGFR`.
2. App resolves identifiers and retrieves structure metadata.
3. User sees protein overview plus an interactive 3D structure.
4. User can rotate, zoom, reset, change representation, and highlight supported ligands.
5. User opens related diseases/compounds from the relationship panel.

### Journey C - Disease network
1. User searches `Breast cancer`.
2. App retrieves source-supported target/disease associations.
3. App builds a visually understandable target network.
4. User clicks ERBB2/HER2 or another source-supported target.
5. App transitions to the target/protein explorer.
6. User loads a source-supported structure and related drug context.

### Journey D - Ask BioVerse
1. User asks `Why is HER2 important in breast cancer?`
2. AI intent layer identifies entity + requested explanation.
3. Backend retrieves structured source facts.
4. Explanation model receives only those facts.
5. UI displays explanation plus a `Based on` section with sources/identifiers.

---

## 8. MVP Scope

### 8.1 Global search
Must resolve at least:
- compounds/drugs by common name;
- proteins/genes by common symbol/name where supported;
- diseases through Open Targets search/resolution.

Search response should contain typed candidates rather than immediately assuming the first result is correct.

### 8.2 Compound Explorer
Must include:
- BioVerse normalized ID;
- PubChem CID;
- preferred name;
- molecular formula;
- molecular weight;
- canonical/isomeric SMILES when available;
- 2D structure representation;
- 3D conformer/structure when available;
- selected physicochemical properties;
- similar compounds;
- provenance.

### 8.3 Protein Explorer
Must include:
- target/protein name;
- gene symbol where relevant;
- stable external identifiers available from sources;
- basic source-grounded description;
- available structure list;
- one selectable 3D structure;
- structure metadata;
- representation controls;
- ligands when source-supported;
- provenance.

### 8.4 Disease Explorer
Must include:
- disease name/identifier;
- source-grounded short description when available;
- associated targets;
- network visualization;
- source association evidence/score metadata where exposed and meaningful;
- ability to click a target and open its explorer.

### 8.5 Grounded explanation
Must support:
- beginner mode;
- student mode (optional in first implementation, mandatory before demo if easy);
- scientific mode.

The model must only receive structured factual context supplied by BioVerse services. The user-facing explanation must expose the sources that backed it.

### 8.6 Demo/offline mode
Must pre-cache the final set of demo entities and source payloads/normalized records.

---

## 9. Post-MVP Features

Prioritize only after MVP tests and demo journeys pass.

### P1 - Visual Story Mode
Animated sequence connecting a disease to target/protein to structure to drug/compound.

### P2 - Chemical similarity universe
Network/constellation visualization of source-supported similar compounds.

### P3 - Binding/ligand focus
For structures where source data clearly identifies ligands, visually isolate or focus the ligand and surrounding structural region. Avoid claiming a mechanistic binding interpretation unless sourced.

### P4 - Mutation map
Use an approved variant source added later. Never infer disease significance from geometry alone.

### P5 - Pathway explorer
Add Reactome or another approved pathway source after provenance architecture is stable.

---

## 10. Scientific Source Strategy

### 10.1 PubChem
**Purpose:** compounds, structures/conformers, identifiers, physicochemical properties, similarity results.

Use PUG REST behind a backend adapter.

Official documentation:
`https://pubchem.ncbi.nlm.nih.gov/docs/pug-rest`

Expected adapter capabilities:
- resolve name -> CID;
- fetch core properties;
- fetch 2D record/image or structure representation;
- fetch 3D compound record/SDF when available;
- fetch similar compound CIDs through source-supported similarity endpoints;
- normalize rate-limit/throttling errors.

### 10.2 RCSB PDB
**Purpose:** macromolecular structures, structure metadata, entities, ligands, coordinates/files.

Official web API overview:
`https://www.rcsb.org/docs/programmatic-access/web-apis-overview`

Expected adapter capabilities:
- search structures by target/entity/identifier;
- retrieve structure metadata;
- retrieve or provide a safe URL/stream for supported structure files;
- normalize ligand/entity metadata;
- enforce file size/time limits.

### 10.3 Open Targets Platform
**Purpose:** target-disease associations and drug/target/disease relationships.

Official API:
`https://api.platform.opentargets.org/`

Expected adapter capabilities:
- resolve disease/target entities;
- retrieve target-disease associations;
- retrieve linked drug context when available through source schema;
- preserve source IDs and association metadata.

### 10.4 Later sources
Possible additions only after architecture review:
- UniProt;
- Ensembl;
- ClinVar;
- Reactome;
- ChEMBL.

Every new source requires:
1. adapter;
2. normalization mapping;
3. provenance mapping;
4. fixtures;
5. mocked tests;
6. documented licensing/usage considerations.

---

## 11. Source Grounding Policy

### 11.1 Allowed AI behavior
AI may:
- parse natural-language intent;
- identify likely entity type candidates;
- rephrase source facts for different knowledge levels;
- create a narrative ordering of existing facts;
- generate UI-friendly headings/summaries based on supplied facts;
- suggest navigation actions using entities present in supplied data.

### 11.2 Prohibited AI behavior
AI may not:
- invent a target;
- invent a protein structure or PDB ID;
- invent a disease association;
- invent a molecular property;
- invent a ligand or binding residue;
- infer drug efficacy;
- infer clinical relevance not supplied by sources;
- fill missing fields from pretrained knowledge;
- create fake citations.

### 11.3 Missing data behavior
Use explicit states:
- `Not available from current sources`
- `No supported structure found`
- `No source-supported relationship found`
- `BioVerse cannot explain this claim from the currently retrieved data`

---

## 12. System Architecture

```text
                           +-----------------------+
                           |      Next.js UI       |
                           | Search / 3D / Graph   |
                           +-----------+-----------+
                                       |
                                  HTTPS/JSON
                                       |
                           +-----------v-----------+
                           |       FastAPI API      |
                           |   /api/v1 endpoints    |
                           +-----------+-----------+
                                       |
                    +------------------+------------------+
                    |                  |                  |
             +------v------+    +------v------+    +------v------+
             | Search/     |    | Graph/      |    | Explanation |
             | Resolver    |    | Relation    |    | Service     |
             +------+------+    +------+------+    +------+------+ 
                    |                  |                  |
                    +------------------+------------------+
                                       |
                             +---------v---------+
                             | Normalized Domain |
                             | + Provenance      |
                             +---------+---------+
                                       |
                   +-------------------+-------------------+
                   |                   |                   |
            +------v------+     +------v------+     +------v------+
            | PubChem     |     | RCSB PDB    |     | Open Targets|
            | Adapter     |     | Adapter      |     | Adapter     |
            +------+------+     +------+------+     +------+------+ 
                   |                   |                   |
                   +-------------------+-------------------+
                                       |
                             External scientific APIs

Separate concern:
            +---------------------+
            | Cache / Repository  |
            | DB + demo fixtures  |
            +---------------------+
```

---

## 13. Frontend Architecture

### 13.1 Stack
- Next.js latest stable compatible with project environment;
- TypeScript strict mode;
- React;
- Tailwind CSS;
- Framer Motion;
- Mol* / 3Dmol.js adapter components;
- Cytoscape.js for graphs.

### 13.2 Major routes
Suggested:
- `/` - landing/search;
- `/explore/compound/[id]`;
- `/explore/protein/[id]`;
- `/explore/disease/[id]`;
- optional `/story/[id]` after MVP.

### 13.3 Main visual layout
Desktop-first explorer:

```text
+----------------+------------------------------+------------------+
| Entity/context |                              | Explanation /    |
| metadata       |          3D VIEWER           | provenance       |
|                |        or GRAPH CANVAS       |                  |
+----------------+------------------------------+------------------+
| Overview | Structure | Relationships | Similar | Sources         |
+-------------------------------------------------------------------+
```

### 13.4 UX rules
- One dominant visualization.
- Do not clutter with >8 cards on a single viewport.
- Use plain-language names before IDs.
- IDs appear in detail/provenance areas.
- Provide `Reset view` for every 3D viewer.
- Provide clear skeleton/loading states.
- Provide source unavailable/fallback indicators.
- Cache demo paths client-side/server-side where useful.

---

## 14. Backend Architecture

### 14.1 Stack
- Python 3.12+;
- FastAPI;
- Pydantic v2;
- httpx async client;
- SQLAlchemy 2.x;
- PostgreSQL;
- pytest;
- optional SQLite developer profile.

### 14.2 Layers

#### API layer
HTTP validation and response serialization only.

#### Service layer
Coordinates use cases: search, resolve, network, structure selection, explanation.

#### Adapter layer
Owns external API specifics. No raw source schema should leak past adapters.

#### Domain/model layer
Normalized BioVerse entities/relationships.

#### Repository/cache layer
Stores normalized results, source snapshots/metadata, and demo cache.

---

## 15. Normalized Data Model

### 15.1 Provenance
```json
{
  "source_name": "pubchem",
  "source_record_id": "2244",
  "source_url": "...",
  "retrieved_at": "2026-09-28T...Z",
  "field_path": "PropertyTable.Properties[0].MolecularFormula"
}
```

### 15.2 Compound
```json
{
  "id": "compound:pubchem:2244",
  "type": "compound",
  "name": "Aspirin",
  "synonyms": [],
  "external_ids": {"pubchem_cid": "2244"},
  "formula": "C9H8O4",
  "molecular_weight": 180.16,
  "canonical_smiles": null,
  "isomeric_smiles": null,
  "structure_2d": null,
  "structure_3d": null,
  "properties": {},
  "provenance": []
}
```

### 15.3 Protein/target
```json
{
  "id": "protein:...",
  "type": "protein",
  "name": "...",
  "symbol": "EGFR",
  "external_ids": {},
  "description": null,
  "structures": [],
  "provenance": []
}
```

### 15.4 Disease
```json
{
  "id": "disease:opentargets:...",
  "type": "disease",
  "name": "Breast cancer",
  "external_ids": {},
  "description": null,
  "provenance": []
}
```

### 15.5 Structure
```json
{
  "id": "structure:pdb:XXXX",
  "type": "structure",
  "pdb_id": "XXXX",
  "title": "...",
  "method": "...",
  "resolution": null,
  "file_format": "mmcif",
  "file_reference": "...",
  "ligands": [],
  "provenance": []
}
```

### 15.6 Relationship
```json
{
  "id": "rel:...",
  "source_entity_id": "...",
  "target_entity_id": "...",
  "relationship_type": "ASSOCIATED_WITH",
  "attributes": {},
  "provenance": []
}
```

---

## 16. Initial API Contract

### `GET /health`
Returns service/database/cache status suitable for readiness checks.

### `GET /api/v1/search?q={query}`
Returns typed search candidates:
```json
{
  "query": "aspirin",
  "results": [
    {
      "entity_type": "compound",
      "id": "compound:pubchem:2244",
      "label": "Aspirin",
      "subtitle": "Compound",
      "source": "pubchem"
    }
  ]
}
```

### `GET /api/v1/compounds/{id}`
Normalized compound entity plus provenance.

### `GET /api/v1/compounds/{id}/similar`
Normalized similar compound summaries; include source similarity metadata when available.

### `GET /api/v1/proteins/{id}`
Normalized protein/target.

### `GET /api/v1/proteins/{id}/structures`
List of normalized structures.

### `GET /api/v1/diseases/{id}`
Normalized disease entity.

### `GET /api/v1/network/{entity_type}/{id}`
Graph response:
```json
{
  "nodes": [],
  "edges": [],
  "provenance": []
}
```

### `POST /api/v1/explain`
Request:
```json
{
  "entity_ids": ["..."],
  "question": "Why is this important?",
  "level": "beginner"
}
```

Backend resolves allowed factual context itself. Frontend MUST NOT send arbitrary fabricated fact context for the model to trust.

Response:
```json
{
  "text": "...",
  "based_on": [
    {"source_name": "...", "source_record_id": "..."}
  ],
  "limitations": []
}
```

---

## 17. AI / LLM Design

### 17.1 Intent parser
Input: raw user search/question.
Output structured JSON such as:
```json
{
  "intent": "explain_relationship",
  "entities": [
    {"text": "HER2", "candidate_type": "protein"},
    {"text": "breast cancer", "candidate_type": "disease"}
  ],
  "explanation_level": "beginner"
}
```

The intent parser is not allowed to assert the biological relationship. It only proposes what to resolve.

### 17.2 Explanation generator
Backend retrieves the facts first.

Model context should resemble:
```json
{
  "question": "Why is HER2 important in breast cancer?",
  "level": "beginner",
  "facts": [
    {
      "fact_id": "F1",
      "subject": "...",
      "predicate": "...",
      "object": "...",
      "source": {...}
    }
  ]
}
```

System instruction must require:
- use only supplied facts;
- do not use pretrained biological knowledge to add claims;
- cite/associate statements to fact IDs internally;
- state limitations when facts are insufficient.

### 17.3 AI provider abstraction
Implement a provider interface rather than hardcoding a single model SDK. Keep prompts/versioning under `backend/app/ai/` or `backend/app/services/explanation/`.

---

## 18. 3D Visualization Design

### 18.1 Compound viewer
Capabilities:
- load source 3D conformer/SDF where available;
- rotate;
- zoom;
- reset;
- optional representation choices;
- graceful 2D-only fallback when no 3D record is available.

### 18.2 Protein viewer
Capabilities:
- load selected PDB/mmCIF structure;
- cartoon representation default;
- surface representation option;
- stick/ball option as practical;
- reset view;
- highlight ligand if ligand metadata/selection is source-supported;
- show structure metadata without blocking rendering.

### 18.3 Guardrail
Visualization may illustrate real coordinates. It must not imply that visual proximity proves a new mechanism unless the source explicitly supports that interpretation.

---

## 19. Graph Visualization Design

Cytoscape.js graph uses normalized nodes and edges.

Recommended node categories:
- disease;
- gene/target;
- protein;
- drug/compound.

Interactions:
- hover -> concise metadata;
- click -> select;
- double-click or explicit action -> navigate to explorer;
- filter by relationship type;
- reset layout.

Avoid presenting graph edge thickness as scientific confidence unless the underlying score is explicitly mapped and labeled.

---

## 20. Caching & Demo Resilience

### 20.1 Cache layers
- normalized entity cache;
- external source response cache where terms permit;
- structure-file cache;
- explicit demo fixture/cache directory.

### 20.2 Demo cache manifest
Each demo should have a manifest containing:
- query;
- resolved IDs;
- required source payload fixtures;
- structure file(s);
- expected relationships;
- expected screenshots or smoke-test assertions where practical.

### 20.3 Runtime behavior
1. Try fresh/cache-valid application data.
2. If external source fails, use cached normalized data when available and visibly mark it as cached.
3. For demo mode, support a configuration that prioritizes known fixtures to guarantee repeatability.

---

## 21. Error Handling

Typed errors should distinguish:
- `ENTITY_NOT_FOUND`
- `SOURCE_UNAVAILABLE`
- `SOURCE_RATE_LIMITED`
- `STRUCTURE_NOT_AVAILABLE`
- `UNSUPPORTED_ENTITY_TYPE`
- `EXPLANATION_INSUFFICIENT_CONTEXT`
- `INVALID_EXTERNAL_PAYLOAD`
- `CACHE_MISS_OFFLINE`

The UI should translate these into useful states rather than raw stack traces.

---

## 22. Observability

Backend structured logs should capture:
- request ID;
- use case;
- source adapter;
- source latency;
- cache hit/miss;
- normalization errors;
- AI request metadata excluding secrets/private data;
- model latency/usage if applicable.

Do not log API keys or full sensitive headers.

---

## 23. Security

- Keep all secrets server-side.
- Provide `.env.example`, not `.env` with real values.
- Validate query lengths.
- Apply outbound timeouts.
- Restrict scientific fetches to approved hosts.
- Limit external structure download size.
- Sanitize all source text rendered as HTML.
- Avoid arbitrary URL fetch endpoints.
- Use CORS configuration appropriate to deployment.

---

## 24. Repository Structure

```text
bioverse-ai/
├── AGENTS.md
├── BIOVERSE_MASTER_SPEC.md
├── PLAN.md
├── README.md
├── .env.example
├── docker-compose.yml
├── docs/
│   ├── ARCHITECTURE.md
│   ├── DECISIONS.md
│   ├── DATA_PROVENANCE.md
│   └── DEMO_RUNBOOK.md
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── api/
│   │   │   └── v1/
│   │   ├── adapters/
│   │   │   ├── pubchem.py
│   │   │   ├── rcsb.py
│   │   │   └── opentargets.py
│   │   ├── core/
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── services/
│   │   ├── repositories/
│   │   ├── cache/
│   │   └── ai/
│   ├── tests/
│   │   ├── fixtures/
│   │   ├── unit/
│   │   ├── contract/
│   │   └── integration/
│   └── pyproject.toml
├── frontend/
│   ├── app/
│   ├── components/
│   │   ├── viewer3d/
│   │   ├── graph/
│   │   ├── search/
│   │   └── provenance/
│   ├── features/
│   ├── lib/
│   ├── types/
│   ├── tests/
│   └── package.json
└── demo_data/
    ├── manifests/
    ├── compounds/
    ├── structures/
    └── relationships/
```

---

## 25. Testing Strategy

### 25.1 Backend unit tests
- normalization functions;
- adapter parsing;
- source error mapping;
- provenance creation;
- graph building;
- explanation-context building.

### 25.2 Contract tests
For every external adapter fixture:
- parse known payload;
- validate normalized Pydantic model;
- confirm required provenance fields.

### 25.3 AI grounding tests
Must prove:
- model receives facts resolved server-side;
- arbitrary frontend-provided biology cannot become trusted fact context;
- empty facts cause insufficient-context behavior;
- explanation response retains `based_on` provenance.

### 25.4 Frontend tests
- search state;
- entity rendering;
- source chips/provenance;
- error states;
- viewer controls where testable;
- graph click/navigation.

### 25.5 E2E smoke tests
At least the three demo journeys in cached mode.

### 25.6 Live tests
Optional marker only. CI must not require live PubChem/RCSB/Open Targets availability.

---

## 26. Demo Journeys and Narrative

### Demo 1 - Aspirin
Goal: immediately show accessible molecular visualization.

Flow:
`Search Aspirin -> 3D compound -> properties -> related target/context -> source-backed explanation`

### Demo 2 - Breast cancer / HER2
Goal: show cross-domain knowledge graph and protein structure.

Flow:
`Search Breast cancer -> target network -> ERBB2/HER2 -> structure -> related drug context -> beginner explanation`

### Demo 3 - Ibuprofen similarity
Goal: show chemistry intelligence and visual exploration.

Flow:
`Search Ibuprofen -> 3D compound -> similar compounds -> select comparison -> explain visible/source-backed differences`

Important: finalize exact source-supported entities during integration testing. Never force a planned story if the APIs do not support it cleanly.

---

## 27. Milestone Implementation Plan

### Milestone 0 - Freeze specification
Deliver:
- `AGENTS.md`;
- master spec;
- `PLAN.md`;
- initial decisions log.

Done when:
- repo target and MVP are unambiguous;
- non-goals and grounding rules are explicit.

### Milestone 1 - Repository scaffold
Implement:
- frontend/backend directories;
- FastAPI health endpoint;
- Next.js landing page;
- Docker Compose;
- database connectivity;
- test/lint/typecheck commands;
- `.env.example`.

Done when:
- one command starts frontend + backend + database;
- health endpoint passes;
- CI/local checks pass.

### Milestone 2 - PubChem adapter + Compound Explorer backend
Implement:
- name resolution;
- compound normalization;
- properties;
- 2D/3D structure retrieval metadata;
- similarity endpoint;
- fixtures/tests/cache.

Done when:
- Aspirin and Ibuprofen fixtures pass contract tests;
- app API returns normalized entity with provenance.

### Milestone 3 - Compound UI + 3D molecule viewer
Implement:
- compound explorer route;
- 2D/3D viewer;
- properties;
- source panel;
- similar compound navigation.

Done when:
- Demo 1 compound segment works without live APIs in fixture mode.

### Milestone 4 - RCSB adapter + Protein Explorer backend
Implement:
- protein/structure resolution strategy;
- structure metadata;
- downloadable/renderable structure reference;
- ligands metadata where available;
- fixtures/tests.

Done when:
- at least one chosen demo protein reliably resolves to renderable structure(s).

### Milestone 5 - Protein UI + 3D macromolecular viewer
Implement:
- protein explorer;
- structure selection;
- Mol* integration;
- reset/representation controls;
- ligand highlight/focus only when supported.

Done when:
- cached structure renders reliably on the demo laptop/browser.

### Milestone 6 - Open Targets adapter + Disease Graph backend
Implement:
- disease resolution;
- target associations;
- normalized graph construction;
- source metadata;
- fixtures/tests.

Done when:
- chosen breast-cancer demo fixture produces a stable target graph.

### Milestone 7 - Disease graph UI + cross-navigation
Implement:
- Cytoscape.js graph;
- entity hover/click;
- disease -> target/protein navigation;
- provenance panel.

Done when:
- Demo 2 reaches the protein viewer from disease graph.

### Milestone 8 - Grounded AI
Implement:
- AI provider interface;
- intent parser;
- explanation-context builder;
- grounded explanation endpoint;
- beginner/scientific modes;
- provenance mapping;
- grounding tests.

Done when:
- an explanation is impossible without backend-resolved facts;
- empty facts produce a controlled limitation message.

### Milestone 9 - Visual Story Mode
Only after MVP is green.
Implement:
- scripted narrative states derived from real graph/entity data;
- smooth transitions;
- user-controlled next/back;
- no fabricated intermediate biological relationships.

### Milestone 10 - Demo hardening
Implement:
- demo cache pack;
- offline/fallback mode;
- loading/error polishing;
- performance optimization;
- demo runbook;
- E2E smoke tests.

### Milestone 11 - Deployment
Implement:
- production Docker configuration;
- hosted frontend/backend choice;
- environment docs;
- final README;
- health/readiness checks.

---

## 28. PLAN.md Template for Codex

Codex should create/update `PLAN.md` with one active milestone at a time.

```markdown
# Current Milestone
Milestone 2 - PubChem adapter

## Scope
...

## Files expected to change
...

## Implementation steps
- [ ] ...

## Validation commands
- `...`

## Acceptance criteria
- [ ] ...

## Decisions / deviations
...
```

Stop-and-fix rule: if any milestone validation fails, repair it before moving to the next milestone.

---

## 29. Coding Standards

### Python
- typed public functions;
- Pydantic models at boundaries;
- async external HTTP;
- no requests scattered through services: only adapters;
- dependency injection for adapter/cache/repository clients where practical;
- no blanket `except Exception` without rethrow/mapping/logging rationale.

### TypeScript
- strict mode;
- generated/shared API types where practical;
- no `any` in domain models without explicit justification;
- separate server-fetch logic from visual components;
- viewer libraries wrapped behind local adapter components.

### Naming
Use explicit domain names such as `CompoundEntity`, `StructureSummary`, `SourceProvenance`, `DiseaseTargetAssociation` rather than generic `Data`, `Item`, or `Result` where ambiguity matters.

---

## 30. Performance & Reliability Targets

For cached demo mode on the target laptop:
- search result target <1 second;
- entity metadata target <1 second;
- 3D structure begins display in ~2 seconds when file size allows;
- graph interactions remain smooth for demo-sized graphs;
- API failures never produce an unhandled blank page.

Live-source performance is best-effort and must expose progress/error states.

---

## 31. Visual Design Direction

Theme: premium scientific exploration / molecular universe.

Characteristics:
- dark canvas;
- high contrast text;
- one strong visualization focal point;
- subtle depth/glow effects, not excessive neon;
- restrained motion;
- source/provenance visually clear but secondary;
- avoid generic medical stock imagery and cliché DNA wallpaper.

Landing copy example:

**BIOVERSE AI**  
*Explore life in 3D.*  
`Drugs • Proteins • Genes • Diseases`

Search placeholder:
`Search aspirin, EGFR, breast cancer...`

---

## 32. Scientific/Medical Safety Copy

BioVerse is an educational and research exploration tool. It must not present outputs as diagnosis, treatment advice, or individualized medical guidance.

When clinical topics appear, UI footer/help text should clarify that relationships and explanations are derived from public scientific data and are not medical advice.

---

## 33. Decision Log - Initial Decisions

1. Product name: BioVerse AI.
2. Visual-first exploration is prioritized over broad feature count.
3. Initial sources: PubChem, RCSB PDB, Open Targets.
4. LLM is a grounding-controlled explanation/intention layer, not a scientific fact source.
5. Next.js + TypeScript frontend; FastAPI backend.
6. 3D viewer and graph are MVP components.
7. Demo/offline cache is mandatory.
8. No autonomous multi-agent system for MVP.
9. No docking/efficacy prediction/clinical recommendation.
10. Work proceeds milestone-by-milestone through Codex with tests before progression.

---

## 34. First Prompt to Give Codex in VS Code

Use this after placing `AGENTS.md` and `BIOVERSE_MASTER_SPEC.md` at the repository root:

```text
Read AGENTS.md and BIOVERSE_MASTER_SPEC.md completely before making any changes.

This is a new BioVerse AI repository. Start with Milestone 0 and Milestone 1 only. Do not implement PubChem, RCSB, Open Targets, AI features, 3D viewers, or disease graphs yet.

Tasks:
1. Inspect the current workspace and report any existing files that conflict with the target structure.
2. Create PLAN.md for Milestone 1 with concrete steps, files, validation commands, and acceptance criteria.
3. Scaffold the repository according to the master specification:
   - Next.js + TypeScript frontend
   - FastAPI Python backend
   - PostgreSQL via Docker Compose
   - .env.example
   - backend /health endpoint
   - minimal premium dark BioVerse landing page
   - backend pytest setup
   - frontend lint/typecheck/test setup
4. Add docs/DECISIONS.md and docs/ARCHITECTURE.md reflecting only decisions already frozen in the master spec.
5. Run the relevant install/build/lint/typecheck/test/health validations.
6. Fix every failure before declaring the milestone complete.

Constraints:
- Do not add features outside Milestone 1.
- Do not choose additional scientific databases.
- Do not hardcode secrets.
- Keep the frontend/backend boundaries ready for later adapter-based integrations.
- Preserve AGENTS.md and BIOVERSE_MASTER_SPEC.md as authoritative project instructions.

At the end, give a concise completion report containing:
- files created/modified;
- commands run and whether they passed;
- architecture decisions made;
- any blockers;
- the exact recommended next milestone, but do not implement it yet.
```

---

## 35. Definition of MVP Done

BioVerse MVP is done only when all of these work in cached/demo mode:

- [ ] Search Aspirin/Ibuprofen and render a compound explorer.
- [ ] Render at least one compound in interactive 3D.
- [ ] Show real, sourced compound properties.
- [ ] Show real, sourced similar compounds.
- [ ] Search/open at least one demo protein/target.
- [ ] Render at least one real protein structure interactively.
- [ ] Search/open the chosen disease demo.
- [ ] Render a real source-derived disease-target graph.
- [ ] Navigate from disease -> target/protein -> structure.
- [ ] Produce beginner and scientific explanations from retrieved facts only.
- [ ] Display provenance for key facts.
- [ ] Fail gracefully when a source is offline.
- [ ] Three demo journeys pass E2E smoke checks.
- [ ] No secrets are committed.
- [ ] Backend tests/lint/type checks pass.
- [ ] Frontend tests/lint/type checks/build pass.

---

## 36. Final Instruction to Codex

When implementation convenience conflicts with scientific grounding, **scientific grounding wins**.

When adding more features conflicts with demo reliability, **demo reliability wins**.

When advanced terminology conflicts with first-time comprehensibility, **progressive disclosure wins**.

BioVerse should look impressive because it connects and visualizes real biology well - not because it fabricates intelligence.

# BioVerse AI Data Provenance

## Approved implemented sources

PubChem PUG REST supplies compound data. RCSB PDB Search, Data, and file-download services supply experimental protein/structure data. Open Targets, AI-generated explanations, and other biological sources are not active. The backend uses fixed approved HTTPS hosts; clients cannot supply an upstream host or URL.

## Normalized compound provenance

Each normalized compound carries:

- `source`: `pubchem`
- `source_id`: the PubChem CID as text
- `source_url`: the reconstructable PubChem compound page
- `provenance[]`: source name, CID, URL, retrieval timestamp, and PubChem field path

The CID always receives provenance. Each populated property receives its own field entry. Optional values absent from PubChem remain null and do not receive a property provenance entry. BioVerse does not infer or fill molecular formulae, weights, SMILES, InChI, logP, hydrogen-bond counts, polar surface area, titles, or conformer availability.

Current normalization maps PubChem `ConnectivitySMILES` to `canonical_smiles` and PubChem `SMILES` to `isomeric_smiles`, following the current PUG REST property vocabulary. PubChem `ConformerCount3D > 0` controls `has_3d_conformer` and whether a 3D structure reference is present.

## Structure and similarity provenance

The 2D PNG and 3D SDF endpoints proxy bytes retrieved from PubChem for a validated CID. The backend enforces content-type and size limits. A missing 3D conformer returns `STRUCTURE_NOT_AVAILABLE`; no fallback geometry is generated.

Similar-compound results use PubChem's `fastsimilarity_2d` operation. The response records the requested threshold and limit, excludes the query compound itself, and normalizes returned CIDs through the same property and provenance pipeline.

## Retrieval, caching, and failures

Successful responses are cached in memory with a bounded size and TTL. Cache hits retain the timestamp and provenance from the original source retrieval. Timeouts, throttling, source unavailability, missing records, invalid payloads, and missing structures are never converted into scientific values and are not cached.

Tests use captured PubChem fixtures so CI does not depend on live scientific services. A separately marked opt-in integration suite checks the current live source contract for aspirin, ibuprofen, and caffeine.

## RCSB protein provenance

Each `ProteinEntity` corresponds to an RCSB polymer-entity identifier, not to an inferred gene record. It carries `source=rcsb_pdb`, the polymer entity ID, parent PDB ID, RCSB structure URL, retrieval timestamp, and field-level provenance.

Protein names, polymer types, lengths, author/label chain identifiers, organisms, source gene names, and external references appear only when present in the selected RCSB Data API response. User search text is retained only as response query metadata and never becomes a scientific name or symbol.

The associated structure summary is built mechanically from the polymer entity's parent entry. Its provenance points to the exact entry fields used.

## RCSB structure provenance

Each `StructureEntity` records the PDB ID and RCSB entry URL plus provenance for populated entry fields, including title, experimental method, resolution, accession dates, status, and entity/assembly counts.

- RCSB `exptl[].method` is preserved as a tuple of source strings.
- The first reported value in `rcsb_entry_info.resolution_combined` maps mechanically to nullable `resolution_angstroms`. Missing resolution stays null and is valid.
- Polymer descriptions, types, lengths, organisms, reference identifiers, and chain arrays retain entity-level provenance.
- Non-polymer entities become `LigandEntity` records with chemical component and chain/asym context. This naming does not add a mechanistic binding claim.
- Assemblies retain source IDs and reported details only.

BioVerse does not calculate quality scores, choose a scientifically "best" structure, infer protein function, infer ligand affinity, or map an RCSB ligand to PubChem.

## RCSB structure files

The mmCIF endpoint proxies bytes from `https://files.rcsb.org/download/{pdb_id}.cif`. Bytes are not parsed, rewritten, minimized, or otherwise modified. The adapter validates the fixed host/path, PDB identifier, status, known RCSB content type, timeout, and configured maximum byte size. The BioVerse response is labeled `chemical/x-mmcif` for a stable future-viewer contract.

## RCSB cache and fixtures

Successful searches, structure details, and mmCIF resources use bounded process-local TTL caches. Ligand responses derive from cached structure details. Cached normalized objects keep the initial retrieval timestamps. Failures and malformed payloads are not cached.

Automated tests use captured RCSB fixtures for `1M17` and `1D3Z`. The opt-in live suite checks EGFR search, the ligand-containing `1M17` entry, the resolution-null/ligand-free solution-NMR entry `1D3Z`, and the unmodified `1M17` mmCIF file.

export type ScientificSource = "pubchem" | "rcsb_pdb";

export interface SourceProvenance {
  source_name: ScientificSource;
  source_record_id: string;
  source_url: string;
  retrieved_at: string;
  field_path: string;
}

export interface StructureReference {
  dimension: "2d" | "3d";
  format: "png" | "sdf";
  endpoint: string;
}

export interface CompoundEntity {
  id: string;
  type: "compound";
  source: "pubchem";
  source_id: string;
  cid: number;
  name: string | null;
  external_ids: { pubchem_cid: string };
  molecular_formula: string | null;
  molecular_weight: number | null;
  canonical_smiles: string | null;
  isomeric_smiles: string | null;
  inchi: string | null;
  inchikey: string | null;
  xlogp: number | null;
  hydrogen_bond_donor_count: number | null;
  hydrogen_bond_acceptor_count: number | null;
  tpsa: number | null;
  has_3d_conformer: boolean;
  structure_2d: StructureReference;
  structure_3d: StructureReference | null;
  source_url: string;
  provenance: SourceProvenance[];
}

export interface CompoundSearchResponse {
  query: string;
  results: CompoundEntity[];
}

export interface ExternalReference {
  database_name: string;
  database_accession: string;
}

export interface StructureSummary {
  id: string;
  type: "structure";
  source: "rcsb_pdb";
  pdb_id: string;
  title: string | null;
  experimental_methods: string[];
  resolution_angstroms: number | null;
  release_date: string | null;
  detail_endpoint: string;
  provenance: SourceProvenance[];
}

export interface ProteinEntity {
  id: string;
  type: "protein";
  source: "rcsb_pdb";
  source_id: string;
  name: string | null;
  gene_symbols: string[];
  pdb_id: string;
  entity_id: string;
  polymer_type: string | null;
  sequence_length: number | null;
  auth_chain_ids: string[];
  asym_ids: string[];
  source_organisms: string[];
  external_references: ExternalReference[];
  associated_structures: StructureSummary[];
  source_url: string;
  provenance: SourceProvenance[];
}

export interface ProteinSearchResponse {
  query: string;
  results: ProteinEntity[];
}

export interface ChainIdentifiers {
  entity_id: string;
  auth_chain_ids: string[];
  asym_ids: string[];
}

export interface PolymerEntity {
  source_id: string;
  entity_id: string;
  description: string | null;
  polymer_type: string | null;
  sequence_length: number | null;
  chains: ChainIdentifiers;
  source_organisms: string[];
  external_references: ExternalReference[];
  provenance: SourceProvenance[];
}

export interface LigandEntity {
  id: string;
  type: "ligand";
  source: "rcsb_pdb";
  source_id: string;
  pdb_id: string;
  entity_id: string;
  chemical_component_id: string;
  name: string | null;
  formula: string | null;
  molecular_weight: number | null;
  auth_chain_ids: string[];
  asym_ids: string[];
  source_url: string;
  provenance: SourceProvenance[];
}

export interface AssemblySummary {
  source_id: string;
  assembly_id: string;
  details: string | null;
  method_details: string | null;
  provenance: SourceProvenance[];
}

export interface MacromolecularStructureReference {
  format: "mmcif";
  endpoint: string;
  source_url: string;
}

export interface StructureEntity {
  id: string;
  type: "structure";
  source: "rcsb_pdb";
  source_id: string;
  pdb_id: string;
  title: string | null;
  experimental_methods: string[];
  resolution_angstroms: number | null;
  deposition_date: string | null;
  release_date: string | null;
  revision_date: string | null;
  entry_status: string | null;
  polymer_entity_count: number | null;
  nonpolymer_entity_count: number | null;
  assembly_count: number | null;
  polymer_entities: PolymerEntity[];
  chains: ChainIdentifiers[];
  ligands: LigandEntity[];
  assemblies: AssemblySummary[];
  structure_reference: MacromolecularStructureReference;
  source_url: string;
  provenance: SourceProvenance[];
}

export interface ErrorDetail {
  code: string;
  message: string;
  source: string | null;
  retryable: boolean;
}

export interface ErrorResponse {
  error: ErrorDetail;
}

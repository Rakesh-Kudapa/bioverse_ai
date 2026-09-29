import { fireEvent, render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import Home from "@/app/page";
import { CompoundExplorer } from "@/components/compound/compound-explorer";
import { ProteinResults } from "@/components/protein/protein-results";
import { StructureExplorer } from "@/components/protein/structure-explorer";
import { ProvenancePanel } from "@/components/provenance/provenance-panel";
import { SearchResults } from "@/components/search/search-results";
import { bioverseApi } from "@/lib/api";
import type { CompoundEntity, ProteinEntity, SourceProvenance, StructureEntity } from "@/types/bioverse";

const push = vi.fn();
vi.mock("next/navigation", () => ({ useRouter: () => ({ push }) }));
vi.mock("next/image", () => ({ default: ({ alt, onLoad }: { alt: string; onLoad?: () => void }) => <button aria-label={alt} onClick={onLoad}>2D image</button> }));
vi.mock("@/components/molecular-viewer/molecule-viewer", () => ({ MoleculeViewer: ({ name }: { name: string }) => <div>3D molecule for {name}</div> }));
vi.mock("@/components/protein-viewer/protein-structure-viewer", () => ({ ProteinStructureViewer: ({ pdbId }: { pdbId: string }) => <div>Molstar structure {pdbId}</div> }));

const provenance: SourceProvenance[] = [{
  source_name: "pubchem",
  source_record_id: "2244",
  source_url: "https://pubchem.ncbi.nlm.nih.gov/compound/2244",
  retrieved_at: "2026-09-29T00:00:00Z",
  field_path: "PropertyTable.Properties[0].Title",
}];

const aspirin: CompoundEntity = {
  id: "compound:pubchem:2244", type: "compound", source: "pubchem", source_id: "2244", cid: 2244,
  name: "Aspirin", external_ids: { pubchem_cid: "2244" }, molecular_formula: "C9H8O4", molecular_weight: 180.16,
  canonical_smiles: "CC(=O)OC1=CC=CC=C1C(=O)O", isomeric_smiles: "CC(=O)OC1=CC=CC=C1C(=O)O",
  inchi: "InChI=1S/C9H8O4", inchikey: "BSYNRYMUTXBXSQ-UHFFFAOYSA-N", xlogp: 1.2,
  hydrogen_bond_donor_count: 1, hydrogen_bond_acceptor_count: 4, tpsa: 63.6, has_3d_conformer: true,
  structure_2d: { dimension: "2d", format: "png", endpoint: "/api/v1/compounds/2244/structure/2d" },
  structure_3d: { dimension: "3d", format: "sdf", endpoint: "/api/v1/compounds/2244/structure/3d" },
  source_url: provenance[0].source_url, provenance,
};

const proteinProvenance: SourceProvenance[] = [{ ...provenance[0], source_name: "rcsb_pdb", source_record_id: "1M17_1", source_url: "https://www.rcsb.org/structure/1M17", field_path: "data.polymer_entities[0]" }];
const egfr: ProteinEntity = {
  id: "protein:rcsb_pdb:1M17_1", type: "protein", source: "rcsb_pdb", source_id: "1M17_1", name: "Epidermal growth factor receptor",
  gene_symbols: ["EGFR"], pdb_id: "1M17", entity_id: "1", polymer_type: "Protein", sequence_length: 333,
  auth_chain_ids: ["A"], asym_ids: ["A"], source_organisms: ["Homo sapiens"], external_references: [], source_url: proteinProvenance[0].source_url,
  associated_structures: [{ id: "structure:rcsb_pdb:1M17", type: "structure", source: "rcsb_pdb", pdb_id: "1M17", title: "EGFR kinase domain", experimental_methods: ["X-RAY DIFFRACTION"], resolution_angstroms: 2.6, release_date: "2002-09-04", detail_endpoint: "/api/v1/structures/1M17", provenance: proteinProvenance }],
  provenance: proteinProvenance,
};

function structure({ resolution = 2.6, ligands = true }: { resolution?: number | null; ligands?: boolean } = {}): StructureEntity {
  return {
    id: "structure:rcsb_pdb:1M17", type: "structure", source: "rcsb_pdb", source_id: "1M17", pdb_id: resolution === null ? "1D3Z" : "1M17",
    title: resolution === null ? "UBIQUITIN" : "EGFR kinase domain", experimental_methods: [resolution === null ? "SOLUTION NMR" : "X-RAY DIFFRACTION"], resolution_angstroms: resolution,
    deposition_date: null, release_date: "2002-09-04", revision_date: null, entry_status: "REL", polymer_entity_count: 1, nonpolymer_entity_count: ligands ? 1 : 0, assembly_count: 1,
    polymer_entities: [{ source_id: "1M17_1", entity_id: "1", description: "EGFR kinase domain", polymer_type: "Protein", sequence_length: 333, chains: { entity_id: "1", auth_chain_ids: ["A"], asym_ids: ["A"] }, source_organisms: ["Homo sapiens"], external_references: [], provenance: proteinProvenance }],
    chains: [{ entity_id: "1", auth_chain_ids: ["A"], asym_ids: ["A"] }],
    ligands: ligands ? [{ id: "ligand:rcsb_pdb:1M17:AQ4", type: "ligand", source: "rcsb_pdb", source_id: "1M17_2", pdb_id: "1M17", entity_id: "2", chemical_component_id: "AQ4", name: "QUINAZOLINE INHIBITOR", formula: "C16 H16 N4 O", molecular_weight: 280.33, auth_chain_ids: ["A"], asym_ids: ["B"], source_url: proteinProvenance[0].source_url, provenance: proteinProvenance }] : [],
    assemblies: [], structure_reference: { format: "mmcif", endpoint: "/api/v1/structures/1M17/file", source_url: "https://files.rcsb.org/download/1M17.cif" }, source_url: proteinProvenance[0].source_url, provenance: proteinProvenance,
  };
}

describe("BioVerse visual explorer", () => {
  beforeEach(() => { vi.restoreAllMocks(); push.mockReset(); });

  it("provides a functional deterministic landing search", () => {
    render(<Home />);
    fireEvent.change(screen.getByRole("searchbox", { name: /search bioverse/i }), { target: { value: "aspirin" } });
    fireEvent.click(screen.getByRole("button", { name: /explore/i }));
    expect(push).toHaveBeenCalledWith("/explore?q=aspirin");
    expect(screen.getByText(/not medical advice/i)).toBeInTheDocument();
  });

  it("renders typed compound and protein search results", async () => {
    vi.spyOn(bioverseApi, "searchCompounds").mockResolvedValue({ query: "EGFR", results: [aspirin] });
    vi.spyOn(bioverseApi, "searchProteins").mockResolvedValue({ query: "EGFR", results: [egfr] });
    render(<SearchResults query="EGFR" />);
    expect(screen.getByText(/Searching BioVerse/i)).toBeInTheDocument();
    expect(await screen.findByText("Aspirin")).toBeInTheDocument();
    expect(screen.getByText("Epidermal growth factor receptor")).toBeInTheDocument();
    expect(screen.getByText(/source order does not indicate/i)).toBeInTheDocument();
  });

  it("renders compound detail, PubChem properties, 2D label, and the 3D viewer", async () => {
    vi.spyOn(bioverseApi, "getCompound").mockResolvedValue(aspirin);
    render(<CompoundExplorer cid={2244} />);
    expect(await screen.findByRole("heading", { name: "Aspirin" })).toBeInTheDocument();
    expect(screen.getByText("C9H8O4")).toBeInTheDocument();
    expect(screen.getByLabelText(/PubChem 2D molecular structure for Aspirin/i)).toBeInTheDocument();
    expect(await screen.findByText("3D molecule for Aspirin")).toBeInTheDocument();
  });

  it("handles missing compound fields and unavailable 3D without hiding 2D data", async () => {
    vi.spyOn(bioverseApi, "getCompound").mockResolvedValue({ ...aspirin, xlogp: null, has_3d_conformer: false, structure_3d: null });
    render(<CompoundExplorer cid={2244} />);
    expect(await screen.findByText("No 3D conformer")).toBeInTheDocument();
    expect(screen.getAllByText("Not reported").length).toBeGreaterThan(0);
    expect(screen.getByLabelText(/2D molecular structure/i)).toBeInTheDocument();
  });

  it("renders protein search metadata and selection", async () => {
    vi.spyOn(bioverseApi, "searchProteins").mockResolvedValue({ query: "EGFR", results: [egfr] });
    render(<ProteinResults query="EGFR" />);
    expect(await screen.findByText("EGFR kinase domain")).toBeInTheDocument();
    expect(screen.getByText("2.6 Å")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /explore structure/i })).toHaveAttribute("href", "/structure/1M17");
  });

  it("renders structure metadata, AQ4 ligand facts, and provenance", async () => {
    vi.spyOn(bioverseApi, "getStructure").mockResolvedValue(structure());
    render(<StructureExplorer pdbId="1M17" />);
    expect(await screen.findByText("Molstar structure 1M17")).toBeInTheDocument();
    expect(screen.getByText("X-RAY DIFFRACTION")).toBeInTheDocument();
    expect(screen.getByText("AQ4")).toBeInTheDocument();
    expect(screen.getByText("QUINAZOLINE INHIBITOR")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /open source record/i })).toBeInTheDocument();
  });

  it("shows missing resolution and no-ligand states for a source-grounded NMR record", async () => {
    vi.spyOn(bioverseApi, "getStructure").mockResolvedValue(structure({ resolution: null, ligands: false }));
    render(<StructureExplorer pdbId="1D3Z" />);
    expect(await screen.findByText("SOLUTION NMR")).toBeInTheDocument();
    expect(screen.getAllByText("Not reported").length).toBeGreaterThan(0);
    expect(screen.getByText(/No bound non-polymer ligands were reported/i)).toBeInTheDocument();
  });

  it("renders a controlled API error without a stack trace", async () => {
    vi.spyOn(bioverseApi, "searchCompounds").mockRejectedValue(new Error("network"));
    vi.spyOn(bioverseApi, "searchProteins").mockResolvedValue({ query: "missing", results: [] });
    render(<SearchResults query="missing" />);
    expect(await screen.findByText("Compound search unavailable")).toBeInTheDocument();
    expect(screen.queryByText(/Error: network/)).not.toBeInTheDocument();
  });

  it("displays reusable field-level provenance", () => {
    render(<ProvenancePanel source="pubchem" sourceId="2244" sourceUrl={provenance[0].source_url} provenance={provenance} />);
    expect(screen.getByRole("heading", { name: "PubChem" })).toBeInTheDocument();
    expect(screen.getByText("CID 2244")).toBeInTheDocument();
    fireEvent.click(screen.getByText("Field provenance"));
    expect(screen.getByText("PropertyTable.Properties[0].Title")).toBeInTheDocument();
  });
});

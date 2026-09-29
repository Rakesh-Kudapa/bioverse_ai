from datetime import UTC, datetime
from typing import Literal

from app.core.errors import BioVerseError, EntityNotFoundError
from app.models.compound import CompoundEntity, SourceProvenance, StructureReference
from app.models.ligand import LigandEntity
from app.models.protein import ExternalReference, ProteinEntity, StructureSummary
from app.models.provenance import SourceProvenance as SharedSourceProvenance
from app.models.resource import BinaryResource
from app.models.structure import (
    AssemblySummary,
    ChainIdentifiers,
    MacromolecularStructureReference,
    PolymerEntity,
    StructureEntity,
)


def make_compound(
    cid: int = 2244,
    *,
    name: str = "Aspirin",
    has_3d_conformer: bool = True,
) -> CompoundEntity:
    source_id = str(cid)
    source_url = f"https://pubchem.ncbi.nlm.nih.gov/compound/{cid}"
    return CompoundEntity(
        id=f"compound:pubchem:{cid}",
        source_id=source_id,
        cid=cid,
        name=name,
        external_ids={"pubchem_cid": source_id},
        molecular_formula="C9H8O4",
        molecular_weight=180.16,
        canonical_smiles="CC(=O)OC1=CC=CC=C1C(=O)O",
        isomeric_smiles="CC(=O)OC1=CC=CC=C1C(=O)O",
        inchi=None,
        inchikey=None,
        xlogp=None,
        hydrogen_bond_donor_count=None,
        hydrogen_bond_acceptor_count=None,
        tpsa=None,
        has_3d_conformer=has_3d_conformer,
        structure_2d=StructureReference(
            dimension="2d",
            format="png",
            endpoint=f"/api/v1/compounds/{cid}/structure/2d",
        ),
        structure_3d=(
            StructureReference(
                dimension="3d",
                format="sdf",
                endpoint=f"/api/v1/compounds/{cid}/structure/3d",
            )
            if has_3d_conformer
            else None
        ),
        source_url=source_url,
        provenance=(
            SourceProvenance(
                source_name="pubchem",
                source_record_id=source_id,
                source_url=source_url,
                retrieved_at=datetime(2026, 9, 28, tzinfo=UTC),
                field_path="PropertyTable.Properties[].CID",
            ),
        ),
    )


class FakePubChemGateway:
    def __init__(self, compounds: tuple[CompoundEntity, ...]) -> None:
        self.compounds = {compound.cid: compound for compound in compounds}
        self.resolve_result = tuple(self.compounds)
        self.similar_result: tuple[int, ...] = ()
        self.resolve_error: BioVerseError | None = None
        self.resolve_calls = 0
        self.fetch_compound_calls = 0
        self.fetch_similarity_calls = 0
        self.fetch_structure_calls = 0

    async def resolve_name(self, _name: str) -> tuple[int, ...]:
        self.resolve_calls += 1
        if self.resolve_error is not None:
            raise self.resolve_error
        return self.resolve_result

    async def fetch_compounds(self, cids: tuple[int, ...]) -> tuple[CompoundEntity, ...]:
        self.fetch_compound_calls += 1
        compounds = tuple(self.compounds[cid] for cid in cids if cid in self.compounds)
        if not compounds:
            raise EntityNotFoundError("Compound not found.", source="pubchem")
        return compounds

    async def fetch_similar_cids(
        self,
        _cid: int,
        *,
        threshold: int,
        limit: int,
    ) -> tuple[int, ...]:
        del threshold
        self.fetch_similarity_calls += 1
        return self.similar_result[:limit]

    async def fetch_structure(
        self,
        cid: int,
        dimension: Literal["2d", "3d"],
    ) -> BinaryResource:
        self.fetch_structure_calls += 1
        if dimension == "2d":
            return BinaryResource(b"\x89PNG\r\nfixture", "image/png", f"pubchem-{cid}-2d.png")
        return BinaryResource(
            b"fixture sdf",
            "chemical/x-mdl-sdfile",
            f"pubchem-{cid}-3d.sdf",
        )

    async def aclose(self) -> None:
        return None


def make_rcsb_provenance(
    source_id: str = "1M17",
    *,
    field_path: str = "entry.rcsb_id",
) -> SharedSourceProvenance:
    return SharedSourceProvenance(
        source_name="rcsb_pdb",
        source_record_id=source_id,
        source_url="https://www.rcsb.org/structure/1M17",
        retrieved_at=datetime(2026, 9, 28, tzinfo=UTC),
        field_path=field_path,
    )


def make_protein() -> ProteinEntity:
    provenance = (make_rcsb_provenance("1M17_1", field_path="polymer_entities[].rcsb_id"),)
    summary = StructureSummary(
        id="structure:pdb:1M17",
        pdb_id="1M17",
        title="EGFR kinase domain with erlotinib",
        experimental_methods=("X-RAY DIFFRACTION",),
        resolution_angstroms=2.6,
        release_date="2002-09-04T00:00:00Z",
        detail_endpoint="/api/v1/structures/1M17",
        provenance=(make_rcsb_provenance(),),
    )
    return ProteinEntity(
        id="protein:rcsb:1M17_1",
        source_id="1M17_1",
        name="epidermal growth factor receptor",
        gene_symbols=("egfr",),
        pdb_id="1M17",
        entity_id="1",
        polymer_type="Protein",
        sequence_length=333,
        auth_chain_ids=("A",),
        asym_ids=("A",),
        source_organisms=("Homo sapiens",),
        external_references=(
            ExternalReference(database_name="UniProt", database_accession="P00533"),
        ),
        associated_structures=(summary,),
        source_url="https://www.rcsb.org/structure/1M17",
        provenance=provenance,
    )


def make_structure(*, with_ligand: bool = True) -> StructureEntity:
    chain = ChainIdentifiers(entity_id="1", auth_chain_ids=("A",), asym_ids=("A",))
    polymer = PolymerEntity(
        source_id="1M17_1",
        entity_id="1",
        description="epidermal growth factor receptor",
        polymer_type="Protein",
        sequence_length=333,
        chains=chain,
        source_organisms=("Homo sapiens",),
        external_references=(
            ExternalReference(database_name="UniProt", database_accession="P00533"),
        ),
        provenance=(make_rcsb_provenance("1M17_1"),),
    )
    ligands = (
        (
            LigandEntity(
                id="ligand:rcsb:1M17_2",
                source_id="1M17_2",
                pdb_id="1M17",
                entity_id="2",
                chemical_component_id="AQ4",
                name="ERLOTINIB COMPONENT",
                formula="C22 H23 N3 O4",
                molecular_weight=393.436,
                auth_chain_ids=("A",),
                asym_ids=("B",),
                source_url="https://www.rcsb.org/structure/1M17",
                provenance=(make_rcsb_provenance("1M17_2"),),
            ),
        )
        if with_ligand
        else ()
    )
    assembly = AssemblySummary(
        source_id="1M17-1",
        assembly_id="1",
        details="author_defined_assembly",
        provenance=(make_rcsb_provenance("1M17-1"),),
    )
    return StructureEntity(
        id="structure:pdb:1M17",
        source_id="1M17",
        pdb_id="1M17",
        title="EGFR kinase domain with erlotinib",
        experimental_methods=("X-RAY DIFFRACTION",),
        resolution_angstroms=2.6,
        deposition_date="2002-06-17T00:00:00Z",
        release_date="2002-09-04T00:00:00Z",
        revision_date="2024-02-14T00:00:00Z",
        entry_status="REL",
        polymer_entity_count=1,
        nonpolymer_entity_count=len(ligands),
        assembly_count=1,
        polymer_entities=(polymer,),
        chains=(chain,),
        ligands=ligands,
        assemblies=(assembly,),
        structure_reference=MacromolecularStructureReference(
            endpoint="/api/v1/structures/1M17/file",
            source_url="https://files.rcsb.org/download/1M17.cif",
        ),
        source_url="https://www.rcsb.org/structure/1M17",
        provenance=(make_rcsb_provenance(),),
    )


class FakeRcsbGateway:
    def __init__(self) -> None:
        self.proteins: tuple[ProteinEntity, ...] = (make_protein(),)
        self.structure: StructureEntity = make_structure()
        self.search_error: BioVerseError | None = None
        self.structure_error: BioVerseError | None = None
        self.search_calls = 0
        self.structure_calls = 0
        self.file_calls = 0

    async def search_proteins(self, _query: str) -> tuple[ProteinEntity, ...]:
        self.search_calls += 1
        if self.search_error:
            raise self.search_error
        return self.proteins

    async def fetch_structure(self, _pdb_id: str) -> StructureEntity:
        self.structure_calls += 1
        if self.structure_error:
            raise self.structure_error
        return self.structure

    async def fetch_structure_file(self, pdb_id: str) -> BinaryResource:
        self.file_calls += 1
        return BinaryResource(
            b"data_1M17\n#\n",
            "chemical/x-mmcif",
            f"{pdb_id}.cif",
        )

    @staticmethod
    def normalize_pdb_id(pdb_id: str) -> str:
        return pdb_id.strip().upper()

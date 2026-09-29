from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, HttpUrl

from app.models.ligand import LigandEntity
from app.models.protein import ExternalReference
from app.models.provenance import SourceProvenance


class ChainIdentifiers(BaseModel):
    """Source chain identifiers grouped by their polymer entity."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    entity_id: str
    auth_chain_ids: tuple[str, ...]
    asym_ids: tuple[str, ...]


class PolymerEntity(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    source_id: str
    entity_id: str
    description: str | None = None
    polymer_type: str | None = None
    sequence_length: int | None = Field(default=None, ge=0)
    chains: ChainIdentifiers
    source_organisms: tuple[str, ...]
    external_references: tuple[ExternalReference, ...]
    provenance: tuple[SourceProvenance, ...]


class AssemblySummary(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    source_id: str
    assembly_id: str
    details: str | None = None
    method_details: str | None = None
    provenance: tuple[SourceProvenance, ...]


class MacromolecularStructureReference(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    format: Literal["mmcif"] = "mmcif"
    endpoint: str
    source_url: HttpUrl


class StructureEntity(BaseModel):
    """Normalized structural facts for a released RCSB PDB entry."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    type: Literal["structure"] = "structure"
    source: Literal["rcsb_pdb"] = "rcsb_pdb"
    source_id: str
    pdb_id: str
    title: str | None = None
    experimental_methods: tuple[str, ...]
    resolution_angstroms: float | None = Field(default=None, gt=0)
    deposition_date: str | None = None
    release_date: str | None = None
    revision_date: str | None = None
    entry_status: str | None = None
    polymer_entity_count: int | None = Field(default=None, ge=0)
    nonpolymer_entity_count: int | None = Field(default=None, ge=0)
    assembly_count: int | None = Field(default=None, ge=0)
    polymer_entities: tuple[PolymerEntity, ...]
    chains: tuple[ChainIdentifiers, ...]
    ligands: tuple[LigandEntity, ...]
    assemblies: tuple[AssemblySummary, ...]
    structure_reference: MacromolecularStructureReference
    source_url: HttpUrl
    provenance: tuple[SourceProvenance, ...]

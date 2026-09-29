from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, HttpUrl

from app.models.provenance import SourceProvenance


class ExternalReference(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    database_name: str
    database_accession: str


class StructureSummary(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    type: Literal["structure"] = "structure"
    source: Literal["rcsb_pdb"] = "rcsb_pdb"
    pdb_id: str
    title: str | None = None
    experimental_methods: tuple[str, ...]
    resolution_angstroms: float | None = None
    release_date: str | None = None
    detail_endpoint: str
    provenance: tuple[SourceProvenance, ...]


class ProteinEntity(BaseModel):
    """A source-reported RCSB polymer entity, never an inferred gene record."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    type: Literal["protein"] = "protein"
    source: Literal["rcsb_pdb"] = "rcsb_pdb"
    source_id: str
    name: str | None = None
    gene_symbols: tuple[str, ...]
    pdb_id: str
    entity_id: str
    polymer_type: str | None = None
    sequence_length: int | None = Field(default=None, ge=0)
    auth_chain_ids: tuple[str, ...]
    asym_ids: tuple[str, ...]
    source_organisms: tuple[str, ...]
    external_references: tuple[ExternalReference, ...]
    associated_structures: tuple[StructureSummary, ...]
    source_url: HttpUrl
    provenance: tuple[SourceProvenance, ...]

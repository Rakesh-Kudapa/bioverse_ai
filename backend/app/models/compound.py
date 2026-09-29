from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, HttpUrl

from app.models.provenance import SourceProvenance as SourceProvenance


class StructureReference(BaseModel):
    """A BioVerse-owned route for source-derived structure content."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    dimension: Literal["2d", "3d"]
    format: Literal["png", "sdf"]
    endpoint: str


class CompoundEntity(BaseModel):
    """Normalized compound facts owned by the BioVerse API contract."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    type: Literal["compound"] = "compound"
    source: Literal["pubchem"] = "pubchem"
    source_id: str
    cid: int = Field(gt=0)
    name: str | None = None
    external_ids: dict[Literal["pubchem_cid"], str]
    molecular_formula: str | None = None
    molecular_weight: float | None = None
    canonical_smiles: str | None = None
    isomeric_smiles: str | None = None
    inchi: str | None = None
    inchikey: str | None = None
    xlogp: float | None = None
    hydrogen_bond_donor_count: int | None = None
    hydrogen_bond_acceptor_count: int | None = None
    tpsa: float | None = None
    has_3d_conformer: bool
    structure_2d: StructureReference
    structure_3d: StructureReference | None = None
    source_url: HttpUrl
    provenance: tuple[SourceProvenance, ...]

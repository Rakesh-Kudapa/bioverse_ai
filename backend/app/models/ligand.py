from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, HttpUrl

from app.models.provenance import SourceProvenance


class LigandEntity(BaseModel):
    """A non-polymer chemical entity reported for one PDB entry."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    type: Literal["ligand"] = "ligand"
    source: Literal["rcsb_pdb"] = "rcsb_pdb"
    source_id: str
    pdb_id: str
    entity_id: str
    chemical_component_id: str
    name: str | None = None
    formula: str | None = None
    molecular_weight: float | None = Field(default=None, ge=0)
    auth_chain_ids: tuple[str, ...]
    asym_ids: tuple[str, ...]
    source_url: HttpUrl
    provenance: tuple[SourceProvenance, ...]

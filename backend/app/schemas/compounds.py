from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.models.compound import CompoundEntity, SourceProvenance


class CompoundSearchResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    query: str
    results: tuple[CompoundEntity, ...]


class SimilarityQuery(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    source: Literal["pubchem"] = "pubchem"
    source_record_id: str
    algorithm: Literal["pubchem_2d_tanimoto"] = "pubchem_2d_tanimoto"
    threshold: int = Field(ge=0, le=100)
    limit: int = Field(ge=1, le=25)


class SimilarCompoundsResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    query: SimilarityQuery
    results: tuple[CompoundEntity, ...]
    provenance: SourceProvenance

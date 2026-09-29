from pydantic import BaseModel, ConfigDict

from app.models.protein import ProteinEntity


class ProteinSearchResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    query: str
    results: tuple[ProteinEntity, ...]

from pydantic import BaseModel, ConfigDict

from app.models.ligand import LigandEntity


class LigandListResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    pdb_id: str
    results: tuple[LigandEntity, ...]

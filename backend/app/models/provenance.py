from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, HttpUrl


class SourceProvenance(BaseModel):
    """Trace one normalized field back to an approved scientific source."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    source_name: Literal["pubchem", "rcsb_pdb"]
    source_record_id: str
    source_url: HttpUrl
    retrieved_at: datetime
    field_path: str

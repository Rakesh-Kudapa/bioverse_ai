from typing import Annotated, Any

from fastapi import APIRouter, Query, status
from pydantic import StringConstraints

from app.api.dependencies import ProteinServiceDependency
from app.schemas.errors import ErrorResponse
from app.schemas.proteins import ProteinSearchResponse

router = APIRouter(prefix="/api/v1/proteins", tags=["proteins"])

ProteinQuery = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1, max_length=200),
    Query(description="Protein-related term to resolve through experimental RCSB PDB records"),
]

_ERROR_RESPONSES: dict[int | str, dict[str, Any]] = {
    status.HTTP_502_BAD_GATEWAY: {"model": ErrorResponse},
    status.HTTP_503_SERVICE_UNAVAILABLE: {"model": ErrorResponse},
    status.HTTP_504_GATEWAY_TIMEOUT: {"model": ErrorResponse},
}


@router.get("/search", response_model=ProteinSearchResponse, responses=_ERROR_RESPONSES)
async def search_proteins(
    service: ProteinServiceDependency,
    q: ProteinQuery,
) -> ProteinSearchResponse:
    return await service.search(q)

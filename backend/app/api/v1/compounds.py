from typing import Annotated, Any, Literal

from fastapi import APIRouter, Path, Query, status
from fastapi.responses import Response
from pydantic import StringConstraints

from app.api.dependencies import CompoundServiceDependency
from app.models.compound import CompoundEntity
from app.schemas.compounds import CompoundSearchResponse, SimilarCompoundsResponse
from app.schemas.errors import ErrorResponse

router = APIRouter(prefix="/api/v1/compounds", tags=["compounds"])

CompoundQuery = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1, max_length=200),
    Query(description="Common compound name to resolve through PubChem"),
]
CompoundCid = Annotated[int, Path(gt=0, description="PubChem compound identifier")]

_ERROR_RESPONSES: dict[int | str, dict[str, Any]] = {
    status.HTTP_404_NOT_FOUND: {"model": ErrorResponse},
    status.HTTP_502_BAD_GATEWAY: {"model": ErrorResponse},
    status.HTTP_503_SERVICE_UNAVAILABLE: {"model": ErrorResponse},
    status.HTTP_504_GATEWAY_TIMEOUT: {"model": ErrorResponse},
}


@router.get("/search", response_model=CompoundSearchResponse, responses=_ERROR_RESPONSES)
async def search_compounds(
    service: CompoundServiceDependency,
    q: CompoundQuery,
) -> CompoundSearchResponse:
    return await service.search(q)


@router.get("/{cid}", response_model=CompoundEntity, responses=_ERROR_RESPONSES)
async def get_compound(
    service: CompoundServiceDependency,
    cid: CompoundCid,
) -> CompoundEntity:
    return await service.get_compound(cid)


@router.get("/{cid}/similar", response_model=SimilarCompoundsResponse, responses=_ERROR_RESPONSES)
async def get_similar_compounds(
    service: CompoundServiceDependency,
    cid: CompoundCid,
    threshold: Annotated[int, Query(ge=0, le=100)] = 90,
    limit: Annotated[int, Query(ge=1, le=25)] = 10,
) -> SimilarCompoundsResponse:
    return await service.get_similar_compounds(cid, threshold=threshold, limit=limit)


@router.get("/{cid}/structure/{dimension}", responses=_ERROR_RESPONSES)
async def get_compound_structure(
    service: CompoundServiceDependency,
    cid: CompoundCid,
    dimension: Literal["2d", "3d"],
) -> Response:
    resource = await service.get_structure(cid, dimension)
    return Response(
        content=resource.content,
        media_type=resource.media_type,
        headers={"Content-Disposition": f'inline; filename="{resource.filename}"'},
    )

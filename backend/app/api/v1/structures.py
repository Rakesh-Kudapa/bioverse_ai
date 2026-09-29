from typing import Annotated, Any

from fastapi import APIRouter, Path, status
from fastapi.responses import Response

from app.api.dependencies import StructureServiceDependency
from app.models.structure import StructureEntity
from app.schemas.errors import ErrorResponse
from app.schemas.structures import LigandListResponse

router = APIRouter(prefix="/api/v1/structures", tags=["structures"])

PdbId = Annotated[
    str,
    Path(
        min_length=4,
        max_length=12,
        pattern=r"^(?:[0-9][A-Za-z0-9]{3}|[Pp][Dd][Bb]_[A-Za-z0-9]{8})$",
        description="Released RCSB PDB identifier",
    ),
]

_ERROR_RESPONSES: dict[int | str, dict[str, Any]] = {
    status.HTTP_404_NOT_FOUND: {"model": ErrorResponse},
    status.HTTP_502_BAD_GATEWAY: {"model": ErrorResponse},
    status.HTTP_503_SERVICE_UNAVAILABLE: {"model": ErrorResponse},
    status.HTTP_504_GATEWAY_TIMEOUT: {"model": ErrorResponse},
}


@router.get("/{pdb_id}", response_model=StructureEntity, responses=_ERROR_RESPONSES)
async def get_structure(
    service: StructureServiceDependency,
    pdb_id: PdbId,
) -> StructureEntity:
    return await service.get_structure(pdb_id)


@router.get("/{pdb_id}/ligands", response_model=LigandListResponse, responses=_ERROR_RESPONSES)
async def get_structure_ligands(
    service: StructureServiceDependency,
    pdb_id: PdbId,
) -> LigandListResponse:
    return await service.get_ligands(pdb_id)


@router.get("/{pdb_id}/file", responses=_ERROR_RESPONSES)
async def get_structure_file(
    service: StructureServiceDependency,
    pdb_id: PdbId,
) -> Response:
    resource = await service.get_structure_file(pdb_id)
    return Response(
        content=resource.content,
        media_type=resource.media_type,
        headers={"Content-Disposition": f'inline; filename="{resource.filename}"'},
    )

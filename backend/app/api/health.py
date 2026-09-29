from typing import Annotated

from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse

from app.core.database import check_database_connection
from app.schemas.health import ComponentHealth, HealthResponse, HealthStatus

router = APIRouter(tags=["health"])


@router.get(
    "/health",
    response_model=HealthResponse,
    responses={status.HTTP_503_SERVICE_UNAVAILABLE: {"model": HealthResponse}},
)
async def health(
    database_ready: Annotated[bool, Depends(check_database_connection)],
) -> HealthResponse | JSONResponse:
    """Report API and database readiness using a stable response shape."""
    response = HealthResponse(
        status=HealthStatus.READY if database_ready else HealthStatus.DEGRADED,
        service="bioverse-api",
        version="0.1.0",
        components={
            "database": ComponentHealth(
                status=HealthStatus.READY if database_ready else HealthStatus.UNAVAILABLE
            )
        },
    )

    if not database_ready:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content=response.model_dump(mode="json"),
        )
    return response

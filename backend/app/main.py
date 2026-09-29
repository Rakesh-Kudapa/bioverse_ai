from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.adapters.pubchem import PubChemAdapter
from app.adapters.rcsb import RcsbAdapter
from app.api.health import router as health_router
from app.api.v1.compounds import router as compounds_router
from app.api.v1.proteins import router as proteins_router
from app.api.v1.structures import router as structures_router
from app.core.config import get_settings
from app.core.errors import BioVerseError
from app.core.logging import configure_logging
from app.schemas.errors import ErrorDetail, ErrorResponse
from app.services.compounds import CompoundService
from app.services.proteins import ProteinService
from app.services.structures import StructureService


@asynccontextmanager
async def lifespan(application: FastAPI) -> AsyncIterator[None]:
    """Own shared source clients for the lifetime of the API process."""
    settings = get_settings()
    compound_service = CompoundService(PubChemAdapter(settings), settings)
    rcsb_adapter = RcsbAdapter(settings)
    application.state.compound_service = compound_service
    application.state.protein_service = ProteinService(rcsb_adapter, settings)
    application.state.structure_service = StructureService(rcsb_adapter, settings)
    try:
        yield
    finally:
        await compound_service.aclose()
        await rcsb_adapter.aclose()


async def bioverse_error_handler(_request: Request, error: Exception) -> JSONResponse:
    """Convert controlled application failures to the stable error envelope."""
    if not isinstance(error, BioVerseError):
        raise error
    response = ErrorResponse(
        error=ErrorDetail(
            code=error.code,
            message=error.message,
            source=error.source,
            retryable=error.retryable,
        )
    )
    return JSONResponse(
        status_code=error.status_code,
        content=response.model_dump(mode="json"),
    )


def create_app() -> FastAPI:
    """Create and configure the BioVerse API application."""
    settings = get_settings()
    configure_logging(settings.log_level)

    application = FastAPI(
        title="BioVerse AI API",
        description="Source-grounded biology exploration API",
        version="0.1.0",
        lifespan=lifespan,
    )
    application.add_exception_handler(BioVerseError, bioverse_error_handler)
    application.include_router(health_router)
    application.include_router(compounds_router)
    application.include_router(proteins_router)
    application.include_router(structures_router)
    return application


app = create_app()

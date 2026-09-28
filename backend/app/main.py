from fastapi import FastAPI

from app.api.health import router as health_router
from app.core.config import get_settings
from app.core.logging import configure_logging


def create_app() -> FastAPI:
    """Create and configure the BioVerse API application."""
    settings = get_settings()
    configure_logging(settings.log_level)

    application = FastAPI(
        title="BioVerse AI API",
        description="Source-grounded biology exploration API",
        version="0.1.0",
    )
    application.include_router(health_router)
    return application


app = create_app()


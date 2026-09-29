from typing import Annotated

from fastapi import Depends, Request

from app.services.compounds import CompoundService
from app.services.proteins import ProteinService
from app.services.structures import StructureService


def get_compound_service(request: Request) -> CompoundService:
    """Return the application-owned compound service."""
    service: CompoundService = request.app.state.compound_service
    return service


CompoundServiceDependency = Annotated[CompoundService, Depends(get_compound_service)]


def get_protein_service(request: Request) -> ProteinService:
    """Return the application-owned protein service."""
    service: ProteinService = request.app.state.protein_service
    return service


def get_structure_service(request: Request) -> StructureService:
    """Return the application-owned structure service."""
    service: StructureService = request.app.state.structure_service
    return service


ProteinServiceDependency = Annotated[ProteinService, Depends(get_protein_service)]
StructureServiceDependency = Annotated[StructureService, Depends(get_structure_service)]

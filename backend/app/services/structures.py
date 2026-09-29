import logging
from typing import Protocol

from app.cache.ttl import TTLCache
from app.core.config import Settings
from app.models.resource import BinaryResource
from app.models.structure import StructureEntity
from app.schemas.structures import LigandListResponse

logger = logging.getLogger(__name__)


class StructureGateway(Protocol):
    async def fetch_structure(self, pdb_id: str) -> StructureEntity: ...

    async def fetch_structure_file(self, pdb_id: str) -> BinaryResource: ...

    def normalize_pdb_id(self, pdb_id: str) -> str: ...


class StructureService:
    """Coordinate RCSB structure use cases and bounded successful-result caches."""

    def __init__(self, gateway: StructureGateway, settings: Settings) -> None:
        self._gateway = gateway
        self._structure_cache: TTLCache[str, StructureEntity] = TTLCache(
            ttl_seconds=settings.rcsb_cache_ttl_seconds,
            max_entries=settings.rcsb_cache_max_entries,
        )
        self._file_cache: TTLCache[str, BinaryResource] = TTLCache(
            ttl_seconds=settings.rcsb_cache_ttl_seconds,
            max_entries=settings.rcsb_cache_max_entries,
        )

    async def get_structure(self, pdb_id: str) -> StructureEntity:
        canonical_id = self._gateway.normalize_pdb_id(pdb_id)
        cached = await self._structure_cache.get(canonical_id)
        if cached is not None:
            self._log_cache("structure", "hit")
            return cached
        self._log_cache("structure", "miss")
        structure = await self._gateway.fetch_structure(canonical_id)
        await self._structure_cache.set(canonical_id, structure)
        return structure

    async def get_ligands(self, pdb_id: str) -> LigandListResponse:
        structure = await self.get_structure(pdb_id)
        return LigandListResponse(pdb_id=structure.pdb_id, results=structure.ligands)

    async def get_structure_file(self, pdb_id: str) -> BinaryResource:
        canonical_id = self._gateway.normalize_pdb_id(pdb_id)
        cached = await self._file_cache.get(canonical_id)
        if cached is not None:
            self._log_cache("structure_file", "hit")
            return cached
        self._log_cache("structure_file", "miss")
        resource = await self._gateway.fetch_structure_file(canonical_id)
        await self._file_cache.set(canonical_id, resource)
        return resource

    @staticmethod
    def _log_cache(operation: str, cache_status: str) -> None:
        logger.info(
            "Structure cache access",
            extra={
                "event": "cache_access",
                "operation": operation,
                "cache_status": cache_status,
            },
        )

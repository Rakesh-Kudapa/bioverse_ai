import logging
from typing import Protocol

from app.cache.ttl import TTLCache
from app.core.config import Settings
from app.models.protein import ProteinEntity
from app.schemas.proteins import ProteinSearchResponse

logger = logging.getLogger(__name__)


class ProteinGateway(Protocol):
    async def search_proteins(self, query: str) -> tuple[ProteinEntity, ...]: ...


class ProteinService:
    """Coordinate conservative RCSB polymer-entity search and caching."""

    def __init__(self, gateway: ProteinGateway, settings: Settings) -> None:
        self._gateway = gateway
        self._search_cache: TTLCache[str, tuple[ProteinEntity, ...]] = TTLCache(
            ttl_seconds=settings.rcsb_cache_ttl_seconds,
            max_entries=settings.rcsb_cache_max_entries,
        )

    async def search(self, query: str) -> ProteinSearchResponse:
        normalized_query = query.strip()
        cache_key = normalized_query.casefold()
        results = await self._search_cache.get(cache_key)
        if results is None:
            self._log_cache("miss")
            results = await self._gateway.search_proteins(normalized_query)
            await self._search_cache.set(cache_key, results)
        else:
            self._log_cache("hit")
        return ProteinSearchResponse(query=normalized_query, results=results)

    @staticmethod
    def _log_cache(cache_status: str) -> None:
        logger.info(
            "Protein cache access",
            extra={
                "event": "cache_access",
                "operation": "protein_search",
                "cache_status": cache_status,
            },
        )

import logging
from datetime import UTC, datetime
from typing import Literal, Protocol

from app.cache.ttl import TTLCache
from app.core.config import Settings
from app.core.errors import EntityNotFoundError, StructureNotAvailableError
from app.models.compound import CompoundEntity, SourceProvenance
from app.models.resource import BinaryResource
from app.schemas.compounds import (
    CompoundSearchResponse,
    SimilarCompoundsResponse,
    SimilarityQuery,
)

logger = logging.getLogger(__name__)


class PubChemGateway(Protocol):
    async def resolve_name(self, name: str) -> tuple[int, ...]: ...

    async def fetch_compounds(self, cids: tuple[int, ...]) -> tuple[CompoundEntity, ...]: ...

    async def fetch_similar_cids(
        self,
        cid: int,
        *,
        threshold: int,
        limit: int,
    ) -> tuple[int, ...]: ...

    async def fetch_structure(
        self,
        cid: int,
        dimension: Literal["2d", "3d"],
    ) -> BinaryResource: ...

    async def aclose(self) -> None: ...


class CompoundService:
    """Coordinate source-grounded compound use cases and bounded caching."""

    def __init__(self, gateway: PubChemGateway, settings: Settings) -> None:
        self._gateway = gateway
        self._max_search_results = settings.pubchem_max_search_results
        ttl_seconds = settings.compound_cache_ttl_seconds
        max_entries = settings.compound_cache_max_entries
        self._entity_cache: TTLCache[int, CompoundEntity] = TTLCache(
            ttl_seconds=ttl_seconds,
            max_entries=max_entries,
        )
        self._search_cache: TTLCache[str, tuple[int, ...]] = TTLCache(
            ttl_seconds=ttl_seconds,
            max_entries=max_entries,
        )
        self._similarity_cache: TTLCache[tuple[int, int, int], SimilarCompoundsResponse] = TTLCache(
            ttl_seconds=ttl_seconds, max_entries=max_entries
        )
        self._structure_cache: TTLCache[tuple[int, str], BinaryResource] = TTLCache(
            ttl_seconds=ttl_seconds,
            max_entries=max_entries,
        )

    async def aclose(self) -> None:
        await self._gateway.aclose()

    async def search(self, query: str) -> CompoundSearchResponse:
        normalized_query = query.strip()
        cache_key = normalized_query.casefold()
        cids = await self._search_cache.get(cache_key)
        if cids is None:
            self._log_cache("search", "miss")
            resolved = await self._gateway.resolve_name(normalized_query)
            cids = resolved[: self._max_search_results]
            await self._search_cache.set(cache_key, cids)
        else:
            self._log_cache("search", "hit")
        compounds = await self._get_compounds(cids)
        return CompoundSearchResponse(query=normalized_query, results=compounds)

    async def get_compound(self, cid: int) -> CompoundEntity:
        compounds = await self._get_compounds((cid,))
        if not compounds:
            raise EntityNotFoundError(
                f"PubChem compound CID {cid} was not found.",
                source="pubchem",
            )
        return compounds[0]

    async def get_similar_compounds(
        self,
        cid: int,
        *,
        threshold: int,
        limit: int,
    ) -> SimilarCompoundsResponse:
        await self.get_compound(cid)
        cache_key = (cid, threshold, limit)
        cached = await self._similarity_cache.get(cache_key)
        if cached is not None:
            self._log_cache("similarity", "hit")
            return cached

        self._log_cache("similarity", "miss")
        similar_cids = await self._gateway.fetch_similar_cids(
            cid,
            threshold=threshold,
            limit=limit,
        )
        compounds = await self._get_compounds(similar_cids)
        retrieved_at = datetime.now(UTC)
        source_url = f"https://pubchem.ncbi.nlm.nih.gov/compound/{cid}"
        response = SimilarCompoundsResponse(
            query=SimilarityQuery(
                source_record_id=str(cid),
                threshold=threshold,
                limit=limit,
            ),
            results=compounds,
            provenance=SourceProvenance(
                source_name="pubchem",
                source_record_id=str(cid),
                source_url=source_url,
                retrieved_at=retrieved_at,
                field_path=(
                    f"PUG_REST.fastsimilarity_2d[Threshold={threshold},MaxRecords={limit + 1}]"
                ),
            ),
        )
        await self._similarity_cache.set(cache_key, response)
        return response

    async def get_structure(
        self,
        cid: int,
        dimension: Literal["2d", "3d"],
    ) -> BinaryResource:
        compound = await self.get_compound(cid)
        if dimension == "3d" and not compound.has_3d_conformer:
            raise StructureNotAvailableError(
                f"PubChem does not provide a 3D conformer for CID {cid}.",
                source="pubchem",
            )
        cache_key = (cid, dimension)
        cached = await self._structure_cache.get(cache_key)
        if cached is not None:
            self._log_cache(f"structure_{dimension}", "hit")
            return cached

        self._log_cache(f"structure_{dimension}", "miss")
        resource = await self._gateway.fetch_structure(cid, dimension)
        await self._structure_cache.set(cache_key, resource)
        return resource

    async def _get_compounds(self, cids: tuple[int, ...]) -> tuple[CompoundEntity, ...]:
        if not cids:
            return ()

        compounds_by_cid: dict[int, CompoundEntity] = {}
        missing: list[int] = []
        for cid in cids:
            cached = await self._entity_cache.get(cid)
            if cached is None:
                missing.append(cid)
            else:
                compounds_by_cid[cid] = cached

        if missing:
            self._log_cache("compound", "miss")
            fetched = await self._gateway.fetch_compounds(tuple(missing))
            for compound in fetched:
                compounds_by_cid[compound.cid] = compound
                await self._entity_cache.set(compound.cid, compound)
        else:
            self._log_cache("compound", "hit")

        return tuple(compounds_by_cid[cid] for cid in cids if cid in compounds_by_cid)

    @staticmethod
    def _log_cache(operation: str, cache_status: Literal["hit", "miss"]) -> None:
        logger.info(
            "Compound cache access",
            extra={
                "event": "cache_access",
                "operation": operation,
                "cache_status": cache_status,
            },
        )

import pytest

from app.core.config import Settings
from app.core.errors import StructureNotAvailableError
from app.services.compounds import CompoundService
from tests.factories import FakePubChemGateway, make_compound


def make_service(gateway: FakePubChemGateway) -> CompoundService:
    return CompoundService(
        gateway,
        Settings(compound_cache_ttl_seconds=60, compound_cache_max_entries=10),
    )


async def test_search_caches_resolution_and_normalized_entity_with_provenance() -> None:
    aspirin = make_compound()
    gateway = FakePubChemGateway((aspirin,))
    service = make_service(gateway)

    first = await service.search(" Aspirin ")
    second = await service.search("aspirin")

    assert first.results == second.results
    assert first.query == "Aspirin"
    assert second.query == "aspirin"
    assert first.results[0].provenance == aspirin.provenance
    assert gateway.resolve_calls == 1
    assert gateway.fetch_compound_calls == 1


async def test_similarity_is_cached_and_retains_source_metadata() -> None:
    aspirin = make_compound()
    related = make_compound(5161, name="Related compound")
    gateway = FakePubChemGateway((aspirin, related))
    gateway.resolve_result = (2244,)
    gateway.similar_result = (5161,)
    service = make_service(gateway)

    first = await service.get_similar_compounds(2244, threshold=95, limit=5)
    second = await service.get_similar_compounds(2244, threshold=95, limit=5)

    assert first == second
    assert first.results == (related,)
    assert first.query.source == "pubchem"
    assert first.query.threshold == 95
    assert first.provenance.source_record_id == "2244"
    assert gateway.fetch_similarity_calls == 1


async def test_structure_bytes_are_cached() -> None:
    gateway = FakePubChemGateway((make_compound(),))
    service = make_service(gateway)

    first = await service.get_structure(2244, "2d")
    second = await service.get_structure(2244, "2d")

    assert first == second
    assert gateway.fetch_structure_calls == 1


async def test_missing_3d_conformer_never_calls_structure_source() -> None:
    gateway = FakePubChemGateway((make_compound(5360545, name="Sodium", has_3d_conformer=False),))
    service = make_service(gateway)

    with pytest.raises(StructureNotAvailableError):
        await service.get_structure(5360545, "3d")

    assert gateway.fetch_structure_calls == 0

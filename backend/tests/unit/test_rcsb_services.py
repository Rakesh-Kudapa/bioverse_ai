import pytest

from app.core.config import Settings
from app.core.errors import EntityNotFoundError
from app.services.proteins import ProteinService
from app.services.structures import StructureService
from tests.factories import FakeRcsbGateway


def service_settings() -> Settings:
    return Settings(rcsb_cache_ttl_seconds=60, rcsb_cache_max_entries=10)


async def test_protein_search_cache_preserves_normalized_model_and_provenance() -> None:
    gateway = FakeRcsbGateway()
    service = ProteinService(gateway, service_settings())

    first = await service.search("EGFR")
    second = await service.search(" egfr ")

    assert gateway.search_calls == 1
    assert first.results == second.results
    assert first.query == "EGFR"
    assert second.query == "egfr"
    assert second.results[0].source_id == "1M17_1"
    assert second.results[0].provenance == first.results[0].provenance


async def test_empty_search_is_cacheable_source_result() -> None:
    gateway = FakeRcsbGateway()
    gateway.proteins = ()
    service = ProteinService(gateway, service_settings())

    assert (await service.search("unknown")).results == ()
    assert (await service.search("UNKNOWN")).results == ()
    assert gateway.search_calls == 1


async def test_search_errors_are_not_cached() -> None:
    gateway = FakeRcsbGateway()
    gateway.search_error = EntityNotFoundError("failure", source="rcsb_pdb")
    service = ProteinService(gateway, service_settings())

    for _attempt in range(2):
        with pytest.raises(EntityNotFoundError):
            await service.search("EGFR")
    assert gateway.search_calls == 2


async def test_structure_ligands_reuse_cached_detail() -> None:
    gateway = FakeRcsbGateway()
    service = StructureService(gateway, service_settings())

    structure = await service.get_structure("1m17")
    ligands = await service.get_ligands("1M17")

    assert gateway.structure_calls == 1
    assert ligands.pdb_id == "1M17"
    assert ligands.results == structure.ligands
    assert ligands.results[0].provenance == structure.ligands[0].provenance


async def test_structure_file_cache_preserves_exact_bytes() -> None:
    gateway = FakeRcsbGateway()
    service = StructureService(gateway, service_settings())

    first = await service.get_structure_file("1m17")
    second = await service.get_structure_file("1M17")

    assert gateway.file_calls == 1
    assert first == second
    assert second.content == b"data_1M17\n#\n"


async def test_structure_errors_are_not_cached() -> None:
    gateway = FakeRcsbGateway()
    gateway.structure_error = EntityNotFoundError("not found", source="rcsb_pdb")
    service = StructureService(gateway, service_settings())

    for _attempt in range(2):
        with pytest.raises(EntityNotFoundError):
            await service.get_structure("9ZZZ")
    assert gateway.structure_calls == 2

from httpx import AsyncClient

from app.api.dependencies import get_protein_service, get_structure_service
from app.core.config import Settings
from app.core.errors import EntityNotFoundError, SourceTimeoutError
from app.main import app
from app.services.proteins import ProteinService
from app.services.structures import StructureService
from tests.factories import FakeRcsbGateway, make_structure


def install_services(gateway: FakeRcsbGateway) -> None:
    settings = Settings(rcsb_cache_ttl_seconds=60, rcsb_cache_max_entries=10)
    protein_service = ProteinService(gateway, settings)
    structure_service = StructureService(gateway, settings)
    app.dependency_overrides[get_protein_service] = lambda: protein_service
    app.dependency_overrides[get_structure_service] = lambda: structure_service


async def test_protein_search_returns_normalized_entities(client: AsyncClient) -> None:
    install_services(FakeRcsbGateway())

    response = await client.get("/api/v1/proteins/search", params={"q": "EGFR"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["query"] == "EGFR"
    assert payload["results"][0]["id"] == "protein:rcsb:1M17_1"
    assert payload["results"][0]["source"] == "rcsb_pdb"
    assert payload["results"][0]["provenance"][0]["source_record_id"] == "1M17_1"


async def test_empty_protein_search_is_controlled(client: AsyncClient) -> None:
    gateway = FakeRcsbGateway()
    gateway.proteins = ()
    install_services(gateway)

    response = await client.get("/api/v1/proteins/search", params={"q": "unknown"})

    assert response.status_code == 200
    assert response.json() == {"query": "unknown", "results": []}


async def test_structure_detail_and_ligand_contracts(client: AsyncClient) -> None:
    install_services(FakeRcsbGateway())

    detail = await client.get("/api/v1/structures/1m17")
    ligands = await client.get("/api/v1/structures/1M17/ligands")

    assert detail.status_code == 200
    assert detail.json()["pdb_id"] == "1M17"
    assert detail.json()["experimental_methods"] == ["X-RAY DIFFRACTION"]
    assert ligands.status_code == 200
    assert ligands.json()["results"][0]["chemical_component_id"] == "AQ4"


async def test_ligand_free_structure_returns_empty_list(client: AsyncClient) -> None:
    gateway = FakeRcsbGateway()
    gateway.structure = make_structure(with_ligand=False)
    install_services(gateway)

    response = await client.get("/api/v1/structures/1M17/ligands")

    assert response.status_code == 200
    assert response.json() == {"pdb_id": "1M17", "results": []}


async def test_structure_file_is_proxied_as_mmcif(client: AsyncClient) -> None:
    install_services(FakeRcsbGateway())

    response = await client.get("/api/v1/structures/1M17/file")

    assert response.status_code == 200
    assert response.headers["content-type"] == "chemical/x-mmcif"
    assert response.headers["content-disposition"] == 'inline; filename="1M17.cif"'
    assert response.content == b"data_1M17\n#\n"


async def test_unknown_structure_returns_stable_typed_error(client: AsyncClient) -> None:
    gateway = FakeRcsbGateway()
    gateway.structure_error = EntityNotFoundError(
        "RCSB PDB entry 9ZZZ was not found.", source="rcsb_pdb"
    )
    install_services(gateway)

    response = await client.get("/api/v1/structures/9ZZZ")

    assert response.status_code == 404
    assert response.json()["error"] == {
        "code": "ENTITY_NOT_FOUND",
        "message": "RCSB PDB entry 9ZZZ was not found.",
        "source": "rcsb_pdb",
        "retryable": False,
    }


async def test_upstream_timeout_returns_stable_error(client: AsyncClient) -> None:
    gateway = FakeRcsbGateway()
    gateway.search_error = SourceTimeoutError("RCSB request timed out.", source="rcsb_pdb")
    install_services(gateway)

    response = await client.get("/api/v1/proteins/search", params={"q": "EGFR"})

    assert response.status_code == 504
    assert response.json()["error"]["code"] == "SOURCE_TIMEOUT"
    assert response.json()["error"]["source"] == "rcsb_pdb"


async def test_queries_and_pdb_ids_are_bounded(client: AsyncClient) -> None:
    install_services(FakeRcsbGateway())

    empty_query = await client.get("/api/v1/proteins/search", params={"q": "   "})
    invalid_id = await client.get("/api/v1/structures/not-a-pdb-id")

    assert empty_query.status_code == 422
    assert invalid_id.status_code == 422

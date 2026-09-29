from httpx import AsyncClient

from app.api.dependencies import get_compound_service
from app.core.config import Settings
from app.core.errors import SourceTimeoutError
from app.main import app
from app.services.compounds import CompoundService
from tests.factories import FakePubChemGateway, make_compound


def install_service(gateway: FakePubChemGateway) -> None:
    service = CompoundService(
        gateway,
        Settings(compound_cache_ttl_seconds=60, compound_cache_max_entries=10),
    )
    app.dependency_overrides[get_compound_service] = lambda: service


async def test_search_returns_normalized_compound_schema(client: AsyncClient) -> None:
    install_service(FakePubChemGateway((make_compound(),)))

    response = await client.get("/api/v1/compounds/search", params={"q": "aspirin"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["query"] == "aspirin"
    assert payload["results"][0]["id"] == "compound:pubchem:2244"
    assert payload["results"][0]["source"] == "pubchem"
    assert payload["results"][0]["provenance"][0]["source_record_id"] == "2244"


async def test_unknown_search_returns_empty_results(client: AsyncClient) -> None:
    gateway = FakePubChemGateway(())
    gateway.resolve_result = ()
    install_service(gateway)

    response = await client.get("/api/v1/compounds/search", params={"q": "unknown"})

    assert response.status_code == 200
    assert response.json() == {"query": "unknown", "results": []}


async def test_unknown_cid_returns_typed_not_found(client: AsyncClient) -> None:
    install_service(FakePubChemGateway((make_compound(),)))

    response = await client.get("/api/v1/compounds/999999999")

    assert response.status_code == 404
    assert response.json()["error"] == {
        "code": "ENTITY_NOT_FOUND",
        "message": "Compound not found.",
        "source": "pubchem",
        "retryable": False,
    }


async def test_source_timeout_returns_stable_error_envelope(client: AsyncClient) -> None:
    gateway = FakePubChemGateway(())
    gateway.resolve_error = SourceTimeoutError("PubChem request timed out.", source="pubchem")
    install_service(gateway)

    response = await client.get("/api/v1/compounds/search", params={"q": "aspirin"})

    assert response.status_code == 504
    assert response.json()["error"] == {
        "code": "SOURCE_TIMEOUT",
        "message": "PubChem request timed out.",
        "source": "pubchem",
        "retryable": True,
    }


async def test_2d_structure_is_proxied_with_source_media_type(client: AsyncClient) -> None:
    install_service(FakePubChemGateway((make_compound(),)))

    response = await client.get("/api/v1/compounds/2244/structure/2d")

    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"
    assert response.content == b"\x89PNG\r\nfixture"


async def test_no_3d_conformer_returns_typed_error(client: AsyncClient) -> None:
    sodium = make_compound(5360545, name="Sodium", has_3d_conformer=False)
    install_service(FakePubChemGateway((sodium,)))

    response = await client.get("/api/v1/compounds/5360545/structure/3d")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "STRUCTURE_NOT_AVAILABLE"


async def test_similarity_response_exposes_source_query_metadata(client: AsyncClient) -> None:
    aspirin = make_compound()
    related = make_compound(5161, name="Related compound")
    gateway = FakePubChemGateway((aspirin, related))
    gateway.similar_result = (5161,)
    install_service(gateway)

    response = await client.get(
        "/api/v1/compounds/2244/similar",
        params={"threshold": 95, "limit": 5},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["query"] == {
        "source": "pubchem",
        "source_record_id": "2244",
        "algorithm": "pubchem_2d_tanimoto",
        "threshold": 95,
        "limit": 5,
    }
    assert payload["results"][0]["cid"] == 5161


async def test_query_and_cid_validation_are_bounded(client: AsyncClient) -> None:
    install_service(FakePubChemGateway((make_compound(),)))

    empty_query = await client.get("/api/v1/compounds/search", params={"q": "   "})
    invalid_cid = await client.get("/api/v1/compounds/0")
    invalid_limit = await client.get("/api/v1/compounds/2244/similar", params={"limit": 26})

    assert empty_query.status_code == 422
    assert invalid_cid.status_code == 422
    assert invalid_limit.status_code == 422

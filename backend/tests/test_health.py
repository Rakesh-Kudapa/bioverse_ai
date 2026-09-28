from collections.abc import AsyncIterator

import pytest
from httpx import ASGITransport, AsyncClient

from app.core.database import check_database_connection
from app.main import app


@pytest.fixture
async def client() -> AsyncIterator[AsyncClient]:
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://testserver",
    ) as test_client:
        yield test_client
    app.dependency_overrides.clear()


async def test_health_returns_ready_when_database_is_available(client: AsyncClient) -> None:
    async def database_is_ready() -> bool:
        return True

    app.dependency_overrides[check_database_connection] = database_is_ready

    response = await client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ready",
        "service": "bioverse-api",
        "version": "0.1.0",
        "components": {"database": {"status": "ready"}},
    }


async def test_health_returns_structured_503_when_database_is_unavailable(
    client: AsyncClient,
) -> None:
    async def database_is_unavailable() -> bool:
        return False

    app.dependency_overrides[check_database_connection] = database_is_unavailable

    response = await client.get("/health")

    assert response.status_code == 503
    assert response.json() == {
        "status": "degraded",
        "service": "bioverse-api",
        "version": "0.1.0",
        "components": {"database": {"status": "unavailable"}},
    }


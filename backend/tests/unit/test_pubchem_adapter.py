import copy
import json
from pathlib import Path
from typing import cast

import httpx
import pytest

from app.adapters.pubchem import PUBCHEM_BASE_URL, PubChemAdapter
from app.core.config import Settings
from app.core.errors import (
    EntityNotFoundError,
    InvalidExternalPayloadError,
    SourceRateLimitedError,
    SourceTimeoutError,
    StructureNotAvailableError,
)

FIXTURE_DIRECTORY = Path(__file__).parents[1] / "fixtures" / "pubchem"


def load_fixture(name: str) -> dict[str, object]:
    payload = json.loads((FIXTURE_DIRECTORY / name).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise TypeError("Fixture root must be a JSON object.")
    return cast(dict[str, object], payload)


def adapter_settings(*, pubchem_max_structure_bytes: int = 5_000_000) -> Settings:
    return Settings(
        pubchem_retry_count=0,
        pubchem_retry_backoff_seconds=0,
        pubchem_max_structure_bytes=pubchem_max_structure_bytes,
    )


def make_adapter(handler: httpx.MockTransport) -> PubChemAdapter:
    client = httpx.AsyncClient(base_url=PUBCHEM_BASE_URL, transport=handler)
    return PubChemAdapter(adapter_settings(), client=client)


async def test_successful_name_lookup_and_compound_normalization() -> None:
    properties = load_fixture("compound_properties.json")
    cids = load_fixture("aspirin_cids.json")

    def handler(request: httpx.Request) -> httpx.Response:
        if "/name/aspirin/cids/JSON" in request.url.path:
            return httpx.Response(200, json=cids)
        return httpx.Response(200, json=properties)

    adapter = make_adapter(httpx.MockTransport(handler))

    resolved = await adapter.resolve_name("aspirin")
    compounds = await adapter.fetch_compounds(resolved)

    assert resolved == (2244,)
    assert len(compounds) == 1
    aspirin = compounds[0]
    assert aspirin.id == "compound:pubchem:2244"
    assert aspirin.name == "Aspirin"
    assert aspirin.molecular_formula == "C9H8O4"
    assert aspirin.molecular_weight == 180.16
    assert aspirin.canonical_smiles == "CC(=O)OC1=CC=CC=C1C(=O)O"
    assert aspirin.isomeric_smiles == "CC(=O)OC1=CC=CC=C1C(=O)O"
    assert aspirin.has_3d_conformer is True
    assert aspirin.structure_3d is not None
    assert aspirin.source_url.unicode_string() == "https://pubchem.ncbi.nlm.nih.gov/compound/2244"
    assert {item.source_record_id for item in aspirin.provenance} == {"2244"}


async def test_missing_optional_property_remains_null_without_fake_provenance() -> None:
    payload = copy.deepcopy(load_fixture("compound_properties.json"))
    properties = payload["PropertyTable"]
    assert isinstance(properties, dict)
    rows = properties["Properties"]
    assert isinstance(rows, list)
    aspirin = rows[0]
    assert isinstance(aspirin, dict)
    aspirin.pop("XLogP")

    adapter = make_adapter(httpx.MockTransport(lambda _request: httpx.Response(200, json=payload)))
    compound = (await adapter.fetch_compounds((2244,)))[0]

    assert compound.xlogp is None
    assert all(not item.field_path.endswith("XLogP") for item in compound.provenance)


async def test_compound_without_3d_conformer_has_no_3d_reference() -> None:
    payload = load_fixture("compound_properties.json")
    adapter = make_adapter(httpx.MockTransport(lambda _request: httpx.Response(200, json=payload)))

    sodium = (await adapter.fetch_compounds((5360545,)))[0]

    assert sodium.has_3d_conformer is False
    assert sodium.structure_3d is None
    assert sodium.xlogp is None


async def test_unknown_name_returns_empty_result_and_unknown_cid_is_typed() -> None:
    adapter = make_adapter(
        httpx.MockTransport(
            lambda _request: httpx.Response(
                404,
                json={"Fault": {"Code": "PUGREST.NotFound"}},
            )
        )
    )

    assert await adapter.resolve_name("not-a-compound") == ()
    with pytest.raises(EntityNotFoundError):
        await adapter.fetch_compounds((999999999,))


async def test_timeout_is_mapped_to_typed_source_timeout() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("timed out", request=request)

    adapter = make_adapter(httpx.MockTransport(handler))

    with pytest.raises(SourceTimeoutError):
        await adapter.resolve_name("aspirin")


async def test_pubchem_busy_is_mapped_to_rate_limit_error() -> None:
    adapter = make_adapter(httpx.MockTransport(lambda _request: httpx.Response(503, text="busy")))

    with pytest.raises(SourceRateLimitedError):
        await adapter.resolve_name("aspirin")


async def test_malformed_pubchem_payload_is_rejected() -> None:
    adapter = make_adapter(
        httpx.MockTransport(lambda _request: httpx.Response(200, json={"unexpected": []}))
    )

    with pytest.raises(InvalidExternalPayloadError):
        await adapter.fetch_compounds((2244,))


async def test_similarity_is_source_derived_limited_and_excludes_query_cid() -> None:
    payload = load_fixture("aspirin_similarity.json")

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.params["Threshold"] == "95"
        assert request.url.params["MaxRecords"] == "4"
        return httpx.Response(200, json=payload)

    adapter = make_adapter(httpx.MockTransport(handler))

    assert await adapter.fetch_similar_cids(2244, threshold=95, limit=3) == (5161, 68484, 61159)


@pytest.mark.parametrize(
    ("dimension", "content_type", "content"),
    [
        ("2d", "image/png", b"\x89PNG\r\nfixture"),
        ("3d", "chemical/x-mdl-sdfile", b"fixture sdf"),
    ],
)
async def test_structure_content_is_returned_from_pubchem(
    dimension: str,
    content_type: str,
    content: bytes,
) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.params["record_type"] == dimension
        return httpx.Response(200, content=content, headers={"content-type": content_type})

    adapter = make_adapter(httpx.MockTransport(handler))

    resource = await adapter.fetch_structure(2244, dimension)  # type: ignore[arg-type]

    assert resource.content == content
    assert resource.media_type == content_type


async def test_missing_3d_structure_is_typed() -> None:
    adapter = make_adapter(
        httpx.MockTransport(lambda _request: httpx.Response(404, text="not found"))
    )

    with pytest.raises(StructureNotAvailableError):
        await adapter.fetch_structure(5360545, "3d")


async def test_oversized_structure_is_rejected() -> None:
    settings = adapter_settings(pubchem_max_structure_bytes=1000)
    client = httpx.AsyncClient(
        base_url=PUBCHEM_BASE_URL,
        transport=httpx.MockTransport(
            lambda _request: httpx.Response(
                200,
                content=b"x" * 1001,
                headers={"content-type": "image/png"},
            )
        ),
    )
    adapter = PubChemAdapter(settings, client=client)

    with pytest.raises(InvalidExternalPayloadError):
        await adapter.fetch_structure(2244, "2d")

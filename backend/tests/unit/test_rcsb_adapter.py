import json
from pathlib import Path
from typing import cast

import httpx
import pytest

from app.adapters.rcsb import RCSB_GRAPHQL_URL, RCSB_SEARCH_URL, RcsbAdapter
from app.core.config import Settings
from app.core.errors import (
    EntityNotFoundError,
    InvalidExternalPayloadError,
    SourceRateLimitedError,
    SourceTimeoutError,
    StructureNotAvailableError,
)

FIXTURE_DIRECTORY = Path(__file__).parents[1] / "fixtures" / "rcsb"


def load_fixture(name: str) -> dict[str, object]:
    payload = json.loads((FIXTURE_DIRECTORY / name).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise TypeError("Fixture root must be a JSON object.")
    return cast(dict[str, object], payload)


def adapter_settings(*, max_structure_bytes: int = 25_000_000) -> Settings:
    return Settings(
        rcsb_retry_count=0,
        rcsb_retry_backoff_seconds=0,
        rcsb_max_structure_bytes=max_structure_bytes,
    )


def make_adapter(handler: httpx.MockTransport, *, max_bytes: int = 25_000_000) -> RcsbAdapter:
    client = httpx.AsyncClient(transport=handler)
    return RcsbAdapter(adapter_settings(max_structure_bytes=max_bytes), client=client)


async def test_successful_search_returns_normalized_source_polymer_entity() -> None:
    search = load_fixture("search_egfr.json")
    entities = load_fixture("protein_entities.json")

    def handler(request: httpx.Request) -> httpx.Response:
        if str(request.url) == RCSB_SEARCH_URL:
            body = json.loads(request.content)
            assert body["return_type"] == "polymer_entity"
            assert body["request_options"]["results_content_type"] == ["experimental"]
            return httpx.Response(200, json=search)
        assert str(request.url) == RCSB_GRAPHQL_URL
        return httpx.Response(200, json=entities)

    adapter = make_adapter(httpx.MockTransport(handler))
    results = await adapter.search_proteins("EGFR")

    assert len(results) == 1
    protein = results[0]
    assert protein.id == "protein:rcsb:1M17_1"
    assert protein.name == "epidermal growth factor receptor"
    assert protein.gene_symbols == ("egfr",)
    assert protein.external_references[0].database_accession == "P00533"
    assert protein.associated_structures[0].resolution_angstroms == 2.6
    assert {item.source_name for item in protein.provenance} == {"rcsb_pdb"}


async def test_structure_detail_normalizes_metadata_chains_ligand_and_assembly() -> None:
    payload = load_fixture("structure_1m17.json")
    adapter = make_adapter(httpx.MockTransport(lambda _request: httpx.Response(200, json=payload)))

    structure = await adapter.fetch_structure("1m17")

    assert structure.pdb_id == "1M17"
    assert structure.experimental_methods == ("X-RAY DIFFRACTION",)
    assert structure.resolution_angstroms == 2.6
    assert structure.chains[0].auth_chain_ids == ("A",)
    assert structure.polymer_entities[0].sequence_length == 333
    assert structure.ligands[0].chemical_component_id == "AQ4"
    assert structure.ligands[0].molecular_weight == 393.436
    assert structure.assemblies[0].assembly_id == "1"
    assert structure.structure_reference.endpoint == "/api/v1/structures/1M17/file"
    assert all(item.source_name == "rcsb_pdb" for item in structure.provenance)


async def test_nmr_structure_without_resolution_or_ligands_is_valid() -> None:
    payload = load_fixture("structure_1d3z.json")
    adapter = make_adapter(httpx.MockTransport(lambda _request: httpx.Response(200, json=payload)))

    structure = await adapter.fetch_structure("1D3Z")

    assert structure.experimental_methods == ("SOLUTION NMR",)
    assert structure.resolution_angstroms is None
    assert structure.nonpolymer_entity_count == 0
    assert structure.ligands == ()


async def test_empty_search_response_is_controlled() -> None:
    adapter = make_adapter(httpx.MockTransport(lambda _request: httpx.Response(204)))

    assert await adapter.search_proteins("definitely-not-a-protein") == ()


async def test_unknown_structure_is_typed() -> None:
    payload = load_fixture("structure_missing.json")
    adapter = make_adapter(httpx.MockTransport(lambda _request: httpx.Response(200, json=payload)))

    with pytest.raises(EntityNotFoundError):
        await adapter.fetch_structure("9ZZZ")


async def test_timeout_is_mapped_to_typed_source_timeout() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("timed out", request=request)

    adapter = make_adapter(httpx.MockTransport(handler))

    with pytest.raises(SourceTimeoutError):
        await adapter.search_proteins("EGFR")


async def test_busy_source_is_mapped_to_rate_limit_error() -> None:
    adapter = make_adapter(httpx.MockTransport(lambda _request: httpx.Response(503, text="busy")))

    with pytest.raises(SourceRateLimitedError):
        await adapter.search_proteins("EGFR")


@pytest.mark.parametrize(
    "payload",
    [
        {"unexpected": []},
        {"errors": [{"message": "schema changed"}], "data": None},
    ],
)
async def test_malformed_or_graphql_error_payload_is_rejected(
    payload: dict[str, object],
) -> None:
    adapter = make_adapter(httpx.MockTransport(lambda _request: httpx.Response(200, json=payload)))

    with pytest.raises(InvalidExternalPayloadError):
        await adapter.fetch_structure("1M17")


async def test_structure_file_is_unmodified_and_media_type_is_normalized() -> None:
    content = (FIXTURE_DIRECTORY / "1m17.cif").read_bytes()

    def handler(request: httpx.Request) -> httpx.Response:
        assert str(request.url) == "https://files.rcsb.org/download/1M17.cif"
        return httpx.Response(
            200,
            content=content,
            headers={"content-type": "application/octet-stream"},
        )

    adapter = make_adapter(httpx.MockTransport(handler))
    resource = await adapter.fetch_structure_file("1m17")

    assert resource.content == content
    assert resource.media_type == "chemical/x-mmcif"
    assert resource.filename == "1M17.cif"


async def test_missing_structure_file_is_typed() -> None:
    adapter = make_adapter(
        httpx.MockTransport(lambda _request: httpx.Response(404, text="not found"))
    )

    with pytest.raises(StructureNotAvailableError):
        await adapter.fetch_structure_file("9ZZZ")


async def test_unexpected_content_type_and_oversized_files_are_rejected() -> None:
    wrong_type = make_adapter(
        httpx.MockTransport(
            lambda _request: httpx.Response(
                200,
                content=b"<html>not cif</html>",
                headers={"content-type": "text/html"},
            )
        )
    )
    oversized = make_adapter(
        httpx.MockTransport(
            lambda _request: httpx.Response(
                200,
                content=b"x" * 10_001,
                headers={"content-type": "application/octet-stream"},
            )
        ),
        max_bytes=10_000,
    )

    with pytest.raises(InvalidExternalPayloadError):
        await wrong_type.fetch_structure_file("1M17")
    with pytest.raises(InvalidExternalPayloadError):
        await oversized.fetch_structure_file("1M17")


@pytest.mark.parametrize("pdb_id", ["../x", "http://evil", "ABCD", "1M17.cif"])
async def test_invalid_pdb_identifiers_never_reach_upstream(pdb_id: str) -> None:
    adapter = make_adapter(
        httpx.MockTransport(lambda _request: pytest.fail("upstream must not be called"))
    )

    with pytest.raises(InvalidExternalPayloadError):
        await adapter.fetch_structure(pdb_id)

import os

import pytest

from app.adapters.pubchem import PubChemAdapter
from app.core.config import Settings

pytestmark = [
    pytest.mark.live,
    pytest.mark.skipif(
        os.getenv("RUN_LIVE_PUBCHEM_TESTS") != "1",
        reason="Set RUN_LIVE_PUBCHEM_TESTS=1 to run live PubChem checks.",
    ),
]


@pytest.mark.parametrize(
    ("query", "expected_cid"),
    [("aspirin", 2244), ("ibuprofen", 3672), ("caffeine", 2519)],
)
async def test_required_compounds_resolve_from_live_pubchem(
    query: str,
    expected_cid: int,
) -> None:
    adapter = PubChemAdapter(Settings())
    try:
        cids = await adapter.resolve_name(query)
        compounds = await adapter.fetch_compounds(cids[:1])
    finally:
        await adapter.aclose()

    assert cids[0] == expected_cid
    assert compounds[0].cid == expected_cid
    assert compounds[0].source == "pubchem"
    assert compounds[0].molecular_formula is not None
    assert compounds[0].provenance


async def test_aspirin_structures_come_from_live_pubchem() -> None:
    adapter = PubChemAdapter(Settings())
    try:
        image = await adapter.fetch_structure(2244, "2d")
        conformer = await adapter.fetch_structure(2244, "3d")
    finally:
        await adapter.aclose()

    assert image.content.startswith(b"\x89PNG")
    assert image.media_type == "image/png"
    assert b"2244" in conformer.content
    assert conformer.media_type == "chemical/x-mdl-sdfile"

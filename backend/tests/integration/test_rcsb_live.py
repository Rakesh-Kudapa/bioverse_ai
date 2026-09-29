import os

import pytest

from app.adapters.rcsb import RcsbAdapter
from app.core.config import Settings

pytestmark = [
    pytest.mark.live,
    pytest.mark.skipif(
        os.getenv("RUN_LIVE_RCSB_TESTS") != "1",
        reason="Set RUN_LIVE_RCSB_TESTS=1 to run live RCSB checks.",
    ),
]


async def test_egfr_search_returns_experimental_rcsb_polymer_entities() -> None:
    adapter = RcsbAdapter(Settings())
    try:
        proteins = await adapter.search_proteins("EGFR")
    finally:
        await adapter.aclose()

    assert proteins
    assert all(protein.source == "rcsb_pdb" for protein in proteins)
    assert all("_" in protein.source_id for protein in proteins)
    assert all(protein.associated_structures for protein in proteins)
    assert all(protein.provenance for protein in proteins)


async def test_1m17_structure_and_ligand_are_source_reported() -> None:
    adapter = RcsbAdapter(Settings())
    try:
        structure = await adapter.fetch_structure("1M17")
    finally:
        await adapter.aclose()

    assert structure.pdb_id == "1M17"
    assert "X-RAY DIFFRACTION" in structure.experimental_methods
    assert structure.resolution_angstroms == 2.6
    assert any(
        entity.description == "epidermal growth factor receptor"
        for entity in structure.polymer_entities
    )
    assert any(ligand.chemical_component_id == "AQ4" for ligand in structure.ligands)
    assert structure.provenance


async def test_1d3z_nmr_missing_resolution_and_ligands_are_valid() -> None:
    adapter = RcsbAdapter(Settings())
    try:
        structure = await adapter.fetch_structure("1D3Z")
    finally:
        await adapter.aclose()

    assert structure.experimental_methods == ("SOLUTION NMR",)
    assert structure.resolution_angstroms is None
    assert structure.nonpolymer_entity_count == 0
    assert structure.ligands == ()


async def test_1m17_mmcif_file_is_retrievable_unmodified() -> None:
    adapter = RcsbAdapter(Settings())
    try:
        resource = await adapter.fetch_structure_file("1M17")
    finally:
        await adapter.aclose()

    assert resource.media_type == "chemical/x-mmcif"
    assert resource.content.startswith(b"data_1M17")
    assert b"_atom_site." in resource.content

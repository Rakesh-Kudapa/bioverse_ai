from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from app.models.compound import CompoundEntity, SourceProvenance, StructureReference


def test_compound_contract_preserves_nulls_and_provenance() -> None:
    source_url = "https://pubchem.ncbi.nlm.nih.gov/compound/2244"
    compound = CompoundEntity(
        id="compound:pubchem:2244",
        source_id="2244",
        cid=2244,
        name="Aspirin",
        external_ids={"pubchem_cid": "2244"},
        molecular_formula="C9H8O4",
        molecular_weight=180.16,
        canonical_smiles=None,
        isomeric_smiles=None,
        inchi=None,
        inchikey=None,
        xlogp=None,
        hydrogen_bond_donor_count=None,
        hydrogen_bond_acceptor_count=None,
        tpsa=None,
        has_3d_conformer=False,
        structure_2d=StructureReference(
            dimension="2d",
            format="png",
            endpoint="/api/v1/compounds/2244/structure/2d",
        ),
        source_url=source_url,
        provenance=(
            SourceProvenance(
                source_name="pubchem",
                source_record_id="2244",
                source_url=source_url,
                retrieved_at=datetime(2026, 9, 28, tzinfo=UTC),
                field_path="PropertyTable.Properties[].CID",
            ),
        ),
    )

    payload = compound.model_dump(mode="json")

    assert payload["canonical_smiles"] is None
    assert payload["structure_3d"] is None
    assert payload["provenance"][0]["source_name"] == "pubchem"


def test_compound_contract_rejects_unknown_fields() -> None:
    with pytest.raises(ValidationError):
        SourceProvenance.model_validate(
            {
                "source_name": "pubchem",
                "source_record_id": "2244",
                "source_url": "https://pubchem.ncbi.nlm.nih.gov/compound/2244",
                "retrieved_at": "2026-09-28T00:00:00Z",
                "field_path": "PropertyTable.Properties[].CID",
                "fabricated_confidence": 1.0,
            }
        )

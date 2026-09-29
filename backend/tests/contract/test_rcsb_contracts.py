import pytest
from pydantic import ValidationError

from app.models.protein import ProteinEntity
from app.models.structure import StructureEntity
from tests.factories import make_protein, make_structure


def test_protein_contract_is_normalized_and_strict() -> None:
    payload = make_protein().model_dump(mode="json")

    assert payload["type"] == "protein"
    assert payload["source"] == "rcsb_pdb"
    assert payload["source_id"] == "1M17_1"
    assert payload["associated_structures"][0]["pdb_id"] == "1M17"
    assert payload["provenance"][0]["source_name"] == "rcsb_pdb"

    payload["fabricated_function"] = "oncogenic"
    with pytest.raises(ValidationError):
        ProteinEntity.model_validate(payload)


def test_structure_contract_preserves_nested_entities_and_rejects_unknown_fields() -> None:
    payload = make_structure().model_dump(mode="json")

    assert payload["experimental_methods"] == ["X-RAY DIFFRACTION"]
    assert payload["ligands"][0]["chemical_component_id"] == "AQ4"
    assert payload["structure_reference"]["format"] == "mmcif"

    payload["predicted_quality"] = 0.99
    with pytest.raises(ValidationError):
        StructureEntity.model_validate(payload)


def test_missing_resolution_is_explicitly_valid() -> None:
    payload = make_structure().model_dump(mode="json")
    payload["resolution_angstroms"] = None
    payload["experimental_methods"] = ["SOLUTION NMR"]

    structure = StructureEntity.model_validate(payload)

    assert structure.resolution_angstroms is None

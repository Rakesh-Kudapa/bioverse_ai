"""Normalized BioVerse domain models."""

from app.models.compound import CompoundEntity, SourceProvenance, StructureReference

__all__ = ["CompoundEntity", "SourceProvenance", "StructureReference"]
from app.models.ligand import LigandEntity
from app.models.protein import ProteinEntity
from app.models.structure import StructureEntity

__all__ = ["LigandEntity", "ProteinEntity", "StructureEntity"]

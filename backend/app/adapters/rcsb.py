import asyncio
import logging
import re
from datetime import UTC, datetime
from time import monotonic
from typing import Any, Literal

import httpx
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from app.core.config import Settings
from app.core.errors import (
    EntityNotFoundError,
    InvalidExternalPayloadError,
    SourceRateLimitedError,
    SourceTimeoutError,
    SourceUnavailableError,
    StructureNotAvailableError,
)
from app.models.ligand import LigandEntity
from app.models.protein import ExternalReference, ProteinEntity, StructureSummary
from app.models.provenance import SourceProvenance
from app.models.resource import BinaryResource
from app.models.structure import (
    AssemblySummary,
    ChainIdentifiers,
    MacromolecularStructureReference,
    PolymerEntity,
    StructureEntity,
)

logger = logging.getLogger(__name__)

RCSB_SEARCH_URL = "https://search.rcsb.org/rcsbsearch/v2/query"
RCSB_GRAPHQL_URL = "https://data.rcsb.org/graphql"
RCSB_FILES_BASE_URL = "https://files.rcsb.org/download"

_PDB_ID_PATTERN = re.compile(r"^(?:[0-9][A-Z0-9]{3}|PDB_[A-Z0-9]{8})$")
_ENTITY_ID_PATTERN = re.compile(r"^[1-9][0-9]*$")

_PROTEIN_ENTITIES_QUERY = """
query ProteinEntities($ids: [String!]!) {
  polymer_entities(entity_ids: $ids) {
    rcsb_id
    rcsb_polymer_entity { pdbx_description }
    entity_poly { rcsb_entity_polymer_type rcsb_sample_sequence_length type }
    rcsb_polymer_entity_container_identifiers {
      entry_id entity_id auth_asym_ids asym_ids
      reference_sequence_identifiers { database_name database_accession }
    }
    rcsb_entity_source_organism {
      ncbi_scientific_name
      rcsb_gene_name { value }
    }
    entry {
      rcsb_id
      struct { title }
      exptl { method }
      rcsb_entry_info {
        resolution_combined polymer_entity_count nonpolymer_entity_count
      }
      rcsb_accession_info { deposit_date initial_release_date }
    }
  }
}
"""

_STRUCTURE_QUERY = """
query Structure($id: String!) {
  entry(entry_id: $id) {
    rcsb_id
    struct { title }
    exptl { method }
    rcsb_entry_info {
      resolution_combined polymer_entity_count nonpolymer_entity_count assembly_count
    }
    rcsb_accession_info { deposit_date initial_release_date revision_date }
    pdbx_database_status { status_code pdb_format_compatible }
    polymer_entities {
      rcsb_id
      rcsb_polymer_entity { pdbx_description }
      entity_poly { rcsb_entity_polymer_type rcsb_sample_sequence_length type }
      rcsb_polymer_entity_container_identifiers {
        entity_id auth_asym_ids asym_ids
        reference_sequence_identifiers { database_name database_accession }
      }
      rcsb_entity_source_organism { ncbi_scientific_name }
    }
    nonpolymer_entities {
      rcsb_id
      rcsb_nonpolymer_entity_container_identifiers { entity_id auth_asym_ids asym_ids }
      nonpolymer_comp { chem_comp { id name formula formula_weight type } }
    }
    assemblies {
      rcsb_id
      rcsb_assembly_container_identifiers { assembly_id }
      pdbx_struct_assembly { details method_details }
    }
  }
}
"""


class _SearchResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")

    result_type: str
    total_count: int = Field(ge=0)
    result_set: list[str]


class _ReferenceIdentifier(BaseModel):
    model_config = ConfigDict(extra="ignore")

    database_name: str
    database_accession: str


class _GeneName(BaseModel):
    model_config = ConfigDict(extra="ignore")

    value: str


class _SourceOrganism(BaseModel):
    model_config = ConfigDict(extra="ignore")

    ncbi_scientific_name: str | None = None
    rcsb_gene_name: list[_GeneName] | None = None


class _PolymerContainerIdentifiers(BaseModel):
    model_config = ConfigDict(extra="ignore")

    entry_id: str | None = None
    entity_id: str
    auth_asym_ids: list[str] | None = None
    asym_ids: list[str] | None = None
    reference_sequence_identifiers: list[_ReferenceIdentifier] | None = None


class _RcsbPolymerEntity(BaseModel):
    model_config = ConfigDict(extra="ignore")

    pdbx_description: str | None = None


class _EntityPoly(BaseModel):
    model_config = ConfigDict(extra="ignore")

    rcsb_entity_polymer_type: str | None = None
    rcsb_sample_sequence_length: int | None = Field(default=None, ge=0)
    type: str | None = None


class _Struct(BaseModel):
    model_config = ConfigDict(extra="ignore")

    title: str | None = None


class _ExperimentalMethod(BaseModel):
    model_config = ConfigDict(extra="ignore")

    method: str


class _EntryInfo(BaseModel):
    model_config = ConfigDict(extra="ignore")

    resolution_combined: list[float] | None = None
    polymer_entity_count: int | None = Field(default=None, ge=0)
    nonpolymer_entity_count: int | None = Field(default=None, ge=0)
    assembly_count: int | None = Field(default=None, ge=0)


class _AccessionInfo(BaseModel):
    model_config = ConfigDict(extra="ignore")

    deposit_date: str | None = None
    initial_release_date: str | None = None
    revision_date: str | None = None


class _DatabaseStatus(BaseModel):
    model_config = ConfigDict(extra="ignore")

    status_code: str | None = None
    pdb_format_compatible: str | None = None


class _EntrySummary(BaseModel):
    model_config = ConfigDict(extra="ignore")

    rcsb_id: str
    struct: _Struct | None = None
    exptl: list[_ExperimentalMethod] | None = None
    rcsb_entry_info: _EntryInfo | None = None
    rcsb_accession_info: _AccessionInfo | None = None


class _RawPolymerEntity(BaseModel):
    model_config = ConfigDict(extra="ignore")

    rcsb_id: str
    rcsb_polymer_entity: _RcsbPolymerEntity | None = None
    entity_poly: _EntityPoly | None = None
    rcsb_polymer_entity_container_identifiers: _PolymerContainerIdentifiers
    rcsb_entity_source_organism: list[_SourceOrganism] | None = None
    entry: _EntrySummary | None = None


class _ProteinData(BaseModel):
    model_config = ConfigDict(extra="ignore")

    polymer_entities: list[_RawPolymerEntity] | None = None


class _GraphQlError(BaseModel):
    model_config = ConfigDict(extra="ignore")

    message: str


class _ProteinEnvelope(BaseModel):
    model_config = ConfigDict(extra="ignore")

    data: _ProteinData | None
    errors: list[_GraphQlError] | None = None


class _NonpolymerIdentifiers(BaseModel):
    model_config = ConfigDict(extra="ignore")

    entity_id: str
    auth_asym_ids: list[str] | None = None
    asym_ids: list[str] | None = None


class _ChemicalComponent(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: str
    name: str | None = None
    formula: str | None = None
    formula_weight: float | None = Field(default=None, ge=0)
    type: str | None = None


class _NonpolymerCompound(BaseModel):
    model_config = ConfigDict(extra="ignore")

    chem_comp: _ChemicalComponent


class _RawNonpolymerEntity(BaseModel):
    model_config = ConfigDict(extra="ignore")

    rcsb_id: str
    rcsb_nonpolymer_entity_container_identifiers: _NonpolymerIdentifiers
    nonpolymer_comp: _NonpolymerCompound


class _AssemblyIdentifiers(BaseModel):
    model_config = ConfigDict(extra="ignore")

    assembly_id: str


class _PdbxStructAssembly(BaseModel):
    model_config = ConfigDict(extra="ignore")

    details: str | None = None
    method_details: str | None = None


class _RawAssembly(BaseModel):
    model_config = ConfigDict(extra="ignore")

    rcsb_id: str
    rcsb_assembly_container_identifiers: _AssemblyIdentifiers
    pdbx_struct_assembly: _PdbxStructAssembly | None = None


class _RawEntry(_EntrySummary):
    pdbx_database_status: _DatabaseStatus | None = None
    polymer_entities: list[_RawPolymerEntity] | None = None
    nonpolymer_entities: list[_RawNonpolymerEntity] | None = None
    assemblies: list[_RawAssembly] | None = None


class _EntryData(BaseModel):
    model_config = ConfigDict(extra="ignore")

    entry: _RawEntry | None = None


class _EntryEnvelope(BaseModel):
    model_config = ConfigDict(extra="ignore")

    data: _EntryData | None
    errors: list[_GraphQlError] | None = None


class RcsbAdapter:
    """Translate approved RCSB services into BioVerse-owned domain models."""

    def __init__(self, settings: Settings, *, client: httpx.AsyncClient | None = None) -> None:
        self._settings = settings
        self._owns_client = client is None
        self._client = client or httpx.AsyncClient(
            timeout=httpx.Timeout(settings.rcsb_timeout_seconds),
            headers={"User-Agent": "BioVerseAI/0.3 (source-grounded structure explorer)"},
            follow_redirects=False,
        )

    async def aclose(self) -> None:
        if self._owns_client:
            await self._client.aclose()

    async def search_proteins(self, query: str) -> tuple[ProteinEntity, ...]:
        search_payload: dict[str, Any] = {
            "query": {
                "type": "group",
                "logical_operator": "and",
                "nodes": [
                    {
                        "type": "terminal",
                        "service": "full_text",
                        "parameters": {"value": query},
                    },
                    {
                        "type": "terminal",
                        "service": "text",
                        "parameters": {
                            "attribute": "entity_poly.rcsb_entity_polymer_type",
                            "operator": "exact_match",
                            "value": "Protein",
                        },
                    },
                ],
            },
            "request_options": {
                "paginate": {"start": 0, "rows": self._settings.rcsb_max_search_results},
                "results_content_type": ["experimental"],
                "results_verbosity": "compact",
            },
            "return_type": "polymer_entity",
        }
        status_code, content = await self._request(
            "POST",
            RCSB_SEARCH_URL,
            json_payload=search_payload,
            expected_media_type="application/json",
            max_bytes=self._settings.rcsb_max_json_bytes,
            operation="search_proteins",
            allow_no_content=True,
        )
        if status_code == 204:
            return ()
        search = self._validate_json(_SearchResponse, content)
        if search.result_type != "polymer_entity":
            raise InvalidExternalPayloadError(
                "RCSB search returned an unexpected result type.", source="rcsb_pdb"
            )
        source_ids = tuple(
            dict.fromkeys(self._validate_polymer_entity_id(value) for value in search.result_set)
        )
        if not source_ids:
            return ()

        envelope = await self._graphql(
            _ProteinEnvelope,
            _PROTEIN_ENTITIES_QUERY,
            {"ids": list(source_ids)},
            operation="fetch_protein_entities",
        )
        if envelope.errors or envelope.data is None:
            raise InvalidExternalPayloadError(
                "RCSB returned an invalid protein-entity response.", source="rcsb_pdb"
            )
        raw_entities = envelope.data.polymer_entities or []
        retrieved_at = datetime.now(UTC)
        normalized = {
            item.rcsb_id.upper(): self._normalize_protein(item, retrieved_at=retrieved_at)
            for item in raw_entities
        }
        if any(source_id not in normalized for source_id in source_ids):
            raise InvalidExternalPayloadError(
                "RCSB omitted a requested protein entity.", source="rcsb_pdb"
            )
        return tuple(normalized[source_id] for source_id in source_ids)

    async def fetch_structure(self, pdb_id: str) -> StructureEntity:
        canonical_id = self.normalize_pdb_id(pdb_id)
        envelope = await self._graphql(
            _EntryEnvelope,
            _STRUCTURE_QUERY,
            {"id": canonical_id},
            operation="fetch_structure",
        )
        if envelope.errors:
            raise InvalidExternalPayloadError(
                "RCSB returned an invalid structure response.", source="rcsb_pdb"
            )
        if envelope.data is None or envelope.data.entry is None:
            raise EntityNotFoundError(
                f"RCSB PDB entry {canonical_id} was not found.", source="rcsb_pdb"
            )
        if self.normalize_pdb_id(envelope.data.entry.rcsb_id) != canonical_id:
            raise InvalidExternalPayloadError(
                "RCSB returned a different structure than requested.", source="rcsb_pdb"
            )
        return self._normalize_structure(envelope.data.entry, retrieved_at=datetime.now(UTC))

    async def fetch_structure_file(self, pdb_id: str) -> BinaryResource:
        canonical_id = self.normalize_pdb_id(pdb_id)
        try:
            _status, content = await self._request(
                "GET",
                f"{RCSB_FILES_BASE_URL}/{canonical_id}.cif",
                json_payload=None,
                expected_media_type=("application/octet-stream", "chemical/x-cif"),
                max_bytes=self._settings.rcsb_max_structure_bytes,
                operation="fetch_structure_file",
            )
        except EntityNotFoundError as error:
            raise StructureNotAvailableError(
                f"RCSB does not provide an mmCIF file for {canonical_id}.",
                source="rcsb_pdb",
            ) from error
        return BinaryResource(
            content=content,
            media_type="chemical/x-mmcif",
            filename=f"{canonical_id}.cif",
        )

    async def _graphql[EnvelopeT: BaseModel](
        self,
        model: type[EnvelopeT],
        query: str,
        variables: dict[str, Any],
        *,
        operation: str,
    ) -> EnvelopeT:
        _status, content = await self._request(
            "POST",
            RCSB_GRAPHQL_URL,
            json_payload={"query": query, "variables": variables},
            expected_media_type="application/json",
            max_bytes=self._settings.rcsb_max_json_bytes,
            operation=operation,
        )
        return self._validate_json(model, content)

    async def _request(
        self,
        method: Literal["GET", "POST"],
        url: str,
        *,
        json_payload: dict[str, Any] | None,
        expected_media_type: str | tuple[str, ...],
        max_bytes: int,
        operation: str,
        allow_no_content: bool = False,
    ) -> tuple[int, bytes]:
        attempts = self._settings.rcsb_retry_count + 1
        for attempt in range(attempts):
            started_at = monotonic()
            try:
                status_code, content_type, content = await self._perform_request(
                    method,
                    url,
                    json_payload=json_payload,
                    max_bytes=max_bytes,
                )
            except httpx.TimeoutException as error:
                if attempt + 1 < attempts:
                    await self._backoff(attempt)
                    continue
                raise SourceTimeoutError("RCSB request timed out.", source="rcsb_pdb") from error
            except httpx.RequestError as error:
                if attempt + 1 < attempts:
                    await self._backoff(attempt)
                    continue
                raise SourceUnavailableError("RCSB is unavailable.", source="rcsb_pdb") from error

            logger.info(
                "RCSB request completed",
                extra={
                    "event": "source_request",
                    "source_adapter": "rcsb_pdb",
                    "operation": operation,
                    "source_latency_ms": round((monotonic() - started_at) * 1000, 2),
                    "source_status_code": status_code,
                },
            )

            if status_code in {429, 500, 502, 503} and attempt + 1 < attempts:
                await self._backoff(attempt)
                continue
            if allow_no_content and status_code == 204:
                return status_code, b""
            self._raise_for_status(status_code)
            normalized_content_type = content_type.partition(";")[0].strip().lower()
            allowed_media_types = (
                (expected_media_type,)
                if isinstance(expected_media_type, str)
                else expected_media_type
            )
            if normalized_content_type not in allowed_media_types:
                raise InvalidExternalPayloadError(
                    f"RCSB returned an unexpected content type for {operation}.",
                    source="rcsb_pdb",
                )
            return status_code, content
        raise SourceUnavailableError("RCSB is unavailable.", source="rcsb_pdb")

    async def _perform_request(
        self,
        method: Literal["GET", "POST"],
        url: str,
        *,
        json_payload: dict[str, Any] | None,
        max_bytes: int,
    ) -> tuple[int, str, bytes]:
        async with self._client.stream(method, url, json=json_payload) as response:
            content = bytearray()
            async for chunk in response.aiter_bytes():
                content.extend(chunk)
                if len(content) > max_bytes:
                    raise InvalidExternalPayloadError(
                        "RCSB response exceeded the configured size limit.",
                        source="rcsb_pdb",
                    )
            return response.status_code, response.headers.get("content-type", ""), bytes(content)

    async def _backoff(self, attempt: int) -> None:
        delay = self._settings.rcsb_retry_backoff_seconds * (2**attempt)
        if delay > 0:
            await asyncio.sleep(delay)

    @staticmethod
    def _raise_for_status(status_code: int) -> None:
        if status_code == 404:
            raise EntityNotFoundError("The requested RCSB record was not found.", source="rcsb_pdb")
        if status_code in {429, 503}:
            raise SourceRateLimitedError(
                "RCSB is busy or rate limited; retry later.", source="rcsb_pdb"
            )
        if status_code == 504:
            raise SourceTimeoutError("RCSB request timed out.", source="rcsb_pdb")
        if status_code >= 500:
            raise SourceUnavailableError("RCSB is unavailable.", source="rcsb_pdb")
        if status_code != 200:
            raise InvalidExternalPayloadError(
                "RCSB rejected the source request.", source="rcsb_pdb"
            )

    @staticmethod
    def _validate_json[ModelT: BaseModel](model: type[ModelT], content: bytes) -> ModelT:
        try:
            payload = httpx.Response(200, content=content).json()
            return model.model_validate(payload)
        except (ValueError, ValidationError) as error:
            raise InvalidExternalPayloadError(
                "RCSB returned a payload that does not match the expected contract.",
                source="rcsb_pdb",
            ) from error

    @classmethod
    def normalize_pdb_id(cls, pdb_id: str) -> str:
        canonical = pdb_id.strip().upper()
        if not _PDB_ID_PATTERN.fullmatch(canonical):
            raise InvalidExternalPayloadError("The PDB identifier is invalid.", source="rcsb_pdb")
        return canonical

    @classmethod
    def _validate_polymer_entity_id(cls, source_id: str) -> str:
        try:
            pdb_id, entity_id = source_id.rsplit("_", 1)
        except ValueError as error:
            raise InvalidExternalPayloadError(
                "RCSB returned an invalid polymer-entity identifier.", source="rcsb_pdb"
            ) from error
        canonical_pdb_id = cls.normalize_pdb_id(pdb_id)
        if not _ENTITY_ID_PATTERN.fullmatch(entity_id):
            raise InvalidExternalPayloadError(
                "RCSB returned an invalid polymer-entity identifier.", source="rcsb_pdb"
            )
        return f"{canonical_pdb_id}_{entity_id}"

    @classmethod
    def _normalize_protein(
        cls,
        raw: _RawPolymerEntity,
        *,
        retrieved_at: datetime,
    ) -> ProteinEntity:
        source_id = cls._validate_polymer_entity_id(raw.rcsb_id)
        identifiers = raw.rcsb_polymer_entity_container_identifiers
        if raw.entry is None:
            raise InvalidExternalPayloadError(
                "RCSB protein data omitted its parent entry.", source="rcsb_pdb"
            )
        pdb_id = cls.normalize_pdb_id(identifiers.entry_id or raw.entry.rcsb_id)
        source_url = f"https://www.rcsb.org/structure/{pdb_id}"
        provenance = cls._protein_provenance(raw, source_id, source_url, retrieved_at)
        organisms = tuple(
            cls._unique(
                item.ncbi_scientific_name
                for item in (raw.rcsb_entity_source_organism or [])
                if item.ncbi_scientific_name
            )
        )
        gene_symbols = tuple(
            cls._unique(
                gene.value
                for organism in (raw.rcsb_entity_source_organism or [])
                for gene in (organism.rcsb_gene_name or [])
                if gene.value
            )
        )
        refs = cls._external_references(identifiers.reference_sequence_identifiers)
        summary = cls._normalize_structure_summary(raw.entry, retrieved_at=retrieved_at)
        entity_poly = raw.entity_poly
        name = raw.rcsb_polymer_entity.pdbx_description if raw.rcsb_polymer_entity else None
        return ProteinEntity(
            id=f"protein:rcsb:{source_id}",
            source_id=source_id,
            name=name,
            gene_symbols=gene_symbols,
            pdb_id=pdb_id,
            entity_id=identifiers.entity_id,
            polymer_type=entity_poly.rcsb_entity_polymer_type if entity_poly else None,
            sequence_length=entity_poly.rcsb_sample_sequence_length if entity_poly else None,
            auth_chain_ids=tuple(identifiers.auth_asym_ids or []),
            asym_ids=tuple(identifiers.asym_ids or []),
            source_organisms=organisms,
            external_references=refs,
            associated_structures=(summary,),
            source_url=source_url,
            provenance=provenance,
        )

    @classmethod
    def _normalize_structure(
        cls,
        raw: _RawEntry,
        *,
        retrieved_at: datetime,
    ) -> StructureEntity:
        pdb_id = cls.normalize_pdb_id(raw.rcsb_id)
        source_url = f"https://www.rcsb.org/structure/{pdb_id}"
        entry_info = raw.rcsb_entry_info
        accession = raw.rcsb_accession_info
        methods = tuple(cls._unique(item.method for item in (raw.exptl or [])))
        resolutions = entry_info.resolution_combined if entry_info else None
        resolution = resolutions[0] if resolutions else None
        polymers = tuple(
            cls._normalize_polymer(item, pdb_id, source_url, retrieved_at)
            for item in (raw.polymer_entities or [])
        )
        ligands = tuple(
            cls._normalize_ligand(item, pdb_id, source_url, retrieved_at)
            for item in (raw.nonpolymer_entities or [])
        )
        assemblies = tuple(
            cls._normalize_assembly(item, pdb_id, source_url, retrieved_at)
            for item in (raw.assemblies or [])
        )
        status = raw.pdbx_database_status
        return StructureEntity(
            id=f"structure:pdb:{pdb_id}",
            source_id=pdb_id,
            pdb_id=pdb_id,
            title=raw.struct.title if raw.struct else None,
            experimental_methods=methods,
            resolution_angstroms=resolution,
            deposition_date=accession.deposit_date if accession else None,
            release_date=accession.initial_release_date if accession else None,
            revision_date=accession.revision_date if accession else None,
            entry_status=status.status_code if status else None,
            polymer_entity_count=entry_info.polymer_entity_count if entry_info else None,
            nonpolymer_entity_count=(entry_info.nonpolymer_entity_count if entry_info else None),
            assembly_count=entry_info.assembly_count if entry_info else None,
            polymer_entities=polymers,
            chains=tuple(polymer.chains for polymer in polymers),
            ligands=ligands,
            assemblies=assemblies,
            structure_reference=MacromolecularStructureReference(
                endpoint=f"/api/v1/structures/{pdb_id}/file",
                source_url=f"{RCSB_FILES_BASE_URL}/{pdb_id}.cif",
            ),
            source_url=source_url,
            provenance=cls._entry_provenance(raw, pdb_id, source_url, retrieved_at),
        )

    @classmethod
    def _normalize_structure_summary(
        cls,
        raw: _EntrySummary,
        *,
        retrieved_at: datetime,
    ) -> StructureSummary:
        pdb_id = cls.normalize_pdb_id(raw.rcsb_id)
        source_url = f"https://www.rcsb.org/structure/{pdb_id}"
        entry_info = raw.rcsb_entry_info
        resolutions = entry_info.resolution_combined if entry_info else None
        provenance = [cls._provenance(pdb_id, source_url, retrieved_at, "entry.rcsb_id")]
        fields: tuple[tuple[str, object | None], ...] = (
            ("entry.struct.title", raw.struct.title if raw.struct else None),
            ("entry.exptl[].method", raw.exptl),
            ("entry.rcsb_entry_info.resolution_combined", resolutions),
            (
                "entry.rcsb_accession_info.initial_release_date",
                raw.rcsb_accession_info.initial_release_date if raw.rcsb_accession_info else None,
            ),
        )
        for path, value in fields:
            if value is not None:
                provenance.append(cls._provenance(pdb_id, source_url, retrieved_at, path))
        return StructureSummary(
            id=f"structure:pdb:{pdb_id}",
            pdb_id=pdb_id,
            title=raw.struct.title if raw.struct else None,
            experimental_methods=tuple(cls._unique(item.method for item in (raw.exptl or []))),
            resolution_angstroms=resolutions[0] if resolutions else None,
            release_date=(
                raw.rcsb_accession_info.initial_release_date if raw.rcsb_accession_info else None
            ),
            detail_endpoint=f"/api/v1/structures/{pdb_id}",
            provenance=tuple(provenance),
        )

    @classmethod
    def _normalize_polymer(
        cls,
        raw: _RawPolymerEntity,
        pdb_id: str,
        source_url: str,
        retrieved_at: datetime,
    ) -> PolymerEntity:
        identifiers = raw.rcsb_polymer_entity_container_identifiers
        source_id = cls._validate_polymer_entity_id(raw.rcsb_id)
        entity_poly = raw.entity_poly
        description = raw.rcsb_polymer_entity.pdbx_description if raw.rcsb_polymer_entity else None
        organisms = tuple(
            cls._unique(
                item.ncbi_scientific_name
                for item in (raw.rcsb_entity_source_organism or [])
                if item.ncbi_scientific_name
            )
        )
        provenance = [
            cls._provenance(source_id, source_url, retrieved_at, "entry.polymer_entities[].rcsb_id")
        ]
        values: tuple[tuple[str, object | None], ...] = (
            ("entry.polymer_entities[].rcsb_polymer_entity.pdbx_description", description),
            (
                "entry.polymer_entities[].entity_poly.rcsb_entity_polymer_type",
                entity_poly.rcsb_entity_polymer_type if entity_poly else None,
            ),
            (
                "entry.polymer_entities[].entity_poly.rcsb_sample_sequence_length",
                entity_poly.rcsb_sample_sequence_length if entity_poly else None,
            ),
            (
                "entry.polymer_entities[].rcsb_polymer_entity_container_identifiers.auth_asym_ids",
                identifiers.auth_asym_ids,
            ),
            (
                "entry.polymer_entities[].rcsb_polymer_entity_container_identifiers.asym_ids",
                identifiers.asym_ids,
            ),
            (
                "entry.polymer_entities[].rcsb_entity_source_organism",
                raw.rcsb_entity_source_organism,
            ),
            (
                "entry.polymer_entities[].rcsb_polymer_entity_container_identifiers.reference_sequence_identifiers",
                identifiers.reference_sequence_identifiers,
            ),
        )
        for path, value in values:
            if value is not None:
                provenance.append(cls._provenance(source_id, source_url, retrieved_at, path))
        chains = ChainIdentifiers(
            entity_id=identifiers.entity_id,
            auth_chain_ids=tuple(identifiers.auth_asym_ids or []),
            asym_ids=tuple(identifiers.asym_ids or []),
        )
        return PolymerEntity(
            source_id=source_id,
            entity_id=identifiers.entity_id,
            description=description,
            polymer_type=entity_poly.rcsb_entity_polymer_type if entity_poly else None,
            sequence_length=entity_poly.rcsb_sample_sequence_length if entity_poly else None,
            chains=chains,
            source_organisms=organisms,
            external_references=cls._external_references(
                identifiers.reference_sequence_identifiers
            ),
            provenance=tuple(provenance),
        )

    @classmethod
    def _normalize_ligand(
        cls,
        raw: _RawNonpolymerEntity,
        pdb_id: str,
        source_url: str,
        retrieved_at: datetime,
    ) -> LigandEntity:
        identifiers = raw.rcsb_nonpolymer_entity_container_identifiers
        component = raw.nonpolymer_comp.chem_comp
        source_id = raw.rcsb_id
        provenance = [
            cls._provenance(
                source_id, source_url, retrieved_at, "entry.nonpolymer_entities[].rcsb_id"
            )
        ]
        values: tuple[tuple[str, object | None], ...] = (
            ("entry.nonpolymer_entities[].nonpolymer_comp.chem_comp.id", component.id),
            ("entry.nonpolymer_entities[].nonpolymer_comp.chem_comp.name", component.name),
            ("entry.nonpolymer_entities[].nonpolymer_comp.chem_comp.formula", component.formula),
            (
                "entry.nonpolymer_entities[].nonpolymer_comp.chem_comp.formula_weight",
                component.formula_weight,
            ),
            (
                "entry.nonpolymer_entities[].rcsb_nonpolymer_entity_container_identifiers.auth_asym_ids",
                identifiers.auth_asym_ids,
            ),
            (
                "entry.nonpolymer_entities[].rcsb_nonpolymer_entity_container_identifiers.asym_ids",
                identifiers.asym_ids,
            ),
        )
        for path, value in values:
            if value is not None:
                provenance.append(cls._provenance(source_id, source_url, retrieved_at, path))
        return LigandEntity(
            id=f"ligand:rcsb:{source_id}",
            source_id=source_id,
            pdb_id=pdb_id,
            entity_id=identifiers.entity_id,
            chemical_component_id=component.id,
            name=component.name,
            formula=component.formula,
            molecular_weight=component.formula_weight,
            auth_chain_ids=tuple(identifiers.auth_asym_ids or []),
            asym_ids=tuple(identifiers.asym_ids or []),
            source_url=source_url,
            provenance=tuple(provenance),
        )

    @classmethod
    def _normalize_assembly(
        cls,
        raw: _RawAssembly,
        pdb_id: str,
        source_url: str,
        retrieved_at: datetime,
    ) -> AssemblySummary:
        details = raw.pdbx_struct_assembly
        provenance = [
            cls._provenance(raw.rcsb_id, source_url, retrieved_at, "entry.assemblies[].rcsb_id")
        ]
        if details and details.details is not None:
            provenance.append(
                cls._provenance(
                    raw.rcsb_id,
                    source_url,
                    retrieved_at,
                    "entry.assemblies[].pdbx_struct_assembly.details",
                )
            )
        if details and details.method_details is not None:
            provenance.append(
                cls._provenance(
                    raw.rcsb_id,
                    source_url,
                    retrieved_at,
                    "entry.assemblies[].pdbx_struct_assembly.method_details",
                )
            )
        return AssemblySummary(
            source_id=raw.rcsb_id,
            assembly_id=raw.rcsb_assembly_container_identifiers.assembly_id,
            details=details.details if details else None,
            method_details=details.method_details if details else None,
            provenance=tuple(provenance),
        )

    @classmethod
    def _protein_provenance(
        cls,
        raw: _RawPolymerEntity,
        source_id: str,
        source_url: str,
        retrieved_at: datetime,
    ) -> tuple[SourceProvenance, ...]:
        identifiers = raw.rcsb_polymer_entity_container_identifiers
        entity_poly = raw.entity_poly
        values: tuple[tuple[str, object | None], ...] = (
            ("polymer_entities[].rcsb_id", raw.rcsb_id),
            (
                "polymer_entities[].rcsb_polymer_entity.pdbx_description",
                raw.rcsb_polymer_entity.pdbx_description if raw.rcsb_polymer_entity else None,
            ),
            (
                "polymer_entities[].entity_poly.rcsb_entity_polymer_type",
                entity_poly.rcsb_entity_polymer_type if entity_poly else None,
            ),
            (
                "polymer_entities[].entity_poly.rcsb_sample_sequence_length",
                entity_poly.rcsb_sample_sequence_length if entity_poly else None,
            ),
            (
                "polymer_entities[].rcsb_polymer_entity_container_identifiers.auth_asym_ids",
                identifiers.auth_asym_ids,
            ),
            (
                "polymer_entities[].rcsb_polymer_entity_container_identifiers.asym_ids",
                identifiers.asym_ids,
            ),
            ("polymer_entities[].rcsb_entity_source_organism", raw.rcsb_entity_source_organism),
            (
                "polymer_entities[].rcsb_polymer_entity_container_identifiers.reference_sequence_identifiers",
                identifiers.reference_sequence_identifiers,
            ),
        )
        return tuple(
            cls._provenance(source_id, source_url, retrieved_at, path)
            for path, value in values
            if value is not None
        )

    @classmethod
    def _entry_provenance(
        cls,
        raw: _RawEntry,
        pdb_id: str,
        source_url: str,
        retrieved_at: datetime,
    ) -> tuple[SourceProvenance, ...]:
        info = raw.rcsb_entry_info
        accession = raw.rcsb_accession_info
        status = raw.pdbx_database_status
        values: tuple[tuple[str, object | None], ...] = (
            ("entry.rcsb_id", raw.rcsb_id),
            ("entry.struct.title", raw.struct.title if raw.struct else None),
            ("entry.exptl[].method", raw.exptl),
            (
                "entry.rcsb_entry_info.resolution_combined",
                info.resolution_combined if info else None,
            ),
            (
                "entry.rcsb_accession_info.deposit_date",
                accession.deposit_date if accession else None,
            ),
            (
                "entry.rcsb_accession_info.initial_release_date",
                accession.initial_release_date if accession else None,
            ),
            (
                "entry.rcsb_accession_info.revision_date",
                accession.revision_date if accession else None,
            ),
            ("entry.pdbx_database_status.status_code", status.status_code if status else None),
            (
                "entry.rcsb_entry_info.polymer_entity_count",
                info.polymer_entity_count if info else None,
            ),
            (
                "entry.rcsb_entry_info.nonpolymer_entity_count",
                info.nonpolymer_entity_count if info else None,
            ),
            ("entry.rcsb_entry_info.assembly_count", info.assembly_count if info else None),
        )
        return tuple(
            cls._provenance(pdb_id, source_url, retrieved_at, path)
            for path, value in values
            if value is not None
        )

    @staticmethod
    def _external_references(
        raw: list[_ReferenceIdentifier] | None,
    ) -> tuple[ExternalReference, ...]:
        return tuple(
            ExternalReference(
                database_name=item.database_name,
                database_accession=item.database_accession,
            )
            for item in (raw or [])
        )

    @staticmethod
    def _provenance(
        source_record_id: str,
        source_url: str,
        retrieved_at: datetime,
        field_path: str,
    ) -> SourceProvenance:
        return SourceProvenance(
            source_name="rcsb_pdb",
            source_record_id=source_record_id,
            source_url=source_url,
            retrieved_at=retrieved_at,
            field_path=field_path,
        )

    @staticmethod
    def _unique(values: Any) -> list[str]:
        seen: set[str] = set()
        result: list[str] = []
        for value in values:
            if value not in seen:
                seen.add(value)
                result.append(value)
        return result

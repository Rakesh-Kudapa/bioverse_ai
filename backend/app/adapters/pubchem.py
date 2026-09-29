import asyncio
import logging
from datetime import UTC, datetime
from time import monotonic
from typing import Any, Literal
from urllib.parse import quote

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
from app.models.compound import CompoundEntity, SourceProvenance, StructureReference
from app.models.resource import BinaryResource

logger = logging.getLogger(__name__)

PUBCHEM_BASE_URL = "https://pubchem.ncbi.nlm.nih.gov"
_MAX_JSON_BYTES = 1_000_000
_PROPERTY_NAMES = (
    "Title",
    "MolecularFormula",
    "MolecularWeight",
    "ConnectivitySMILES",
    "SMILES",
    "InChI",
    "InChIKey",
    "XLogP",
    "HBondDonorCount",
    "HBondAcceptorCount",
    "TPSA",
    "ConformerCount3D",
)


class _PubChemIdentifierList(BaseModel):
    model_config = ConfigDict(extra="ignore")

    cid: list[int] = Field(alias="CID")


class _PubChemIdentifierResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")

    identifier_list: _PubChemIdentifierList = Field(alias="IdentifierList")


class _PubChemProperty(BaseModel):
    model_config = ConfigDict(extra="ignore")

    cid: int = Field(alias="CID", gt=0)
    title: str | None = Field(default=None, alias="Title")
    molecular_formula: str | None = Field(default=None, alias="MolecularFormula")
    molecular_weight: float | None = Field(default=None, alias="MolecularWeight")
    smiles: str | None = Field(default=None, alias="SMILES")
    connectivity_smiles: str | None = Field(default=None, alias="ConnectivitySMILES")
    inchi: str | None = Field(default=None, alias="InChI")
    inchikey: str | None = Field(default=None, alias="InChIKey")
    xlogp: float | None = Field(default=None, alias="XLogP")
    tpsa: float | None = Field(default=None, alias="TPSA")
    hydrogen_bond_donor_count: int | None = Field(default=None, alias="HBondDonorCount")
    hydrogen_bond_acceptor_count: int | None = Field(
        default=None,
        alias="HBondAcceptorCount",
    )
    conformer_count_3d: int = Field(alias="ConformerCount3D", ge=0)


class _PubChemPropertyTable(BaseModel):
    model_config = ConfigDict(extra="ignore")

    properties: list[_PubChemProperty] = Field(alias="Properties")


class _PubChemPropertyResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")

    property_table: _PubChemPropertyTable = Field(alias="PropertyTable")


class PubChemAdapter:
    """Translate PubChem PUG REST responses into BioVerse-owned models."""

    def __init__(self, settings: Settings, *, client: httpx.AsyncClient | None = None) -> None:
        self._settings = settings
        self._owns_client = client is None
        self._client = client or httpx.AsyncClient(
            base_url=PUBCHEM_BASE_URL,
            timeout=httpx.Timeout(settings.pubchem_timeout_seconds),
            headers={"User-Agent": "BioVerseAI/0.2 (source-grounded compound explorer)"},
            follow_redirects=False,
        )

    async def aclose(self) -> None:
        if self._owns_client:
            await self._client.aclose()

    async def resolve_name(self, name: str) -> tuple[int, ...]:
        encoded_name = quote(name, safe="")
        try:
            payload = await self._request_json(
                f"/rest/pug/compound/name/{encoded_name}/cids/JSON",
                operation="resolve_name",
            )
        except EntityNotFoundError:
            return ()
        response = self._validate_json(_PubChemIdentifierResponse, payload)
        return self._validated_cids(response.identifier_list.cid)

    async def fetch_compounds(self, cids: tuple[int, ...]) -> tuple[CompoundEntity, ...]:
        if not cids:
            return ()
        validated_cids = self._validated_cids(cids)
        cid_path = ",".join(str(cid) for cid in validated_cids)
        property_path = ",".join(_PROPERTY_NAMES)
        payload = await self._request_json(
            f"/rest/pug/compound/cid/{cid_path}/property/{property_path}/JSON",
            operation="fetch_properties",
        )
        response = self._validate_json(_PubChemPropertyResponse, payload)
        retrieved_at = datetime.now(UTC)
        requested = set(validated_cids)
        compounds = tuple(
            self._normalize_property(item, retrieved_at=retrieved_at)
            for item in response.property_table.properties
            if item.cid in requested
        )
        if not compounds:
            raise EntityNotFoundError(
                "No PubChem compound was found for the requested CID.",
                source="pubchem",
            )
        return compounds

    async def fetch_similar_cids(
        self,
        cid: int,
        *,
        threshold: int,
        limit: int,
    ) -> tuple[int, ...]:
        self._validate_cid(cid)
        payload = await self._request_json(
            f"/rest/pug/compound/fastsimilarity_2d/cid/{cid}/cids/JSON",
            params={"Threshold": threshold, "MaxRecords": limit + 1},
            operation="fetch_similar_cids",
        )
        response = self._validate_json(_PubChemIdentifierResponse, payload)
        return tuple(
            result_cid
            for result_cid in self._validated_cids(response.identifier_list.cid)
            if result_cid != cid
        )[:limit]

    async def fetch_structure(self, cid: int, dimension: Literal["2d", "3d"]) -> BinaryResource:
        self._validate_cid(cid)
        output_format = "PNG" if dimension == "2d" else "SDF"
        media_type = "image/png" if dimension == "2d" else "chemical/x-mdl-sdfile"
        extension = "png" if dimension == "2d" else "sdf"
        try:
            content = await self._request_bytes(
                f"/rest/pug/compound/cid/{cid}/{output_format}",
                params={"record_type": dimension},
                expected_media_type=media_type,
                max_bytes=self._settings.pubchem_max_structure_bytes,
                operation=f"fetch_structure_{dimension}",
            )
        except EntityNotFoundError as error:
            raise StructureNotAvailableError(
                f"PubChem does not provide a {dimension.upper()} structure for CID {cid}.",
                source="pubchem",
            ) from error
        return BinaryResource(
            content=content,
            media_type=media_type,
            filename=f"pubchem-{cid}-{dimension}.{extension}",
        )

    async def _request_json(
        self,
        path: str,
        *,
        params: dict[str, int | str] | None = None,
        operation: str,
    ) -> Any:
        content = await self._request_bytes(
            path,
            params=params,
            expected_media_type="application/json",
            max_bytes=_MAX_JSON_BYTES,
            operation=operation,
        )
        try:
            return httpx.Response(200, content=content).json()
        except ValueError as error:
            raise InvalidExternalPayloadError(
                "PubChem returned malformed JSON.",
                source="pubchem",
            ) from error

    async def _request_bytes(
        self,
        path: str,
        *,
        params: dict[str, int | str] | None,
        expected_media_type: str,
        max_bytes: int,
        operation: str,
    ) -> bytes:
        attempts = self._settings.pubchem_retry_count + 1
        last_request_error: httpx.RequestError | None = None

        for attempt in range(attempts):
            started_at = monotonic()
            try:
                status_code, content_type, content = await self._perform_request(
                    path,
                    params=params,
                    max_bytes=max_bytes,
                )
            except httpx.TimeoutException as error:
                last_request_error = error
                if attempt + 1 < attempts:
                    await self._backoff(attempt)
                    continue
                raise SourceTimeoutError("PubChem request timed out.", source="pubchem") from error
            except httpx.RequestError as error:
                last_request_error = error
                if attempt + 1 < attempts:
                    await self._backoff(attempt)
                    continue
                raise SourceUnavailableError("PubChem is unavailable.", source="pubchem") from error

            latency_ms = round((monotonic() - started_at) * 1000, 2)
            logger.info(
                "PubChem request completed",
                extra={
                    "event": "source_request",
                    "source_adapter": "pubchem",
                    "operation": operation,
                    "source_latency_ms": latency_ms,
                    "source_status_code": status_code,
                },
            )

            if status_code in {429, 503} and attempt + 1 < attempts:
                await self._backoff(attempt)
                continue
            if status_code in {500, 502} and attempt + 1 < attempts:
                await self._backoff(attempt)
                continue
            self._raise_for_status(status_code)

            normalized_content_type = content_type.partition(";")[0].strip().lower()
            if normalized_content_type != expected_media_type:
                raise InvalidExternalPayloadError(
                    f"PubChem returned an unexpected content type for {operation}.",
                    source="pubchem",
                )
            return content

        if last_request_error is not None:
            raise SourceUnavailableError(
                "PubChem is unavailable.",
                source="pubchem",
            ) from last_request_error
        raise SourceUnavailableError("PubChem is unavailable.", source="pubchem")

    async def _perform_request(
        self,
        path: str,
        *,
        params: dict[str, int | str] | None,
        max_bytes: int,
    ) -> tuple[int, str, bytes]:
        async with self._client.stream("GET", path, params=params) as response:
            content = bytearray()
            async for chunk in response.aiter_bytes():
                content.extend(chunk)
                if len(content) > max_bytes:
                    raise InvalidExternalPayloadError(
                        "PubChem response exceeded the configured size limit.",
                        source="pubchem",
                    )
            return (
                response.status_code,
                response.headers.get("content-type", ""),
                bytes(content),
            )

    async def _backoff(self, attempt: int) -> None:
        delay = self._settings.pubchem_retry_backoff_seconds * (2**attempt)
        if delay > 0:
            await asyncio.sleep(delay)

    @staticmethod
    def _raise_for_status(status_code: int) -> None:
        if status_code == 404:
            raise EntityNotFoundError(
                "The requested PubChem record was not found.",
                source="pubchem",
            )
        if status_code in {429, 503}:
            raise SourceRateLimitedError(
                "PubChem is busy or rate limited; retry later.",
                source="pubchem",
            )
        if status_code == 504:
            raise SourceTimeoutError("PubChem request timed out.", source="pubchem")
        if status_code >= 500:
            raise SourceUnavailableError("PubChem is unavailable.", source="pubchem")
        if status_code != 200:
            raise InvalidExternalPayloadError(
                "PubChem rejected the source request.",
                source="pubchem",
            )

    @staticmethod
    def _validate_json(model: type[BaseModel], payload: Any) -> Any:
        try:
            return model.model_validate(payload)
        except ValidationError as error:
            raise InvalidExternalPayloadError(
                "PubChem returned a payload that does not match the expected contract.",
                source="pubchem",
            ) from error

    @classmethod
    def _validated_cids(cls, cids: list[int] | tuple[int, ...]) -> tuple[int, ...]:
        validated: list[int] = []
        seen: set[int] = set()
        for cid in cids:
            cls._validate_cid(cid)
            if cid not in seen:
                validated.append(cid)
                seen.add(cid)
        return tuple(validated)

    @staticmethod
    def _validate_cid(cid: int) -> None:
        if cid <= 0:
            raise InvalidExternalPayloadError(
                "PubChem returned an invalid compound identifier.",
                source="pubchem",
            )

    @staticmethod
    def _normalize_property(
        item: _PubChemProperty,
        *,
        retrieved_at: datetime,
    ) -> CompoundEntity:
        source_id = str(item.cid)
        source_url = f"https://pubchem.ncbi.nlm.nih.gov/compound/{item.cid}"
        provenance: list[SourceProvenance] = []

        def add_provenance(field_path: str) -> None:
            provenance.append(
                SourceProvenance(
                    source_name="pubchem",
                    source_record_id=source_id,
                    source_url=source_url,
                    retrieved_at=retrieved_at,
                    field_path=f"PropertyTable.Properties[].{field_path}",
                )
            )

        add_provenance("CID")
        field_values: tuple[tuple[str, object | None], ...] = (
            ("Title", item.title),
            ("MolecularFormula", item.molecular_formula),
            ("MolecularWeight", item.molecular_weight),
            ("ConnectivitySMILES", item.connectivity_smiles),
            ("SMILES", item.smiles),
            ("InChI", item.inchi),
            ("InChIKey", item.inchikey),
            ("XLogP", item.xlogp),
            ("HBondDonorCount", item.hydrogen_bond_donor_count),
            ("HBondAcceptorCount", item.hydrogen_bond_acceptor_count),
            ("TPSA", item.tpsa),
            ("ConformerCount3D", item.conformer_count_3d),
        )
        for field_path, value in field_values:
            if value is not None:
                add_provenance(field_path)

        has_3d_conformer = item.conformer_count_3d > 0
        return CompoundEntity(
            id=f"compound:pubchem:{item.cid}",
            source_id=source_id,
            cid=item.cid,
            name=item.title,
            external_ids={"pubchem_cid": source_id},
            molecular_formula=item.molecular_formula,
            molecular_weight=item.molecular_weight,
            canonical_smiles=item.connectivity_smiles,
            isomeric_smiles=item.smiles,
            inchi=item.inchi,
            inchikey=item.inchikey,
            xlogp=item.xlogp,
            hydrogen_bond_donor_count=item.hydrogen_bond_donor_count,
            hydrogen_bond_acceptor_count=item.hydrogen_bond_acceptor_count,
            tpsa=item.tpsa,
            has_3d_conformer=has_3d_conformer,
            structure_2d=StructureReference(
                dimension="2d",
                format="png",
                endpoint=f"/api/v1/compounds/{item.cid}/structure/2d",
            ),
            structure_3d=(
                StructureReference(
                    dimension="3d",
                    format="sdf",
                    endpoint=f"/api/v1/compounds/{item.cid}/structure/3d",
                )
                if has_3d_conformer
                else None
            ),
            source_url=source_url,
            provenance=tuple(provenance),
        )

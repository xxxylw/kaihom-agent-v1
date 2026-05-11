from typing import Any

from pydantic import BaseModel, Field


REQUIRED_DRAFT_FIELDS: tuple[str, ...] = (
    "customer_name",
    "shipper_name",
    "shipper_phone",
    "shipper_address",
    "consignee_name",
    "consignee_phone",
    "consignee_address",
    "cargo_name",
    "package_count",
    "gross_weight_kg",
)

OPTIONAL_DRAFT_FIELDS: tuple[str, ...] = (
    "origin",
    "destination",
    "cargo_volume_cbm",
    "package_type",
    "transport_mode",
    "service_type",
    "pickup_date",
    "remarks",
)

RESERVED_INTERNATIONAL_FIELDS: tuple[str, ...] = (
    "hs_code",
    "declared_value",
    "currency",
    "incoterm",
    "invoice_no",
    "container_type",
    "container_count",
    "booking_no",
    "bill_of_lading_no",
)

ALL_DRAFT_FIELDS: tuple[str, ...] = (
    *REQUIRED_DRAFT_FIELDS,
    *OPTIONAL_DRAFT_FIELDS,
    *RESERVED_INTERNATIONAL_FIELDS,
)


class OrderDraftFields(BaseModel):
    customer_name: str | None = None
    shipper_name: str | None = None
    shipper_phone: str | None = None
    shipper_address: str | None = None
    consignee_name: str | None = None
    consignee_phone: str | None = None
    consignee_address: str | None = None
    cargo_name: str | None = None
    package_count: int | None = None
    gross_weight_kg: float | None = None
    origin: str | None = None
    destination: str | None = None
    cargo_volume_cbm: float | None = None
    package_type: str | None = None
    transport_mode: str | None = None
    service_type: str | None = None
    pickup_date: str | None = None
    remarks: str | None = None
    hs_code: str | None = None
    declared_value: float | None = None
    currency: str | None = None
    incoterm: str | None = None
    invoice_no: str | None = None
    container_type: str | None = None
    container_count: int | None = None
    booking_no: str | None = None
    bill_of_lading_no: str | None = None


class FieldEvidence(BaseModel):
    source_file_id: str
    source_filename: str | None = None
    source_text: str
    confidence: float = 1.0


class FieldConflict(BaseModel):
    field_name: str
    kept_value: Any | None = None
    conflicting_value: Any | None = None
    source_file_id: str
    source_filename: str | None = None
    source_text: str


class OrderDraftPreview(BaseModel):
    fields: OrderDraftFields = Field(default_factory=OrderDraftFields)
    missing_fields: list[str] = Field(default_factory=list)
    field_evidence: dict[str, FieldEvidence] = Field(default_factory=dict)
    conflicts: list[FieldConflict] = Field(default_factory=list)

from dataclasses import dataclass
import re
from typing import Any

from app.schemas.order_draft import (
    REQUIRED_DRAFT_FIELDS,
    FieldConflict,
    FieldEvidence,
    OrderDraftFields,
    OrderDraftPreview,
)


@dataclass(frozen=True)
class OcrDocument:
    file_id: str
    filename: str | None
    text: str


FIELD_LABELS: dict[str, str] = {
    "customer": "customer_name",
    "客户": "customer_name",
    "shipper name": "shipper_name",
    "发货人": "shipper_name",
    "寄件人": "shipper_name",
    "shipper phone": "shipper_phone",
    "发货人电话": "shipper_phone",
    "寄件人电话": "shipper_phone",
    "shipper address": "shipper_address",
    "发货地址": "shipper_address",
    "consignee name": "consignee_name",
    "收货人": "consignee_name",
    "consignee phone": "consignee_phone",
    "收货人电话": "consignee_phone",
    "consignee address": "consignee_address",
    "收货地址": "consignee_address",
    "cargo": "cargo_name",
    "cargo name": "cargo_name",
    "货物": "cargo_name",
    "货物名称": "cargo_name",
    "packages": "package_count",
    "package count": "package_count",
    "件数": "package_count",
    "gross weight kg": "gross_weight_kg",
    "毛重": "gross_weight_kg",
    "origin": "origin",
    "起运地": "origin",
    "始发地": "origin",
    "destination": "destination",
    "目的地": "destination",
    "volume cbm": "cargo_volume_cbm",
    "cargo volume cbm": "cargo_volume_cbm",
    "体积": "cargo_volume_cbm",
    "package type": "package_type",
    "包装类型": "package_type",
    "transport mode": "transport_mode",
    "运输方式": "transport_mode",
    "service type": "service_type",
    "服务类型": "service_type",
    "pickup date": "pickup_date",
    "提货日期": "pickup_date",
    "remarks": "remarks",
    "备注": "remarks",
    "hs code": "hs_code",
    "hs编码": "hs_code",
    "declared value": "declared_value",
    "申报价值": "declared_value",
    "currency": "currency",
    "币种": "currency",
    "incoterm": "incoterm",
    "贸易条款": "incoterm",
    "invoice no": "invoice_no",
    "invoice number": "invoice_no",
    "发票号": "invoice_no",
    "container type": "container_type",
    "箱型": "container_type",
    "container count": "container_count",
    "箱量": "container_count",
    "booking no": "booking_no",
    "订舱号": "booking_no",
    "bill of lading no": "bill_of_lading_no",
    "提单号": "bill_of_lading_no",
}

INT_FIELDS = {"package_count", "container_count"}
FLOAT_FIELDS = {"gross_weight_kg", "cargo_volume_cbm", "declared_value"}


def extract_order_draft(documents: list[OcrDocument]) -> OrderDraftPreview:
    fields = OrderDraftFields()
    evidence: dict[str, FieldEvidence] = {}
    conflicts: list[FieldConflict] = []

    for document in documents:
        for source_line, field_name, raw_value in _iter_field_lines(document.text):
            parsed_value = _parse_field_value(field_name, raw_value)
            current_value = getattr(fields, field_name)
            if _is_empty(current_value):
                setattr(fields, field_name, parsed_value)
                evidence[field_name] = FieldEvidence(
                    source_file_id=document.file_id,
                    source_filename=document.filename,
                    source_text=source_line,
                    confidence=1.0,
                )
                continue

            if current_value != parsed_value:
                conflicts.append(
                    FieldConflict(
                        field_name=field_name,
                        kept_value=current_value,
                        conflicting_value=parsed_value,
                        source_file_id=document.file_id,
                        source_filename=document.filename,
                        source_text=source_line,
                    )
                )

    missing_fields = [
        field_name
        for field_name in REQUIRED_DRAFT_FIELDS
        if _is_empty(getattr(fields, field_name))
    ]
    return OrderDraftPreview(
        fields=fields,
        missing_fields=missing_fields,
        field_evidence=evidence,
        conflicts=conflicts,
    )


def _iter_field_lines(text: str):
    for line in text.splitlines():
        source_line = line.strip()
        if not source_line:
            continue
        if ":" in source_line:
            label, value = source_line.split(":", 1)
        elif "：" in source_line:
            label, value = source_line.split("：", 1)
        else:
            continue

        field_name = FIELD_LABELS.get(_normalize_label(label))
        if field_name is None:
            continue
        value = value.strip()
        if value:
            yield source_line, field_name, value


def _normalize_label(label: str) -> str:
    return re.sub(r"\s+", " ", label.strip().casefold())


def _parse_field_value(field_name: str, value: str) -> Any:
    if field_name in INT_FIELDS:
        match = re.search(r"-?\d+", value)
        return int(match.group(0)) if match else None
    if field_name in FLOAT_FIELDS:
        match = re.search(r"-?\d+(?:\.\d+)?", value.replace(",", ""))
        return float(match.group(0)) if match else None
    return value.strip()


def _is_empty(value: Any | None) -> bool:
    return value is None or value == ""

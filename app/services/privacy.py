import re
from typing import Any

from app.schemas.order_draft import OrderDraftPreview


PHONE_PATTERN = re.compile(r"(?<!\d)(?:\+?\d[\d\-\s]{6,}\d)(?!\d)")

NAME_FIELDS = (
    "customer_name",
    "shipper_name",
    "consignee_name",
)

ADDRESS_FIELDS = (
    "shipper_address",
    "consignee_address",
)


def build_redacted_context(
    preview: OrderDraftPreview,
    answer_text: str | None = None,
) -> tuple[dict[str, Any], dict[str, str]]:
    raw_context: dict[str, Any] = {
        "fields": preview.fields.model_dump(),
        "missing_fields": preview.missing_fields,
        "conflicts": [conflict.model_dump(mode="json") for conflict in preview.conflicts],
    }
    if answer_text is not None:
        raw_context["answer_text"] = answer_text

    privacy_map: dict[str, str] = {}
    replacements = _collect_field_replacements(preview)
    redacted = _redact_value(raw_context, replacements, privacy_map)
    return redacted, privacy_map


def redact_text(text: str, privacy_map: dict[str, str] | None = None) -> tuple[str, dict[str, str]]:
    result_map = dict(privacy_map or {})
    redacted = _redact_string(text, {}, result_map)
    return redacted, result_map


def _collect_field_replacements(preview: OrderDraftPreview) -> dict[str, str]:
    replacements: dict[str, str] = {}
    fields = preview.fields

    for index, field_name in enumerate(NAME_FIELDS, start=1):
        value = getattr(fields, field_name)
        if value:
            label = "CUSTOMER" if field_name == "customer_name" else "PARTY"
            replacements[value] = f"[{label}_{index}]"

    for index, field_name in enumerate(ADDRESS_FIELDS, start=1):
        value = getattr(fields, field_name)
        if value:
            replacements[value] = f"[ADDRESS_{index}]"

    return replacements


def _redact_value(
    value: Any,
    replacements: dict[str, str],
    privacy_map: dict[str, str],
) -> Any:
    if isinstance(value, str):
        return _redact_string(value, replacements, privacy_map)
    if isinstance(value, list):
        return [_redact_value(item, replacements, privacy_map) for item in value]
    if isinstance(value, dict):
        return {
            key: _redact_value(item, replacements, privacy_map)
            for key, item in value.items()
        }
    return value


def _redact_string(
    text: str,
    replacements: dict[str, str],
    privacy_map: dict[str, str],
) -> str:
    redacted = text
    for raw, placeholder in sorted(replacements.items(), key=lambda item: len(item[0]), reverse=True):
        if raw and raw in redacted:
            redacted = redacted.replace(raw, placeholder)
            privacy_map[placeholder] = raw

    def replace_phone(match: re.Match[str]) -> str:
        raw = match.group(0)
        placeholder = _next_placeholder("PHONE", privacy_map)
        privacy_map[placeholder] = raw
        return placeholder

    return PHONE_PATTERN.sub(replace_phone, redacted)


def _next_placeholder(prefix: str, privacy_map: dict[str, str]) -> str:
    index = 1
    while f"[{prefix}_{index}]" in privacy_map:
        index += 1
    return f"[{prefix}_{index}]"

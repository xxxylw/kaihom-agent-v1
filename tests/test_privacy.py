from app.schemas.order_draft import OrderDraftFields, OrderDraftPreview
from app.services.privacy import build_redacted_context, redact_text


def test_build_redacted_context_replaces_sensitive_fields():
    preview = OrderDraftPreview(
        fields=OrderDraftFields(
            customer_name="Ningbo Future Trading Co., Ltd.",
            shipper_phone="13800000001",
            shipper_address="88 Harbor Road, Ningbo",
            cargo_name="Auto parts",
            gross_weight_kg=1200,
        ),
        missing_fields=["consignee_name"],
    )

    redacted, privacy_map = build_redacted_context(preview)

    text = str(redacted)
    assert "Ningbo Future Trading Co., Ltd." not in text
    assert "13800000001" not in text
    assert "88 Harbor Road, Ningbo" not in text
    assert "[CUSTOMER_1]" in text
    assert "[PHONE_1]" in text
    assert "[ADDRESS_1]" in text
    assert "Auto parts" in text
    assert privacy_map["[CUSTOMER_1]"] == "Ningbo Future Trading Co., Ltd."


def test_redact_text_adds_phone_placeholder_to_existing_map():
    redacted, privacy_map = redact_text("Call 13800000002 tomorrow", {"[CUSTOMER_1]": "A"})

    assert "13800000002" not in redacted
    assert "[PHONE_1]" in redacted
    assert privacy_map["[PHONE_1]"] == "13800000002"

from app.models.uploaded_file import UploadedFileRecord
from app.schemas.order_draft import ALL_DRAFT_FIELDS, REQUIRED_DRAFT_FIELDS, OrderDraftFields
from app.services.extraction import OcrDocument, extract_order_draft
from app.services.mock_ocr import get_mock_ocr_text


def upload_record(
    filename: str,
    file_id: str = "file_test_001",
    document_type: str | None = None,
) -> UploadedFileRecord:
    return UploadedFileRecord(
        id=file_id,
        original_filename=filename,
        stored_filename=filename,
        storage_path=f"uploads/{filename}",
        content_type="image/jpeg",
        file_kind="image",
        size_bytes=12,
        sha256="fake-sha",
        uploaded_by="yw001",
        document_type=document_type,
    )


def test_order_draft_fields_cover_all_canonical_fields():
    schema_fields = set(OrderDraftFields.model_fields)

    assert len(ALL_DRAFT_FIELDS) == 27
    assert len(REQUIRED_DRAFT_FIELDS) == 10
    assert set(ALL_DRAFT_FIELDS).issubset(schema_fields)
    assert set(REQUIRED_DRAFT_FIELDS).issubset(schema_fields)


def test_mock_ocr_fixture_is_deterministic():
    upload = upload_record("complete-entrustment.jpg")

    first = get_mock_ocr_text(upload)
    second = get_mock_ocr_text(upload)

    assert first == second
    assert "Customer:" in first
    assert "Gross Weight KG:" in first


def test_extract_complete_fixture_has_no_required_missing_fields():
    upload = upload_record("complete-entrustment.jpg")
    preview = extract_order_draft(
        [
            OcrDocument(
                file_id=upload.id,
                filename=upload.original_filename,
                text=get_mock_ocr_text(upload),
            )
        ]
    )

    assert preview.fields.customer_name == "Ningbo Future Trading Co., Ltd."
    assert preview.fields.cargo_name == "Auto parts"
    assert preview.fields.package_count == 20
    assert preview.fields.gross_weight_kg == 1200.0
    assert preview.missing_fields == []
    assert preview.field_evidence["cargo_name"].source_file_id == upload.id


def test_extract_incomplete_fixture_reports_required_missing_fields():
    upload = upload_record("incomplete-receipt.jpg")
    preview = extract_order_draft(
        [
            OcrDocument(
                file_id=upload.id,
                filename=upload.original_filename,
                text=get_mock_ocr_text(upload),
            )
        ]
    )

    assert preview.fields.customer_name == "Shanghai United Logistics Importer"
    assert "shipper_phone" in preview.missing_fields
    assert "consignee_address" in preview.missing_fields
    assert "cargo_name" not in preview.missing_fields
    assert "origin" not in preview.missing_fields


def test_extract_international_optional_fields_when_present():
    upload = upload_record("ocean-booking.pdf", document_type="bill_of_lading")
    preview = extract_order_draft(
        [
            OcrDocument(
                file_id=upload.id,
                filename=upload.original_filename,
                text=get_mock_ocr_text(upload),
            )
        ]
    )

    assert preview.fields.hs_code == "870899"
    assert preview.fields.invoice_no == "INV-2026-0501"
    assert preview.fields.container_type == "40HQ"
    assert preview.fields.container_count == 1
    assert preview.fields.bill_of_lading_no == "BL-NGB-LAX-001"
    assert "hs_code" not in preview.missing_fields


def test_extract_records_conflicts_and_keeps_first_value():
    first = OcrDocument(
        file_id="file_a",
        filename="a.jpg",
        text="Customer: Ningbo Future Trading Co., Ltd.\nCargo: Auto parts\nPackages: 20\nGross Weight KG: 1200",
    )
    second = OcrDocument(
        file_id="file_b",
        filename="b.jpg",
        text="Customer: Other Customer\nCargo: Electronics\nPackages: 20",
    )

    preview = extract_order_draft([first, second])

    assert preview.fields.customer_name == "Ningbo Future Trading Co., Ltd."
    assert any(conflict.field_name == "customer_name" for conflict in preview.conflicts)
    assert any(conflict.field_name == "cargo_name" for conflict in preview.conflicts)

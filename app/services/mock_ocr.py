from app.models.uploaded_file import UploadedFileRecord


COMPLETE_LOGISTICS_OCR = """Customer: Ningbo Future Trading Co., Ltd.
Shipper Name: Alice Chen
Shipper Phone: 13800000001
Shipper Address: Ningbo Export Warehouse
Consignee Name: Bob Wang
Consignee Phone: 13800000002
Consignee Address: Los Angeles Distribution Center
Cargo: Auto parts
Packages: 20
Gross Weight KG: 1200
Origin: Ningbo
Destination: Los Angeles
Package Type: Carton
Transport Mode: Ocean export
Service Type: LCL
Pickup Date: 2026-05-15
Remarks: Handle with care
"""

INCOMPLETE_LOGISTICS_OCR = """Customer: Shanghai United Logistics Importer
Shipper Name: Alice Chen
Shipper Address: Shanghai Bonded Warehouse
Consignee Name: Bob Wang
Cargo: Consumer electronics
Packages: 8
Gross Weight KG: 320
Destination: Tokyo
"""

INTERNATIONAL_LOGISTICS_OCR = """Customer: Ningbo Future Trading Co., Ltd.
Shipper Name: Alice Chen
Shipper Phone: 13800000001
Shipper Address: Ningbo Export Warehouse
Consignee Name: Bob Wang
Consignee Phone: 13800000002
Consignee Address: Los Angeles Distribution Center
Cargo: Auto parts
Packages: 20
Gross Weight KG: 1200
Origin: Ningbo
Destination: Los Angeles
Transport Mode: Ocean export
HS Code: 870899
Declared Value: 25000
Currency: USD
Incoterm: FOB
Invoice No: INV-2026-0501
Container Type: 40HQ
Container Count: 1
Booking No: BK-NGB-LAX-001
Bill of Lading No: BL-NGB-LAX-001
"""


def get_mock_ocr_text(upload: UploadedFileRecord) -> str:
    selector = " ".join(
        value.casefold()
        for value in [
            upload.original_filename,
            upload.stored_filename,
            upload.document_type or "",
        ]
    )
    if any(token in selector for token in ["ocean", "international", "bill_of_lading", "bl"]):
        return INTERNATIONAL_LOGISTICS_OCR
    if any(token in selector for token in ["incomplete", "receipt", "pod"]):
        return INCOMPLETE_LOGISTICS_OCR
    return COMPLETE_LOGISTICS_OCR

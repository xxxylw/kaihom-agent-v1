import json
from datetime import UTC, datetime
from uuid import uuid4

from sqlmodel import Session

from app.models.draft import OrderDraftRecord
from app.schemas.mock_kaihong import (
    MockCustomerResponse,
    MockDictionariesResponse,
    MockDictionaryItem,
    MockDraftCreateRequest,
    MockDraftResponse,
    MockRecentOrderResponse,
    MockUserResponse,
)


_USERS = {
    "yw001": MockUserResponse(
        id="user_001",
        username="yw001",
        display_name="Mock Operator One",
        department="Business Operations",
    )
}

_PASSWORDS = {"yw001": "mock123456"}

_CUSTOMERS = [
    MockCustomerResponse(
        id="cust_001",
        name="Ningbo Future Trading Co., Ltd.",
        short_name="Ningbo Future",
        contact_name="Alice Chen",
        contact_phone="13800000001",
    ),
    MockCustomerResponse(
        id="cust_002",
        name="Shanghai United Logistics Importer",
        short_name="SH United",
        contact_name="Bob Wang",
        contact_phone="13800000002",
    ),
]

_DICTIONARIES = MockDictionariesResponse(
    ports=[
        MockDictionaryItem(code="CNNGB", name="Ningbo"),
        MockDictionaryItem(code="CNSHA", name="Shanghai"),
        MockDictionaryItem(code="USLAX", name="Los Angeles"),
    ],
    warehouses=[
        MockDictionaryItem(code="NB_WH_01", name="Ningbo Export Warehouse"),
        MockDictionaryItem(code="SH_WH_01", name="Shanghai Bonded Warehouse"),
    ],
    yards=[
        MockDictionaryItem(code="NB_YARD_01", name="Ningbo Port Yard"),
        MockDictionaryItem(code="SH_YARD_01", name="Shanghai Port Yard"),
    ],
    fee_types=[
        MockDictionaryItem(code="line_haul", name="Line haul"),
        MockDictionaryItem(code="customs_service", name="Customs service"),
        MockDictionaryItem(code="terminal_handling", name="Terminal handling"),
    ],
    document_types=[
        MockDictionaryItem(code="entrustment", name="Entrustment letter"),
        MockDictionaryItem(code="commercial_invoice", name="Commercial invoice"),
        MockDictionaryItem(code="packing_list", name="Packing list"),
        MockDictionaryItem(code="bill_of_lading", name="Bill of lading"),
        MockDictionaryItem(code="air_waybill", name="Air waybill"),
        MockDictionaryItem(code="customs_declaration", name="Customs declaration"),
        MockDictionaryItem(code="pod_receipt", name="POD receipt"),
    ],
    transport_modes=[
        MockDictionaryItem(code="domestic_road", name="Domestic road"),
        MockDictionaryItem(code="domestic_warehouse", name="Domestic warehouse"),
        MockDictionaryItem(code="ocean_export", name="Ocean export"),
        MockDictionaryItem(code="air_export", name="Air export"),
        MockDictionaryItem(code="cross_border_road", name="Cross-border road"),
    ],
    route_types=[
        MockDictionaryItem(code="domestic", name="Domestic"),
        MockDictionaryItem(code="international_export", name="International export"),
        MockDictionaryItem(code="international_import", name="International import"),
        MockDictionaryItem(code="multimodal", name="Multimodal"),
    ],
)

_RECENT_ORDERS = [
    MockRecentOrderResponse(
        id="recent_001",
        customer_id="cust_001",
        route="Ningbo -> Los Angeles",
        cargo_name="Auto parts",
        container_type="40HQ",
        created_at=datetime(2026, 4, 20, 10, 0, 0),
    ),
    MockRecentOrderResponse(
        id="recent_002",
        customer_id="cust_002",
        route="Shanghai -> Tokyo",
        cargo_name="Consumer electronics",
        container_type="LCL",
        created_at=datetime(2026, 4, 22, 15, 30, 0),
    ),
]


def authenticate_user(username: str, password: str) -> MockUserResponse | None:
    if _PASSWORDS.get(username) != password:
        return None
    return _USERS.get(username)


def token_for_user(user: MockUserResponse) -> str:
    return f"mock-token-{user.username}"


def get_user_by_token(token: str) -> MockUserResponse | None:
    prefix = "mock-token-"
    if not token.startswith(prefix):
        return None
    return _USERS.get(token.removeprefix(prefix))


def list_customers(q: str | None = None) -> list[MockCustomerResponse]:
    if not q:
        return list(_CUSTOMERS)

    keyword = q.casefold()
    return [
        customer
        for customer in _CUSTOMERS
        if keyword in customer.id.casefold()
        or keyword in customer.name.casefold()
        or (customer.short_name and keyword in customer.short_name.casefold())
        or (customer.contact_name and keyword in customer.contact_name.casefold())
    ]


def get_customer(customer_id: str) -> MockCustomerResponse | None:
    return next((customer for customer in _CUSTOMERS if customer.id == customer_id), None)


def get_dictionaries() -> MockDictionariesResponse:
    return _DICTIONARIES


def list_recent_orders(customer_id: str) -> list[MockRecentOrderResponse]:
    return [order for order in _RECENT_ORDERS if order.customer_id == customer_id]


def create_draft(session: Session, request: MockDraftCreateRequest) -> MockDraftResponse:
    draft_id = f"draft_{uuid4().hex[:12]}"
    now = datetime.now(UTC)
    payload_json = json.dumps(
        {
            "source_documents": [
                document.model_dump(mode="json") for document in request.source_documents
            ],
            "order_items": [
                order_item.model_dump(mode="json")
                for order_item in request.order_items
            ],
            "payload": request.payload,
        },
        ensure_ascii=True,
    )

    record = OrderDraftRecord(
        id=draft_id,
        customer_id=request.customer_id,
        created_by=request.created_by,
        payload_json=payload_json,
        source=request.source,
        created_at=now,
        updated_at=now,
    )
    session.add(record)
    session.commit()
    session.refresh(record)
    return _record_to_response(record)


def get_draft(session: Session, draft_id: str) -> MockDraftResponse | None:
    record = session.get(OrderDraftRecord, draft_id)
    if record is None:
        return None
    return _record_to_response(record)


def _record_to_response(record: OrderDraftRecord) -> MockDraftResponse:
    data = json.loads(record.payload_json)
    return MockDraftResponse(
        draft_id=record.id,
        customer_id=record.customer_id,
        created_by=record.created_by,
        status=record.status,
        source_documents=data.get("source_documents", []),
        order_items=data.get("order_items", []),
        payload=data.get("payload", {}),
        source=record.source,
        created_at=record.created_at,
        updated_at=record.updated_at,
    )

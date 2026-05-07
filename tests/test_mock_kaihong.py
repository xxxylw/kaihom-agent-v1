from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def login_headers() -> dict[str, str]:
    response = client.post(
        "/mock/kaihong/auth/login",
        json={"username": "yw001", "password": "mock123456"},
    )
    assert response.status_code == 200
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_mock_login_returns_bearer_token():
    response = client.post(
        "/mock/kaihong/auth/login",
        json={"username": "yw001", "password": "mock123456"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"].startswith("mock-token-")


def test_mock_login_rejects_invalid_credentials():
    response = client.post(
        "/mock/kaihong/auth/login",
        json={"username": "yw001", "password": "wrong"},
    )

    assert response.status_code == 401


def test_current_user_requires_and_accepts_bearer_token():
    unauthorized = client.get("/mock/kaihong/users/me")
    assert unauthorized.status_code == 401

    response = client.get("/mock/kaihong/users/me", headers=login_headers())

    assert response.status_code == 200
    body = response.json()
    assert body["id"] == "user_001"
    assert body["username"] == "yw001"


def test_customers_list_filter_and_detail():
    headers = login_headers()

    list_response = client.get("/mock/kaihong/customers", headers=headers)
    assert list_response.status_code == 200
    customers = list_response.json()
    assert len(customers) >= 2
    assert customers[0]["id"] == "cust_001"

    filter_response = client.get(
        "/mock/kaihong/customers",
        params={"q": "ningbo"},
        headers=headers,
    )
    assert filter_response.status_code == 200
    assert [customer["id"] for customer in filter_response.json()] == ["cust_001"]

    detail_response = client.get("/mock/kaihong/customers/cust_001", headers=headers)
    assert detail_response.status_code == 200
    assert detail_response.json()["name"] == "Ningbo Future Trading Co., Ltd."

    missing_response = client.get("/mock/kaihong/customers/missing", headers=headers)
    assert missing_response.status_code == 404


def test_dictionaries_include_logistics_lookup_groups():
    response = client.get("/mock/kaihong/dictionaries", headers=login_headers())

    assert response.status_code == 200
    body = response.json()
    assert set(body) == {
        "ports",
        "warehouses",
        "yards",
        "fee_types",
        "document_types",
        "transport_modes",
        "route_types",
    }
    assert any(item["code"] == "bill_of_lading" for item in body["document_types"])
    assert any(item["code"] == "ocean_export" for item in body["transport_modes"])
    assert any(item["code"] == "international_export" for item in body["route_types"])


def test_recent_orders_are_customer_specific():
    headers = login_headers()
    response = client.get(
        "/mock/kaihong/customers/cust_001/recent-orders",
        headers=headers,
    )

    assert response.status_code == 200
    orders = response.json()
    assert orders
    assert all(order["customer_id"] == "cust_001" for order in orders)


def test_create_and_get_draft_preserves_payload_documents_and_order_items():
    headers = login_headers()
    payload = {
        "customer_id": "cust_001",
        "created_by": "yw001",
        "source_documents": [
            {
                "document_id": "doc_001",
                "document_type": "commercial_invoice",
                "filename": "invoice.jpg",
                "confidence": 0.92,
            },
            {
                "document_id": "doc_002",
                "document_type": "packing_list",
                "filename": "packing-list.jpg",
                "confidence": 0.89,
            },
        ],
        "order_items": [
            {
                "order_index": 1,
                "transport_mode": "ocean_export",
                "route_type": "international_export",
                "fields": {
                    "pol": "Ningbo",
                    "pod": "Los Angeles",
                    "cargo_name": "Auto parts",
                },
                "missing_fields": ["hs_code", "bl_release_type"],
            },
            {
                "order_index": 2,
                "transport_mode": "domestic_road",
                "route_type": "domestic",
                "fields": {
                    "pickup_address": "Ningbo warehouse",
                    "delivery_address": "Shanghai port yard",
                },
                "missing_fields": ["vehicle_type"],
            },
        ],
        "payload": {
            "customer_order_no": "PO-2026-0507",
            "remark": "Mock draft from multi-document upload.",
        },
    }

    create_response = client.post(
        "/mock/kaihong/drafts",
        json=payload,
        headers=headers,
    )
    assert create_response.status_code == 201
    created = create_response.json()
    assert created["draft_id"].startswith("draft_")
    assert created["payload"] == payload["payload"]
    assert created["source_documents"] == payload["source_documents"]
    assert created["order_items"] == payload["order_items"]

    get_response = client.get(
        f"/mock/kaihong/drafts/{created['draft_id']}",
        headers=headers,
    )
    assert get_response.status_code == 200
    retrieved = get_response.json()
    assert retrieved["payload"] == payload["payload"]
    assert retrieved["source_documents"] == payload["source_documents"]
    assert retrieved["order_items"] == payload["order_items"]


def test_openapi_documents_mock_kaihong_contracts():
    response = client.get("/openapi.json")

    assert response.status_code == 200
    paths = response.json()["paths"]
    assert "/mock/kaihong/auth/login" in paths
    assert "/mock/kaihong/drafts" in paths

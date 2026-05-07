from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class MockLoginRequest(BaseModel):
    username: str
    password: str


class MockTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class MockUserResponse(BaseModel):
    id: str
    username: str
    display_name: str
    department: str


class MockCustomerResponse(BaseModel):
    id: str
    name: str
    short_name: str | None = None
    contact_name: str | None = None
    contact_phone: str | None = None


class MockDictionaryItem(BaseModel):
    code: str
    name: str


class MockDictionariesResponse(BaseModel):
    ports: list[MockDictionaryItem]
    warehouses: list[MockDictionaryItem]
    yards: list[MockDictionaryItem]
    fee_types: list[MockDictionaryItem]
    document_types: list[MockDictionaryItem]
    transport_modes: list[MockDictionaryItem]
    route_types: list[MockDictionaryItem]


class MockRecentOrderResponse(BaseModel):
    id: str
    customer_id: str
    route: str
    cargo_name: str
    container_type: str
    created_at: datetime


class MockSourceDocument(BaseModel):
    document_id: str | None = None
    document_type: str
    filename: str | None = None
    confidence: float | None = None


class MockDraftOrderItem(BaseModel):
    order_index: int
    transport_mode: str
    route_type: str
    fields: dict[str, Any]
    missing_fields: list[str] = Field(default_factory=list)


class MockDraftCreateRequest(BaseModel):
    customer_id: str
    created_by: str
    source_documents: list[MockSourceDocument] = Field(default_factory=list)
    order_items: list[MockDraftOrderItem] = Field(default_factory=list)
    payload: dict[str, Any] = Field(default_factory=dict)
    source: str = "mock-kaihong"


class MockDraftResponse(BaseModel):
    draft_id: str
    customer_id: str
    created_by: str
    status: str
    source_documents: list[MockSourceDocument]
    order_items: list[MockDraftOrderItem]
    payload: dict[str, Any]
    source: str
    created_at: datetime
    updated_at: datetime

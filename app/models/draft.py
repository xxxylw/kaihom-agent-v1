from datetime import UTC, datetime

from sqlmodel import Field, SQLModel


def utc_now() -> datetime:
    return datetime.now(UTC)


class OrderDraftRecord(SQLModel, table=True):
    id: str = Field(primary_key=True)
    customer_id: str
    created_by: str
    status: str = "draft"
    payload_json: str
    source: str = "mock-kaihong"
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)

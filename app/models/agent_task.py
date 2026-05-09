from datetime import UTC, datetime

from sqlmodel import Field, SQLModel


def utc_now() -> datetime:
    return datetime.now(UTC)


class AgentTaskRecord(SQLModel, table=True):
    id: str = Field(primary_key=True)
    created_by: str
    customer_id: str | None = None
    status: str = "created"
    file_ids_json: str
    error_code: str | None = None
    error_message: str | None = None
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class AgentTaskEventRecord(SQLModel, table=True):
    id: str = Field(primary_key=True)
    task_id: str = Field(index=True)
    event_type: str
    actor: str | None = None
    from_status: str | None = None
    to_status: str | None = None
    message: str | None = None
    details_json: str | None = None
    created_at: datetime = Field(default_factory=utc_now)

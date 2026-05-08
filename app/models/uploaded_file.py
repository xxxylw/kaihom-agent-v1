from datetime import UTC, datetime

from sqlmodel import Field, SQLModel


def utc_now() -> datetime:
    return datetime.now(UTC)


class UploadedFileRecord(SQLModel, table=True):
    id: str = Field(primary_key=True)
    original_filename: str
    stored_filename: str
    storage_path: str
    content_type: str
    file_kind: str
    size_bytes: int
    sha256: str
    uploaded_by: str
    customer_id: str | None = None
    task_id: str | None = None
    document_type: str | None = None
    status: str = "uploaded"
    source: str = "local-upload"
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)

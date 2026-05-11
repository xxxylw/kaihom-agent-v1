from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.schemas.order_draft import OrderDraftPreview
from app.schemas.uploads import UploadedFileResponse


class AgentTaskCreateRequest(BaseModel):
    file_ids: list[str] = Field(min_length=1)
    customer_id: str | None = None


class AgentTaskEventResponse(BaseModel):
    event_id: str
    task_id: str
    event_type: str
    actor: str | None = None
    from_status: str | None = None
    to_status: str | None = None
    message: str | None = None
    details: dict[str, Any] | None = None
    created_at: datetime


class AgentTaskResponse(BaseModel):
    task_id: str
    status: str
    customer_id: str | None = None
    file_ids: list[str]
    files: list[UploadedFileResponse]
    draft_preview: OrderDraftPreview | None = None
    questions: list[dict[str, Any]] = Field(default_factory=list)
    error_code: str | None = None
    error_message: str | None = None
    created_at: datetime
    updated_at: datetime


class AgentTaskEventsResponse(BaseModel):
    events: list[AgentTaskEventResponse]

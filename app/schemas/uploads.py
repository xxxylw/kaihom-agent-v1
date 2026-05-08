from datetime import datetime

from pydantic import BaseModel


class UploadedFileResponse(BaseModel):
    file_id: str
    original_filename: str
    file_kind: str
    content_type: str
    size_bytes: int
    status: str
    customer_id: str | None = None
    task_id: str | None = None
    document_type: str | None = None
    created_at: datetime


class UploadFilesResponse(BaseModel):
    files: list[UploadedFileResponse]


class LinkFileTaskRequest(BaseModel):
    task_id: str

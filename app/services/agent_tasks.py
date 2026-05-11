from fastapi import status
import json
from typing import Any
from uuid import uuid4

from sqlmodel import Session, select

from app.models.agent_task import AgentTaskEventRecord, AgentTaskRecord, utc_now
from app.models.uploaded_file import UploadedFileRecord
from app.schemas.agent_tasks import (
    AgentTaskEventResponse,
    AgentTaskResponse,
)
from app.schemas.order_draft import OrderDraftPreview
from app.schemas.uploads import UploadedFileResponse
from app.services.extraction import OcrDocument, extract_order_draft
from app.services.mock_ocr import get_mock_ocr_text


CREATED_STATUS = "created"
EXTRACTING_STATUS = "extracting"
NEED_MORE_INFO_STATUS = "need_more_info"
READY_FOR_REVIEW_STATUS = "ready_for_review"
FINALIZED_STATUS = "finalized"
FAILED_STATUS = "failed"

TASK_CREATED_EVENT = "task_created"
FILES_ATTACHED_EVENT = "files_attached"
STATUS_CHANGED_EVENT = "status_changed"
TASK_FAILED_EVENT = "task_failed"
EXTRACTION_STARTED_EVENT = "extraction_started"
MOCK_OCR_COMPLETED_EVENT = "mock_ocr_completed"
FIELDS_EXTRACTED_EVENT = "fields_extracted"
MISSING_FIELDS_DETECTED_EVENT = "missing_fields_detected"

ALLOWED_TRANSITIONS: dict[str, set[str]] = {
    CREATED_STATUS: {EXTRACTING_STATUS, FAILED_STATUS},
    EXTRACTING_STATUS: {NEED_MORE_INFO_STATUS, READY_FOR_REVIEW_STATUS, FAILED_STATUS},
    NEED_MORE_INFO_STATUS: {READY_FOR_REVIEW_STATUS, FAILED_STATUS},
    READY_FOR_REVIEW_STATUS: {FINALIZED_STATUS, FAILED_STATUS},
    FINALIZED_STATUS: set(),
    FAILED_STATUS: set(),
}


class AgentTaskError(ValueError):
    def __init__(
        self,
        message: str,
        status_code: int = status.HTTP_400_BAD_REQUEST,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def create_agent_task(
    session: Session,
    file_ids: list[str],
    created_by: str,
    customer_id: str | None = None,
) -> AgentTaskResponse:
    if not file_ids:
        raise AgentTaskError("At least one file_id is required")

    records = _get_accessible_uploads(session, file_ids, created_by)
    task_id = f"task_{uuid4().hex[:12]}"
    now = utc_now()
    task = AgentTaskRecord(
        id=task_id,
        created_by=created_by,
        customer_id=customer_id,
        status=CREATED_STATUS,
        file_ids_json=json.dumps(file_ids),
        created_at=now,
        updated_at=now,
    )
    session.add(task)

    for record in records:
        record.task_id = task_id
        record.updated_at = now
        session.add(record)

    _add_event(
        session=session,
        task_id=task_id,
        event_type=TASK_CREATED_EVENT,
        actor=created_by,
        from_status=None,
        to_status=CREATED_STATUS,
        message="Agent task created from uploaded files.",
    )
    _add_event(
        session=session,
        task_id=task_id,
        event_type=FILES_ATTACHED_EVENT,
        actor=created_by,
        from_status=CREATED_STATUS,
        to_status=CREATED_STATUS,
        message="Uploaded files attached to Agent task.",
        details={"file_ids": file_ids},
    )
    session.commit()
    session.refresh(task)
    for record in records:
        session.refresh(record)
    return _task_to_response(task, records)


def get_agent_task(
    session: Session,
    task_id: str,
    current_username: str,
) -> AgentTaskResponse | None:
    task = session.get(AgentTaskRecord, task_id)
    if task is None or task.created_by != current_username:
        return None
    records = _get_task_uploads(session, task)
    return _task_to_response(task, records)


def list_task_events(
    session: Session,
    task_id: str,
    current_username: str,
) -> list[AgentTaskEventResponse] | None:
    task = session.get(AgentTaskRecord, task_id)
    if task is None or task.created_by != current_username:
        return None
    events = session.exec(
        select(AgentTaskEventRecord)
        .where(AgentTaskEventRecord.task_id == task_id)
        .order_by(AgentTaskEventRecord.created_at)
    ).all()
    return [_event_to_response(event) for event in events]


def extract_agent_task(
    session: Session,
    task_id: str,
    current_username: str,
) -> AgentTaskResponse | None:
    task = session.get(AgentTaskRecord, task_id)
    if task is None or task.created_by != current_username:
        return None
    if task.status != CREATED_STATUS:
        raise AgentTaskError(f"Cannot extract task in status {task.status}")

    records = _get_task_uploads(session, task)
    if not records:
        raise AgentTaskError("Agent task has no uploaded files")

    _set_task_status(
        task=task,
        new_status=EXTRACTING_STATUS,
    )
    _add_event(
        session=session,
        task_id=task_id,
        event_type=EXTRACTION_STARTED_EVENT,
        actor=current_username,
        from_status=CREATED_STATUS,
        to_status=EXTRACTING_STATUS,
        message="Mock OCR and field extraction started.",
    )

    documents = [
        OcrDocument(
            file_id=record.id,
            filename=record.original_filename,
            text=get_mock_ocr_text(record),
        )
        for record in records
    ]
    _add_event(
        session=session,
        task_id=task_id,
        event_type=MOCK_OCR_COMPLETED_EVENT,
        actor=current_username,
        from_status=EXTRACTING_STATUS,
        to_status=EXTRACTING_STATUS,
        message="Deterministic mock OCR completed.",
        details={"file_ids": [record.id for record in records]},
    )

    preview = extract_order_draft(documents)
    final_status = NEED_MORE_INFO_STATUS if preview.missing_fields else READY_FOR_REVIEW_STATUS
    task.draft_preview_json = preview.model_dump_json()
    task.missing_fields_json = json.dumps(preview.missing_fields)
    task.extraction_result_json = json.dumps(
        {
            "ocr_documents": [
                {
                    "file_id": document.file_id,
                    "filename": document.filename,
                    "text": document.text,
                }
                for document in documents
            ],
            "conflicts": [
                conflict.model_dump(mode="json") for conflict in preview.conflicts
            ],
        },
        ensure_ascii=True,
    )
    _set_task_status(
        task=task,
        new_status=final_status,
    )
    session.add(task)
    _add_event(
        session=session,
        task_id=task_id,
        event_type=FIELDS_EXTRACTED_EVENT,
        actor=current_username,
        from_status=EXTRACTING_STATUS,
        to_status=final_status,
        message="Draft fields extracted from mock OCR text.",
        details={
            "extracted_fields": [
                field_name
                for field_name, value in preview.fields.model_dump().items()
                if value is not None
            ],
            "missing_fields": preview.missing_fields,
        },
    )
    if preview.missing_fields:
        _add_event(
            session=session,
            task_id=task_id,
            event_type=MISSING_FIELDS_DETECTED_EVENT,
            actor=current_username,
            from_status=final_status,
            to_status=final_status,
            message="Required fields are missing from extracted draft preview.",
            details={"missing_fields": preview.missing_fields},
        )
    session.commit()
    session.refresh(task)
    return _task_to_response(task, records)


def transition_task_status(
    session: Session,
    task_id: str,
    new_status: str,
    actor: str,
    message: str | None = None,
    error_code: str | None = None,
    error_message: str | None = None,
) -> AgentTaskRecord:
    task = session.get(AgentTaskRecord, task_id)
    if task is None:
        raise AgentTaskError("Agent task not found", status.HTTP_404_NOT_FOUND)

    allowed = ALLOWED_TRANSITIONS.get(task.status, set())
    if new_status not in allowed:
        raise AgentTaskError(
            f"Invalid status transition: {task.status} -> {new_status}",
            status.HTTP_400_BAD_REQUEST,
        )

    previous_status = task.status
    _set_task_status(task=task, new_status=new_status)
    if new_status == FAILED_STATUS:
        task.error_code = error_code
        task.error_message = error_message or message

    session.add(task)
    _add_event(
        session=session,
        task_id=task_id,
        event_type=TASK_FAILED_EVENT if new_status == FAILED_STATUS else STATUS_CHANGED_EVENT,
        actor=actor,
        from_status=previous_status,
        to_status=new_status,
        message=message,
        details={"error_code": error_code} if error_code else None,
    )
    session.commit()
    session.refresh(task)
    return task


def _set_task_status(task: AgentTaskRecord, new_status: str) -> None:
    task.status = new_status
    task.updated_at = utc_now()


def _get_accessible_uploads(
    session: Session,
    file_ids: list[str],
    username: str,
) -> list[UploadedFileRecord]:
    records: list[UploadedFileRecord] = []
    for file_id in file_ids:
        record = session.get(UploadedFileRecord, file_id)
        if record is None:
            raise AgentTaskError(
                f"Uploaded file not found: {file_id}",
                status.HTTP_404_NOT_FOUND,
            )
        if record.uploaded_by != username:
            raise AgentTaskError(
                f"Uploaded file is not accessible: {file_id}",
                status.HTTP_403_FORBIDDEN,
            )
        records.append(record)
    return records


def _get_task_uploads(
    session: Session,
    task: AgentTaskRecord,
) -> list[UploadedFileRecord]:
    records_by_id = {
        record.id: record
        for record in session.exec(
            select(UploadedFileRecord).where(UploadedFileRecord.task_id == task.id)
        ).all()
    }
    return [
        records_by_id[file_id]
        for file_id in _file_ids_for_task(task)
        if file_id in records_by_id
    ]


def _add_event(
    session: Session,
    task_id: str,
    event_type: str,
    actor: str | None,
    from_status: str | None,
    to_status: str | None,
    message: str | None,
    details: dict[str, Any] | None = None,
) -> AgentTaskEventRecord:
    event = AgentTaskEventRecord(
        id=f"evt_{uuid4().hex[:12]}",
        task_id=task_id,
        event_type=event_type,
        actor=actor,
        from_status=from_status,
        to_status=to_status,
        message=message,
        details_json=json.dumps(details) if details is not None else None,
        created_at=utc_now(),
    )
    session.add(event)
    return event


def _task_to_response(
    task: AgentTaskRecord,
    records: list[UploadedFileRecord],
) -> AgentTaskResponse:
    return AgentTaskResponse(
        task_id=task.id,
        status=task.status,
        customer_id=task.customer_id,
        file_ids=_file_ids_for_task(task),
        files=[_upload_to_response(record) for record in records],
        draft_preview=_draft_preview_for_task(task),
        questions=[],
        error_code=task.error_code,
        error_message=task.error_message,
        created_at=task.created_at,
        updated_at=task.updated_at,
    )


def _draft_preview_for_task(task: AgentTaskRecord) -> OrderDraftPreview | None:
    if task.draft_preview_json is None:
        return None
    return OrderDraftPreview.model_validate_json(task.draft_preview_json)


def _event_to_response(event: AgentTaskEventRecord) -> AgentTaskEventResponse:
    details = json.loads(event.details_json) if event.details_json else None
    return AgentTaskEventResponse(
        event_id=event.id,
        task_id=event.task_id,
        event_type=event.event_type,
        actor=event.actor,
        from_status=event.from_status,
        to_status=event.to_status,
        message=event.message,
        details=details,
        created_at=event.created_at,
    )


def _upload_to_response(record: UploadedFileRecord) -> UploadedFileResponse:
    return UploadedFileResponse(
        file_id=record.id,
        original_filename=record.original_filename,
        file_kind=record.file_kind,
        content_type=record.content_type,
        size_bytes=record.size_bytes,
        status=record.status,
        customer_id=record.customer_id,
        task_id=record.task_id,
        document_type=record.document_type,
        created_at=record.created_at,
    )


def _file_ids_for_task(task: AgentTaskRecord) -> list[str]:
    return list(json.loads(task.file_ids_json))

import json
from typing import Any
from uuid import uuid4

from fastapi import status
from sqlmodel import Session, select

from app.core.config import get_settings
from app.models.agent_graph_session import AgentGraphSessionRecord
from app.models.agent_task import AgentTaskRecord, utc_now
from app.models.uploaded_file import UploadedFileRecord
from app.schemas.agent_tasks import AgentTaskFinalizeResponse
from app.schemas.clarification import (
    ClarificationAnswerRecord,
    ClarificationAnswerResponse,
    ClarificationAnswerRequest,
    ClarificationGraphState,
    ClarificationStatusResponse,
    ParsedClarificationAnswer,
)
from app.schemas.mock_kaihong import MockDraftCreateRequest, MockDraftOrderItem, MockSourceDocument
from app.schemas.order_draft import (
    ALL_DRAFT_FIELDS,
    REQUIRED_DRAFT_FIELDS,
    FieldEvidence,
    OrderDraftFields,
    OrderDraftPreview,
)
from app.services import agent_tasks, mock_kaihong
from app.services.clarification_graph import ClarificationModel, run_answer_graph, run_question_graph
from app.services.deepseek_client import DeepSeekClient, DeepSeekError
from app.services.privacy import build_redacted_context


CLARIFICATION_STARTED_EVENT = "clarification_started"
CLARIFICATION_QUESTION_GENERATED_EVENT = "clarification_question_generated"
CLARIFICATION_ANSWER_SUBMITTED_EVENT = "clarification_answer_submitted"
DRAFT_FIELDS_MERGED_EVENT = "draft_fields_merged"
CLARIFICATION_COMPLETED_EVENT = "clarification_completed"
DRAFT_FINALIZED_EVENT = "draft_finalized"

ACTIVE_SESSION_STATUS = "active"
COMPLETED_SESSION_STATUS = "completed"

_MODEL_OVERRIDE: ClarificationModel | None = None


class ClarificationError(ValueError):
    def __init__(self, message: str, status_code: int = status.HTTP_400_BAD_REQUEST) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def set_model_override_for_tests(model: ClarificationModel | None) -> None:
    global _MODEL_OVERRIDE
    _MODEL_OVERRIDE = model


def get_or_create_clarification(
    session: Session,
    task_id: str,
    current_username: str,
) -> ClarificationStatusResponse:
    task = _get_owned_task(session, task_id, current_username)
    preview = _require_preview(task)

    if task.status == agent_tasks.READY_FOR_REVIEW_STATUS:
        existing = _get_graph_session(session, task_id)
        return _status_response(task, existing, preview, is_complete=True)
    if task.status != agent_tasks.NEED_MORE_INFO_STATUS:
        raise ClarificationError(f"Cannot clarify task in status {task.status}")

    graph_session = _get_or_create_graph_session(session, task)
    answer_history = _answer_history(graph_session)
    redacted_context, privacy_map = build_redacted_context(preview)
    graph_state = ClarificationGraphState(
        task_id=task.id,
        draft_preview=preview,
        round_number=len(answer_history) + 1,
        answer_history=answer_history,
        redacted_context=redacted_context,
        privacy_map=privacy_map,
    )
    model = _get_model(required=False)
    try:
        graph_state = run_question_graph(graph_state, model)
    except DeepSeekError as exc:
        raise ClarificationError(str(exc), status.HTTP_502_BAD_GATEWAY) from exc

    graph_session.state_json = graph_state.model_dump_json()
    graph_session.current_question_json = (
        graph_state.current_question.model_dump_json()
        if graph_state.current_question is not None
        else None
    )
    graph_session.privacy_map_json = json.dumps(graph_state.privacy_map, ensure_ascii=True)
    graph_session.updated_at = utc_now()
    session.add(graph_session)

    if not _has_event(session, task.id, CLARIFICATION_STARTED_EVENT):
        agent_tasks.add_task_event(
            session=session,
            task_id=task.id,
            event_type=CLARIFICATION_STARTED_EVENT,
            actor=current_username,
            from_status=task.status,
            to_status=task.status,
            message="Clarification session started.",
        )
    if graph_state.current_question is not None:
        agent_tasks.add_task_event(
            session=session,
            task_id=task.id,
            event_type=CLARIFICATION_QUESTION_GENERATED_EVENT,
            actor=current_username,
            from_status=task.status,
            to_status=task.status,
            message="Clarification question generated.",
            details={"question_id": graph_state.current_question.question_id},
        )

    session.commit()
    session.refresh(graph_session)
    session.refresh(task)
    return _status_response(task, graph_session, preview, is_complete=False)


def submit_clarification_answer(
    session: Session,
    task_id: str,
    current_username: str,
    request: ClarificationAnswerRequest,
) -> ClarificationAnswerResponse:
    task = _get_owned_task(session, task_id, current_username)
    if task.status != agent_tasks.NEED_MORE_INFO_STATUS:
        raise ClarificationError(f"Cannot answer clarification in status {task.status}")
    preview = _require_preview(task)
    graph_session = _get_or_create_graph_session(session, task)
    answer_history = _answer_history(graph_session)

    redacted_context, privacy_map = build_redacted_context(preview, request.answer_text)
    model = _get_model(required=True)
    graph_state = ClarificationGraphState(
        task_id=task.id,
        draft_preview=preview,
        round_number=len(answer_history) + 1,
        answer_text=request.answer_text,
        answer_history=answer_history,
        redacted_context=redacted_context,
        privacy_map=privacy_map,
        mode="answer",
    )
    try:
        graph_state = run_answer_graph(graph_state, model)
    except DeepSeekError as exc:
        raise ClarificationError(str(exc), status.HTTP_502_BAD_GATEWAY) from exc

    parsed = graph_state.parsed_answer or ParsedClarificationAnswer()
    updated_preview = _merge_parsed_answer(preview, parsed, request.answer_text)
    completed = not updated_preview.missing_fields and not updated_preview.conflicts

    answer_record = ClarificationAnswerRecord(
        answer_text=request.answer_text,
        parsed_fields=parsed.fields,
        resolved_conflicts=parsed.resolved_conflicts,
    )
    answer_history.append(answer_record)

    task.draft_preview_json = updated_preview.model_dump_json()
    task.missing_fields_json = json.dumps(updated_preview.missing_fields)
    previous_status = task.status
    if completed:
        agent_tasks.set_task_status(task, agent_tasks.READY_FOR_REVIEW_STATUS)

    next_question = None
    if not completed:
        next_state = ClarificationGraphState(
            task_id=task.id,
            draft_preview=updated_preview,
            round_number=len(answer_history) + 1,
            answer_history=answer_history,
            redacted_context=build_redacted_context(updated_preview)[0],
        )
        try:
            next_state = run_question_graph(next_state, _get_model(required=False))
        except DeepSeekError as exc:
            raise ClarificationError(str(exc), status.HTTP_502_BAD_GATEWAY) from exc
        next_question = next_state.current_question
        graph_session.current_question_json = next_question.model_dump_json() if next_question else None
        graph_session.state_json = next_state.model_dump_json()
    else:
        graph_session.status = COMPLETED_SESSION_STATUS
        graph_session.current_question_json = None
        graph_session.state_json = graph_state.model_dump_json()

    graph_session.answer_history_json = json.dumps(
        [answer.model_dump(mode="json") for answer in answer_history],
        ensure_ascii=True,
    )
    graph_session.privacy_map_json = json.dumps(privacy_map, ensure_ascii=True)
    graph_session.updated_at = utc_now()
    session.add(task)
    session.add(graph_session)

    agent_tasks.add_task_event(
        session=session,
        task_id=task.id,
        event_type=CLARIFICATION_ANSWER_SUBMITTED_EVENT,
        actor=current_username,
        from_status=previous_status,
        to_status=task.status,
        message="Clarification answer submitted.",
    )
    agent_tasks.add_task_event(
        session=session,
        task_id=task.id,
        event_type=DRAFT_FIELDS_MERGED_EVENT,
        actor=current_username,
        from_status=previous_status,
        to_status=task.status,
        message="Clarification fields merged into draft preview.",
        details={"fields": sorted(parsed.fields)},
    )
    if completed:
        agent_tasks.add_task_event(
            session=session,
            task_id=task.id,
            event_type=CLARIFICATION_COMPLETED_EVENT,
            actor=current_username,
            from_status=previous_status,
            to_status=task.status,
            message="Clarification completed; draft is ready for review.",
        )

    session.commit()
    session.refresh(task)
    session.refresh(graph_session)
    return ClarificationAnswerResponse(
        task_id=task.id,
        task_status=task.status,
        session_id=graph_session.id,
        parsed_fields=parsed.fields,
        remaining_missing_fields=updated_preview.missing_fields,
        remaining_conflicts=updated_preview.conflicts,
        next_question=next_question,
        is_complete=completed,
        draft_preview=updated_preview,
    )


def finalize_agent_task(
    session: Session,
    task_id: str,
    current_username: str,
) -> AgentTaskFinalizeResponse:
    task = _get_owned_task(session, task_id, current_username)
    if task.status != agent_tasks.READY_FOR_REVIEW_STATUS:
        raise ClarificationError(f"Cannot finalize task in status {task.status}")
    preview = _require_preview(task)
    if preview.missing_fields or preview.conflicts:
        raise ClarificationError("Draft still has missing fields or conflicts")

    uploads = _task_uploads(session, task)
    request = MockDraftCreateRequest(
        customer_id=task.customer_id or preview.fields.customer_name or "mock_customer",
        created_by=current_username,
        source_documents=[
            MockSourceDocument(
                document_id=record.id,
                document_type=record.document_type or record.file_kind,
                filename=record.original_filename,
                confidence=1.0,
            )
            for record in uploads
        ],
        order_items=[
            MockDraftOrderItem(
                order_index=1,
                transport_mode=preview.fields.transport_mode or "unknown",
                route_type="mock",
                fields=preview.fields.model_dump(),
                missing_fields=preview.missing_fields,
            )
        ],
        payload={
            "task_id": task.id,
            "field_evidence": {
                key: value.model_dump(mode="json")
                for key, value in preview.field_evidence.items()
            },
            "conflicts": [conflict.model_dump(mode="json") for conflict in preview.conflicts],
            "source_file_ids": [record.id for record in uploads],
        },
        source="kaihom-agent-v1",
    )
    draft = mock_kaihong.create_draft(session, request)
    previous_status = task.status
    task.finalized_draft_id = draft.draft_id
    agent_tasks.set_task_status(task, agent_tasks.FINALIZED_STATUS)
    session.add(task)
    agent_tasks.add_task_event(
        session=session,
        task_id=task.id,
        event_type=DRAFT_FINALIZED_EVENT,
        actor=current_username,
        from_status=previous_status,
        to_status=task.status,
        message="Draft finalized through Mock Kaihong boundary.",
        details={"draft_id": draft.draft_id},
    )
    session.commit()
    session.refresh(task)
    return AgentTaskFinalizeResponse(
        task_id=task.id,
        status=task.status,
        draft_id=draft.draft_id,
        draft_preview=preview,
        source_file_ids=[record.id for record in uploads],
        audit={"event_type": DRAFT_FINALIZED_EVENT, "draft_id": draft.draft_id},
    )


def _get_owned_task(session: Session, task_id: str, current_username: str) -> AgentTaskRecord:
    task = session.get(AgentTaskRecord, task_id)
    if task is None or task.created_by != current_username:
        raise ClarificationError("Agent task not found", status.HTTP_404_NOT_FOUND)
    return task


def _require_preview(task: AgentTaskRecord) -> OrderDraftPreview:
    if task.draft_preview_json is None:
        raise ClarificationError("Agent task has no draft preview")
    return OrderDraftPreview.model_validate_json(task.draft_preview_json)


def _get_graph_session(session: Session, task_id: str) -> AgentGraphSessionRecord | None:
    return session.exec(
        select(AgentGraphSessionRecord)
        .where(AgentGraphSessionRecord.task_id == task_id)
        .order_by(AgentGraphSessionRecord.created_at)
    ).first()


def _get_or_create_graph_session(
    session: Session,
    task: AgentTaskRecord,
) -> AgentGraphSessionRecord:
    graph_session = _get_graph_session(session, task.id)
    if graph_session is not None:
        return graph_session
    graph_session = AgentGraphSessionRecord(
        id=f"graph_{uuid4().hex[:12]}",
        task_id=task.id,
        graph_thread_id=f"thread_{task.id}",
        status=ACTIVE_SESSION_STATUS,
        answer_history_json="[]",
        created_at=utc_now(),
        updated_at=utc_now(),
    )
    session.add(graph_session)
    return graph_session


def _status_response(
    task: AgentTaskRecord,
    graph_session: AgentGraphSessionRecord | None,
    preview: OrderDraftPreview,
    is_complete: bool,
) -> ClarificationStatusResponse:
    return ClarificationStatusResponse(
        task_id=task.id,
        task_status=task.status,
        session_id=graph_session.id if graph_session else None,
        current_question=_current_question(graph_session),
        answer_history=_answer_history(graph_session),
        missing_fields=preview.missing_fields,
        conflicts=preview.conflicts,
        is_complete=is_complete,
        draft_preview=preview,
    )


def _current_question(graph_session: AgentGraphSessionRecord | None):
    if graph_session is None or not graph_session.current_question_json:
        return None
    from app.schemas.clarification import ClarificationQuestion

    return ClarificationQuestion.model_validate_json(graph_session.current_question_json)


def _answer_history(graph_session: AgentGraphSessionRecord | None) -> list[ClarificationAnswerRecord]:
    if graph_session is None or not graph_session.answer_history_json:
        return []
    return [
        ClarificationAnswerRecord.model_validate(item)
        for item in json.loads(graph_session.answer_history_json)
    ]


def _merge_parsed_answer(
    preview: OrderDraftPreview,
    parsed: ParsedClarificationAnswer,
    answer_text: str,
) -> OrderDraftPreview:
    for field_name in parsed.fields:
        if field_name not in ALL_DRAFT_FIELDS:
            raise ClarificationError(f"Unknown draft field from model: {field_name}")

    field_data = preview.fields.model_dump()
    field_data.update(parsed.fields)
    fields = OrderDraftFields.model_validate(field_data)
    missing = [
        field_name
        for field_name in REQUIRED_DRAFT_FIELDS
        if _is_missing(getattr(fields, field_name))
    ]
    evidence = dict(preview.field_evidence)
    for field_name in parsed.fields:
        evidence[field_name] = FieldEvidence(
            source_file_id="user_clarification",
            source_filename=None,
            source_text=answer_text,
            confidence=parsed.confidence,
        )
    resolved = set(parsed.resolved_conflicts) | set(parsed.fields)
    conflicts = [
        conflict
        for conflict in preview.conflicts
        if conflict.field_name not in resolved
    ]
    return OrderDraftPreview(
        fields=fields,
        missing_fields=missing,
        field_evidence=evidence,
        conflicts=conflicts,
    )


def _is_missing(value: Any) -> bool:
    return value is None or (isinstance(value, str) and not value.strip())


def _get_model(required: bool) -> ClarificationModel | None:
    if _MODEL_OVERRIDE is not None:
        return _MODEL_OVERRIDE
    if get_settings().deepseek_api_key:
        return DeepSeekClient()
    if required:
        raise ClarificationError("DeepSeek API key is required to parse clarification answers", status.HTTP_503_SERVICE_UNAVAILABLE)
    return None


def _task_uploads(session: Session, task: AgentTaskRecord) -> list[UploadedFileRecord]:
    file_ids = list(json.loads(task.file_ids_json))
    records_by_id = {
        record.id: record
        for record in session.exec(
            select(UploadedFileRecord).where(UploadedFileRecord.task_id == task.id)
        ).all()
    }
    return [records_by_id[file_id] for file_id in file_ids if file_id in records_by_id]


def _has_event(session: Session, task_id: str, event_type: str) -> bool:
    from app.models.agent_task import AgentTaskEventRecord

    return (
        session.exec(
            select(AgentTaskEventRecord)
            .where(AgentTaskEventRecord.task_id == task_id)
            .where(AgentTaskEventRecord.event_type == event_type)
        ).first()
        is not None
    )

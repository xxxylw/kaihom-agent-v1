from typing import Any, Literal

from pydantic import BaseModel, Field

from app.schemas.order_draft import FieldConflict, OrderDraftPreview


class ClarificationFieldRequest(BaseModel):
    field_name: str
    label: str | None = None
    reason: str | None = None
    current_value: Any | None = None
    evidence: dict[str, Any] | None = None
    candidate_values: list[Any] = Field(default_factory=list)


class ClarificationQuestion(BaseModel):
    question_id: str
    text: str
    requested_fields: list[ClarificationFieldRequest] = Field(default_factory=list)
    conflicts: list[FieldConflict] = Field(default_factory=list)
    round_number: int = 1


class ClarificationAnswerRecord(BaseModel):
    answer_text: str
    parsed_fields: dict[str, Any] = Field(default_factory=dict)
    resolved_conflicts: list[str] = Field(default_factory=list)


class ClarificationStatusResponse(BaseModel):
    task_id: str
    task_status: str
    session_id: str | None = None
    current_question: ClarificationQuestion | None = None
    answer_history: list[ClarificationAnswerRecord] = Field(default_factory=list)
    missing_fields: list[str] = Field(default_factory=list)
    conflicts: list[FieldConflict] = Field(default_factory=list)
    is_complete: bool = False
    draft_preview: OrderDraftPreview | None = None


class ClarificationAnswerRequest(BaseModel):
    answer_text: str = Field(min_length=1)


class ParsedClarificationAnswer(BaseModel):
    fields: dict[str, Any] = Field(default_factory=dict)
    resolved_conflicts: list[str] = Field(default_factory=list)
    confidence: float = 1.0
    notes: str | None = None


class ClarificationAnswerResponse(BaseModel):
    task_id: str
    task_status: str
    session_id: str
    parsed_fields: dict[str, Any] = Field(default_factory=dict)
    remaining_missing_fields: list[str] = Field(default_factory=list)
    remaining_conflicts: list[FieldConflict] = Field(default_factory=list)
    next_question: ClarificationQuestion | None = None
    is_complete: bool = False
    draft_preview: OrderDraftPreview


class ClarificationGraphState(BaseModel):
    task_id: str
    draft_preview: OrderDraftPreview
    round_number: int = 1
    answer_text: str | None = None
    answer_history: list[ClarificationAnswerRecord] = Field(default_factory=list)
    current_question: ClarificationQuestion | None = None
    parsed_answer: ParsedClarificationAnswer | None = None
    redacted_context: dict[str, Any] = Field(default_factory=dict)
    privacy_map: dict[str, str] = Field(default_factory=dict)
    mode: Literal["question", "answer"] = "question"
    is_complete: bool = False

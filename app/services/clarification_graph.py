from typing import Any, Protocol
from uuid import uuid4

from app.schemas.clarification import (
    ClarificationFieldRequest,
    ClarificationGraphState,
    ClarificationQuestion,
    ParsedClarificationAnswer,
)

try:  # pragma: no cover - exercised when langgraph is installed locally.
    from langgraph.graph import END, StateGraph
except Exception:  # pragma: no cover - current test env may not have langgraph installed.
    END = None
    StateGraph = None


class ClarificationModel(Protocol):
    def generate_question(self, redacted_context: dict[str, Any]) -> ClarificationQuestion:
        ...

    def parse_answer(
        self,
        redacted_context: dict[str, Any],
        answer_text: str,
    ) -> ParsedClarificationAnswer:
        ...


LANGGRAPH_AVAILABLE = StateGraph is not None


def run_question_graph(
    state: ClarificationGraphState,
    model: ClarificationModel | None = None,
) -> ClarificationGraphState:
    if _is_complete(state):
        state.is_complete = True
        state.current_question = None
        return state

    if LANGGRAPH_AVAILABLE:
        graph = _build_question_graph(model)
        result = graph.invoke(state.model_dump(mode="json"))
        return ClarificationGraphState.model_validate(result)

    return _generate_question(state, model)


def run_answer_graph(
    state: ClarificationGraphState,
    model: ClarificationModel,
) -> ClarificationGraphState:
    if LANGGRAPH_AVAILABLE:
        graph = _build_answer_graph(model)
        result = graph.invoke(state.model_dump(mode="json"))
        return ClarificationGraphState.model_validate(result)

    return _parse_answer(state, model)


def _build_question_graph(model: ClarificationModel | None):
    graph = StateGraph(dict)
    graph.add_node("inspect_draft", lambda raw: _as_dict(_inspect_draft(_as_state(raw))))
    graph.add_node("generate_question", lambda raw: _as_dict(_generate_question(_as_state(raw), model)))
    graph.set_entry_point("inspect_draft")
    graph.add_conditional_edges(
        "inspect_draft",
        lambda raw: "done" if raw.get("is_complete") else "question",
        {"done": END, "question": "generate_question"},
    )
    graph.add_edge("generate_question", END)
    return graph.compile()


def _build_answer_graph(model: ClarificationModel):
    graph = StateGraph(dict)
    graph.add_node("parse_answer", lambda raw: _as_dict(_parse_answer(_as_state(raw), model)))
    graph.set_entry_point("parse_answer")
    graph.add_edge("parse_answer", END)
    return graph.compile()


def _inspect_draft(state: ClarificationGraphState) -> ClarificationGraphState:
    state.is_complete = _is_complete(state)
    return state


def _generate_question(
    state: ClarificationGraphState,
    model: ClarificationModel | None,
) -> ClarificationGraphState:
    if model is not None:
        state.current_question = model.generate_question(state.redacted_context)
        return state

    requested_fields = [
        ClarificationFieldRequest(
            field_name=field_name,
            label=field_name.replace("_", " "),
            reason="required field is missing",
        )
        for field_name in state.draft_preview.missing_fields[:3]
    ]
    conflicts = state.draft_preview.conflicts[:3]
    if conflicts and not requested_fields:
        requested_fields = [
            ClarificationFieldRequest(
                field_name=conflict.field_name,
                label=conflict.field_name.replace("_", " "),
                reason="conflicting values need confirmation",
                current_value=conflict.kept_value,
                candidate_values=[
                    value
                    for value in [conflict.kept_value, conflict.conflicting_value]
                    if value is not None
                ],
            )
            for conflict in conflicts
        ]
    names = [item.label or item.field_name for item in requested_fields]
    text = "Please confirm " + ", ".join(names) + "." if names else "Please confirm the draft details."
    state.current_question = ClarificationQuestion(
        question_id=f"question_{uuid4().hex[:12]}",
        text=text,
        requested_fields=requested_fields,
        conflicts=conflicts,
        round_number=state.round_number,
    )
    return state


def _parse_answer(
    state: ClarificationGraphState,
    model: ClarificationModel,
) -> ClarificationGraphState:
    if not state.answer_text:
        raise ValueError("answer_text is required for answer parsing")
    state.parsed_answer = model.parse_answer(state.redacted_context, state.answer_text)
    return state


def _is_complete(state: ClarificationGraphState) -> bool:
    return not state.draft_preview.missing_fields and not state.draft_preview.conflicts


def _as_state(raw: dict[str, Any]) -> ClarificationGraphState:
    return ClarificationGraphState.model_validate(raw)


def _as_dict(state: ClarificationGraphState) -> dict[str, Any]:
    return state.model_dump(mode="json")

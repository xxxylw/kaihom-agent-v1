from app.schemas.clarification import ClarificationGraphState, ClarificationQuestion, ParsedClarificationAnswer
from app.schemas.order_draft import FieldConflict, OrderDraftFields, OrderDraftPreview
from app.services.clarification_graph import run_answer_graph, run_question_graph


class FakeModel:
    def generate_question(self, redacted_context):
        return ClarificationQuestion(
            question_id="q_fake",
            text="Please provide shipper phone and consignee address.",
            requested_fields=[
                {"field_name": "shipper_phone"},
                {"field_name": "consignee_address"},
            ],
            round_number=1,
        )

    def parse_answer(self, redacted_context, answer_text):
        return ParsedClarificationAnswer(
            fields={
                "shipper_phone": "13800000001",
                "consignee_address": "Ningbo Port",
            },
            resolved_conflicts=[],
        )


def test_missing_fields_produce_structured_question_with_fake_model():
    state = ClarificationGraphState(
        task_id="task_1",
        draft_preview=OrderDraftPreview(missing_fields=["shipper_phone", "consignee_address"]),
        redacted_context={"missing_fields": ["shipper_phone", "consignee_address"]},
    )

    result = run_question_graph(state, FakeModel())

    assert result.current_question is not None
    assert result.current_question.question_id == "q_fake"
    assert [field.field_name for field in result.current_question.requested_fields] == [
        "shipper_phone",
        "consignee_address",
    ]


def test_conflicts_produce_question_with_candidate_values_without_model():
    conflict = FieldConflict(
        field_name="cargo_name",
        kept_value="Auto parts",
        conflicting_value="Electronics",
        source_file_id="file_1",
        source_text="Cargo: Electronics",
    )
    state = ClarificationGraphState(
        task_id="task_1",
        draft_preview=OrderDraftPreview(conflicts=[conflict]),
    )

    result = run_question_graph(state)

    assert result.current_question is not None
    field = result.current_question.requested_fields[0]
    assert field.field_name == "cargo_name"
    assert field.candidate_values == ["Auto parts", "Electronics"]


def test_answer_graph_parses_answer_with_fake_model():
    state = ClarificationGraphState(
        task_id="task_1",
        draft_preview=OrderDraftPreview(missing_fields=["shipper_phone"]),
        answer_text="phone is 13800000001",
    )

    result = run_answer_graph(state, FakeModel())

    assert result.parsed_answer is not None
    assert result.parsed_answer.fields["shipper_phone"] == "13800000001"


def test_complete_draft_marks_graph_complete():
    state = ClarificationGraphState(
        task_id="task_1",
        draft_preview=OrderDraftPreview(fields=OrderDraftFields(customer_name="A")),
    )

    result = run_question_graph(state)

    assert result.is_complete is True
    assert result.current_question is None

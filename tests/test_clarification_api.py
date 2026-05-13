from fastapi.testclient import TestClient

from app.main import app
from app.schemas.clarification import ClarificationQuestion, ParsedClarificationAnswer
from app.services import clarification


client = TestClient(app)


class FakeClarificationModel:
    def __init__(self, fields=None, resolved_conflicts=None):
        self.fields = fields or {}
        self.resolved_conflicts = resolved_conflicts or []

    def generate_question(self, redacted_context):
        missing = redacted_context.get("missing_fields") or []
        requested_fields = [{"field_name": field_name} for field_name in missing[:3]]
        return ClarificationQuestion(
            question_id="q_test",
            text="Please provide the missing logistics details.",
            requested_fields=requested_fields,
            round_number=1,
        )

    def parse_answer(self, redacted_context, answer_text):
        return ParsedClarificationAnswer(
            fields=self.fields,
            resolved_conflicts=self.resolved_conflicts,
            confidence=0.95,
        )


def login_headers(username: str = "yw001") -> dict[str, str]:
    response = client.post(
        "/mock/kaihong/auth/login",
        json={"username": username, "password": "mock123456"},
    )
    assert response.status_code == 200
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def upload_file(name: str, headers: dict[str, str]) -> str:
    response = client.post(
        "/uploads",
        files=[("files", (name, b"fake-file", "image/jpeg"))],
        headers=headers,
    )
    assert response.status_code == 201
    return response.json()["files"][0]["file_id"]


def create_and_extract(filename: str, headers: dict[str, str], customer_id: str | None = "cust_001"):
    file_id = upload_file(filename, headers)
    payload = {"file_ids": [file_id], "customer_id": customer_id}
    create_response = client.post("/agent/tasks", json=payload, headers=headers)
    assert create_response.status_code == 201
    task_id = create_response.json()["task_id"]
    extract_response = client.post(f"/agent/tasks/{task_id}/extract", headers=headers)
    assert extract_response.status_code == 200
    return task_id, file_id, extract_response.json()


def teardown_function():
    clarification.set_model_override_for_tests(None)


def test_clarification_routes_require_bearer_token():
    get_response = client.get("/agent/tasks/task_missing/clarification")
    answer_response = client.post(
        "/agent/tasks/task_missing/clarification/answers",
        json={"answer_text": "hello"},
    )
    finalize_response = client.post("/agent/tasks/task_missing/finalize")

    assert get_response.status_code == 401
    assert answer_response.status_code == 401
    assert finalize_response.status_code == 401


def test_get_clarification_returns_current_question():
    headers = login_headers()
    task_id, _file_id, extracted = create_and_extract("incomplete-receipt.jpg", headers)
    assert extracted["status"] == "need_more_info"

    response = client.get(f"/agent/tasks/{task_id}/clarification", headers=headers)

    assert response.status_code == 200
    body = response.json()
    assert body["task_id"] == task_id
    assert body["task_status"] == "need_more_info"
    assert body["session_id"].startswith("graph_")
    assert body["current_question"]["question_id"].startswith("question_")
    assert body["current_question"]["requested_fields"]
    assert "shipper_phone" in body["missing_fields"]


def test_submit_answer_merges_fields_and_reaches_ready_for_review():
    headers = login_headers()
    task_id, _file_id, extracted = create_and_extract("incomplete-receipt.jpg", headers)
    missing_fields = extracted["draft_preview"]["missing_fields"]
    clarification.set_model_override_for_tests(
        FakeClarificationModel(
            fields={
                field_name: _value_for_field(field_name)
                for field_name in missing_fields
            }
        )
    )
    client.get(f"/agent/tasks/{task_id}/clarification", headers=headers)

    response = client.post(
        f"/agent/tasks/{task_id}/clarification/answers",
        json={"answer_text": "Here are the missing details."},
        headers=headers,
    )

    assert response.status_code == 200
    body = response.json()
    assert body["task_status"] == "ready_for_review"
    assert body["remaining_missing_fields"] == []
    assert body["is_complete"] is True
    assert body["draft_preview"]["field_evidence"]["shipper_phone"]["source_file_id"] == "user_clarification"


def test_submit_answer_rejects_unknown_model_field_without_mutating_draft():
    headers = login_headers()
    task_id, _file_id, extracted = create_and_extract("incomplete-receipt.jpg", headers)
    before_missing = extracted["draft_preview"]["missing_fields"]
    clarification.set_model_override_for_tests(FakeClarificationModel(fields={"not_a_field": "x"}))
    client.get(f"/agent/tasks/{task_id}/clarification", headers=headers)

    response = client.post(
        f"/agent/tasks/{task_id}/clarification/answers",
        json={"answer_text": "bad model output"},
        headers=headers,
    )

    assert response.status_code == 400
    detail_response = client.get(f"/agent/tasks/{task_id}", headers=headers)
    assert detail_response.json()["draft_preview"]["missing_fields"] == before_missing


def test_finalize_rejects_need_more_info_task():
    headers = login_headers()
    task_id, _file_id, _extracted = create_and_extract("incomplete-receipt.jpg", headers)

    response = client.post(f"/agent/tasks/{task_id}/finalize", headers=headers)

    assert response.status_code == 400
    assert "need_more_info" in response.json()["detail"]


def test_finalize_ready_task_saves_mock_kaihong_draft():
    headers = login_headers()
    task_id, file_id, extracted = create_and_extract("complete-entrustment.jpg", headers)
    assert extracted["status"] == "ready_for_review"

    response = client.post(f"/agent/tasks/{task_id}/finalize", headers=headers)

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "finalized"
    assert body["draft_id"].startswith("draft_")
    assert body["source_file_ids"] == [file_id]
    assert body["draft_preview"]["fields"]["cargo_name"] == "Auto parts"
    assert body["audit"]["event_type"] == "draft_finalized"

    detail_response = client.get(f"/agent/tasks/{task_id}", headers=headers)
    assert detail_response.json()["status"] == "finalized"


def test_openapi_documents_clarification_and_finalize_contracts():
    response = client.get("/openapi.json")

    assert response.status_code == 200
    paths = response.json()["paths"]
    assert "/agent/tasks/{task_id}/clarification" in paths
    assert "/agent/tasks/{task_id}/clarification/answers" in paths
    assert "/agent/tasks/{task_id}/finalize" in paths


def _value_for_field(field_name: str):
    values = {
        "customer_name": "Ningbo Future Trading Co., Ltd.",
        "shipper_name": "Alice Chen",
        "shipper_phone": "13800000001",
        "shipper_address": "Ningbo Port",
        "consignee_name": "Bob Wang",
        "consignee_phone": "13800000002",
        "consignee_address": "Shanghai Port",
        "cargo_name": "Auto parts",
        "package_count": 20,
        "gross_weight_kg": 1200.0,
    }
    return values[field_name]

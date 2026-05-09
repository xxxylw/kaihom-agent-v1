from pathlib import Path

from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app.db.session import engine
from app.main import app


client = TestClient(app)


def login_headers(username: str = "yw001") -> dict[str, str]:
    response = client.post(
        "/mock/kaihong/auth/login",
        json={"username": username, "password": "mock123456"},
    )
    assert response.status_code == 200
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def upload_file(
    name: str,
    content: bytes,
    content_type: str,
    headers: dict[str, str] | None = None,
) -> str:
    response = client.post(
        "/uploads",
        files=[("files", (name, content, content_type))],
        headers=headers or login_headers(),
    )
    assert response.status_code == 201
    return response.json()["files"][0]["file_id"]


def create_task(
    file_ids: list[str],
    headers: dict[str, str] | None = None,
    customer_id: str | None = None,
):
    payload: dict[str, object] = {"file_ids": file_ids}
    if customer_id is not None:
        payload["customer_id"] = customer_id
    return client.post("/agent/tasks", json=payload, headers=headers or login_headers())


def test_agent_task_routes_require_bearer_token():
    create_response = client.post("/agent/tasks", json={"file_ids": ["file_missing"]})
    get_response = client.get("/agent/tasks/task_missing")
    events_response = client.get("/agent/tasks/task_missing/events")

    assert create_response.status_code == 401
    assert get_response.status_code == 401
    assert events_response.status_code == 401


def test_create_agent_task_from_one_file_starts_created():
    file_id = upload_file("agent-single.jpg", b"fake-jpeg", "image/jpeg")

    response = create_task([file_id])

    assert response.status_code == 201
    body = response.json()
    assert body["task_id"].startswith("task_")
    assert body["status"] == "created"
    assert body["customer_id"] is None
    assert body["file_ids"] == [file_id]
    assert body["draft_preview"] is None
    assert body["questions"] == []
    assert body["error_code"] is None
    assert body["error_message"] is None
    assert body["files"][0]["file_id"] == file_id
    assert body["files"][0]["task_id"] == body["task_id"]


def test_create_agent_task_from_multiple_files_links_upload_metadata():
    headers = login_headers()
    file_a = upload_file("agent-a.png", b"fake-png", "image/png", headers)
    file_b = upload_file("agent-b.pdf", b"%PDF-1.4 fake", "application/pdf", headers)

    response = create_task([file_a, file_b], headers=headers)

    assert response.status_code == 201
    body = response.json()
    assert body["file_ids"] == [file_a, file_b]
    for file_id in [file_a, file_b]:
        upload_response = client.get(f"/uploads/{file_id}", headers=headers)
        assert upload_response.status_code == 200
        assert upload_response.json()["task_id"] == body["task_id"]


def test_create_agent_task_preserves_optional_customer_id():
    file_id = upload_file("agent-customer.webp", b"fake-webp", "image/webp")

    response = create_task([file_id], customer_id="cust_sh_001")

    assert response.status_code == 201
    assert response.json()["customer_id"] == "cust_sh_001"


def test_create_agent_task_with_unknown_file_rejects_without_partial_task():
    from app.models.agent_task import AgentTaskRecord

    with Session(engine) as session:
        before_count = len(session.exec(select(AgentTaskRecord)).all())

    response = create_task(["file_does_not_exist"])

    assert response.status_code == 404
    assert "not found" in response.json()["detail"]
    with Session(engine) as session:
        after_count = len(session.exec(select(AgentTaskRecord)).all())
    assert after_count == before_count


def test_get_agent_task_returns_safe_file_metadata():
    headers = login_headers()
    file_id = upload_file("agent-detail.jpg", b"fake-jpeg", "image/jpeg", headers)
    create_response = create_task([file_id], headers=headers)
    task_id = create_response.json()["task_id"]

    response = client.get(f"/agent/tasks/{task_id}", headers=headers)

    assert response.status_code == 200
    body = response.json()
    assert body["task_id"] == task_id
    assert body["status"] == "created"
    assert body["file_ids"] == [file_id]
    assert body["questions"] == []
    assert body["draft_preview"] is None
    file_metadata = body["files"][0]
    assert "storage_path" not in file_metadata
    assert not any(
        Path(value).is_absolute()
        for value in file_metadata.values()
        if isinstance(value, str)
    )


def test_agent_task_events_are_queryable_in_chronological_order():
    file_id = upload_file("agent-events.jpg", b"fake-jpeg", "image/jpeg")
    create_response = create_task([file_id])
    task_id = create_response.json()["task_id"]

    response = client.get(f"/agent/tasks/{task_id}/events", headers=login_headers())

    assert response.status_code == 200
    events = response.json()["events"]
    assert [event["event_type"] for event in events] == [
        "task_created",
        "files_attached",
    ]
    assert events[0]["from_status"] is None
    assert events[0]["to_status"] == "created"


def test_agent_task_transition_rules_allow_valid_and_reject_invalid():
    from app.services import agent_tasks

    headers = login_headers()
    file_id = upload_file("agent-transition.pdf", b"%PDF-1.4 fake", "application/pdf", headers)
    task_id = create_task([file_id], headers=headers).json()["task_id"]

    with Session(engine) as session:
        extracting = agent_tasks.transition_task_status(
            session=session,
            task_id=task_id,
            new_status=agent_tasks.EXTRACTING_STATUS,
            actor="yw001",
        )
        assert extracting.status == "extracting"
        ready = agent_tasks.transition_task_status(
            session=session,
            task_id=task_id,
            new_status=agent_tasks.READY_FOR_REVIEW_STATUS,
            actor="yw001",
        )
        assert ready.status == "ready_for_review"
        finalized = agent_tasks.transition_task_status(
            session=session,
            task_id=task_id,
            new_status=agent_tasks.FINALIZED_STATUS,
            actor="yw001",
        )
        assert finalized.status == "finalized"

        try:
            agent_tasks.transition_task_status(
                session=session,
                task_id=task_id,
                new_status=agent_tasks.EXTRACTING_STATUS,
                actor="yw001",
            )
        except agent_tasks.AgentTaskError as exc:
            assert exc.status_code == 400
            assert "Invalid status transition" in exc.message
        else:
            raise AssertionError("finalized task should not transition to extracting")


def test_openapi_documents_agent_task_contracts():
    response = client.get("/openapi.json")

    assert response.status_code == 200
    paths = response.json()["paths"]
    assert "/agent/tasks" in paths
    assert "/agent/tasks/{task_id}" in paths
    assert "/agent/tasks/{task_id}/events" in paths

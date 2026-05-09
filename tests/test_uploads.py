from pathlib import Path

from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine, select

from app.core.config import get_settings
from app.main import app
from app.models.uploaded_file import UploadedFileRecord
from app.services.uploads import cleanup_uploaded_files


client = TestClient(app)


def login_headers() -> dict[str, str]:
    response = client.post(
        "/mock/kaihong/auth/login",
        json={"username": "yw001", "password": "mock123456"},
    )
    assert response.status_code == 200
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def upload_file(
    name: str,
    content: bytes,
    content_type: str,
    headers: dict[str, str] | None = None,
):
    return client.post(
        "/uploads",
        files=[("files", (name, content, content_type))],
        headers=headers or login_headers(),
    )


def test_upload_requires_bearer_token():
    response = client.post(
        "/uploads",
        files=[("files", ("invoice.jpg", b"fake-jpeg", "image/jpeg"))],
    )

    assert response.status_code == 401


def test_single_image_upload_returns_safe_metadata():
    response = upload_file("IMG_0012.jpg", b"fake-jpeg", "image/jpeg")

    assert response.status_code == 201
    body = response.json()
    assert len(body["files"]) == 1
    uploaded = body["files"][0]
    assert uploaded["file_id"].startswith("file_")
    assert uploaded["original_filename"] == "IMG_0012.jpg"
    assert uploaded["file_kind"] == "image"
    assert uploaded["content_type"] == "image/jpeg"
    assert uploaded["size_bytes"] == len(b"fake-jpeg")
    assert uploaded["status"] == "uploaded"
    assert uploaded["customer_id"] is None
    assert uploaded["document_type"] is None
    assert "storage_path" not in uploaded
    assert not any(
        Path(value).is_absolute()
        for value in uploaded.values()
        if isinstance(value, str)
    )


def test_multi_file_upload_accepts_image_and_pdf_with_same_endpoint():
    response = client.post(
        "/uploads",
        files=[
            ("files", ("invoice.png", b"fake-png", "image/png")),
            ("files", ("entrustment.pdf", b"%PDF-1.4 fake", "application/pdf")),
        ],
        headers=login_headers(),
    )

    assert response.status_code == 201
    files = response.json()["files"]
    assert len(files) == 2
    assert [item["file_kind"] for item in files] == ["image", "pdf"]
    assert [item["original_filename"] for item in files] == [
        "invoice.png",
        "entrustment.pdf",
    ]


def test_unsupported_file_type_is_rejected():
    response = upload_file("script.exe", b"not-a-document", "application/octet-stream")

    assert response.status_code == 400
    assert "not supported" in response.json()["detail"]


def test_oversize_file_is_rejected_without_metadata(monkeypatch):
    settings = get_settings()
    original_limit = settings.upload_max_file_size_bytes
    settings.upload_max_file_size_bytes = 4
    try:
        response = upload_file("large.pdf", b"12345", "application/pdf")
    finally:
        settings.upload_max_file_size_bytes = original_limit

    assert response.status_code == 413
    assert "exceeds" in response.json()["detail"]


def test_too_many_files_are_rejected(monkeypatch):
    settings = get_settings()
    original_limit = settings.upload_max_files_per_request
    settings.upload_max_files_per_request = 1
    try:
        response = client.post(
            "/uploads",
            files=[
                ("files", ("a.jpg", b"a", "image/jpeg")),
                ("files", ("b.jpg", b"b", "image/jpeg")),
            ],
            headers=login_headers(),
        )
    finally:
        settings.upload_max_files_per_request = original_limit

    assert response.status_code == 400
    assert "Too many files" in response.json()["detail"]


def test_uploaded_file_metadata_can_be_retrieved_and_linked_to_task():
    create_response = upload_file("packing-list.webp", b"fake-webp", "image/webp")
    assert create_response.status_code == 201
    file_id = create_response.json()["files"][0]["file_id"]

    get_response = client.get(f"/uploads/{file_id}", headers=login_headers())
    assert get_response.status_code == 200
    assert get_response.json()["file_id"] == file_id
    assert get_response.json()["task_id"] is None

    link_response = client.patch(
        f"/uploads/{file_id}/task",
        json={"task_id": "task_future_001"},
        headers=login_headers(),
    )
    assert link_response.status_code == 200
    assert link_response.json()["file_id"] == file_id
    assert link_response.json()["task_id"] == "task_future_001"


def test_openapi_documents_upload_contracts():
    response = client.get("/openapi.json")

    assert response.status_code == 200
    paths = response.json()["paths"]
    assert "/uploads" in paths
    assert "/uploads/{file_id}" in paths
    assert "/uploads/{file_id}/task" in paths


def test_cleanup_uploaded_files_removes_storage_and_metadata(tmp_path):
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    SQLModel.metadata.create_all(engine)
    stored_file = tmp_path / "file_cleanup_001.jpg"
    stored_file.write_bytes(b"fake-jpeg")

    with Session(engine) as session:
        session.add(
            UploadedFileRecord(
                id="file_cleanup_001",
                original_filename="cleanup.jpg",
                stored_filename=stored_file.name,
                storage_path=f"{tmp_path.name}/{stored_file.name}",
                content_type="image/jpeg",
                file_kind="image",
                size_bytes=9,
                sha256="fake-sha",
                uploaded_by="yw001",
                task_id="task_keep_history",
            )
        )
        session.commit()

        result = cleanup_uploaded_files(session=session, upload_dir=tmp_path)

        assert result.records_deleted == 1
        assert result.files_deleted == 1
        assert not stored_file.exists()
        assert session.exec(select(UploadedFileRecord)).all() == []

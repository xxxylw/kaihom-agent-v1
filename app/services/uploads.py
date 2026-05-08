from pathlib import Path
from uuid import uuid4
import hashlib

from fastapi import UploadFile, status
from sqlmodel import Session

from app.core.config import Settings, get_settings
from app.models.uploaded_file import UploadedFileRecord, utc_now
from app.schemas.uploads import UploadedFileResponse


ALLOWED_UPLOAD_TYPES: dict[str, tuple[str, str]] = {
    ".jpg": ("image/jpeg", "image"),
    ".jpeg": ("image/jpeg", "image"),
    ".png": ("image/png", "image"),
    ".webp": ("image/webp", "image"),
    ".pdf": ("application/pdf", "pdf"),
}


class UploadValidationError(ValueError):
    def __init__(
        self,
        message: str,
        status_code: int = status.HTTP_400_BAD_REQUEST,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def validate_upload_batch(files: list[UploadFile], settings: Settings) -> None:
    if not files:
        raise UploadValidationError("At least one file is required")

    if len(files) > settings.upload_max_files_per_request:
        raise UploadValidationError(
            f"Too many files: maximum is {settings.upload_max_files_per_request}"
        )

    total_size = 0
    for upload in files:
        extension = _extension_for(upload)
        if extension not in ALLOWED_UPLOAD_TYPES:
            raise UploadValidationError(f"{upload.filename} is not supported")

        expected_content_type, _file_kind = ALLOWED_UPLOAD_TYPES[extension]
        if upload.content_type != expected_content_type:
            raise UploadValidationError(
                f"{upload.filename} content type {upload.content_type} is not supported"
            )

        size = _file_size(upload)
        if size <= 0:
            raise UploadValidationError(f"{upload.filename} is empty")
        if size > settings.upload_max_file_size_bytes:
            raise UploadValidationError(
                f"{upload.filename} exceeds {settings.upload_max_file_size_bytes} bytes",
                413,
            )
        total_size += size

    if total_size > settings.upload_max_request_size_bytes:
        raise UploadValidationError(
            f"Upload batch exceeds {settings.upload_max_request_size_bytes} bytes",
            413,
        )


def save_uploaded_files(
    session: Session,
    files: list[UploadFile],
    uploaded_by: str,
    customer_id: str | None = None,
) -> list[UploadedFileResponse]:
    settings = get_settings()
    validate_upload_batch(files, settings)

    upload_root = Path(settings.upload_dir)
    upload_root.mkdir(parents=True, exist_ok=True)

    records: list[UploadedFileRecord] = []
    for upload in files:
        extension = _extension_for(upload)
        content_type, file_kind = ALLOWED_UPLOAD_TYPES[extension]
        file_id = f"file_{uuid4().hex[:12]}"
        stored_filename = f"{file_id}{extension}"
        destination = upload_root / stored_filename

        content = _read_content(upload)
        destination.write_bytes(content)
        now = utc_now()
        record = UploadedFileRecord(
            id=file_id,
            original_filename=upload.filename or stored_filename,
            stored_filename=stored_filename,
            storage_path=_relative_storage_path(upload_root, stored_filename),
            content_type=content_type,
            file_kind=file_kind,
            size_bytes=len(content),
            sha256=hashlib.sha256(content).hexdigest(),
            uploaded_by=uploaded_by,
            customer_id=customer_id,
            created_at=now,
            updated_at=now,
        )
        session.add(record)
        records.append(record)

    session.commit()
    for record in records:
        session.refresh(record)
    return [_record_to_response(record) for record in records]


def get_uploaded_file(
    session: Session,
    file_id: str,
) -> UploadedFileResponse | None:
    record = session.get(UploadedFileRecord, file_id)
    if record is None:
        return None
    return _record_to_response(record)


def link_file_to_task(
    session: Session,
    file_id: str,
    task_id: str,
) -> UploadedFileResponse | None:
    record = session.get(UploadedFileRecord, file_id)
    if record is None:
        return None
    record.task_id = task_id
    record.updated_at = utc_now()
    session.add(record)
    session.commit()
    session.refresh(record)
    return _record_to_response(record)


def _record_to_response(record: UploadedFileRecord) -> UploadedFileResponse:
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


def _extension_for(upload: UploadFile) -> str:
    return Path(upload.filename or "").suffix.lower()


def _file_size(upload: UploadFile) -> int:
    upload.file.seek(0, 2)
    size = upload.file.tell()
    upload.file.seek(0)
    return size


def _read_content(upload: UploadFile) -> bytes:
    upload.file.seek(0)
    content = upload.file.read()
    upload.file.seek(0)
    return content


def _relative_storage_path(upload_root: Path, stored_filename: str) -> str:
    return str(Path(upload_root.name) / stored_filename).replace("\\", "/")

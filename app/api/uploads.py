from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlmodel import Session

from app.api.mock_kaihong import get_current_user
from app.db.session import get_session
from app.schemas.mock_kaihong import MockUserResponse
from app.schemas.uploads import (
    LinkFileTaskRequest,
    UploadedFileResponse,
    UploadFilesResponse,
)
from app.services import uploads


router = APIRouter(prefix="/uploads", tags=["Uploads"])


@router.post("", response_model=UploadFilesResponse, status_code=201)
def upload_files(
    files: Annotated[list[UploadFile], File()],
    customer_id: Annotated[str | None, Form()] = None,
    session: Session = Depends(get_session),
    current_user: MockUserResponse = Depends(get_current_user),
) -> UploadFilesResponse:
    try:
        saved = uploads.save_uploaded_files(
            session=session,
            files=files,
            uploaded_by=current_user.username,
            customer_id=customer_id,
        )
    except uploads.UploadValidationError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc
    return UploadFilesResponse(files=saved)


@router.get("/{file_id}", response_model=UploadedFileResponse)
def get_uploaded_file(
    file_id: str,
    session: Session = Depends(get_session),
    current_user: MockUserResponse = Depends(get_current_user),
) -> UploadedFileResponse:
    uploaded = uploads.get_uploaded_file(session, file_id)
    if uploaded is None:
        raise HTTPException(status_code=404, detail="Uploaded file not found")
    return uploaded


@router.patch("/{file_id}/task", response_model=UploadedFileResponse)
def link_uploaded_file_to_task(
    file_id: str,
    request: LinkFileTaskRequest,
    session: Session = Depends(get_session),
    current_user: MockUserResponse = Depends(get_current_user),
) -> UploadedFileResponse:
    uploaded = uploads.link_file_to_task(session, file_id, request.task_id)
    if uploaded is None:
        raise HTTPException(status_code=404, detail="Uploaded file not found")
    return uploaded

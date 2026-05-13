from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

from app.api.mock_kaihong import get_current_user
from app.db.session import get_session
from app.schemas.agent_tasks import (
    AgentTaskFinalizeResponse,
    AgentTaskCreateRequest,
    AgentTaskEventsResponse,
    AgentTaskResponse,
)
from app.schemas.clarification import (
    ClarificationAnswerRequest,
    ClarificationAnswerResponse,
    ClarificationStatusResponse,
)
from app.schemas.mock_kaihong import MockUserResponse
from app.services import agent_tasks, clarification


router = APIRouter(prefix="/agent/tasks", tags=["Agent Tasks"])


@router.post("", response_model=AgentTaskResponse, status_code=status.HTTP_201_CREATED)
def create_agent_task(
    request: AgentTaskCreateRequest,
    session: Session = Depends(get_session),
    current_user: MockUserResponse = Depends(get_current_user),
) -> AgentTaskResponse:
    try:
        return agent_tasks.create_agent_task(
            session=session,
            file_ids=request.file_ids,
            created_by=current_user.username,
            customer_id=request.customer_id,
        )
    except agent_tasks.AgentTaskError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc


@router.get("/{task_id}", response_model=AgentTaskResponse)
def get_agent_task(
    task_id: str,
    session: Session = Depends(get_session),
    current_user: MockUserResponse = Depends(get_current_user),
) -> AgentTaskResponse:
    task = agent_tasks.get_agent_task(session, task_id, current_user.username)
    if task is None:
        raise HTTPException(status_code=404, detail="Agent task not found")
    return task


@router.post("/{task_id}/extract", response_model=AgentTaskResponse)
def extract_agent_task(
    task_id: str,
    session: Session = Depends(get_session),
    current_user: MockUserResponse = Depends(get_current_user),
) -> AgentTaskResponse:
    try:
        task = agent_tasks.extract_agent_task(session, task_id, current_user.username)
    except agent_tasks.AgentTaskError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc
    if task is None:
        raise HTTPException(status_code=404, detail="Agent task not found")
    return task


@router.get("/{task_id}/events", response_model=AgentTaskEventsResponse)
def get_agent_task_events(
    task_id: str,
    session: Session = Depends(get_session),
    current_user: MockUserResponse = Depends(get_current_user),
) -> AgentTaskEventsResponse:
    events = agent_tasks.list_task_events(session, task_id, current_user.username)
    if events is None:
        raise HTTPException(status_code=404, detail="Agent task not found")
    return AgentTaskEventsResponse(events=events)


@router.get("/{task_id}/clarification", response_model=ClarificationStatusResponse)
def get_task_clarification(
    task_id: str,
    session: Session = Depends(get_session),
    current_user: MockUserResponse = Depends(get_current_user),
) -> ClarificationStatusResponse:
    try:
        return clarification.get_or_create_clarification(
            session=session,
            task_id=task_id,
            current_username=current_user.username,
        )
    except clarification.ClarificationError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc


@router.post(
    "/{task_id}/clarification/answers",
    response_model=ClarificationAnswerResponse,
)
def submit_task_clarification_answer(
    task_id: str,
    request: ClarificationAnswerRequest,
    session: Session = Depends(get_session),
    current_user: MockUserResponse = Depends(get_current_user),
) -> ClarificationAnswerResponse:
    try:
        return clarification.submit_clarification_answer(
            session=session,
            task_id=task_id,
            current_username=current_user.username,
            request=request,
        )
    except clarification.ClarificationError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc


@router.post("/{task_id}/finalize", response_model=AgentTaskFinalizeResponse)
def finalize_agent_task(
    task_id: str,
    session: Session = Depends(get_session),
    current_user: MockUserResponse = Depends(get_current_user),
) -> AgentTaskFinalizeResponse:
    try:
        return clarification.finalize_agent_task(
            session=session,
            task_id=task_id,
            current_username=current_user.username,
        )
    except clarification.ClarificationError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

from app.api.mock_kaihong import get_current_user
from app.db.session import get_session
from app.schemas.agent_tasks import (
    AgentTaskCreateRequest,
    AgentTaskEventsResponse,
    AgentTaskResponse,
)
from app.schemas.mock_kaihong import MockUserResponse
from app.services import agent_tasks


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

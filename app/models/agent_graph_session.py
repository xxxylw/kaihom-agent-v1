from datetime import datetime

from sqlmodel import Field, SQLModel

from app.models.agent_task import utc_now


class AgentGraphSessionRecord(SQLModel, table=True):
    id: str = Field(primary_key=True)
    task_id: str = Field(index=True)
    graph_thread_id: str
    status: str = "active"
    state_json: str | None = None
    current_question_json: str | None = None
    answer_history_json: str | None = None
    privacy_map_json: str | None = None
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)

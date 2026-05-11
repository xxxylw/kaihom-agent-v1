from collections.abc import Generator

from sqlmodel import Session, SQLModel, create_engine, text

from app.core.config import get_settings
from app.models import agent_task as _agent_task
from app.models import draft as _draft
from app.models import uploaded_file as _uploaded_file


engine = create_engine(
    get_settings().database_url,
    connect_args={"check_same_thread": False},
)


def create_db_and_tables() -> None:
    SQLModel.metadata.create_all(engine)
    _ensure_agent_task_extraction_columns()


def _ensure_agent_task_extraction_columns() -> None:
    if engine.dialect.name != "sqlite":
        return
    with engine.begin() as connection:
        rows = connection.exec_driver_sql("PRAGMA table_info(agenttaskrecord)").all()
        columns = {row[1] for row in rows}
        for column in [
            "draft_preview_json",
            "missing_fields_json",
            "extraction_result_json",
        ]:
            if column not in columns:
                connection.execute(
                    text(f"ALTER TABLE agenttaskrecord ADD COLUMN {column} TEXT")
                )


def get_session() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session

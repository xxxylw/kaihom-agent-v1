# Research: Stack

**Project:** Kaihom Agent v1
**Purpose:** Identify practical stack choices for the first Mock implementation.

## Recommendations

### Backend

- FastAPI for the HTTP API surface, OpenAPI docs, upload endpoints, and dependency injection.
- Uvicorn for local development and container startup.
- Pydantic v2 models for request/response contracts and draft schemas.
- SQLModel over SQLite for the first database layer, with a clean path to PostgreSQL later.

## Evidence

- FastAPI official docs describe `UploadFile` and `File` for receiving uploaded files and note that file/form upload requires `python-multipart`: https://fastapi.tiangolo.com/tutorial/request-files/
- SQLModel official docs show `get_session()` as a FastAPI dependency using `yield`, giving one session per request with cleanup after the response: https://sqlmodel.tiangolo.com/tutorial/fastapi/session-with-dependency/
- Pydantic official docs describe `BaseModel` as the base class for models and `Field` for metadata/defaults/schema constraints: https://docs.pydantic.dev/latest/api/base_model/ and https://docs.pydantic.dev/latest/concepts/fields/

## First Implementation Stack

- Python 3.11+
- FastAPI
- Uvicorn
- SQLModel
- SQLite
- python-multipart
- pytest + httpx/TestClient for API tests
- Local filesystem storage under `storage/uploads/`

## Later Stack

- PostgreSQL
- MinIO/S3/OSS for private document storage
- Real OCR provider or PaddleOCR
- LLM structured output provider for schema-bound extraction
- WeChat Mini Program or enterprise H5 adapter

# Phase 4 Research: Agent Task State Machine

**Phase:** 04 - Agent Task State Machine  
**Goal:** Represent the order-draft Agent workflow as explicit task states and events.  
**Requirements:** TASK-01, TASK-02, TASK-03, TASK-04

## Recommended Approach

Implement Phase 4 as a deterministic FastAPI + SQLModel task ledger, not as a LangChain or LangGraph runtime.

The phase should add:

- `AgentTaskRecord` for durable task metadata and current status.
- `AgentTaskEventRecord` for business-level event history.
- Pydantic request/response schemas for task creation, task detail, and events.
- A service layer that validates uploaded file IDs, creates tasks, links files, records events, and enforces basic transition rules.
- A protected API router under `/agent/tasks`.
- Tests through `TestClient(app)` that cover creation, query, event history, invalid files, auth, OpenAPI, and transition rules.

This keeps the product/API contract stable while leaving room for Phase 5/6 to introduce LangGraph or LangChain behind a workflow service boundary.

## Existing Code Patterns

| Area | Existing Pattern | Phase 4 Use |
|------|------------------|-------------|
| Auth | `app/api/mock_kaihong.py::get_current_user` validates bearer tokens and returns `MockUserResponse`. | Reuse this dependency for protected Agent task endpoints. |
| DB session | `app/db/session.py::get_session` yields SQLModel sessions from the shared SQLite engine. | Use the same session dependency for task/event persistence. |
| Model registration | `app/db/session.py` imports model modules before `SQLModel.metadata.create_all(engine)`. | Import the new Agent task model module there. |
| SQLModel table shape | `OrderDraftRecord` and `UploadedFileRecord` use string IDs, UTC timestamps, and simple scalar fields. | Follow the same style for `AgentTaskRecord` and `AgentTaskEventRecord`. |
| Router organization | API modules live under `app/api/` and are included in `app/main.py`. | Add `app/api/agent_tasks.py` and include its router from `create_app()`. |
| Schemas | Request/response models live under `app/schemas/`. | Add `app/schemas/agent_tasks.py`. |
| Services | Business helpers live under `app/services/`. | Add `app/services/agent_tasks.py`. |
| Upload integration | `UploadedFileRecord.task_id` exists and `uploads.link_file_to_task()` can assign one file to a task. | Task creation should link all referenced uploaded file records to the created task. |
| Tests | Tests use `fastapi.testclient.TestClient` and real app routes. | Add `tests/test_agent_tasks.py` with end-to-end API tests. |

## Task Model Guidance

Recommended `AgentTaskRecord` fields:

- `id: str` primary key, generated as `task_<12 hex>`.
- `created_by: str`.
- `customer_id: str | None`.
- `status: str`, initially `created`.
- `file_ids_json: str` or an equivalent representation that supports multiple files.
- `error_code: str | None`.
- `error_message: str | None`.
- `created_at: datetime`.
- `updated_at: datetime`.

Recommended `AgentTaskEventRecord` fields:

- `id: str` primary key, generated as `evt_<12 hex>`.
- `task_id: str`, indexed.
- `event_type: str`.
- `actor: str | None`.
- `from_status: str | None`.
- `to_status: str | None`.
- `message: str | None`.
- `details_json: str | None`.
- `created_at: datetime`.

SQLite/SQLModel can support this with straightforward scalar fields. A join table is optional, but not required for Phase 4 because the existing upload record already has a nullable `task_id` field and task detail can store the ordered file ID list as JSON.

## State Machine Guidance

Use product-facing statuses:

- `created`
- `extracting`
- `need_more_info`
- `ready_for_review`
- `finalized`
- `failed`

Phase 4 only needs to create tasks in `created` and provide internal service helpers/tests for safe transitions. Avoid exposing arbitrary public status mutation.

Recommended transition constraints:

- `created -> extracting`
- `extracting -> need_more_info`
- `extracting -> ready_for_review`
- `extracting -> failed`
- `need_more_info -> ready_for_review`
- `need_more_info -> failed`
- `ready_for_review -> finalized`
- `ready_for_review -> failed`

`finalized` should not transition back to active states. `failed` should remain terminal for now unless a later retry phase deliberately reopens it.

## API Guidance

Recommended routes:

- `POST /agent/tasks`
  - Protected by the existing mock bearer token.
  - Accepts required `file_ids: list[str]`.
  - Accepts optional `customer_id`.
  - Creates a task in `created`.
  - Links the uploaded file records to the new task.
  - Records `task_created` and `files_attached` events.

- `GET /agent/tasks/{task_id}`
  - Protected.
  - Returns task status, customer ID, file IDs, safe file metadata, empty `draft_preview`, empty `questions`, timestamps, and current error metadata if any.

- `GET /agent/tasks/{task_id}/events`
  - Protected.
  - Returns ordered task events.

No broad `PATCH /agent/tasks/{task_id}/status` should be exposed in Phase 4.

## LangChain/LangGraph Boundary

Do not add LangChain or LangGraph dependencies in Phase 4.

Preserve an internal service boundary such as:

- `create_agent_task(...)`
- `get_agent_task(...)`
- `list_task_events(...)`
- `transition_task_status(...)`

Later phases can route LangGraph node completion or LangChain tool decisions through these functions. The durable product ledger remains `AgentTaskRecord` + `AgentTaskEventRecord`; any future AI framework should update that ledger rather than replace it.

## Risks

- **Partial task/file linkage:** Validate all file IDs before creating the task or committing file links, so invalid batches do not leave inconsistent data.
- **Over-specific statuses:** Keep the status enum business-level; do not leak internal OCR/LLM node names into product API.
- **Auth ownership ambiguity:** Existing mock auth is username-based. Phase 4 should at minimum restrict task creation/query to the authenticated user's created tasks or uploaded files where feasible.
- **Event overgrowth:** Keep Phase 4 events business-level. Detailed OCR/LLM/LangGraph events belong to Phase 5/6.
- **Sandbox SQLite behavior:** Prior phases needed elevated/local write permissions for SQLite tests. The plan should expect the same verification pattern if sandbox disk I/O fails.

## Phase 4 Deliverables

- Agent task and event SQLModel records.
- Agent task request/response schemas.
- Agent task service with file validation, task creation, event recording, and internal status transition rules.
- Protected Agent task routes.
- Tests for TASK-01 through TASK-04.
- README/OpenAPI coverage is already handled by FastAPI docs; no README update is required unless route examples are added.

## RESEARCH COMPLETE

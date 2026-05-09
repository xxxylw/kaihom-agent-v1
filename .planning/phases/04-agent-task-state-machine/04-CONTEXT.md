# Phase 4: Agent Task State Machine - Context

**Gathered:** 2026-05-09
**Status:** Ready for planning

<domain>
## Phase Boundary

Phase 4 delivers the backend task container for the logistics order-entry Agent workflow. Users can create an Agent task from uploaded file IDs and user context, query task state, and inspect business-level task events. The phase establishes durable task status, event history, file linkage, and failure representation so later OCR, extraction, clarification, and draft finalization phases have one stable `task_id` to operate around.

This phase does not perform OCR, extract order fields, generate clarification questions, merge user answers, finalize drafts, build a mobile UI, or introduce LangChain/LangGraph as a runtime dependency.

</domain>

<decisions>
## Implementation Decisions

### Task Creation
- **D-01:** Creating an Agent task should start with `status = "created"`, not `extracting`. Phase 4 does not perform OCR/extraction yet, so `extracting` should begin only when a later phase actually starts extraction work.
- **D-02:** `file_ids` are required when creating a task. Phase 4 should validate that referenced uploaded files exist and can be associated with the requesting user/context.
- **D-03:** `customer_id` is optional during task creation. Earlier upload decisions intentionally avoid forcing employees to pick a customer before documents are interpreted.
- **D-04:** A single Agent task must support multiple file IDs. Logistics order entry can involve a bundle of related documents such as entrustment letters, bills of lading, receipts, screenshots, PDFs, and other supporting files.

### Task Status Model
- **D-05:** Use business-level task statuses: `created`, `extracting`, `need_more_info`, `ready_for_review`, `finalized`, and `failed`.
- **D-06:** Keep statuses stable and product-facing. Do not encode internal implementation nodes such as `ocr_node_done`, `llm_prompt_sent`, `parser_retry`, or future LangGraph node names into the primary status enum.
- **D-07:** Terminal or near-terminal status behavior should be explicit. `finalized` should not transition back to extraction states. `failed` should carry error metadata and may be retried only through a deliberate later design, not an accidental status patch.

### Events and Audit Trail
- **D-08:** Record business-level events in Phase 4, including at least `task_created`, `files_attached`, `status_changed`, and `task_failed`.
- **D-09:** Event records should include enough metadata for debugging and future audit: event type, task ID, actor/user where available, previous status, new status, message/details, and timestamp.
- **D-10:** Do not record low-level OCR/LLM/LangGraph implementation events in Phase 4. Later phases may add events such as `extraction_started`, `questions_generated`, `answers_submitted`, or `draft_revalidated` when those behaviors exist.

### API Shape
- **D-11:** Provide a task creation endpoint such as `POST /agent/tasks`.
- **D-12:** Provide task status/detail retrieval such as `GET /agent/tasks/{task_id}`.
- **D-13:** Provide task event retrieval either embedded in task detail or through a separate endpoint such as `GET /agent/tasks/{task_id}/events`; the planner may choose the exact shape as long as task events are queryable.
- **D-14:** Do not expose a broad public `PATCH /agent/tasks/{task_id}/status` that allows arbitrary external status changes. State transitions should be controlled through service methods and future workflow actions.
- **D-15:** Task detail responses should reserve nullable/empty fields for later phases, such as `draft_preview` and `questions`, without pretending extraction or clarification already exists.

### File Linkage
- **D-16:** Creating a task should link uploaded file records to the task, reusing the Phase 3 `task_id` metadata field.
- **D-17:** The task response should return safe file references and metadata, not absolute local filesystem paths.
- **D-18:** If task creation references an invalid, missing, or inaccessible file ID, return a clear API error and record failure only if a task was actually created before the problem was detected.

### LangChain/LangGraph Reservation
- **D-19:** Do not introduce LangChain or LangGraph as Phase 4 runtime dependencies.
- **D-20:** Preserve a workflow service boundary, for example `AgentWorkflowService`, `TaskStateMachine`, or similar planner-selected names, so later phases can plug in LangGraph or LangChain-backed orchestration without changing the public task API.
- **D-21:** Treat Phase 4 `AgentTask` and `AgentTaskEvent` as the durable product ledger. Future LangGraph, if introduced, should be an internal execution engine that updates task status and events rather than replacing the business task model.
- **D-22:** Phase 5 planning must discuss whether extraction should remain deterministic Python/Pydantic logic or become LangGraph-compatible. Phase 6 planning must explicitly evaluate LangGraph for clarification loops, human-in-the-loop state transitions, and future tool orchestration.

### the agent's Discretion
- The planner may choose exact table names, schema class names, route names, event metadata shape, and service function names, provided they follow existing FastAPI/SQLModel project patterns.
- The planner may decide whether task-file relationships are represented as a JSON list on the task, a join table, or a task ID stored on uploaded file records, as long as multiple files per task are supported and Phase 3 upload metadata remains usable.
- The planner may include narrowly scoped internal/test-only transition helpers to verify state rules, but public APIs should not allow arbitrary state mutation.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Project Scope
- `.planning/PROJECT.md` - Defines the mock-first mobile logistics Agent product, target upload-to-draft loop, data-safety constraints, and the decision to prefer deterministic task state before complex Agent frameworks.
- `.planning/REQUIREMENTS.md` - Defines TASK-01 through TASK-04 and keeps extraction, clarification, finalization, and H5 UI in later phases.
- `.planning/ROADMAP.md` - Defines Phase 4 as Agent Task State Machine and records the LangChain/LangGraph discussion markers for Phase 5/6.
- `.planning/STATE.md` - Records current project status, Phase 4 focus, and the decision to keep Phase 4 framework-light while preserving later framework evaluation.

### Upstream Phase Outputs
- `.planning/phases/01-fastapi-foundation/01-01-SUMMARY.md` - Establishes FastAPI app factory, settings, router, and test patterns.
- `.planning/phases/02-mock-kaihong-business-api/02-01-SUMMARY.md` - Establishes mock auth/current-user behavior, SQLModel/SQLite persistence, and local draft boundary.
- `.planning/phases/03-file-upload-and-local-storage/03-CONTEXT.md` - Records upload decisions, optional customer/document type behavior, file metadata fields, and deferred Agent task linkage.
- `.planning/phases/03-file-upload-and-local-storage/03-01-SUMMARY.md` - Confirms `POST /uploads`, metadata retrieval, and `PATCH /uploads/{file_id}/task` exist for linking files to future Agent tasks.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `app/main.py`: Includes router modules and initializes local SQLModel tables during app creation.
- `app/db/session.py`: Existing SQLModel engine/session dependency should be reused for task and event persistence.
- `app/api/mock_kaihong.py`: Existing protected router/auth dependency pattern can guide protected Agent task endpoints.
- `app/api/uploads.py`: Existing upload metadata and task-linking behavior is the integration point for associating uploaded files with Agent tasks.
- `app/models/uploaded_file.py`: Existing `UploadedFileRecord` includes optional task linkage that Phase 4 should use or coordinate with.
- `app/schemas/uploads.py` and `app/schemas/mock_kaihong.py`: Existing Pydantic response model style should guide task response schemas.
- `app/services/uploads.py` and `app/services/mock_kaihong.py`: Existing service-layer pattern should guide Agent task creation, transition, and lookup helpers.
- `tests/test_uploads.py` and `tests/test_mock_kaihong.py`: Existing `TestClient(app)` integration-test style should be reused for task API tests.

### Established Patterns
- API routers live under `app/api/`.
- SQLModel tables live under `app/models/`.
- Request/response schemas live under `app/schemas/`.
- Business helpers live under `app/services/`.
- Local persistence uses SQLite through the shared session dependency.
- Protected routes should reuse the existing mock bearer/current-user pattern rather than introduce another auth mechanism.

### Integration Points
- Phase 4 task creation consumes Phase 3 `file_id` values.
- Phase 4 task creation should write task IDs back to uploaded file metadata, directly or through existing upload-linking helpers.
- Phase 5 will use task file references as the source list for mock OCR and field extraction.
- Phase 6 will update task status to `need_more_info`, `ready_for_review`, and `finalized` as clarification and draft finalization progress.
- Future LangGraph orchestration should sit behind the task/workflow service boundary and update the same `AgentTask`/`AgentTaskEvent` ledger.

</code_context>

<specifics>
## Specific Ideas

- Recommended task creation response shape:

```json
{
  "task_id": "task_abc123",
  "status": "created",
  "customer_id": null,
  "file_ids": ["file_001", "file_002"],
  "draft_preview": null,
  "questions": [],
  "created_at": "2026-05-09T00:00:00Z"
}
```

- Recommended event shape:

```json
{
  "event_id": "evt_abc123",
  "task_id": "task_abc123",
  "event_type": "task_created",
  "from_status": null,
  "to_status": "created",
  "message": "Agent task created from uploaded files.",
  "created_at": "2026-05-09T00:00:00Z"
}
```

- Product principle: Phase 4 should make the workflow observable and durable without pretending the intelligent extraction or clarification behavior already exists.

</specifics>

<deferred>
## Deferred Ideas

- Mock OCR and field extraction belong to Phase 5.
- Draft schema extraction, missing field detection, and evidence metadata belong to Phase 5.
- Clarification question generation, answer submission, answer merge, and final draft readiness belong to Phase 6.
- Formal LangGraph introduction should be discussed in Phase 6 if human-in-the-loop clarification becomes complex enough to justify graph orchestration.
- LangChain should be considered later only if prompt chains, tool calling, retrieval, or LLM-driven business lookups become concrete requirements.
- Mobile task progress UI belongs to Phase 7.

</deferred>

---

*Phase: 4-Agent Task State Machine*
*Context gathered: 2026-05-09*

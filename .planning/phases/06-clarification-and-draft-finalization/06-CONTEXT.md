# Phase 06: Clarification and Draft Finalization - Context

**Gathered:** 2026-05-13
**Status:** Ready for planning
**Source:** User discussion plus Phase 6 pre-discussion notes

<domain>
## Phase Boundary

Phase 6 turns the Phase 5 `draft_preview` into a reviewable and finalizable draft through a LangGraph-orchestrated clarification loop.

The phase starts after files have already been uploaded, an Agent task has been created, and `POST /agent/tasks/{task_id}/extract` has populated:

- `draft_preview`
- `missing_fields`
- `field_evidence`
- `conflicts`

Phase 6 must not replace the upload or extraction API. Future image/PDF multimodal recognition can replace the internal extraction engine later while preserving the same `draft_preview` contract.
</domain>

<decisions>
## Implementation Decisions

### D-01: Phase 6 Scope

- Build the human-in-the-loop clarification and draft-finalization loop only.
- Do not implement GLM/DeepSeek image or PDF multimodal field recognition in Phase 6.
- Do not build a generic multi-provider LLM abstraction in Phase 6.
- Keep `draft_preview` as the stable boundary between extraction and clarification.

### D-02: Orchestration

- Use LangGraph to orchestrate clarification state transitions:
  - inspect missing fields and conflicts
  - generate the next clarification question
  - wait for user answer
  - parse the answer
  - merge accepted values into the draft preview
  - decide whether to continue or mark the task `ready_for_review`

### D-03: DeepSeek Text Intelligence

- Configure direct DeepSeek API access for text-only clarification.
- DeepSeek is used to generate natural user-facing questions and parse natural language answers into structured field updates.
- DeepSeek is not used for image/PDF recognition in this phase.
- Configuration should use `KAIHOM_DEEPSEEK_API_KEY`, `KAIHOM_DEEPSEEK_BASE_URL`, `KAIHOM_DEEPSEEK_MODEL`, timeout, and retry settings.
- Tests must not require a real DeepSeek API key or network access.

### D-04: Privacy

- Apply minimal redaction before sending any draft context or user answer to DeepSeek.
- Redact at least customer names, phone numbers, and detailed addresses into placeholders such as `[CUSTOMER_1]`, `[PHONE_1]`, and `[ADDRESS_1]`.
- Store the privacy map locally in the clarification session.
- DeepSeek should receive redacted draft context, conflicts, and answer history.

### D-05: Persistence

- Persist LangGraph clarification state in a separate `agent_graph_sessions` table.
- Do not add graph-state JSON columns to `AgentTaskRecord`.
- Store task id, graph thread id, state JSON, current question JSON, answer history JSON, privacy map JSON, status, and timestamps.

### D-06: API Shape

- Add protected task-owner endpoints:
  - `GET /agent/tasks/{task_id}/clarification`
  - `POST /agent/tasks/{task_id}/clarification/answers`
  - `POST /agent/tasks/{task_id}/finalize`
- The GET endpoint returns or creates the current clarification session/question when the task is in `need_more_info`.
- The answer endpoint submits user text and advances the graph.
- The finalize endpoint saves a complete ready draft through the existing Mock Kaihong draft boundary.

### D-07: Question and Conflict Handling

- Questions may cover a small group of related fields rather than exactly one field.
- Internally, every requested field and conflict must remain structured.
- Conflict questions must include candidate values and source evidence where available.
- Users may select a candidate or answer in natural language; the backend still validates the structured result before merge.

### D-08: Failure Handling

- DeepSeek calls should retry once on transient failures or invalid JSON.
- If retry still fails, keep the task recoverable in `need_more_info` and return an API error with enough detail for the client to retry.
- Do not automatically move the task to `failed` for one clarification model failure unless the failure is unrecoverable.

### D-09: Backend Authority

- Backend code owns validation, type coercion, merge rules, missing-field recalculation, conflict resolution, task status transitions, event recording, and final Mock Kaihong draft save.
- Model output is advisory input and must be schema-validated before changing persisted draft data.
</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Project Planning

- `.planning/PROJECT.md` - Project purpose and v1 value loop.
- `.planning/REQUIREMENTS.md` - CLAR-01 through CLAR-04 and DRAFT-01 through DRAFT-04.
- `.planning/ROADMAP.md` - Phase 6 scope and neighboring phases.
- `.planning/STATE.md` - Current milestone state.
- `.planning/phases/06-clarification-and-draft-finalization/06-PRE-DISCUSSION-NOTES.md` - Superseded pre-discussion notes; use this CONTEXT.md when conflicts exist.

### Prior Phase Outputs

- `.planning/phases/05-mock-ocr-and-field-extraction/05-01-SUMMARY.md` - Existing extraction endpoint, `draft_preview`, missing fields, evidence, and conflicts.
- `.planning/phases/04-agent-task-state-machine/04-01-SUMMARY.md` - Task status and event ledger.
- `.planning/phases/02-mock-kaihong-business-api/02-01-SUMMARY.md` - Existing Mock Kaihong draft save boundary.
</canonical_refs>

<specifics>
## Specific Ideas

- The clarification layer should consume the existing `OrderDraftPreview` shape from `app/schemas/order_draft.py`.
- Use a thin `app/services/deepseek_client.py` for DeepSeek HTTP calls, not a generic model provider framework.
- Add `app/services/privacy.py` for redaction and local privacy-map handling.
- Add `app/models/agent_graph_session.py` for the separate graph session table.
- Add `app/services/clarification_graph.py` for LangGraph node/wiring code.
- Add `app/services/clarification.py` for task-facing orchestration, validation, and persistence.
- Add `app/api/agent_tasks.py` routes under the existing `/agent/tasks` router.
</specifics>

<deferred>
## Deferred Ideas

- DeepSeek/GLM image or PDF multimodal field recognition is deferred to a later phase.
- Replacing mock OCR extraction internals is deferred; Phase 6 keeps the existing `/extract` contract.
- H5 UI consumption is deferred to the mobile demo phase.
- Real Kaihong Wing integration remains out of v1 scope.
</deferred>

---

*Phase: 06-clarification-and-draft-finalization*
*Context gathered: 2026-05-13*

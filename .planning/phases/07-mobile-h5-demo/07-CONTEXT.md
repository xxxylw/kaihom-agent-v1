# Phase 7: Mobile H5 Demo - Context

**Gathered:** 2026-05-14
**Status:** Discussion started; ready for deeper Phase 7 planning

<domain>
## Phase Boundary

Phase 7 delivers a phone-accessible H5 demo for the completed mock workflow: login, upload logistics documents, create an Agent task, run extraction, show progress, ask/answer clarification questions, show the draft preview, and finalize a Mock Kaihong draft.

This phase should make the product feel like an Agent workflow, not just a set of backend API calls. The demo should help a business user understand what the Agent is doing and what input it needs from them.

</domain>

<decisions>
## Implementation Decisions

### Agent Direction
- **D-01:** Phase 7 should present the product as an Agent H5 demo, with visible Agent state, questions, answers, task progress, and draft review.
- **D-02:** Phase 7 should keep the existing Phase 6 backend flow as the source of truth. It should consume existing APIs instead of replacing the backend with a new full Agent runtime.
- **D-03:** Existing backend endpoints can be treated conceptually as future Agent tools, but Phase 7 should not introduce a full MCP server or free-form tool-calling Agent.
- **D-04:** LLM-driven writes remain controlled by backend services. The model may parse answers or generate questions, but task status updates, draft merges, and finalization must continue to go through deterministic service rules.
- **D-05:** Full Agent Tool Layer, MCP exposure, and chatbox integration are deferred to later phases after the H5 demo proves the end-to-end value loop.

### Framework Posture
- **D-06:** Continue using the existing LangGraph-compatible clarification state created in Phase 6.
- **D-07:** Do not introduce HelloAgents `FunctionCallAgent` as the Phase 7 main workflow engine.
- **D-08:** Function calling or structured-output provider work may be considered later for LLM parsing robustness, but should not block the H5 demo.

### the agent's Discretion
The implementation may organize frontend copy and UI sections around Agent concepts such as "current step", "Agent question", "your answer", "draft preview", and "final save", as long as the backend API contract stays unchanged.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Project Scope
- `.planning/ROADMAP.md` - Defines Phase 7 as the Mobile H5 Demo and confirms dependencies on Phase 6.
- `.planning/REQUIREMENTS.md` - Defines MOB-01 through MOB-05 and the v1 mock-only boundaries.
- `.planning/STATE.md` - Captures current project state, Phase 6 completion, and Phase 7 available APIs.

### Phase 6 Backend Capabilities
- `.planning/phases/06-clarification-and-draft-finalization/06-VERIFICATION.md` - Confirms the clarification and finalization backend behavior.
- `.planning/phases/06-clarification-and-draft-finalization/06-UAT.md` - Provides the PowerShell HTTP walkthrough that Phase 7 should turn into a mobile UI flow.
- `app/api/agent_tasks.py` - Exposes the Agent task, extraction, clarification, answer, and finalization endpoints Phase 7 should consume.
- `app/services/clarification.py` - Owns the Phase 6 clarification/finalization business flow.
- `app/models/agent_graph_session.py` - Persists Agent clarification session state.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- FastAPI OpenAPI contracts already describe the backend routes needed by the H5 demo.
- Mock Kaihong auth provides the login boundary for the demo user.
- Upload, task, extraction, clarification, and finalization APIs already form the full workflow.
- Agent task events can be used to show progress and debugging context in the UI.

### Established Patterns
- Backend service methods own business transitions; UI and future Agent tools should call service-backed APIs instead of writing directly to the database.
- Phase 6 already separates product task state from graph/session state through `AgentTaskRecord` and `AgentGraphSessionRecord`.
- Draft finalization remains a save-to-draft action, not formal order submission.

### Integration Points
- Phase 7 should consume:
  - `POST /mock/kaihong/auth/login`
  - `POST /uploads`
  - `POST /agent/tasks`
  - `POST /agent/tasks/{task_id}/extract`
  - `GET /agent/tasks/{task_id}/clarification`
  - `POST /agent/tasks/{task_id}/clarification/answers`
  - `POST /agent/tasks/{task_id}/finalize`
  - `GET /agent/tasks/{task_id}/events`

</code_context>

<specifics>
## Specific Ideas

- The H5 page should feel like an Agent console for logistics order drafting.
- The UI should expose the same flow that was manually verified in PowerShell during Phase 6.
- The frontend should make repeated clarification feel natural: after an answer, if `next_question` exists, show it immediately.
- Future MCP/chatbox integration should be easier if Phase 7 keeps the tool-like boundary visible in code and docs.

</specifics>

<deferred>
## Deferred Ideas

- Full MCP server exposing Kaihom Agent tools to a chatbox.
- Agent Tool Layer with explicit `get_task_context`, `submit_clarification_answer`, `finalize_agent_task`, and query tools.
- Query projection tables optimized for Agent/MCP lookup.
- HelloAgents `FunctionCallAgent` or OpenAI/DeepSeek strict function calling as a provider-level experiment.
- Free-form multi-agent orchestration or handoff flows.

</deferred>

---

*Phase: 7-Mobile H5 Demo*
*Context gathered: 2026-05-14*

# Phase 06: Clarification and Draft Finalization - Research

**Date:** 2026-05-13
**Status:** Complete

## Research Summary

Phase 6 should implement a text-only clarification loop on top of the Phase 5 draft preview contract. The safest architecture is:

1. keep deterministic backend code authoritative for validation and persistence,
2. use LangGraph only for workflow orchestration,
3. call DeepSeek directly for natural question generation and answer parsing,
4. redact sensitive text before model calls,
5. test all AI behavior through fake DeepSeek responses rather than real network calls.

## Official Documentation Notes

- LangGraph's official install docs show the base Python package as `langgraph`; LangChain is a separate install when needed for LLM/tool integrations. Source: https://docs.langchain.com/oss/python/langgraph/install
- DeepSeek's official docs say the API supports an OpenAI-compatible format and can be configured with a base URL and API key. Source: https://api-docs.deepseek.com/
- DeepSeek chat completions are exposed through the chat-completions API. Source: https://api-docs.deepseek.com/api/create-chat-completion/
- DeepSeek multi-round chat is stateless from the server perspective, so the client must send the relevant conversation history each time. Source: https://api-docs.deepseek.com/guides/multi_round_chat/

## Existing Codebase Patterns

- Routes live in `app/api/`.
- Pydantic schemas live in `app/schemas/`.
- SQLModel records live in `app/models/`.
- Business orchestration lives in `app/services/`.
- Settings live in `app/core/config.py` and use the `KAIHOM_` environment prefix.
- Task ownership and auth reuse `get_current_user` from `app/api/mock_kaihong.py`.
- Task status/events are managed in `app/services/agent_tasks.py`.
- Phase 5 persists `draft_preview_json`, `missing_fields_json`, and `extraction_result_json` on `AgentTaskRecord`.
- Mock Kaihong draft save already exists in `app/services/mock_kaihong.py`.

## Recommended Technical Shape

### Dependencies

Add runtime dependencies:

- `langgraph`
- `langchain-core` if prompt templates or parser utilities are useful
- `httpx` or `openai` for DeepSeek-compatible HTTP calls

Use a direct DeepSeek client rather than a provider abstraction. Since the project already uses `httpx` for tests only, promoting `httpx` to runtime is the smallest direct-HTTP option.

### Database

Create `AgentGraphSessionRecord` in `app/models/agent_graph_session.py`:

- `id`
- `task_id` indexed
- `graph_thread_id`
- `status`
- `state_json`
- `current_question_json`
- `answer_history_json`
- `privacy_map_json`
- timestamps

Import the model in `app/db/session.py`. Add a small SQLite additive migration helper if local existing databases need the table or new columns.

### Privacy

Create `app/services/privacy.py` with deterministic redaction:

- known customer names from draft fields
- phone-like strings
- detailed address fields

Return both redacted payload and privacy map. Store the map only locally.

### DeepSeek

Create `app/services/deepseek_client.py`:

- reads `KAIHOM_DEEPSEEK_API_KEY`, `KAIHOM_DEEPSEEK_BASE_URL`, `KAIHOM_DEEPSEEK_MODEL`
- sends non-streaming chat completion requests
- asks for strict JSON output
- validates the response at the service boundary
- supports timeout and one retry
- is easy to monkeypatch in tests

### LangGraph

Create `app/services/clarification_graph.py` with nodes roughly:

- `inspect_draft`
- `generate_question`
- `await_answer`
- `parse_answer`
- `merge_answer`
- `decide_next`

Keep actual persistence and task status changes in `app/services/clarification.py` so graph code does not own database transactions directly.

## Risks and Mitigations

- **Model returns invalid JSON:** retry once, then return a recoverable API error.
- **Sensitive data leakage:** redact before sending draft context or answers.
- **State split across graph/task:** keep `agent_graph_sessions` authoritative for graph state and `AgentTaskRecord` authoritative for product status.
- **Tests become network-dependent:** fake the DeepSeek client in unit/integration tests.
- **LangGraph complexity expands scope:** only implement the small clarification graph needed for CLAR/DRAFT requirements.

## Research Complete

Phase 6 is ready for planning as a LangGraph + DeepSeek text clarification loop with deterministic backend validation and final Mock Kaihong draft save.

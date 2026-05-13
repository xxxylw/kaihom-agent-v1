# Phase 06: Clarification and Draft Finalization - Discussion Log

**Date:** 2026-05-13
**Status:** Complete

## Summary

The original pre-discussion notes were too large for one phase because they combined multimodal recognition, LLM question generation, LangGraph orchestration, privacy, draft merging, finalization, and H5 consumption. The user narrowed Phase 6 to the clarification and finalization loop.

## Decisions

### Scope

- Phase 6 will not implement image/PDF multimodal field recognition.
- Phase 6 will keep using the Phase 5 `draft_preview`, `missing_fields`, `field_evidence`, and `conflicts` output.
- Future recognition work can replace `/extract` internals later without changing the user-facing upload/task/extract flow.

### Framework and Model

- Use LangGraph for the clarification workflow.
- Configure DeepSeek directly for text-only question generation and answer parsing.
- Do not build a generic LLM provider abstraction.

### Persistence

- Persist graph state in a separate `agent_graph_sessions` table.
- Keep graph state out of `AgentTaskRecord`.

### Privacy

- Apply minimum redaction before sending draft context or user answers to DeepSeek.
- Redact customer names, phone numbers, and detailed addresses.
- Store the privacy map locally.

### API Defaults

- Use:
  - `GET /agent/tasks/{task_id}/clarification`
  - `POST /agent/tasks/{task_id}/clarification/answers`
  - `POST /agent/tasks/{task_id}/finalize`
- Allow grouped clarification questions.
- Conflict questions include candidate values and evidence.
- DeepSeek failures retry once and remain recoverable.

## Deferred

- GLM/DeepSeek/other multimodal recognition for uploaded images/PDFs.
- H5 UI.
- Real Kaihong Wing integration.

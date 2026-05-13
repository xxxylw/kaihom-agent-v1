---
phase: 06-clarification-and-draft-finalization
plan: 02
subsystem: clarification-api-finalization
tags: [fastapi, clarification, draft-finalization, mock-kaihong]
requires:
  - phase: 06-01-clarification-foundation
    provides: Graph session persistence, clarification schemas, privacy redaction, DeepSeek client, graph wiring.
provides:
  - Protected clarification status endpoint.
  - Protected clarification answer endpoint.
  - Safe draft preview merge and missing-field recalculation.
  - Protected finalize endpoint.
  - Mock Kaihong draft save from ready Agent tasks.
affects: [phase-07-mobile-h5-demo]
tech-stack:
  added: []
  patterns:
    - Task-owned service orchestration in app/services/clarification.py
    - Business-level task events for clarification and finalization
    - Mock Kaihong draft boundary reuse
key-files:
  created:
    - app/services/clarification.py
    - tests/test_clarification_api.py
  modified:
    - app/models/agent_task.py
    - app/db/session.py
    - app/schemas/agent_tasks.py
    - app/services/agent_tasks.py
    - app/api/agent_tasks.py
key-decisions:
  - "Expose GET /agent/tasks/{task_id}/clarification."
  - "Expose POST /agent/tasks/{task_id}/clarification/answers."
  - "Expose POST /agent/tasks/{task_id}/finalize."
  - "Only finalize tasks in ready_for_review."
  - "Save finalized drafts through the existing Mock Kaihong service."
requirements-completed: [CLAR-01, CLAR-02, CLAR-03, CLAR-04, DRAFT-01, DRAFT-02, DRAFT-03, DRAFT-04]
duration: same session
completed: 2026-05-13
---

# Phase 06 Plan 02 Summary

## Result

Phase 6 clarification API and draft finalization are implemented.

The backend can now:

- Create or return a clarification session for tasks in `need_more_info`.
- Return structured clarification questions based on missing fields and conflicts.
- Submit user answers through a protected endpoint.
- Parse answers through the clarification graph/model boundary.
- Validate model field names and values before mutation.
- Merge accepted fields back into `draft_preview`.
- Recompute `missing_fields`.
- Resolve conflicts when the answer updates or explicitly resolves a conflict field.
- Transition complete tasks to `ready_for_review`.
- Finalize ready tasks and save them through the Mock Kaihong draft boundary.
- Return a finalization response with `draft_id`, field values, source file IDs, and audit metadata.

## Verification

Commands run:

```text
python -m pytest tests/test_clarification_api.py -q
```

Result:

```text
7 passed
```

```text
python -m pytest tests/test_privacy.py tests/test_deepseek_client.py tests/test_clarification_graph.py tests/test_clarification_api.py tests/test_agent_tasks.py -q
```

Result:

```text
30 passed
```

```text
python -m pytest -q
```

Result:

```text
55 passed
```

```text
python -c "from app.main import app; paths=app.openapi()['paths']; print('/agent/tasks/{task_id}/clarification' in paths, '/agent/tasks/{task_id}/clarification/answers' in paths, '/agent/tasks/{task_id}/finalize' in paths)"
```

Result:

```text
True True True
```

## Deviations from Plan

- DeepSeek answer parsing requires either a configured API key or a test override. Question generation can fall back to deterministic local question construction when no API key exists so local demo/testing is not blocked before credentials are configured.

**Total deviations:** 1 auto-handled.
**Impact:** No requirement loss; production text parsing still uses DeepSeek when configured.

## Self-Check: PASSED

- CLAR-01 through CLAR-04 are covered.
- DRAFT-01 through DRAFT-04 are covered.
- Existing upload, task, extraction, and Mock Kaihong tests pass.
- No image/PDF multimodal recognition implementation was added.

## PLAN COMPLETE

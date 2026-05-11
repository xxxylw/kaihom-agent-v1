---
phase: 05-mock-ocr-and-field-extraction
plan: 01
status: complete
subsystem: mock-ocr-field-extraction
tags:
  - extraction
  - agent-task
  - draft-preview
key-files:
  - app/schemas/order_draft.py
  - app/services/mock_ocr.py
  - app/services/extraction.py
  - app/services/agent_tasks.py
  - app/api/agent_tasks.py
  - tests/test_extraction.py
  - tests/test_agent_tasks.py
metrics:
  tests_added: 11
  focused_tests: 19
  full_tests: 38
---

# Phase 5 Plan 01 Summary

## Result

Phase 5 mock OCR and field extraction is implemented.

The backend can now:

- Represent all agreed logistics draft fields in a typed Pydantic schema.
- Generate deterministic mock OCR text from upload metadata.
- Extract structured draft fields from mock OCR text.
- Detect missing Phase 5 required fields.
- Preserve field evidence and conflicts.
- Persist draft preview JSON on Agent tasks.
- Trigger extraction through `POST /agent/tasks/{task_id}/extract`.
- Move tasks from `created` to `extracting`, then to `need_more_info` or `ready_for_review`.
- Return populated `draft_preview` through task detail.

## Commits

| Commit | Description |
|--------|-------------|
| `4641029` | Add mock OCR extraction workflow, typed draft schema, extraction endpoint, persistence, and tests. |

## Files Changed

- `app/schemas/order_draft.py` - Added canonical logistics draft fields, evidence, conflicts, and preview schemas.
- `app/services/mock_ocr.py` - Added deterministic mock OCR fixtures.
- `app/services/extraction.py` - Added deterministic field extraction, missing-field detection, evidence, and conflict handling.
- `app/models/agent_task.py` - Added JSON persistence fields for extraction preview data.
- `app/services/agent_tasks.py` - Added extraction workflow orchestration, persistence, status changes, and events.
- `app/api/agent_tasks.py` - Added protected extract action endpoint.
- `app/db/session.py` - Added SQLite additive column migration for existing local databases.
- `app/schemas/agent_tasks.py` - Typed `draft_preview` as `OrderDraftPreview`.
- `tests/test_extraction.py` - Added focused schema/mock OCR/extraction tests.
- `tests/test_agent_tasks.py` - Added extraction endpoint integration tests.

## Verification

Commands run:

```text
python -m pytest tests/test_extraction.py tests/test_agent_tasks.py -q
```

Result:

```text
19 passed
```

```text
python -m pytest -q
```

Result:

```text
38 passed
```

```text
python -c "from app.main import app; print('/agent/tasks/{task_id}/extract' in app.openapi()['paths'])"
```

Result:

```text
True
```

Dependency check:

```text
Select-String -Path pyproject.toml -Pattern 'langchain|langgraph'
```

Result: no matches.

Smoke test result:

```text
ready_for_review
['conflicts', 'field_evidence', 'fields', 'missing_fields']
Ningbo Future Trading Co., Ltd.
[]
['cargo_name', 'consignee_address', 'consignee_name', 'consignee_phone', 'customer_name']
```

## Deviations

- Added a small SQLite additive migration in `app/db/session.py` so existing local `agenttaskrecord` tables receive the new JSON columns. This prevents local development databases from failing after the schema change.
- Kept Phase 5 extraction deterministic and framework-light. LangChain/LangGraph remain deferred.

## Self-Check

PASSED

- EXTR-01 through EXTR-05 are covered.
- Canonical fields are typed and test-protected.
- Missing required fields are detected.
- Evidence metadata is returned.
- Task preview JSON is persisted and returned.
- Extraction status/events are business-level.
- Existing tests pass.

## PLAN COMPLETE

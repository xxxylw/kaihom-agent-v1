---
phase: 02-mock-kaihong-business-api
plan: 01
subsystem: api
tags: [fastapi, sqlmodel, sqlite, mock-api, logistics-drafts]

requires:
  - phase: 01-fastapi-foundation
    provides: FastAPI app factory, settings, health route, tests, and README commands.
provides:
  - Mock Kaihong auth/current-user API.
  - Mock customer, dictionary, and recent-order lookup APIs.
  - Local SQLModel/SQLite draft persistence.
  - Multi-document and multi-order draft contract support.
affects: [phase-3-file-upload, phase-4-agent-task-workflow, phase-5-mock-ocr-field-extraction, phase-6-clarification-draft-finalization]

tech-stack:
  added: [sqlmodel, sqlite]
  patterns:
    - Router modules under app/api/
    - Pydantic request/response schemas under app/schemas/
    - Business helpers under app/services/
    - SQLModel tables under app/models/
    - Session dependency under app/db/

key-files:
  created:
    - app/api/mock_kaihong.py
    - app/db/__init__.py
    - app/db/session.py
    - app/models/__init__.py
    - app/models/draft.py
    - app/schemas/__init__.py
    - app/schemas/mock_kaihong.py
    - app/services/__init__.py
    - app/services/mock_kaihong.py
    - tests/test_mock_kaihong.py
  modified:
    - .gitignore
    - app/core/config.py
    - app/main.py
    - .planning/ROADMAP.md
    - .planning/REQUIREMENTS.md
    - .planning/STATE.md

key-decisions:
  - "Use /mock/kaihong as an explicit mock business boundary."
  - "Use deterministic bearer-style mock tokens for v1 local testing."
  - "Store drafts in local SQLite through SQLModel, while keeping real Kaihong integration out of scope."
  - "Represent multi-document and multi-order draft structures with source_documents and order_items."

patterns-established:
  - "Protected mock endpoints depend on a shared bearer token helper."
  - "Draft APIs return Pydantic response models reconstructed from SQLModel records."
  - "Mock dictionaries include future recognition lookup groups without implementing recognition in this phase."

requirements-completed: [MOCK-01, MOCK-02, MOCK-03, MOCK-04, MOCK-05]

duration: ~45min
completed: 2026-05-07
---

# Phase 2: Mock Kaihong Business API Summary

**Mock Kaihong business boundary with auth, customers, dictionaries, recent orders, and local multi-document draft persistence**

## Performance

- **Duration:** ~45 min
- **Started:** 2026-05-07
- **Completed:** 2026-05-07
- **Tasks:** 3
- **Files modified:** 16

## Accomplishments

- Added `POST /mock/kaihong/auth/login` and `GET /mock/kaihong/users/me` with deterministic mock bearer tokens.
- Added customer list/filter/detail, dictionaries, and customer-specific recent-order endpoints.
- Added SQLite/SQLModel local draft persistence with create and retrieve endpoints.
- Added draft contracts that preserve multiple `source_documents` and multiple `order_items`.
- Added tests covering Mock Kaihong behavior and OpenAPI route presence.

## Task Commits

This plan is recorded as one phase execution commit after summary creation.

## Files Created/Modified

- `app/api/mock_kaihong.py` - Mock Kaihong FastAPI router and auth dependency.
- `app/schemas/mock_kaihong.py` - Request/response schemas for auth, customers, dictionaries, recent orders, and drafts.
- `app/services/mock_kaihong.py` - Deterministic seed data and draft persistence helpers.
- `app/db/session.py` - SQLModel SQLite engine, table creation, and session dependency.
- `app/models/draft.py` - SQLModel draft table.
- `tests/test_mock_kaihong.py` - End-to-end API tests through `TestClient`.
- `app/main.py` - Includes Mock Kaihong router and initializes local tables.
- `app/core/config.py` - Adds local SQLite database URL.
- `.gitignore` - Ignores local SQLite files.

## Decisions Made

- Used ASCII mock data in Python source while keeping business meaning in field names and dictionaries.
- Used a flexible JSON-backed draft record so real Kaihong fields can be mapped later.
- Kept document recognition and upload out of Phase 2; this phase stores the structure those later phases will produce.

## Deviations from Plan

None - plan executed exactly as written.

**Total deviations:** 0 auto-fixed.
**Impact on plan:** No scope change.

## Issues Encountered

- Initial TDD run failed with 404s for all Mock Kaihong routes, confirming the tests targeted missing behavior.
- First local test run hit sandbox disk I/O restrictions when SQLite tried to create the `.db` file; rerunning with project write permission resolved it.
- `datetime.utcnow()` produced a deprecation warning, so timestamps were changed to timezone-aware UTC.

## Verification

- `python -m pytest tests/test_mock_kaihong.py -q` -> 8 passed
- `python -m pytest` -> 10 passed
- `python -c "from app.main import app; print(sorted(app.openapi()['paths'].keys()))"` -> includes `/mock/kaihong/auth/login`, `/mock/kaihong/users/me`, `/mock/kaihong/customers`, `/mock/kaihong/dictionaries`, `/mock/kaihong/drafts`, and draft/customer detail paths.

## User Setup Required

None. The phase uses local SQLite and deterministic mock data only. The generated local database file is ignored by git.

## Next Phase Readiness

Phase 3 can now upload document images and attach file/document references that later fit into the `source_documents` structure. Phase 4 and Phase 5 can build Agent task state and mock recognition on top of the Mock Kaihong draft contract.

---
*Phase: 02-mock-kaihong-business-api*
*Completed: 2026-05-07*

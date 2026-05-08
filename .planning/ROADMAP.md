# Roadmap: Kaihom Agent v1

**Created:** 2026-05-07
**Milestone Goal:** Build a local Mock version of the mobile logistics order entry Agent that proves the full loop before real Kaihong Wing integration.

## Phase 1: FastAPI Foundation

**Status:** completed
**Goal:** Create the runnable backend project skeleton and development workflow.
**Requirements:** FOUND-01, FOUND-02, FOUND-03, FOUND-04
**Plan:** `.planning/phases/01-fastapi-foundation/01-01-PLAN.md`
**Success Criteria:**
- `uvicorn` can run the app locally.
- `/health` returns a healthy response.
- `/docs` shows OpenAPI documentation.
- Basic tests run and pass.

## Phase 2: Mock Kaihong Business API

**Status:** completed
**Goal:** Simulate the Kaihong Wing business data boundary.
**Requirements:** MOCK-01, MOCK-02, MOCK-03, MOCK-04, MOCK-05
**Dependencies:** Phase 1
**Plan:** `.planning/phases/02-mock-kaihong-business-api/02-01-PLAN.md`
**Success Criteria:**
- Mock login/current user works.
- Customers, dictionaries, recent orders, and drafts are available through documented endpoints.
- Data is stored locally and testable.

## Phase 3: File Upload and Local Storage

**Status:** complete
**Goal:** Accept logistics document images from mobile/H5 and persist file metadata.
**Requirements:** FILE-01, FILE-02, FILE-03, FILE-04, FILE-05
**Dependencies:** Phase 1
**Success Criteria:**
- Single and multi-file uploads work.
- Invalid file types/sizes are rejected.
- Uploaded files are stored locally with file IDs.
- Files can be linked to Agent tasks.

## Phase 4: Agent Task State Machine

**Status:** pending
**Goal:** Represent the order-draft Agent workflow as explicit task states and events.
**Requirements:** TASK-01, TASK-02, TASK-03, TASK-04
**Dependencies:** Phase 2, Phase 3
**Success Criteria:**
- Task creation endpoint accepts user context and file references.
- Task status can be queried.
- Task events are recorded.
- Failure states are represented clearly.

## Phase 5: Mock OCR and Field Extraction

**Status:** pending
**Goal:** Convert deterministic mock OCR text into structured logistics order draft fields.
**Requirements:** EXTR-01, EXTR-02, EXTR-03, EXTR-04, EXTR-05
**Dependencies:** Phase 4
**Success Criteria:**
- Core order draft schema exists.
- Mock OCR text fixtures drive extraction.
- Missing required fields are detected.
- Draft preview includes extracted field values and metadata.

## Phase 6: Clarification and Draft Finalization

**Status:** pending
**Goal:** Let the Agent ask for missing fields, merge answers, and save final drafts.
**Requirements:** CLAR-01, CLAR-02, CLAR-03, CLAR-04, DRAFT-01, DRAFT-02, DRAFT-03, DRAFT-04
**Dependencies:** Phase 5
**Success Criteria:**
- Missing fields produce clear questions.
- User answers update the draft.
- Complete drafts transition to ready_for_review.
- Finalized drafts are saved through the Mock Kaihong boundary.

## Phase 7: Mobile H5 Demo

**Status:** pending
**Goal:** Provide a phone-accessible demonstration UI for the complete Mock workflow.
**Requirements:** MOB-01, MOB-02, MOB-03, MOB-04, MOB-05
**Dependencies:** Phase 6
**Success Criteria:**
- Phone on the same network can open the H5 page.
- User can select/take photos and upload them.
- UI shows progress, questions, answers, and final draft.
- The demo proves the value loop without real Kaihong Wing access.

## Future Milestone: Real Recognition and Kaihong Integration

**Status:** future
**Goal:** Replace mock recognition and mock business APIs with real OCR/LLM and Kaihong Wing integration.
**Candidate Requirements:** OCR-01, OCR-02, OCR-03, INTG-01, INTG-02, INTG-03, INTG-04, WX-01, WX-02, PROD-01, PROD-02, PROD-03, PROD-04

---
*Last updated: 2026-05-07 after initialization*

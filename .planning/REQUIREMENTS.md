# Requirements: Kaihom Agent v1

**Defined:** 2026-05-07
**Core Value:** A business user can upload logistics documents from a phone, let the Agent pre-fill an order draft, answer only missing/uncertain fields, and save a reviewable draft.

## v1 Requirements

### Foundation

- [x] **FOUND-01**: Repository contains a runnable Python FastAPI application structure.
- [x] **FOUND-02**: Application exposes `/health` and OpenAPI documentation.
- [x] **FOUND-03**: Configuration supports local development without secrets committed to git.
- [x] **FOUND-04**: Tests can run locally with a single documented command.

### Mock Kaihong API

- [x] **MOCK-01**: System provides mock login and current-user endpoints.
- [x] **MOCK-02**: System provides mock customer list and customer detail endpoints.
- [x] **MOCK-03**: System provides mock dictionaries for ports, warehouses, yards, and fee types.
- [x] **MOCK-04**: System provides mock recent-order lookup by customer.
- [x] **MOCK-05**: System can save and retrieve local order drafts through Mock Kaihong endpoints.

### Upload and Storage

- [x] **FILE-01**: User can upload one logistics document image through a multipart endpoint.
- [x] **FILE-02**: User can upload multiple logistics document images for one task.
- [x] **FILE-03**: System validates file type and size before saving.
- [x] **FILE-04**: System stores uploaded files locally and records file metadata.
- [x] **FILE-05**: Uploaded files can be associated with an Agent task.

### Agent Task Workflow

- [x] **TASK-01**: System can create an order-draft Agent task from uploaded file references and user context.
- [x] **TASK-02**: System tracks task status through created, extracting, need_more_info, ready_for_review, finalized, and failed.
- [x] **TASK-03**: System can return current task state, extracted fields, questions, and draft preview.
- [x] **TASK-04**: System records task events for audit/debugging.

### Extraction and Draft Schema

- [x] **EXTR-01**: System defines a Pydantic order draft schema for the core logistics fields.
- [x] **EXTR-02**: System supports mock OCR text as a deterministic input source.
- [x] **EXTR-03**: System extracts draft fields from mock OCR text into the schema.
- [x] **EXTR-04**: System marks missing required fields.
- [x] **EXTR-05**: System preserves source/evidence metadata where available.

### Clarification Loop

- [ ] **CLAR-01**: System generates user-facing clarification questions for missing required fields.
- [ ] **CLAR-02**: User can submit answers for clarification questions.
- [ ] **CLAR-03**: System merges user answers into the draft.
- [ ] **CLAR-04**: System transitions to ready_for_review once required fields are complete.

### Draft Finalization

- [ ] **DRAFT-01**: User can finalize a ready draft.
- [ ] **DRAFT-02**: Finalized draft is saved locally through the Mock Kaihong API boundary.
- [ ] **DRAFT-03**: Finalized draft response includes `draft_id`, field values, source file references, and audit metadata.
- [ ] **DRAFT-04**: OpenAPI docs show future Java/Kaihong-facing request and response contracts.

### Mobile Demo

- [ ] **MOB-01**: System provides a mobile H5 page that can be opened from a phone on the same network.
- [ ] **MOB-02**: Mobile page supports choosing/taking document images.
- [ ] **MOB-03**: Mobile page can upload files and show task progress.
- [ ] **MOB-04**: Mobile page can display clarification questions and submit answers.
- [ ] **MOB-05**: Mobile page can display and confirm an order draft.

## v2 Requirements

### Real Recognition

- **OCR-01**: Integrate real OCR or multimodal extraction provider.
- **OCR-02**: Add confidence scoring per extracted field.
- **OCR-03**: Add evaluation set for document extraction accuracy.

### Enterprise Integration

- **INTG-01**: Replace Mock Kaihong API with real Java/Kaihong adapter.
- **INTG-02**: Add service-to-service authentication between Java and Python.
- **INTG-03**: Map Agent draft fields to Kaihong Wing real order fields.
- **INTG-04**: Save confirmed drafts into the real Kaihong Wing draft/order workflow.

### WeChat

- **WX-01**: Build WeChat Mini Program or Enterprise WeChat frontend.
- **WX-02**: Integrate internal staff identity with Enterprise WeChat or Kaihong account system.

### Production Hardening

- **PROD-01**: Add PostgreSQL and migrations.
- **PROD-02**: Add private object storage for uploaded documents.
- **PROD-03**: Add structured audit logs and sensitive-data redaction.
- **PROD-04**: Add deployment artifacts and HTTPS gateway guidance.

## Out of Scope

| Feature | Reason |
|---------|--------|
| Direct Kaihong Wing database access | Unsafe and unavailable; future access should go through business APIs. |
| Direct formal order submission | v1 should generate drafts only for human review. |
| Native mobile app | H5 is enough to validate phone upload and Agent workflow. |
| Full Spring AI implementation | Python Mock Agent is the first integration boundary; Java can be added later. |
| Large-scale OCR accuracy guarantee | v1 validates workflow, not production extraction accuracy. |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| FOUND-01 | Phase 1 | Complete |
| FOUND-02 | Phase 1 | Complete |
| FOUND-03 | Phase 1 | Complete |
| FOUND-04 | Phase 1 | Complete |
| MOCK-01 | Phase 2 | Complete |
| MOCK-02 | Phase 2 | Complete |
| MOCK-03 | Phase 2 | Complete |
| MOCK-04 | Phase 2 | Complete |
| MOCK-05 | Phase 2 | Complete |
| FILE-01 | Phase 3 | Complete |
| FILE-02 | Phase 3 | Complete |
| FILE-03 | Phase 3 | Complete |
| FILE-04 | Phase 3 | Complete |
| FILE-05 | Phase 3 | Complete |
| TASK-01 | Phase 4 | Complete |
| TASK-02 | Phase 4 | Complete |
| TASK-03 | Phase 4 | Complete |
| TASK-04 | Phase 4 | Complete |
| EXTR-01 | Phase 5 | Complete |
| EXTR-02 | Phase 5 | Complete |
| EXTR-03 | Phase 5 | Complete |
| EXTR-04 | Phase 5 | Complete |
| EXTR-05 | Phase 5 | Complete |
| CLAR-01 | Phase 6 | Pending |
| CLAR-02 | Phase 6 | Pending |
| CLAR-03 | Phase 6 | Pending |
| CLAR-04 | Phase 6 | Pending |
| DRAFT-01 | Phase 6 | Pending |
| DRAFT-02 | Phase 6 | Pending |
| DRAFT-03 | Phase 6 | Pending |
| DRAFT-04 | Phase 6 | Pending |
| MOB-01 | Phase 7 | Pending |
| MOB-02 | Phase 7 | Pending |
| MOB-03 | Phase 7 | Pending |
| MOB-04 | Phase 7 | Pending |
| MOB-05 | Phase 7 | Pending |

**Coverage:**
- v1 requirements: 35 total
- Mapped to phases: 35
- Unmapped: 0

---
*Requirements defined: 2026-05-07*
*Last updated: 2026-05-09 after Phase 4 execution*

# Phase 2 Research: Mock Kaihong Business API

**Phase:** 02 - Mock Kaihong Business API  
**Goal:** Simulate the Kaihong Wing business data boundary.  
**Requirements:** MOCK-01, MOCK-02, MOCK-03, MOCK-04, MOCK-05

## Recommended Approach

Build a dedicated Mock Kaihong API router under `/mock/kaihong`. Keep it isolated from future real integration code so later phases can replace the implementation behind the same contract without rewriting Agent workflow code.

Recommended shape:

- `app/api/mock_kaihong.py` owns FastAPI routes.
- `app/schemas/mock_kaihong.py` owns request/response Pydantic models.
- `app/services/mock_kaihong.py` owns deterministic mock business data and draft operations.
- `app/db/session.py` introduces a small SQLModel SQLite session dependency.
- `app/models/draft.py` stores locally saved mock order drafts.
- `tests/test_mock_kaihong.py` verifies the public API behavior.

## Endpoint Contract

| Endpoint | Purpose |
|----------|---------|
| `POST /mock/kaihong/auth/login` | Return a deterministic mock bearer token for seeded staff users. |
| `GET /mock/kaihong/users/me` | Return the current mock staff user from the bearer token. |
| `GET /mock/kaihong/customers` | List mock customers, optionally filtered by keyword. |
| `GET /mock/kaihong/customers/{customer_id}` | Return one mock customer. |
| `GET /mock/kaihong/dictionaries` | Return ports, warehouses, yards, and fee types in one response. |
| `GET /mock/kaihong/customers/{customer_id}/recent-orders` | Return recent order hints for that customer. |
| `POST /mock/kaihong/drafts` | Save a local order draft through the mock boundary. |
| `GET /mock/kaihong/drafts/{draft_id}` | Retrieve a saved local order draft. |

## Data Design

Use static seed data for users, customers, dictionaries, and recent orders. Use SQLite/SQLModel for draft persistence because drafts need to be created and retrieved during later Agent phases.

The first draft schema should stay intentionally flexible:

- Required business identifiers: `customer_id`, `created_by`.
- Source document references: a list of document descriptors that later upload/OCR phases can fill.
- Order items: a list of one or more draft order items, because one upload batch may produce multiple orders or multiple transport legs.
- Draft payload: JSON-compatible dictionary of shared or legacy draft fields.
- Metadata: `source`, timestamps, and status.

This avoids pretending to know the real Kaihong Wing order field list before the company provides API documentation.

See `docs/物流订单字段与多单据识别说明.md` for the business field reference behind the multi-document and multi-order structure.

## Implementation Decisions

| Decision | Reason |
|----------|--------|
| Use `/mock/kaihong` prefix | Makes mock boundary obvious in OpenAPI and avoids confusion with future real adapters. |
| Use bearer token style mock auth | Matches future service/mobile auth shape while staying deterministic. |
| Store drafts in local SQLite | Satisfies local draft persistence and prepares for future SQLModel usage. |
| Keep dictionaries grouped in one endpoint | Mobile/Agent flows can fetch all lookup data cheaply during v1. |
| Return Pydantic response models | Keeps OpenAPI contracts explicit for future Java/Kaihong discussion. |
| Include document types and transport modes in mock dictionaries | Prepares later upload/OCR phases to classify multiple logistics documents without adding real recognition in Phase 2. |

## Risks

- Real Kaihong Wing fields are unknown, so the draft payload must stay flexible.
- Multiple uploaded documents may map to multiple draft orders; Phase 2 stores this structure but does not perform recognition.
- Mock token auth must not be mistaken for production security.
- SQLite database files should stay local and ignored by git.
- Phase 2 should not add upload, OCR, Agent task, clarification, or mobile UI behavior.

## RESEARCH COMPLETE

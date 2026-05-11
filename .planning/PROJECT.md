# Kaihom Agent v1

## What This Is

Kaihom Agent v1 is a mobile-accessible logistics order entry Agent prototype for business staff who need to turn photos of entrustment letters, receipts, bills of lading, freight documents, and related logistics paperwork into structured order drafts.

The first milestone deliberately does not depend on the real Kaihong Wing system. It builds a Python FastAPI Mock version that simulates Kaihong Wing users, customers, dictionaries, historical orders, file upload, Agent clarification, and order draft storage so the full product loop can be demonstrated before real enterprise integration.

## Core Value

A business user can upload logistics documents from a phone, let the Agent pre-fill an order draft, answer only missing/uncertain fields, and save a reviewable draft instead of manually entering everything from scratch.

## Requirements

### Validated

- [x] Build a Python FastAPI backend that exposes Agent APIs and Mock Kaihong APIs. Validated through Phase 4: Agent Task State Machine.
- [x] Support mobile-friendly document image upload and local file metadata tracking. Validated through Phase 3: File Upload and Local Storage.
- [x] Maintain an Agent task lifecycle from upload through extraction, clarification, review, and finalization. Phase 4 validates the task/status/event ledger; later phases fill extraction, clarification, and finalization behavior.
- [x] Use a draft field schema that can later map to Kaihong Wing order fields. Validated through Phase 5: Mock OCR and Field Extraction.

### Active

- [ ] Provide a mock business data layer for users, customers, dictionaries, historical orders, and order drafts.
- [ ] Support missing-field and low-confidence clarification questions.
- [ ] Save confirmed order drafts locally for inspection and future integration.
- [ ] Produce OpenAPI documentation for future Java/Kaihong integration discussion.

### Out of Scope

- Real Kaihong Wing system integration - unavailable in the current phase and must wait for official API/field/access details.
- Direct database access to Kaihong Wing - unsafe and bypasses business permissions; future integration should go through controlled APIs.
- Direct formal order creation - first release saves drafts only to avoid business-risky automation.
- Native iOS/Android apps - first release should use mobile H5; WeChat Mini Program can follow after the core loop is proven.
- Production-grade OCR/LLM accuracy guarantees - first release may use mock OCR or limited real OCR to prove workflow shape.
- Full enterprise SSO/RBAC - first release uses mock login and minimal JWT-style authentication patterns.

## Context

The project starts from `docs/凯鸿之翼手机物流订单录入Agent项目书.md`.

Current repository state is greenfield: only a license and the project brief exist. The working strategy is to establish a Mock system first, then replace the Mock Kaihong API implementation with a Java/Spring Boot or real Kaihong Wing integration layer when the company provides access.

The target product loop is:

1. Mobile user uploads one or more logistics document photos.
2. Backend creates an Agent task and file records.
3. Agent extracts order fields from OCR text or mocked OCR text.
4. Agent identifies missing, conflicting, or low-confidence fields.
5. User answers clarification questions.
6. Agent updates the draft and marks it ready for review.
7. User confirms and saves an order draft.
8. Future Java/Kaihong adapter reads the same draft contract and writes to the real system.

## Constraints

- **Tech stack**: Python FastAPI first - best fit for OCR, document parsing, LLM/Agent iteration, and fast Mock development.
- **Integration**: Do not require real Kaihong Wing access for v1 - use Mock APIs and clear contracts.
- **Data safety**: Treat document photos, OCR text, prompts, drafts, and logs as sensitive business data.
- **Storage**: Start with local filesystem and SQLite/SQLModel; keep boundaries clean so PostgreSQL and object storage can replace them later.
- **Frontend**: Start with mobile H5 instead of native app; keep WeChat Mini Program as a later adapter.
- **Agent design**: Prefer a deterministic task state machine and Pydantic schemas before complex Agent frameworks. Keep Phase 4 framework-light, but explicitly revisit LangChain/LangGraph during Phase 5 or Phase 6 planning when extraction, clarification loops, human-in-the-loop behavior, or tool orchestration become concrete.

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Start with Python FastAPI only | No real Java/Kaihong access yet; Python is strongest for AI/OCR prototype work | Pending |
| Implement Mock Kaihong API | Allows complete demo loop before enterprise integration | Pending |
| Save drafts, not formal orders | Reduces business risk and supports human review | Pending |
| Use Pydantic/SQLModel contracts | Keeps request, response, and draft schemas explicit and future-mappable | Validated through Phase 5 |
| Start with mobile H5 | Fastest way to test phone upload without app-store or mini-program overhead | Pending |
| Defer LangChain/LangGraph dependency decision | Phase 4 needs deterministic task state first; Phase 5/6 should discuss framework value when extraction and clarification behavior are planned | Pending |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition**:
1. Requirements invalidated? Move to Out of Scope with reason.
2. Requirements validated? Move to Validated with phase reference.
3. New requirements emerged? Add to Active.
4. Decisions to log? Add to Key Decisions.
5. "What This Is" still accurate? Update if drifted.

**After each milestone**:
1. Full review of all sections.
2. Core Value check - still the right priority?
3. Audit Out of Scope - reasons still valid?
4. Update Context with current state.

---
*Last updated: 2026-05-11 after Phase 5 execution*

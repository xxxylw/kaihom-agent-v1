# Phase 4: Agent Task State Machine - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md - this log preserves the alternatives considered.

**Date:** 2026-05-09
**Phase:** 4-Agent Task State Machine
**Areas discussed:** Phase purpose, LangChain/LangGraph timing, task creation behavior, status model, event detail, public API boundaries

---

## Phase Purpose

| Option | Description | Selected |
|--------|-------------|----------|
| Build OCR/extraction now | Combine task state with mock OCR and field extraction in this phase. | |
| Build task container first | Create the durable task/status/event layer, leaving OCR and clarification to later phases. | yes |
| Build mobile task UI now | Add frontend progress UI together with task APIs. | |

**User's choice:** Follow the recommended scope.
**Notes:** Phase 4 should be the task/state foundation after Phase 3 upload. Phase 5 handles extraction; Phase 6 handles clarification and finalization; Phase 7 handles mobile UI.

---

## LangChain/LangGraph Timing

| Option | Description | Selected |
|--------|-------------|----------|
| Introduce LangChain/LangGraph in Phase 4 | Use an AI framework immediately for task workflow. | |
| Defer runtime dependency but reserve boundaries | Keep Phase 4 deterministic and leave service boundaries for later framework integration. | yes |
| Never use LangChain/LangGraph | Commit to plain Python for all future phases. | |

**User's choice:** Follow the recommendation but reserve places for later LangChain/LangGraph.
**Notes:** The user wants framework discussion preserved for the appropriate later stage. Roadmap now marks Phase 5/6 for LangChain/LangGraph evaluation. Phase 4 should not bind the public API or database model to a specific AI framework.

---

## Task Creation Behavior

| Option | Description | Selected |
|--------|-------------|----------|
| Start tasks as `created` | Task exists and is ready for later extraction. | yes |
| Start tasks as `extracting` | Task immediately appears to be processing. | |
| Make status caller-selected | Client decides initial task status. | |

**User's choice:** Use the recommended behavior.
**Notes:** Since Phase 4 does not do OCR/extraction, `created` is the honest initial state. Phase 5 can move tasks to `extracting` when extraction work actually begins.

---

## Customer and File Inputs

| Option | Description | Selected |
|--------|-------------|----------|
| Require `customer_id` | User must identify customer before creating a task. | |
| Make `customer_id` optional | Agent can infer or ask about customer later. | yes |
| Create tasks without files | Allow empty tasks before upload. | |

**User's choice:** Use optional `customer_id`, required `file_ids`, and support multiple files.
**Notes:** This follows Phase 3's low-friction upload decision and supports real logistics document bundles.

---

## Event Detail

| Option | Description | Selected |
|--------|-------------|----------|
| Business-level events | Record task creation, file attachment, status changes, and failures. | yes |
| Low-level framework events | Record OCR node, prompt, parser, and retry details now. | |
| No separate events | Rely only on current task status. | |

**User's choice:** Use business-level events in Phase 4.
**Notes:** Future phases can add extraction or clarification events when those behaviors exist. LangGraph node-level details should not leak into the primary status model.

---

## Public API Boundary

| Option | Description | Selected |
|--------|-------------|----------|
| Expose arbitrary status patching | Let clients change task status freely. | |
| Keep transitions service-controlled | Provide create/query/events APIs; keep state transitions behind services. | yes |
| Only build service methods | No public task API yet. | |

**User's choice:** Follow the recommended API boundary.
**Notes:** Public APIs should support task creation and querying. State transitions should be controlled by backend services and future workflow actions to avoid invalid task states.

---

## the agent's Discretion

- Exact route names, table names, schema names, and service names can be selected by the planner.
- The planner can choose the most maintainable representation for task-file linkage as long as multiple files per task work and Phase 3 upload metadata remains usable.
- Internal/test-only transition helpers are acceptable for validating the state machine.

## Deferred Ideas

- Discuss LangGraph compatibility during Phase 5 if extraction becomes multi-node or provider-driven.
- Explicitly evaluate LangGraph during Phase 6 for multi-step clarification and human-in-the-loop flow.
- Consider LangChain later only if prompt chains, tool calling, retrieval, or LLM-driven business lookups become concrete.

# Phase 7: Mobile H5 Demo - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md - this log preserves the alternatives considered.

**Date:** 2026-05-14
**Phase:** 7-Mobile H5 Demo
**Areas discussed:** Agent-oriented architecture direction

---

## Agent-Oriented Architecture Direction

| Option | Description | Selected |
|--------|-------------|----------|
| Agent H5 Demo + existing backend flow | Make the Phase 7 UI feel like an Agent workflow while keeping Phase 6 backend services and APIs as the source of truth. | yes |
| Add Agent Tool Layer in Phase 7 | Introduce explicit backend tool abstractions now, ahead of MCP/chatbox integration. | |
| Replace workflow with FunctionCallAgent/runtime | Make an Agent framework drive the main workflow in Phase 7. | |
| Plain H5 only | Build a straightforward mobile UI without emphasizing Agent concepts. | |

**User's choice:** Record the recommended direction and continue the discussion on another computer.

**Notes:** The project should become more Agent-oriented, but Phase 7 should not perform a large runtime rewrite. The H5 demo should present Agent state, questions, answers, and draft progress clearly. Existing backend actions remain deterministic and service-controlled. MCP, chatbox integration, and full Agent Tool Layer are deferred.

---

## the agent's Discretion

- The planner may choose frontend implementation details that make the Agent workflow clear without expanding Phase 7 scope.
- The planner may keep backend changes minimal unless needed to support the H5 demo.

## Deferred Ideas

- MCP server for chatbox tool calling.
- Agent Tool Layer and query projection tables.
- HelloAgents `FunctionCallAgent` or strict function calling provider work.

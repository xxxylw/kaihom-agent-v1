# Research: Architecture

**Project:** Kaihom Agent v1

## Recommended Architecture

Use a modular monolith FastAPI service for the first milestone. Keep Agent APIs and Mock Kaihong APIs in the same repo but separated by routers and services.

```text
mobile H5 / docs client
        -> FastAPI
           -> api.agent routes
           -> api.mock routes
           -> services.agent_service
           -> services.mock_kaihong_service
           -> db SQLModel models/session
           -> storage local file store
```

## Boundaries

- `api/`: request/response endpoints only.
- `schemas/`: Pydantic contracts.
- `models/`: SQLModel database tables.
- `services/`: business logic and Agent workflow.
- `storage/`: file persistence abstraction.
- `core/`: config, security, app setup.

## Agent Workflow Pattern

Start with an explicit state machine rather than an open-ended Agent loop:

```text
created -> files_uploaded -> extracting -> need_more_info -> ready_for_review -> finalized
                                      \-> failed
```

This keeps the system testable and makes future Java integration easier.

## Future Integration

When Kaihong Wing access exists, add a `kaihong_client` adapter that implements the same interface as `mock_kaihong_service`. The Agent workflow should not need to know whether data comes from Mock storage or real Java/Kaihong APIs.

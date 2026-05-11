# Phase 5 Discussion Log

**Phase:** 05 - Mock OCR and Field Extraction  
**Date:** 2026-05-11  
**Status:** Captured for planning

## Summary

The discussion clarified that Phase 5 should build deterministic mock OCR and field extraction for logistics order draft previews. The user wants the schema to include domestic and international logistics fields now, even if not all fields are required in Phase 5. The user also emphasized that the future complete Agent must support query and decision-making use cases for leadership or operational users.

## Decisions Captured

- Use a standard logistics draft field schema covering sender/receiver, route, cargo, package, service, and international reference fields.
- Treat only the first-layer core fields as required for Phase 5 missing-field detection.
- Include second-layer and third-layer fields in the schema as optional fields, not deferred out of the data model.
- Store Phase 5 draft preview and extraction metadata as JSON on/near the Agent task for now.
- Keep canonical field names and metadata stable so future phases can promote fields to searchable/reportable database structures.
- Use deterministic mock OCR fixtures and deterministic Python/Pydantic extraction.
- Do not introduce LangChain or LangGraph in Phase 5.
- Add an extraction action endpoint such as `POST /agent/tasks/{task_id}/extract`.

## User Emphasis

The user specifically noted that a future complete Agent must support query functionality so leaders or other users can retrieve the data they need and make judgments. This should influence Phase 5 by preserving structured canonical fields and a clear path to future database projections, even while Phase 5 stores extraction previews as JSON.

## Deferred

- Real OCR/LLM extraction.
- Human clarification loop.
- Final draft save.
- Analytics/reporting UI and query APIs.
- Formal LangGraph evaluation in Phase 6.

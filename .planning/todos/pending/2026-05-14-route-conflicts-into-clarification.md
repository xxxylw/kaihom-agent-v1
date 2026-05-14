---
created: 2026-05-14T16:07:06.161Z
title: Route conflicts into clarification
area: api
files:
  - app/services/agent_tasks.py:188
  - app/services/clarification_graph.py:105
  - app/services/clarification.py:261
  - tests/test_clarification_api.py
---

## Problem

Phase 6 has internal support for field conflicts in the clarification flow, but task extraction currently routes the task status based only on `preview.missing_fields`. If extraction produces a draft with no missing required fields but with `preview.conflicts`, the task can incorrectly become `ready_for_review`, skipping the clarification question path. Finalization still blocks unresolved conflicts, so the user would see a draft that appears ready but cannot be finalized.

Relevant current behavior:

- `app/services/agent_tasks.py:188` sets `NEED_MORE_INFO_STATUS` only when `preview.missing_fields` is non-empty.
- `app/services/clarification_graph.py` can generate conflict questions when `draft_preview.conflicts` exists.
- `app/services/clarification.py` already treats unresolved conflicts as incomplete and blocks finalize.

## Solution

Update extraction routing so `preview.missing_fields or preview.conflicts` sends the task to `need_more_info`. Add a conflict-detected task event or include conflicts in the existing extraction/missing-info event details. Add focused tests for a conflict-only draft:

- extraction returns `need_more_info` when conflicts exist even if required fields are complete;
- `GET /agent/tasks/{task_id}/clarification` returns a question with conflict candidate values;
- finalization remains blocked until conflicts are resolved.

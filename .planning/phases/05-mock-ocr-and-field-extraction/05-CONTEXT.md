# Phase 5: Mock OCR and Field Extraction - Context

**Gathered:** 2026-05-11
**Status:** Ready for planning

<domain>
## Phase Boundary

Phase 5 makes the Agent task useful for the first time after upload: it converts deterministic mock OCR text into a structured logistics order draft preview. It should read files already linked to an Agent task, generate mock OCR text from fixtures, extract logistics fields into a typed Pydantic draft schema, identify missing required fields, persist the preview on the task, and update task status to `need_more_info` or `ready_for_review`.

This phase does not perform real OCR, call an LLM, generate user-facing clarification questions, merge user answers, finalize drafts into Mock Kaihong, build reporting dashboards, or introduce LangChain/LangGraph as runtime dependencies.

</domain>

<decisions>
## Implementation Decisions

### Draft Field Scope
- **D-01:** Phase 5 must define one typed logistics draft schema that includes all agreed fields, even if some are optional in this phase.
- **D-02:** Required fields for Phase 5 missing-field detection are: `customer_name`, `shipper_name`, `shipper_phone`, `shipper_address`, `consignee_name`, `consignee_phone`, `consignee_address`, `cargo_name`, `package_count`, and `gross_weight_kg`.
- **D-03:** Important optional v1 fields must be present in the schema and draft preview when extracted: `origin`, `destination`, `cargo_volume_cbm`, `package_type`, `transport_mode`, `service_type`, `pickup_date`, and `remarks`.
- **D-04:** International/advanced fields must be reserved in the schema as optional fields: `hs_code`, `declared_value`, `currency`, `incoterm`, `invoice_no`, `container_type`, `container_count`, `booking_no`, and `bill_of_lading_no`.

### Storage and Query Evolution
- **D-05:** Phase 5 should store draft preview and extraction metadata as JSON on the Agent task, not as one database column per business field yet.
- **D-06:** JSON storage is a Phase 5 tactical choice because this is an extraction preview, field contracts may still evolve, and extraction metadata is semi-structured.
- **D-07:** The implementation must not block future analytics/query use cases. The schema must keep stable canonical field names, typed values, and source/evidence metadata so future phases can promote these fields into queryable tables or projections.
- **D-08:** Future leadership/operations query needs are important. The plan should include a clear later path for searchable/reportable order data, such as an `order_draft_fields` projection table, finalized draft columns, or reporting views after real Kaihong field mapping stabilizes.

### Extraction Behavior
- **D-09:** Phase 5 uses deterministic Python/Pydantic extraction logic, not LangChain/LangGraph.
- **D-10:** Mock OCR text should come from deterministic fixtures keyed by document type, filename pattern, or other stable test inputs. It should not depend on real OCR services.
- **D-11:** Extraction should support multiple files per task by running mock OCR for each file and merging extracted fields into one draft preview.
- **D-12:** When multiple files provide the same field with conflicting values, keep the first extracted value for the preview and record the conflict in extraction metadata for later review.
- **D-13:** Missing required fields should be represented as field names and metadata. Phase 5 should not generate natural-language clarification questions; that belongs to Phase 6.

### Task Status and Events
- **D-14:** Add a protected trigger endpoint such as `POST /agent/tasks/{task_id}/extract`.
- **D-15:** Extraction should transition the task from `created` to `extracting`, then to `need_more_info` if required fields are missing, otherwise `ready_for_review`.
- **D-16:** Phase 5 should record business-level events such as `extraction_started`, `mock_ocr_completed`, `fields_extracted`, and `missing_fields_detected` where appropriate.
- **D-17:** Do not expose a broad public status mutation endpoint. Extraction is a workflow action that controls status changes through the service layer.

### LangChain/LangGraph Reservation
- **D-18:** Do not add LangChain or LangGraph as runtime dependencies in Phase 5.
- **D-19:** Preserve a workflow/extraction service boundary so future real OCR/LLM or LangGraph orchestration can replace the internal execution engine without changing public task APIs.
- **D-20:** Re-evaluate LangGraph in Phase 6, where human-in-the-loop clarification, answer merging, and multi-step state transitions are concrete.

### the agent's Discretion
- The planner may choose exact class names, helper function names, and JSON field names if they preserve the canonical business field names above.
- The planner may decide whether draft preview JSON lives directly on `AgentTaskRecord` as multiple JSON columns or as a small companion extraction table, as long as the public API can return the preview and future query evolution remains clear.
- The planner may choose simple regex/key-value parsing fixtures for Phase 5, provided tests are deterministic and cover missing fields and conflicts.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Project Scope
- `.planning/PROJECT.md` - Defines the mock-first mobile logistics Agent product, target upload-to-draft loop, data safety constraints, and the preference for deterministic schemas before complex Agent frameworks.
- `.planning/REQUIREMENTS.md` - Defines EXTR-01 through EXTR-05 for Phase 5.
- `.planning/ROADMAP.md` - Defines Phase 5 as Mock OCR and Field Extraction and records the LangChain/LangGraph discussion marker.
- `.planning/STATE.md` - Records that Phase 4 is complete and Phase 5 is next.

### Upstream Phase Outputs
- `.planning/phases/04-agent-task-state-machine/04-CONTEXT.md` - Locks the Agent task status/event model and says Phase 5 consumes task file references.
- `.planning/phases/04-agent-task-state-machine/04-01-SUMMARY.md` - Confirms protected `/agent/tasks` APIs, task events, upload linkage, and deterministic transition helpers exist.
- `.planning/phases/03-file-upload-and-local-storage/03-CONTEXT.md` - Records upload metadata, optional customer/document type behavior, and local storage constraints.
- `.planning/phases/02-mock-kaihong-business-api/02-01-SUMMARY.md` - Establishes Mock Kaihong draft storage shape using JSON payloads.

### External Field Research
- `https://www.dhl.com/discover/en-gb/ship-with-dhl/shipping-solutions/shipping-tools/mydhl-user-guides/create-package-shipment` - DHL shipment flow: address details, shipment details, customs invoice, packaging, payment, shipping date, product, optional services, pickup/dropoff.
- `https://developer.fedex.com/api/en-is/catalog/ship/v1/docs.html` - FedEx Ship API required input: account, pickup type, service type, packaging, shipper, recipient, payment, package weights, label specification.
- `https://developer.ups.com/us/en/shipping/how-to-ship-package` - UPS shipment creation: package dimensions/weight, origin/destination addresses, delivery speed/services, payment/label.
- `https://www.maersk.com/support/faqs/mandatory-booking-information` - Maersk booking inputs: from/to location, service mode, contractual customer, departure date, cargo details, container type/size/count, weight.
- `https://openapi.danniao.com/docs/smallb/2.%E6%95%A3%E5%AE%A2%E8%AE%A2%E5%8D%95%E4%B8%8B%E5%8F%91%E6%8E%A5%E5%8F%A3.html` - Cainiao domestic order required fields for sender/receiver, goods, quantity, weight, and order ID.
- `https://openapi.express.cainiao.com/docs/b2c/10.%E5%8F%96%E5%8F%B7%E6%8E%A5%E5%8F%A3.html` - Cainiao waybill number request fields for sender, receiver, package info, item name/count, dimensions/weight.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `app/models/agent_task.py`: Existing `AgentTaskRecord` and `AgentTaskEventRecord` should be extended or paired with extraction storage.
- `app/schemas/agent_tasks.py`: Already exposes nullable `draft_preview` and empty `questions`, which Phase 5 can populate.
- `app/services/agent_tasks.py`: Existing creation, lookup, event, and transition helpers are the correct integration point for extraction.
- `app/api/agent_tasks.py`: Existing protected `/agent/tasks` router should receive the extraction action endpoint.
- `app/models/uploaded_file.py`: Existing upload metadata provides file IDs, filenames, document type, task ID, and safe file references.
- `app/schemas/mock_kaihong.py` and `app/models/draft.py`: Existing Mock Kaihong draft storage uses flexible JSON payloads, aligning with Phase 5 draft preview JSON.
- `tests/test_agent_tasks.py` and `tests/test_uploads.py`: Existing TestClient patterns and upload/task helpers should be reused.

### Established Patterns
- API routers live under `app/api/`.
- SQLModel records live under `app/models/`.
- Pydantic request/response schemas live under `app/schemas/`.
- Business logic lives under `app/services/`.
- Protected routes reuse mock bearer auth from `app/api/mock_kaihong.py`.
- Local persistence uses SQLite/SQLModel through `app/db/session.py`.

### Integration Points
- `POST /agent/tasks/{task_id}/extract` should consume the existing task and linked uploads.
- `GET /agent/tasks/{task_id}` should return populated `draft_preview` after extraction.
- Phase 6 will consume `missing_fields` and preview data to generate clarification questions.
- Future reporting/query features should consume finalized draft data or projections, not force Phase 5 to prematurely normalize every field.

</code_context>

<specifics>
## Specific Ideas

Recommended `draft_preview` response shape:

```json
{
  "fields": {
    "customer_name": "Ningbo Future Trading Co., Ltd.",
    "shipper_name": "Alice Chen",
    "cargo_name": "Auto parts",
    "package_count": 20,
    "gross_weight_kg": 1200.0,
    "destination": "Los Angeles",
    "hs_code": null
  },
  "missing_fields": ["shipper_phone", "consignee_address"],
  "field_evidence": {
    "cargo_name": {
      "source_file_id": "file_001",
      "source_text": "Cargo: Auto parts",
      "confidence": 1.0
    }
  },
  "conflicts": []
}
```

Recommended implementation principle:

- Keep canonical field names stable now.
- Store preview JSON now.
- Add query/reporting projections later once fields and real Kaihong mapping stabilize.

</specifics>

<deferred>
## Deferred Ideas

- Real OCR or multimodal extraction provider belongs to a future OCR/LLM phase.
- LangGraph orchestration belongs to Phase 6 only if clarification state becomes complex enough.
- Natural-language clarification questions belong to Phase 6.
- Final draft save through Mock Kaihong belongs to Phase 6.
- Leadership reporting/search dashboards belong to a future analytics/reporting phase, but Phase 5 must keep field names and evidence metadata stable enough to support them.

</deferred>

---

*Phase: 05-Mock OCR and Field Extraction*
*Context gathered: 2026-05-11*

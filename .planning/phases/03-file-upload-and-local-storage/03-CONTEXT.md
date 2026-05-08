# Phase 3: File Upload and Local Storage - Context

**Gathered:** 2026-05-08
**Status:** Ready for planning

<domain>
## Phase Boundary

Phase 3 delivers the file intake layer for the mobile logistics Agent loop: authenticated users can upload one or more logistics document files, the backend validates only technical acceptability, stores files locally under system-generated IDs, records file metadata, and returns file IDs that later phases can attach to Agent tasks.

This phase does not perform OCR, classify business document content, create Agent tasks, extract order fields, ask clarification questions, finalize drafts, or build the mobile H5 UI.

</domain>

<decisions>
## Implementation Decisions

### Upload Contract
- **D-01:** Use one multipart upload endpoint for both single-file and multi-file uploads. A single upload is represented as a file list of length 1.
- **D-02:** Support `jpg`, `jpeg`, `png`, `webp`, and `pdf` inputs. PDF support is required because employees may receive electronic forms or scanned PDF documents, not only camera photos.
- **D-03:** Do not require employees to select a customer before upload. Customer identification should be inferred later from document contents when possible.
- **D-04:** Do not require employees to select a document type before upload. `document_type` is a business classification such as entrustment, invoice, packing list, or bill of lading; it belongs to later OCR/Agent inference and can remain `unknown` or `null` during Phase 3.
- **D-05:** Upload success responses should return file IDs and display-safe metadata only, not absolute local disk paths.

### Validation Rules
- **D-06:** Phase 3 validates technical constraints only: supported MIME/extension, per-file size, file count, total request size, and ability to save the file.
- **D-07:** Business content problems are not upload failures. Wrong documents, unclear images, missing customer names, incomplete PDFs, unknown document type, or missing logistics fields should be accepted and handled later by Agent/OCR clarification.
- **D-08:** File limits are: single file maximum `20MB`, maximum `10` files per request, and total request maximum `100MB`.
- **D-09:** For multi-file uploads, if any file fails technical validation, fail the request before saving the batch. This keeps the upload result clear and avoids partially-linked batches.

### Storage and Naming
- **D-10:** Generate system IDs and stored filenames rather than trusting user filenames. Original filenames are retained only for display and audit.
- **D-11:** Store files under a local project-controlled upload directory using generated IDs. Directory structure can be date-based or otherwise planner-selected as long as generated IDs prevent collisions and absolute paths are not exposed in API responses.
- **D-12:** Preserve enough metadata for later task linkage and troubleshooting: file ID, original filename, stored filename, relative storage path, content type, file kind, size, hash, upload user, optional customer, optional task, status, and timestamps.

### Metadata Model
- **D-13:** Add an `UploadedFileRecord`-style SQLModel table for file metadata, using the existing local SQLite/SQLModel foundation.
- **D-14:** Recommended fields: `id`, `original_filename`, `stored_filename`, `storage_path`, `content_type`, `file_kind`, `size_bytes`, `sha256`, `uploaded_by`, `customer_id`, `task_id`, `document_type`, `status`, `source`, `created_at`, and `updated_at`.
- **D-15:** `customer_id`, `task_id`, and `document_type` should be nullable in Phase 3. `status` should at least support `uploaded` and rejected/error handling; later phases may extend statuses such as `linked`, `processing`, `extracted`, and `failed`.
- **D-16:** Use `file_kind` to distinguish technical file classes such as `image` and `pdf`; do not confuse this with `document_type`, which is a business classification.

### the agent's Discretion
- The planner may choose exact route names, schema names, service function names, and upload directory layout, provided they fit the existing FastAPI/SQLModel patterns and preserve the product decisions above.
- The planner may decide whether to store `document_type` as nullable `str` or default `"unknown"`, but upload must not require user-provided document classification.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Project Scope
- `.planning/PROJECT.md` - Defines the mock-first mobile logistics Agent product, data-safety constraints, local filesystem/SQLite starting point, and the target upload-to-draft loop.
- `.planning/REQUIREMENTS.md` - Defines FILE-01 through FILE-05 and keeps OCR, Agent task state, clarification, finalization, and H5 UI in later phases.
- `.planning/ROADMAP.md` - Defines Phase 3 as File Upload and Local Storage with dependencies and success criteria.
- `.planning/STATE.md` - Records the current focus on planning file upload and local storage.

### Upstream Phase Context
- `.planning/phases/02-mock-kaihong-business-api/02-01-SUMMARY.md` - Defines the Mock Kaihong draft contract and notes that Phase 3 files later fit into `source_documents`.
- `.planning/phases/02-mock-kaihong-business-api/02-VALIDATION.md` - Confirms Phase 2 mock business API coverage is green and available for downstream phases.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `app/main.py`: App factory includes routers and calls `create_db_and_tables()` during app creation.
- `app/core/config.py`: Existing settings object is the right place to add upload directory and upload limit configuration.
- `app/db/session.py`: Existing SQLModel engine/session dependency should be reused for upload metadata persistence.
- `app/models/draft.py`: Existing SQLModel table pattern can guide `UploadedFileRecord`.
- `app/api/mock_kaihong.py`: Existing router style, auth dependency pattern, and response model usage can guide a new upload router.
- `tests/test_mock_kaihong.py`: Existing `TestClient(app)` integration-test pattern should be reused for upload tests.

### Established Patterns
- Router modules live under `app/api/`.
- Pydantic request/response models live under `app/schemas/`.
- Business helpers live under `app/services/`.
- SQLModel tables live under `app/models/`.
- Local persistence uses SQLite and ignored local database files.
- Protected mock routes use bearer-token auth; Phase 3 should likely reuse or share the current-user dependency rather than invent a separate auth pattern.

### Integration Points
- New upload metadata connects to future Phase 4 Agent tasks through nullable `task_id` and returned `file_id` values.
- Uploaded files later become source document references for the Phase 2 draft shape (`source_documents`).
- Upload configuration should remain local-development friendly and avoid secrets.

</code_context>

<specifics>
## Specific Ideas

- Product principle: employees should have the lightest possible upload burden: take photos or choose existing files, upload them, and let the system infer what it can.
- If content is wrong or incomplete, the system should not reject it during upload; later Agent phases should ask for missing information.
- API response shape should be similar to:

```json
{
  "files": [
    {
      "file_id": "file_abc123",
      "original_filename": "IMG_0012.jpg",
      "file_kind": "image",
      "content_type": "image/jpeg",
      "size_bytes": 1830201,
      "status": "uploaded"
    }
  ]
}
```

</specifics>

<deferred>
## Deferred Ideas

- OCR and field extraction from uploaded images/PDFs belong to Phase 5.
- Creating Agent tasks from uploaded file IDs belongs to Phase 4.
- Clarification questions for missing, unclear, or wrong document content belong to Phase 6.
- Mobile H5 upload UI belongs to Phase 7.

</deferred>

---

*Phase: 3-File Upload and Local Storage*
*Context gathered: 2026-05-08*

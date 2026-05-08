# Phase 3: File Upload and Local Storage - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md - this log preserves the alternatives considered.

**Date:** 2026-05-08
**Phase:** 3-File Upload and Local Storage
**Areas discussed:** Upload contract, Metadata model, File type scope, Validation boundary, Upload response

---

## Upload Contract

| Option | Description | Selected |
|--------|-------------|----------|
| One endpoint | Single and multi-file uploads use the same multipart endpoint; single file is a list of one. | yes |
| Separate endpoints | One endpoint for one file and another endpoint for batches. | |

**User's choice:** One endpoint.
**Notes:** User agreed single-file and multi-file upload should be one interface.

---

## Metadata Model

| Option | Description | Selected |
|--------|-------------|----------|
| Minimal metadata | Only file ID and path. | |
| Rich metadata | Store original name, generated name, path, MIME, kind, size, hash, user, optional customer/task/document type, status, and timestamps. | yes |

**User's choice:** Rich metadata, with upload kept easy for employees.
**Notes:** Metadata means the database record describing a stored file. It should support later task linkage and troubleshooting.

---

## Customer and Document Type

| Option | Description | Selected |
|--------|-------------|----------|
| Require customer and document type at upload | User must classify files before upload. | |
| Keep both optional | Upload first; infer customer and document type later from content when possible. | yes |

**User's choice:** Do not require customer or document type.
**Notes:** User emphasized the employee burden should be minimal: ideally just take photos/upload files, with unknowns handled by later prompts.

---

## File Type Scope

| Option | Description | Selected |
|--------|-------------|----------|
| Images only | Support camera/photo uploads only. | |
| Images and PDFs | Support photos plus electronic/scanned PDF forms. | yes |

**User's choice:** Support PDFs.
**Notes:** User said employees may receive electronic forms; files should be passed into the Agent flow so fields can be extracted and saved later.

---

## Validation Boundary

| Option | Description | Selected |
|--------|-------------|----------|
| Reject business-content problems during upload | Upload fails if the document is not the expected business form. | |
| Reject only technical problems during upload | Accept supported files even if content is wrong/incomplete; later Agent phases clarify missing fields. | yes |

**User's choice:** Reject only technical problems.
**Notes:** Technical problems include unsupported type, oversize file/request, too many files, or inability to save. Business problems include wrong form, missing fields, unclear image, or unknown document type.

---

## Upload Limits

| Option | Description | Selected |
|--------|-------------|----------|
| 20MB per file, 10 files, 100MB total | Enough for phone photos and normal PDFs while protecting local development. | yes |
| Larger limits | More permissive but riskier for local storage. | |

**User's choice:** 20MB per file, 10 files per request, 100MB total.
**Notes:** User accepted the proposed limits.

---

## Upload Response

| Option | Description | Selected |
|--------|-------------|----------|
| Return safe file metadata | Return file IDs and display metadata, not absolute disk paths. | yes |
| Return local paths | Return filesystem paths to clients. | |

**User's choice:** Return safe file metadata.
**Notes:** User accepted response with file ID, original filename, file kind, content type, size, and status.

## the agent's Discretion

- Planner can choose exact route/schema/service names and directory layout.
- Planner can choose nullable `document_type` versus default `"unknown"`, as long as upload does not require user classification.

## Deferred Ideas

- OCR/field extraction: Phase 5.
- Agent task creation and status linkage: Phase 4.
- Clarification prompts for missing or wrong content: Phase 6.
- Mobile H5 UI: Phase 7.

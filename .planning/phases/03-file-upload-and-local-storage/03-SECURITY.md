---
phase: 03
slug: file-upload-and-local-storage
status: verified
threats_open: 0
asvs_level: 1
register_authored_at_plan_time: false
created: 2026-05-09
updated: 2026-05-09
---

# Phase 3 Security: File Upload and Local Storage

Phase 3 did not include a formal `<threat_model>` block in the execution plan, so this audit uses retroactive STRIDE over the implemented upload routes, upload service, metadata model, tests, and GSD verification artifacts.

## Trust Boundaries

| Boundary | Description | Data Crossing |
|----------|-------------|---------------|
| API client -> FastAPI upload routes | Authenticated API clients submit multipart files and later query/link metadata. | Bearer token, multipart file bytes, optional customer ID, task ID. |
| FastAPI upload service -> local filesystem | Validated upload bytes are written to local storage under generated filenames. | User-supplied file bytes, generated storage filename. |
| FastAPI upload service -> SQLite metadata | Upload metadata is persisted for later Agent phases. | File ID, original filename, generated filename, relative storage path, content type, size, SHA-256, uploader, optional linkage fields. |
| API response -> client | Upload routes return file metadata for downstream task creation. | Safe metadata only; no absolute local path or raw file bytes. |

## Threat Register

| Threat ID | Category | Component | Disposition | Mitigation | Status |
|-----------|----------|-----------|-------------|------------|--------|
| T-03-01 | Spoofing | `/uploads` routes | mitigate | All upload routes reuse `get_current_user`; missing/invalid bearer tokens are rejected. | closed |
| T-03-02 | Tampering | Local file write path | mitigate | Stored filenames are generated from `file_` UUID prefixes plus normalized extension; original filenames are not used as filesystem destinations. | closed |
| T-03-03 | Information Disclosure | Upload API responses | mitigate | Response schema omits `storage_path`; tests assert no `storage_path` or absolute path is returned. | closed |
| T-03-04 | Denial of Service | Multipart upload handling | mitigate | Configurable limits exist for per-file size, file count, and total request size; validation rejects empty files and oversize batches. | closed |
| T-03-05 | Tampering | File type handling | mitigate | Extension and declared content type must match the allowlist for JPEG, PNG, WEBP, and PDF. | closed |
| T-03-06 | Repudiation | Upload metadata | mitigate | Metadata stores uploader, timestamps, size, SHA-256, status, and generated file ID. | closed |
| T-03-07 | Information Disclosure | Local storage artifacts | mitigate | `uploads/` is ignored by git and no route serves raw uploaded file bytes in Phase 3. | closed |
| T-03-08 | Elevation of Privilege / Authorization | Cross-user file metadata access | accept | Phase 3 is mock-only local storage with mock bearer auth and no production tenant model yet. Per-customer/user ownership enforcement is deferred to the real authorization model before production use. | closed |

## Verification Evidence

| Threat ID | Evidence |
|-----------|----------|
| T-03-01 | `app/api/uploads.py` depends on `get_current_user` for `POST /uploads`, `GET /uploads/{file_id}`, and `PATCH /uploads/{file_id}/task`; `tests/test_uploads.py::test_upload_requires_bearer_token` verifies `401`. |
| T-03-02 | `app/services/uploads.py` generates `file_id = "file_" + uuid4().hex[:12]`, writes `stored_filename = file_id + extension`, and never writes using `original_filename`. |
| T-03-03 | `app/schemas/uploads.py::UploadedFileResponse` excludes storage path fields; `tests/test_uploads.py::test_single_image_upload_returns_safe_metadata` checks `storage_path` is absent and returned strings are not absolute paths. |
| T-03-04 | `app/core/config.py` defines upload size/count limits; `app/services/uploads.py::validate_upload_batch` enforces count, empty file, per-file size, and batch size; tests cover oversize and too many files. |
| T-03-05 | `app/services/uploads.py::ALLOWED_UPLOAD_TYPES` defines the accepted extension/content-type pairs; `validate_upload_batch` rejects unsupported extensions and content-type mismatches. |
| T-03-06 | `app/models/uploaded_file.py::UploadedFileRecord` includes `sha256`, `uploaded_by`, `created_at`, `updated_at`, `status`, and generated primary key `id`; `app/services/uploads.py` computes SHA-256 before committing metadata. |
| T-03-07 | `.gitignore` contains `uploads/`; `app/api/uploads.py` exposes metadata routes only and does not expose raw file download routes. |
| T-03-08 | Accepted risk is bounded by README/STATE project scope: mock-only local backend, no real Kaihong Wing integration, no company database, and no production authz model in Phase 3. |

## Accepted Risks Log

| Risk ID | Threat Ref | Rationale | Accepted By | Date |
|---------|------------|-----------|-------------|------|
| AR-03-01 | T-03-08 | Phase 3 intentionally uses mock bearer authentication and local SQLite storage. It does not implement production-grade ownership/tenant authorization. This is acceptable only for the mock-first local workflow and must be revisited before real company data or real Kaihong Wing integration. | Project scope / mock-only v1 decision | 2026-05-09 |

## Deferred Production Hardening

These items are not blockers for the mock-only Phase 3 gate, but should be handled before production or real customer data:

- Add real tenant/customer/user ownership checks around upload metadata retrieval and task linking.
- Add malware scanning or content inspection for uploaded PDFs/images.
- Add magic-byte validation in addition to extension and declared MIME checks.
- Add secure lifecycle management for retained uploaded files, including retention and deletion policy.
- Consider object storage or isolated storage paths instead of local filesystem storage.

## Security Audit Trail

| Audit Date | Threats Total | Closed | Open | Run By |
|------------|---------------|--------|------|--------|
| 2026-05-09 | 8 | 8 | 0 | Codex |

## Sign-Off

- [x] All threats have a disposition: mitigate or accept.
- [x] Accepted risks documented in Accepted Risks Log.
- [x] `threats_open: 0` confirmed.
- [x] `status: verified` set in frontmatter.

**Approval:** verified 2026-05-09

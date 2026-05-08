---
phase: 02
slug: mock-kaihong-business-api
status: approved
nyquist_compliant: true
wave_0_complete: true
created: 2026-05-08
---

# Phase 2 - Validation Strategy

Per-phase validation contract for feedback sampling during execution.

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 8.x |
| **Config file** | `pyproject.toml` |
| **Quick run command** | `python -m pytest tests/test_mock_kaihong.py -q` |
| **Full suite command** | `python -m pytest` |
| **Estimated runtime** | ~1 second |

## Sampling Rate

- **After every task commit:** Run `python -m pytest tests/test_mock_kaihong.py -q`
- **After every plan wave:** Run `python -m pytest`
- **Before `$gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** ~1 second

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 02-01-01 | 01 | 1 | MOCK-05 | N/A | Local SQLite draft persistence only; no real Kaihong access | integration | `python -m pytest tests/test_mock_kaihong.py -q` | yes | green |
| 02-01-02 | 01 | 1 | MOCK-01 | N/A | Login accepts only seeded valid credentials | integration | `python -m pytest tests/test_mock_kaihong.py -q` | yes | green |
| 02-01-02 | 01 | 1 | MOCK-02 | N/A | Customer endpoints require bearer auth and return 404 for missing customers | integration | `python -m pytest tests/test_mock_kaihong.py -q` | yes | green |
| 02-01-02 | 01 | 1 | MOCK-03 | N/A | Dictionary lookup groups are deterministic mock data | integration | `python -m pytest tests/test_mock_kaihong.py -q` | yes | green |
| 02-01-02 | 01 | 1 | MOCK-04 | N/A | Recent-order lookup is scoped to the requested seeded customer | integration | `python -m pytest tests/test_mock_kaihong.py -q` | yes | green |
| 02-01-03 | 01 | 1 | MOCK-01 | N/A | Current-user and protected endpoints reject missing bearer tokens | integration | `python -m pytest tests/test_mock_kaihong.py -q` | yes | green |
| 02-01-03 | 01 | 1 | MOCK-05 | N/A | Draft create/retrieve preserves payload, source documents, and order items | integration | `python -m pytest tests/test_mock_kaihong.py -q` | yes | green |
| 02-01-03 | 01 | 1 | MOCK-01..MOCK-05 | N/A | OpenAPI exposes the mock contracts for downstream phases | integration | `python -m pytest tests/test_mock_kaihong.py -q` | yes | green |

## Wave 0 Requirements

Existing infrastructure covers all phase requirements.

## Manual-Only Verifications

All phase behaviors have automated verification.

## Validation Audit 2026-05-08

| Metric | Count |
|--------|-------|
| Requirements audited | 5 |
| Gaps found | 0 |
| Resolved | 0 |
| Escalated | 0 |

## Verification Evidence

- `python -m pytest` -> 10 passed
- `python -c "from app.main import app; print(sorted(app.openapi()['paths'].keys()))"` -> includes `/mock/kaihong/auth/login`, `/mock/kaihong/users/me`, `/mock/kaihong/customers`, `/mock/kaihong/dictionaries`, `/mock/kaihong/drafts`, and draft/customer detail paths.

## Validation Sign-Off

- [x] All tasks have automated verify coverage.
- [x] Sampling continuity: no 3 consecutive tasks without automated verify.
- [x] Wave 0 covers all missing references.
- [x] No watch-mode flags.
- [x] Feedback latency < 2 seconds.
- [x] `nyquist_compliant: true` set in frontmatter.

**Approval:** approved 2026-05-08

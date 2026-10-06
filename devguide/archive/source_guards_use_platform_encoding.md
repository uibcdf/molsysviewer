---
summary: Source inspection guards use platform encoding and fail on Windows
issue: uibcdf/molsysviewer#169
status: resolved
opened: 2026-10-06
closed: 2026-10-06
severity: medium
verification: reproduced
area: [testing, reporting, portability]
guard: tests/test_source_text_encoding.py::test_source_guard_readers_declare_utf8
normative:
blocked_by: []
supersedes: []
---

# Source inspection guards use platform encoding and fail on Windows

## What

Exact-source run `37508347848` on `de32376385858e06635e6d5d1bc60573c8fab2e3`
passes Linux and macOS but fails six Windows tests. Three source inspections
raise `UnicodeDecodeError` and three reporting checks reject the same unreadable
frontend guard. Windows uses cp1252 for unspecified text reads; byte 0x8d in
UTF-8 source is not decodable there.

## How

`tests/loaders/test_load_from_molsysmt.py`, `tests/test_e2e_reliability.py` and
`tests/test_reporting_protocol.py` read authoritative Python/TypeScript sources
without an explicit encoding. Declare UTF-8 at every read in these owners.
`tests/test_source_text_encoding.py` rejects removal of that declaration; the
real native source-pair lane verifies the behavior on Windows.

## Why

Source guards must accept the same repository on each supported platform.
The native provider integration already passes; this is a consumer test and
reporting defect, not a failure in the molecular loader.

## What was refuted

Do not set `PYTHONUTF8` or remove Unicode labels to mask unspecified reads.
No generated runtime or exported HTML needs to be read or modified.

## Resolution

Fixed in `1ed34994`, with the final formatting-only successor
`d7939f08d604138112edfe84ccc9bc4a40428057`. The UTF-8 guard protects every
repository text read in the three affected owners. Exact-source run
`37523291585` passes on Windows: **2,849 passed, 53 skipped, zero failures**.
macOS passes 2,848/54 skipped and Linux 2,875/27 skipped, both with zero failures.
All three installed-source audits, native path guards and real integration pass.
The full local attempt and diagnosed Git-index/format follow-ups remain in
`devguide/ci_workflow_closure_20261006.json`; no second local full suite is run.
This resolves the six encoding failures without a UTF-8 environment workaround.

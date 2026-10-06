---
summary: Source inspection guards use platform encoding and fail on Windows
issue: uibcdf/molsysviewer#169
status: partial
opened: 2026-10-06
closed:
severity: medium
verification: reproduced
area: [testing, reporting, portability]
guard:
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

The 302 focused checks pass. The full Python run has 2,883 passes, 23 skips
and one new-report Git-index failure, fixed by staging the reports; all four
link guards then pass. The full suite is not repeated. Native Windows
confirmation remains pending on the new committed source candidate.

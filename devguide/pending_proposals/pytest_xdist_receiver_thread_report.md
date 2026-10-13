---
summary: Decide whether to report pytest-xdist receiver-thread warning imports upstream
issue: uibcdf/molsysviewer#80
status: open
opened: 2026-09-04
closed:
verification: inspected
area: [testing, coordination]
guard:
normative:
blocked_by: []
supersedes: []
---

# Optional upstream pytest-xdist report

## What

#80 tracks whether to report the upstream receiver-thread import behavior.
The Viewer controller pre-import workaround is already guarded and retained in
`tests/conftest.py`; this is not an unresolved Viewer implementation defect.

## How

Prepare a minimal upstream reproduction if the maintainer chooses to report
to pytest-dev/pytest-xdist. External filing was explicitly left as a separate
decision; reconciliation does not authorize contacting that project.

## Why

Warning-class deserialization can import a package from a receiver thread and
abort a session if that import raises. The owning Viewer workaround and package
fixes remain separate from the optional external reporting decision.

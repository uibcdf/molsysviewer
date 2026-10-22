---
summary: CI backlog verifier requires the retired Python 3.13 JavaScript cell.
issue: uibcdf/molsysviewer#260
status: active
opened: 2026-10-22
closed:
severity: medium
verification: inspected
area: [ci, workflows]
guard:
normative:
blocked_by: []
supersedes: []
---

# CI backlog watermark follows the retired JavaScript route

## What

The routine matrix now has eight Linux/macOS Python 3.11–3.14 cells and runs
JavaScript on Linux 3.14. `devtools/ci_backlog.py` still requires JavaScript on
3.13 and only enumerates three Python minors. Thus completed exact-source run
39704459739 cannot clear the current lane's skipped-commit debt.

## How

`PYTHON_VERSIONS` and the selected JS-cell check retained the old route during
uibcdf/molsysviewer#93. Its synthetic tests repeated the same old assumptions.
The new fixture retains native job/step metadata from the accepted eight-cell
run at `308ce8fb`, including JavaScript skipped on 3.13 and passing on 3.14.

The correction requires all four minors on both operating systems, with
JavaScript on Linux 3.14. Receiving must accept that real receipt and reject
missing 3.14 cells or omitted required Python/JS steps. Qt/E2E watermarks and
failure/unknown-evidence behavior remain independent.

## Why

Nightly recovery can repeat already-qualified work. This is CI accounting,
not a failure of the approved scientific/browser campaign. Historical six-cell
receipts retain their original qualification scope but cannot clear the new
eight-cell requirement.

## Resolution

Implementation and receiving in progress alongside uibcdf/molsysviewer#256.

---
summary: CI backlog verifier requires the retired Python 3.13 JavaScript cell.
issue: uibcdf/molsysviewer#260
status: resolved
opened: 2026-10-22
closed: 2026-10-22
severity: medium
verification: reproduced
area: [ci, workflows]
guard: tests/test_ci_backlog.py::test_current_native_eight_cell_receipt_controls_core_watermark
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


## Resolution — 2026-10-22

Resolved in `e4f8c7c5`. The watermark requires all eight Linux/macOS
3.11–3.14 cells and JavaScript on Linux 3.14. The selected regression guard
uses the actual native 39704459739 receipt and rejects missing Linux/macOS
3.14 cells or omitted required Python/JS steps. An offline replay confirms
that the old code rejects this receipt while the corrected code accepts it.

Hosted control-only probe 39709750593 recognizes `308ce8fb` as the complete
core watermark and correctly reports the two subsequent skipped commits.
It does not claim that this remaining CI debt was cleared. E2E/Qt probes
39709753576/39709756446 retain independent watermarks; their test jobs are
skipped, not newly qualified. Exact-source policy passes, as do 58 backlog
checks, three core/Qt guards and the single complete local core run
(3,224 passed, 21 skipped, 12 Qt deselected).
See [receiving](../pre_documentation_cleanup_20261022.json).

---
summary: Conda promotion uses obsolete matrix coverage and omits the Windows launcher gate.
issue: uibcdf/molsysviewer#134
status: resolved
opened: 2026-10-01
closed: 2026-10-01
severity: medium
verification: reproduced
area: [conda, release, cli]
guard: tests/test_promotion_gates.py
normative:
blocked_by: []
supersedes: []
---

# Conda promotion does not require current candidate evidence

**Reported:** 2026-10-01, during follow-up of uibcdf/molsysviewer#101.

## What

The promotion workflow checks `.total_count == 21`, corresponding to the former
five-platform installed-pair matrix. The supported matrix now has four platforms
and Python 3.11–3.14: 16 cells plus preparation. It does not require a staged
Windows launcher run before calling the exact-file promotion action.

## How

`.github/workflows/promote_conda_package.yaml` checks the overall pair conclusion,
commit, workflow path and title, but neither the individual matrix cells and
scientific steps nor the separate Windows launcher workflow. The fix shares the
local release evidence matrix checks, checks attempt-specific jobs, and requires
a Windows run matching Viewer commit, version, build and SHA-256. Its checkout,
installation and installed launcher steps must all execute successfully.

The Windows dispatch must run from the candidate revision: `candidate_sha`,
`github.sha` and the checked-out HEAD agree. Its run title declares the exact
version, build and digest. The checker independently validates the installed
Conda record and executes all three commands outside the checkout.

## Why

A valid current matrix is rejected, and installed Windows launcher qualification
can be omitted before public promotion. This gate correction does not certify a
repaired package: #101 still needs a frozen candidate, actual staged Windows
evidence, exact-file promotion and independent public Windows verification.

## What was refuted

Changing 21 to 17 alone cannot prove matrix coverage, successful scientific
steps, or installed command execution. Linux imports and recipe inspection do
not certify Windows launchers. This workflow gate does not replace the complete
release gate, whose installed environment artifacts bind the exact package files.

## Resolution

Implemented in the working tree on 2026-10-01. The promotion workflow requires
`windows_run_id` before the authenticated promotion action. The read-only helper
shares `check_pair_run` with the local candidate evidence gate: it accepts the
16 current platform/Python cells plus preparation and rejects old coverage,
duplicate/missing cells, wrong source/commit/build/attempt and skipped scientific
steps. Windows checks bind the exact workflow, commit, version, build and SHA-256
and require checkout, installation and launcher verification to execute.

`tests/test_promotion_gates.py` is the guard: its accepted-case test also checks
the actual promotion workflow's mandatory input, environment binding, helper
call and ordering before publication. Its rejection cases cover invalid pair
and Windows identities, incomplete jobs and omitted/failed/skipped steps. Other
recipe/release tests retain parity, exact-file promotion and Bash syntax checks.
The focused slice passed 103 tests. Complete source regression passed 2,402
tests with 20 skips, exit 0, in 307.36 seconds; log:
`/tmp/msv-promotion-full-python-20261001.log`.

MolSysMT's source checkout had concurrent work, so the complete run used an
isolated export of commit `ece35e622fc3f26c57f5261088fa07a39f081aca` at
`/tmp/msv-promotion-provider-ece35e62`, with the existing native extension and
generated version file copied into that export. Their SHA-256 values were
`50b54c09d6e8191450a69b1703bef82a4c5a123efb17015336258a91973dc33e` and
`6add38474883ca33b356209fd2316ca42a09c1cbab4027aa7dc88a7ee21589d4`,
respectively. Molecular imports were checked against the export; no sibling
source changes were made. This is source regression, not installed/release
certification. The workflow guard was strengthened after the complete run and
the final focused guard/metadata slice was run separately.

No artifact was built or published, no workflow was dispatched, and no new
hosted Windows result is claimed. The corrected workflow must be committed
with its helper before candidate dispatch. The repaired artifact qualification
remains partial under #101. The operator contract is recorded in
[`../release_gate_evidence.md`](../release_gate_evidence.md#exact-file-promotion-and-windows-launchers).

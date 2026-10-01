---
summary: Call the pinned common public Conda verifier and retain independent evidence.
issue: uibcdf/molsysviewer#133
status: resolved
opened: 2026-10-01
closed: 2026-10-01
verification: measured
area: [governance, release]
guard: tests/test_verify_public_package.py
normative:
blocked_by: []
supersedes: []
---

# Shared public Conda verification

**Reported:** 2026-10-01, following uibcdf/molsyssuite#48 and #27.
**Status:** Resolved: common provider adopted and its public-file verification passed.

## What

Replace copied verification or inline shell code with the common exact-file
provider. Keep release identity, platform selection, installed-package checks
and mutation credentials local.

## How

Promotion and independent workflows call the immutable MolSysSuite action
`399d33a4ee0da148571cba7cfc004e3f3a2e71e7`. Its non-login shell avoids the reproduced logout failure.
Anonymous release-metadata and solver-index checks establish each exact file's
main label, identity, build and SHA-256. Evidence is retained with `always()`.
The independent workflow contains no promotion or upload credentials.

## Why

One tested provider prevents duplicated logic from drifting. A read-only recheck
recovers evidence without repeating a public registry mutation.

## What is measured and what is assumed

Source routing is inspected. Provider tests and six original public-file checks
are recorded in uibcdf/molsyssuite#48. Local guard: `tests/test_verify_public_package.py`.
No new installed-pair scientific evidence is claimed.

## Alternatives and refuted paths

Keeping a corrected local copy would retain duplication. Repeating promotion
would conflate verification recovery with registry mutation.

## Scope and exclusions

Conda workflow governance. No package release, promotion or full scientific suite.
Existing component-specific installation checks keep their separate meaning.

## Acceptance criteria

Both workflows call the same pinned provider, retain independent evidence and
pass their local governance guards. Hosted read-only evidence checks the actual
provider call without a registry mutation.

## Local implementation issues

This report owns uibcdf/molsysviewer#133. Provider: uibcdf/molsyssuite#48.

## Dependencies and risks

An unavailable index fails verification; it never triggers another upload.
Policy and broader release routing remain coordinated under uibcdf/molsyssuite#27.

## Provenance

2026-10-01; isolated clean checkout; administrative tests only. Provider revision
`399d33a4ee0da148571cba7cfc004e3f3a2e71e7`. Hosted execution evidence will be appended before closure.

## Resolution and measured evidence

Administrative verification passed 133 selected local tests. Native hosted
run 36860171883 executed the pinned shared action, verified the exact public file
and retained independent evidence. The common provider and six-file inventory
were verified centrally in run 36850953842. The local guard protects the actual
provider pin, package/filename/digest inputs and `always()` evidence retention.
No promotion or package release was repeated.

Only the public label/index job passed in run 36860171883. Its separate existing
Windows installed-launcher job failed with `Missing installed launcher:
molsysviewer` for historical public 0.23.4-py_5. The overall workflow is red,
and no passing Windows-installation claim is made. This is the already-owned
packaging defect uibcdf/molsysviewer#101 / uibcdf/molsyssuite#47. It remains
visible and is not repaired by a registry recheck.

## Integration addendum — 2026-10-01

The published closure above is preserved. The following records the additional
local integration and regression work; no second issue closure was written.

## Local integration follow-up — 2026-10-01

The adopted commits reached `main` while the local candidate gate (#103) and
promotion gate (#134) were still in this working tree. The local branch advanced
from `6f49013c` to `a8aa669c` with automatic preservation of tracked changes;
only the archive index and generated bug index needed conflict resolution.
Both index contents were retained, then queues were regenerated. The preserved
autostash is `d0a4fb2c`; no source work was discarded.

The new tools still imported the deleted local verifier. They now use their
existing channel-independent coordinate/build/MD5/SHA bindings to installed
environment evidence, while the actual independent public-poststate workflows
call the shared provider. There is no restored copy or runtime import of the
deleted script. A subprocess guard imports both the candidate CLI and the
promotion CLI after deletion. #134's staged Windows and matrix checks are
preserved in the integrated promotion workflow.

The bounded suite status inspection preserves both dirty component worktrees.
The full source regression will use the previously tested MolSysMT commit
`ece35e622fc3f26c57f5261088fa07a39f081aca` from its isolated export; current
MolSysMT scientific changes are outside this adoption.

## Executed hosted evidence — 2026-10-01

Existing run `36860171883`, attempt 1, uses adoption commit
`a8aa669c9e3b712f4433511bdf990c5e8df54e30`. Its `Verify public label and
solver-visible index` job succeeds, including the actual pinned provider call
and independent evidence upload. Artifact `11161676599` carries GitHub ZIP
digest `sha256:732e1d16a588166fd6af4ab898f845b1a6edb2a00ec4704f14b11c9f0f9ebe17`.
The downloaded ZIP digest and its run/commit association were checked. Its one
JSON report is `molsyssuite.public-conda@1`, state `verified`, and matches the
expected owner, noarch file, version/build, SHA-256, main label and public index.
This is execution evidence for the adopted shared verification boundary.

The whole workflow concludes failure because its separate Windows launcher
job reproduces #101: `ValueError: Missing installed launcher: molsysviewer`.
That job's installation and exact record verification succeeded first. The
public-file verification success does not certify Windows commands, standalone,
or a new installed scientific pair. #101 remains partial. No dispatch, upload,
promotion or release was performed in this follow-up.

Local evidence: `/tmp/msv-shared-verifier-hosted-20261001.log`,
`/tmp/msv-shared-verifier-hosted-jobs-20261001.json`,
`/tmp/msv-shared-verifier-hosted-receipt-20261001.json` and the native failure
log linked in #101's record. Final focused integration checks pass 114 tests.

## Resolution

Both actual workflows call immutable provider revision
`399d33a4ee0da148571cba7cfc004e3f3a2e71e7`, retain its evidence under
`always()`, and preserve exact noarch filename/SHA inputs. The independent
workflow has no promotion action or mutation credentials. Source adoption
reached `main` in `a8aa669c`; the local follow-up reconciles candidate/promotion
tools with the removed verifier and preserves #134's Windows gate.

The guard `tests/test_verify_public_package.py` checks both actual provider
calls, complete inputs and retained evidence, the independent read-only
boundary, deletion of the old copy, and successful subprocess imports of both
local release CLIs. `tests/test_release_evidence.py` additionally guards the
local installed coordinate/build/MD5/SHA bindings for staging and main, with
ten rejection cases added during this integration.

The 114 focused checks passed; complete source regression passed **2,418 tests
with 20 skips**, exit 0 in 295.06 seconds. Log:
`/tmp/msv-shared-verifier-full-python-20261001.log`. The fixed MolSysMT export
and existing native extension used here are identified in the #134 archived
record; concurrent provider source work was preserved. Ruff, diff and generated
index checks pass. Final archive/metadata guards are checked separately.

Hosted run `36860171883` supplies successful shared-provider and evidence-upload
steps with an independently checked ZIP/report. Its overall failure is the
separate reproduced public Windows defect #101, not a failure of this adoption.
No passing complete public Windows result, installed scientific pair, new
release or promotion is claimed. Public documentation remains deferred.

Final guard/metadata slice: 148 passed, exit 0.

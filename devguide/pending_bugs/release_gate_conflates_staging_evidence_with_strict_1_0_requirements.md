---
summary: Release gate conflates exact staging evidence with strict 1.0 requirements
issue: uibcdf/molsysviewer#103
status: active
opened: 2026-09-25
closed:
severity: medium
verification: reproduced
area: [release, packaging, ci]
guard:
normative:
blocked_by: []
supersedes: []
---

# Release gate conflates exact staging evidence with strict 1.0 requirements

**Reported:** 2026-09-25, during the MolSysMT 0.22.4 / MolSysViewer 0.23.4
release preflight after the exact installed-pair staging matrix passed.

## What

`python devtools/release_gate.py` reports `BLOCKED` for a visible-window Qt
observation that remains genuinely outstanding, but also prints a fixed Conda
dependency-channel blocker despite the exact staged pair passing 20 of 20
platform/interpreter installation cells in Actions run 36121427459. These
different states cannot be read from one undifferentiated release-gate result.

## How

The Conda message is unconditional release-gate prose, not an assessment of
candidate coordinates, immutable artifact digests, or the installed-pair run.
The Qt observation is a separate Phase 7 requirement; complete hosted E2E
certification remains tracked in #100. After the tested 0.23.4 tag, adjust the
gate on `main` to distinguish staging evidence, public-channel publication,
and strict 1.0 observations. A narrowly approved pre-1.0 exception must be
reported as an exception, not converted to a pass.

Add an addressable regression test that rejects missing or mismatched pair
evidence and demonstrates that green staging does not satisfy Qt or hosted
E2E. The reusable staging/promotion policy belongs to
`uibcdf/molsyssuite#27`.

## Why

The release decision must be auditable without weakening the final 1.0 gate.
A stale Conda blocker hides real staging progress; an overly broad pass would
falsely certify visible Qt and hosted E2E.

## What was refuted

The passing 20-cell staging matrix does not close every Phase 10 gate. It
demonstrates installation of the exact candidate pair from staging, not a
visible Qt session, complete hosted E2E, or final public-channel availability.

The later public installed-pair matrix `36129993869` passed 20/20 and does
establish availability of the 0.22.4/0.23.4 pair from `uibcdf`. It still
does not establish the final 1.0 pair or close Qt/E2E observations.

## Resolution

After the 0.23.4 tag, the stale unconditional statement that Phase 10's
dependency channels remain closed was removed. The strict 1.0 gate now says
precisely that it needs a *final-version* pair, while acknowledging that a
pre-1.0 public pair is a separate milestone. A focused gate test guards
against reinstating the old claim. The issue remains active until the Conda
step can assess exact candidate evidence mechanically, report a bounded
pre-1.0 exception separately from a pass, and retain the strict 1.0 check.

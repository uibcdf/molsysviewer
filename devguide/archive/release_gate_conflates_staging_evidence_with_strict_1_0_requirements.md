---
summary: Release gate conflates exact staging evidence with strict 1.0 requirements
issue: uibcdf/molsysviewer#103
status: resolved
opened: 2026-09-25
closed: 2026-10-01
severity: medium
verification: reproduced
area: [release, packaging, ci]
guard: tests/test_release_evidence.py
normative:
blocked_by: []
supersedes: []
---

# Release gate conflates exact staging evidence with strict 1.0 requirements

**Reported:** 2026-09-25, during the MolSysMT 0.22.4 / MolSysViewer 0.23.4
release preflight after the exact installed-pair staging matrix passed.

## What

At the time of the report, `python devtools/release_gate.py` reported `BLOCKED`
for a visible-window Qt observation, while also printing a fixed Conda
dependency-channel blocker despite the exact staged pair passing 20 of 20
platform/interpreter installation cells in Actions run 36121427459. These
different states cannot be read from one undifferentiated release-gate result.

## How

The Conda message is unconditional release-gate prose, not an assessment of
candidate coordinates, immutable artifact digests, or the installed-pair run.
The Qt observation is a separate Phase 7 host requirement. The 2026-09-28
scope decision made standalone experimental for 1.0 and removed Qt from the
strict gate. Hosted **core** browser E2E remains a 1.0 requirement; remote-only scenarios were moved to post-1.0
under #100 on 2026-09-26. After the tested 0.23.4 tag, adjust the
gate on `main` to distinguish staging evidence, public-channel publication,
and strict 1.0 observations. A narrowly approved pre-1.0 exception must be
reported as an exception, not converted to a pass.

Add an addressable regression test that rejects missing or mismatched pair
evidence and demonstrates that green staging does not satisfy hosted core
E2E or final 1.0 artifact verification. The reusable staging/promotion policy belongs to
`uibcdf/molsyssuite#27`.

## Why

The release decision must be auditable without weakening the final 1.0 gate.
A stale Conda blocker hides real staging progress; an overly broad pass would
falsely certify hosted core E2E.

## What was refuted

The passing 20-cell staging matrix does not close every Phase 10 gate. It
demonstrates installation of the exact candidate pair from staging, not a
visible Qt session, complete hosted E2E, or final public-channel availability.
The Qt observation remained outstanding but was later removed from the 1.0
release gate because the host is experimental.

The later public installed-pair matrix `36129993869` passed 20/20 and does
establish availability of the 0.22.4/0.23.4 pair from `uibcdf`. It still
does not establish the final 1.0 pair or close core E2E observations.

## Resolution

After the 0.23.4 tag, the stale unconditional statement that Phase 10's
dependency channels remain closed was removed. The strict 1.0 gate now says
precisely that it needs a *final-version* pair, while acknowledging that a
pre-1.0 public pair is a separate milestone. A focused gate test guards
against reinstating the old claim. At that checkpoint the issue remained
active until the Conda step could assess exact candidate evidence mechanically,
report a bounded pre-1.0 exception separately from a pass, and retain the strict
1.0 check. The implementation and verification below close that remaining work.

### Implementation — 2026-10-01

The local consumer profile now checks a reviewed candidate declaration against
a clean exact Viewer checkout/package version, the selected GitHub run attempts,
the complete four-platform Python 3.11–3.14 pair matrix and each actual installed
environment artifact. GitHub ZIP digests and run/attempt association are checked;
installed URL/MD5 identities are bound to the expected file SHA-256 through
consistent release and solver-visible channel records. Staging, public pair and
hosted core E2E are separate checks. Missing/expired evidence blocks; invalid
or contradictory evidence fails. Remote-only success cannot replace core E2E.

Pre-1.0 declarations are reported as EXCEPTION with nonzero exit, never PASS;
strict 1.0 rejects them. Unknown/duplicate step selections no longer produce an
empty successful gate. The local schema and operator contract are in
[release_gate_evidence.md](../release_gate_evidence.md); shared schema ownership
remains `uibcdf/molsyssuite#27` and publication workflows are unchanged.

Final validation passes **56 focused tests** and **2,370 complete Python tests,
20 skipped**, exit 0 in 311.70 seconds. The complete run was executed once for
this implementation task, after focused checks and all mutations restored the
exact original sources. It also closes the preceding test-import regression
evidence gap. MolSysMT remained clean at
`ece35e622fc3f26c57f5261088fa07a39f081aca` before and after; no provider file or
dependency floor changed. These are development-checkout tests, not final
candidate or published compatible Interactions qualification. TS/runtime product
sources are unchanged by this task; previous JS/core/performance evidence was
not rerun for the Python development-tool change.

The module guard drives positive cached GitHub/registry/archive snapshots
through the actual reader and independent negative checks. Eighteen guard
mutations are rejected: checkout commit/cleanliness, package version, run
commit, matrix coverage, scientific step execution, channel SHA-256/MD5,
installed digest, archive digest/run/attempt, hosted core execution, strict-mode
and exception boundaries, contradictory evidence under an exception, exception
exit status and empty selection. Exact source bytes and original timestamps
are restored after each experiment. These assertions protect the original
failure mechanism: a stale message or unrelated green run cannot qualify the
declared artifacts, and staging cannot satisfy the other release steps.

A real historical public environment artifact also passes archive digest,
run association, coordinate and live registry/index checks: run `36129993869`,
attempt 1, artifact `10861931707`. The historical five-platform release is not
reused as current-candidate clearance. A real CLI invocation with no candidate
evidence returns 2, reporting conda/public_conda/hosted_e2e as independently
BLOCKED. This resolution closes the checker defect; it does not clear the
current dirty working tree, freeze a candidate or publish anything.

Logs: `/tmp/msv-release-gate-final-specific-20261001.log`,
`/tmp/msv-release-gate-mutations-20261001.log`,
`/tmp/msv-release-gate-full-python-20261001.log`,
`/tmp/msv-release-real-probe-20261001.log`,
`/tmp/msv-release-pair-receptor-20261001.log`,
`/tmp/msv-release-gate-missing-evidence-20261001.log`.

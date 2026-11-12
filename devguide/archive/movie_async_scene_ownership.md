---
summary: Async Movie entry rejects transient scene ownership in a real kernel.
issue: uibcdf/molsysviewer#365
status: resolved
opened: 2026-11-12
closed: 2026-11-12
severity: high
verification: reproduced
area: [movie, jupyter, concurrency, studio]
guard: tests/test_movie_async_ownership.py
normative:
blocked_by: []
supersedes: []
---

# Movie async scene ownership

**Resolved in source — 2026-11-12.** Final actual-Jupyter `614`, 549 broader
Python passes and six native Movie entries in `615` receive the correction;
hosted, installed, Qt and human scope remains separate in the linked receipt.

Actual Jupyter attempts `600` and `601` retain failure after partial Movie
authoring. `600` waits after detached Pause; `601` records a rejected seek,
unchanged frame zero and the valid recipe's frame-two key. Seven deterministic
controls in `tests/test_movie_async_ownership.py` fail before the correction
(`602`). All runs preserve inputs and retire their owned processes.

The public async entry tries a nonblocking scene lock before the existing
awaitable owner can wait. A comm callback on another registered kernel thread
can still own that lock. The ArgDigest adapter already releases its entry
guard before awaiting the coroutine; holding a lock across that await is not
the diagnosis. State's two asynchronous save owners already have a precise
entry exception for their owned phases.

Use the same explicit boundary for the seven Movie async methods, keep
synchronous scene and pending-edit refusal, and receive capture/rebase commit
and export-preparation ownership. Preserve all original deadlines and failures.
Acceptance requires both deterministic thread controls and the complete real
notebook/popup authoring, preview, export, session and close/late-reply path.
This defect is part of #320; it is distinct from #361's native-reset observation.

The initial entry correction passes eight controls in `603`. `604` still
retains an unresolved GUI wait: its command had no correlated result. This is
not established evidence of a blocked Python computation or a kernel-thread
deadlock. The diagnostic `605` completes all eight notebook phases, but that
passing attempt alone does not erase the earlier failure.

The missing admission is independently reproduced in `606`: three deferred
intention controls fail while the eight entry/guard cases pass. The correction
uses the existing unlock continuation for the closed set of live/control
Movie intents and revalidates their epoch/endpoint/job after admission. `607`
passes all eleven controls. `608` additionally receives bounded final commits,
expired observations with no late mutation, stale encoder preparation with an
intact destination, and required actual-host CI registration (17 passes).
The full notebook then passes in `609`. #366 adds the separately reproduced
cross-loop completion/runtime projection boundary; the final shared receiving
is recorded in [the notebook receipt](../movie_jupyter_receiving_20261112.json).

Evidence uses source `7dd79c53`, frozen MolSysMT `aee7aa65`, PyUnitWizard
`9bb4f5fa`, the canonical native backend and independently checked kernel
origins. It does not qualify installed packages, hosted CI, native Qt or
postponed human use. Raw diagnostics remain in private ignored receiving
directories; only bounded summaries belong in published receipts.

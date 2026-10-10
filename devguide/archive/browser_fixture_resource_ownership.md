---
summary: Browser export fixtures retain unowned temporary directories after verification
issue: uibcdf/molsysviewer#229
status: resolved
opened: 2026-10-10
closed: 2026-10-10
severity: medium
verification: reproduced
area: ['tests', 'resources']
guard: tests/test_browser_fixture_resources.py
normative:
blocked_by: []
supersedes: []
---

# Browser export fixtures retain unowned temporary directories after verification

**Reported:** 2026-10-10 during the authorized integrated resource-owner review, uibcdf/molsysviewer#200 and uibcdf/molsyssuite#104.

## What

Colour, framing, artifact and controls export fixtures create temporary directories without any owner removing them after browser verification.

## How

The suite/runner owns a managed workspace and propagates TMPDIR/TMP/TEMP to subprocesses. Removal follows child exit and browser/server close on success or failure.

## Why

This affects applicable development or public export/preview operations. Caller-owned outputs and retained scientific evidence must survive cleanup.

## What was refuted

A managed scratch lifetime does not authorize deleting caller output, unrelated historical directories, package files or another session's evidence. Initial diagnosis is source inspection; executed verification is recorded at closure.

## Integration diagnosis

The existing Canvas-controls guard resolver pinned `run().catch(...)`. The
managed entrypoint retains failing catch/exit behavior but becomes
`withFixtureWorkspace("controls-visibility", run).catch(...)`; the first global
run detected the stale exact-string requirement. Its bounded resolver now checks
the exact managed entrypoint, helper import/file and unchanged build/core lane.
No other browser selector or exemption is admitted.

## Resolution

The real Node guard passes for success and failure, preserves the operation's
error/return value and caller evidence, and verifies scratch absence. All three
affected Chromium suites pass, with actual artifact draw/geometry assertions.
The bounded reporting resolver is updated without adding selectors or exemptions; final scoped policy validation and core-browser outcomes are retained in the review receipt.

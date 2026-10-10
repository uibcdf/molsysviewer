---
summary: Preview server can deadlock when interrupted with Ctrl-C
issue: uibcdf/molsysviewer#230
status: resolved
opened: 2026-10-10
closed: 2026-10-10
severity: medium
verification: reproduced
area: ['preview', 'resources']
guard: tests/test_preview_server.py::test_blocking_preview_exits_on_interrupt_and_preserves_caller_directory
normative:
blocked_by: []
supersedes: []
---

# Preview server can deadlock when interrupted with Ctrl-C

**Reported:** 2026-10-10 during the authorized integrated resource-owner review, uibcdf/molsysviewer#200 and uibcdf/molsyssuite#104.

## What

The blocking preview calls shutdown from the same thread after serve_forever exits, so its documented Ctrl-C path can deadlock.

## How

Close the socket after the serving loop exits; reserve shutdown for callers stopping the nonblocking server from another thread.

## Why

This affects applicable development or public export/preview operations. Caller-owned outputs and retained scientific evidence must survive cleanup.

## What was refuted

A managed scratch lifetime does not authorize deleting caller output, unrelated historical directories, package files or another session's evidence. Initial diagnosis is source inspection; executed verification is recorded at closure.

## Resolution

The actual blocking server serves the caller HTML, returns after SIGINT with exit 0, refuses connections on its released port and preserves the caller directory. All eight preview guards pass.

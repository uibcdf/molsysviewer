---
summary: A provider panel close error prevents remaining View resources from closing.
issue: uibcdf/molsysviewer#318
status: active
opened: 2026-11-06
closed:
severity: medium
verification: reproduced
area: [lifecycle, addons, resources]
guard:
normative:
blocked_by: []
supersedes: []
---

# Failed close and independent resource cleanup

**A6 — reproduced; correction pending; P2.** Viewer owns #318 under #315 for
the covering artifact and accepted 1.0 scope. The next gate is failure-tolerant
cleanup with actual provider panels, transports and retained registry evidence.
No scientific provider modification is required.

## Observation and duplicate review

At `e3cf77e0`, a registered real `AddonPanelWidget` subclass raises a controlled
`OSError` from its own `close()`. A real bundled dialanine View mounts one
provider widget in the embedded host and a second at a registered canvas
endpoint. This exercises a failing extension; ordinary closes are not claimed
to fail.

`MolSysView.close()` has already marked the View closed when panel cleanup
raises. The six owned widgets/layouts remain registered, one other panel stays
mounted, and both panels retain their View references. Calling `close()` again
returns without releasing them. The reproduction explicitly releases its own
resources afterward; test teardown is not its success criterion.

The complete duplicate review acquired four pages / 316 records, including
closed issues. #245 covers independent window ownership; #316 covers failed
factory initialization. Neither protects independent cleanup after this error.
The controlled reproduction and full traceback are retained as
`A6-repro.py` and `A6-repro-result.json` in the private execution evidence.

## Required behavior and acceptance

Attempt independent owned cleanup despite a provider, callback or transport
error. Keep failures observable, release callback/transfer/widget/layout
ownership independently, and define retry/idempotence explicitly. A retired
View must not accept new work while cleanup is incomplete.

Use real molecular Views and actual provider widgets, including independent
endpoint panels. Verify registry ownership before global teardown, unchanged
scientific data and an unrelated live View. Exercise both a partial failing
close and a repeated close. Do not silently discard errors or bypass the
provider's resource contract to manufacture a successful close.

Python source receiving, applicable hosted CI, installed artifacts and
postponed visible-host observations retain separate scopes. Both 1.0
publications and candidate/tag/package actions remain paused.

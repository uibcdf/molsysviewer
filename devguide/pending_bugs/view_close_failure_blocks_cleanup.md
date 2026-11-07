---
summary: A provider panel close error prevents remaining View resources from closing.
issue: uibcdf/molsysviewer#318
status: partial
opened: 2026-11-06
closed:
severity: medium
verification: reproduced
area: [lifecycle, addons, resources]
guard: tests/test_view_close_failure.py
normative:
blocked_by: []
supersedes: []
---

# Failed close and independent resource cleanup

**A6 — corrected and source-verified; delivery/hosted checkpoint pending; P2.** Viewer owns #318 under #315 for
the covering artifact and accepted 1.0 scope. The next gate is reviewed source
delivery and the applicable consolidated hosted checkpoint. Provider panels,
transports and registry ownership have directed source receiving below.
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

## Correction and current evidence

Closing retires the View immediately, detaches panel ownership, and attempts
independent cleanup actions. One error is re-raised with its original cause;
multiple errors remain observable as an exception group. Only failed actions
remain for a later `close()`. Successfully released resources and callbacks are
not repeated; reentrant close is safe. Pending provider cleanup receives its
retired View context only while executing, without remounting the panel or
accepting new frontend work. This preserves a provider's ability to retry its
own teardown while dropping inactive panel links between attempts.

The guard first reproduces the original failed close. It also catches the
initial retry prototype losing the provider context and a late inbound click
after failed transport detachment. The final source guards widget/layout
registry ownership, two endpoint panels, exact transfer release, an unchanged
independent View, retries, multiple errors, interruption, reentrancy and
unpresented result siblings.

Seven directed cases pass. The earlier isolated lifecycle/runtime/popup
selection passes 225 cases with one explicit legacy-entry-point skip before
the last retry-context refinement. The final combined source passes **469
cases, one legacy skip**, plus its affected actual-browser entry and canonical
JavaScript unit entry. These scopes overlap. The
[A6 receipt](../view_close_failure_receiving_20261106.json) and
[combined receipt](../robustness_combined_source_receiving_20261106.json) retain
hashes, native outcomes, warnings and the exact scope boundaries.

A resource whose provider keeps failing is not forcibly bypassed or claimed
released. Keep the retired View, correct that cause and retry. `closed=True`
identifies retirement even if cleanup raised; it is not proof that a failing
external resource was freed. Applicable consolidated hosted receiving and
postponed human/visible-host acceptance remain separate. Incremental source
delivery uses the maintainer's explicit `[skip ci]` instruction.

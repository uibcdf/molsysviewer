---
summary: Standalone HTML construction retains internally created Views and widget registrations.
issue: uibcdf/molsysviewer#324
status: resolved
opened: 2026-11-07
closed: 2026-11-16
severity: medium
verification: reproduced
area: [standalone, lifecycle, export]
guard: tests/test_standalone_view_ownership.py
normative:
blocked_by: []
supersedes: []
---

# Standalone HTML ownership

## Source resolution — consolidated receiving, 2026-11-16

HTML builders close internally owned Views on return or error and preserve borrowed Views. Windows guards compare native exceptions rather than assuming a Unix exception subtype; actual Windows JUnit now receives those corrected controls.

The complete source checkpoint
[43748320908](https://github.com/uibcdf/molsysviewer/actions/runs/43748320908)
receives MolSysViewer `3aff1d48a5a38fb9854efe2c95a9a8f35cadbccb` and
MolSysMT `bc5a9297a762d451742734f9e11c7f54c6a832a0`. The durable guard
is `tests/test_standalone_view_ownership.py`.
Its containing module passes **17 cases on each of Linux, macOS arm64
and Windows**, without failures, errors or skips. The [closing receipt](../molstar_closeout_three_blocks_20261115.json)
checks original JUnit ZIP digests and native selected cases; the complete
checkpoint also receives all 25 notebooks.

This supplies the formerly pending consolidated **source** prerequisite.
Earlier causal runs, interrupted/failed receiving and dated pending claims
remain below with their original inputs. Installed artifacts, final producers,
experimental native Qt and postponed human acceptance retain their own owners
and gates under #315/#372; this closure does not declare them passed or
advance the original 40/46 source or 1/46 final-acceptance counters.

## Earlier investigation — original claims and scopes retained


**Corrected, locally verified and delivered in `ebe3d46b`; consolidated
acceptance remains pending.** Repeated real HTML construction with
`None` or a native MolSys retains one unreturned View and two widget/comm
registrations per call. Four calls in each fresh-process control leave four
Views and eight registrations after collection. A borrowed View remains at its
original baseline. Closing only the internally created Views restores the
baseline, identifying an ownership failure rather than a global cleanup need.

The writer now releases a View it creates, on successful export and on error.
Caller-supplied Views retain their exact data, scene, callbacks and comms.
The demo gallery and CLI also release fresh Views obtained from DemoCatalog;
the nested HTML writer borrows those objects. Cleanup must preserve the
original writer/load error, adding a diagnostic note if cleanup also fails;
a cleanup-only failure remains observable. Already written files and unrelated
caller output are preserved.

The durable guard uses real demo systems, actual widget and comm registries,
filesystem/load failures, the default gallery, CLI and a real failing close
callback. Assertions occur before pytest's autouse cleanup, without forced
collection or a registry sweep. Its initial causal run fails four owned cases
while two borrowed controls pass. The corrected module passes **17 cases**;
the existing factory and selected HTML/CLI boundary checks pass **24 cases**.
These counts describe separate recorded selections, not overall plan progress.

Reusing the unchanged original probe in three fresh processes confirms zero
retained internally owned Views and unchanged registration baselines after all
four builds for empty, MolSys and borrowed inputs. Original red observations
remain in approved private custody. The
[sanitized receiving record](../standalone_html_ownership_receiving_20261107.json)
preserves the source/guard hashes, causal results and scope limits. This is
Python ownership evidence, not browser, visible Qt,
installed-package or final candidate qualification.

## Hosted portability follow-up — 2026-11-07

The exact-source Python 3.14 campaign `42348065524` retains its native failure.
Windows exposes five test portability errors: four directory writes raise
`PermissionError` rather than Unix's `IsADirectoryError`, and one assertion
compares an unescaped path with the exception's repr-formatted message.
The ownership mechanism is unchanged. The corrected guards compare native
control exception types, error codes, arguments and filenames, retaining
the original writer error and every resource/data-preservation assertion.
The affected six-module selection passes 66 cases locally; actual Windows
receiving remains pending. See the [hosted checkpoint](../robustness_hosted_checkpoint_20261107.json).

Related #316 concerns initialization failure in `new_view`; #318 concerns a
failed close blocking other cleanup. Neither alone covers this writer's
successful-return lifetime. This follow-up belongs to the A4/A6 boundary of
#315 and does not silently change its original 46-item denominator.

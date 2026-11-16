---
summary: Trajectory plot pixel dimensions are digested as CSS and fail in the public API.
issue: uibcdf/molsysviewer#322
status: resolved
opened: 2026-11-07
closed: 2026-11-16
severity: medium
verification: reproduced
area: [public-api, trajectory-plot, argdigest]
guard: tests/test_trajectory_plot.py
normative:
blocked_by: []
supersedes: []
---

# Pixel dimensions of trajectory plot cards

## Source resolution — consolidated receiving, 2026-11-16

Caller-specific digestion preserves positive integer pixels while rejecting invalid values before retained cards change. The public fixture still requests width 650, and CSS/physical-width domains retain their own tests.

The complete source checkpoint
[43748320908](https://github.com/uibcdf/molsysviewer/actions/runs/43748320908)
receives MolSysViewer `3aff1d48a5a38fb9854efe2c95a9a8f35cadbccb` and
MolSysMT `bc5a9297a762d451742734f9e11c7f54c6a832a0`. The durable guard
is `tests/test_trajectory_plot.py`.
Its containing module passes **34 cases on each of Linux, macOS arm64
and Windows**, without failures, errors or skips. The same complete browser entry also receives the public pixel dimensions. The [closing receipt](../molstar_closeout_three_blocks_20261115.json)
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
acceptance pending.** The #321 precision
fixture exposed a different public-API defect before numerical assertions:
`show(..., width=650)` reaches `int('650px')` and raises ValueError. The same
CSS conversion applies to height. The fixture's preceding explicit `clear()`
explains its empty records; the calculation was not successfully displayed.

The show/update signature declares optional integer pixel dimensions. The
generic digesters also serve CSS embedding and physical molecular widths.
Their caller-specific branches must distinguish those domains. Plot dimensions
must remain positive integer pixels without disabling ArgDigest, changing the
CSS/physical contract or introducing a frontend workaround.

Actual reproduction uses the routine Python 3.14 interpreter, real pentalanine
with local structures `[0, 8, 3]`, the recorded controlled MolSysMT/PyUnitWizard
providers and the real public API. Its independent native traceback is retained
with #321's private receiving evidence. A fresh complete live inventory contains
320 issue/PR records across four pages before opening #322. Closed #143
concerns plot lifecycle, closed #150 numeric axes, and open #321 precision;
none records this dimension-digestion boundary.

Public guards cover show/update, both dimensions, actual records and state
save/reopen, plus rejection of zero, negative, boolean, fractional, CSS and
nonfinite inputs before replacing a retained card. Existing CSS embedding,
Qt window dimensions and physical-width tests must remain applicable. The
actual browser precision fixture keeps its requested width rather than
omitting the broken argument; it now surfaces backend errors before inspecting
records. Fixed-source/browser receiving and normal closeout remain pending.

The first new pytest attempt failed at collection because the test incorrectly
imported a module-level `load_state`. The corrected guard uses the real public
`view.load_state` and `trajectory_plot.records` methods. That driver failure is
retained separately and is not product reproduction or fixed-code evidence.

The corrected public guard reproduces 18 failures with eight passing controls.
Caller-specific pixel digestion now retains positive integers; all **34** plot
module cases pass in 11.70 s, including both aliases, invalid-input atomicity
and actual state-file recovery. This is scoped source evidence. CSS embedding,
physical-width/native-window checks and actual browser receiving of the same
requested dimensions remain pending; #322 stays open.

The affected combined source selection subsequently passes **146/146**, with
four native-window cases explicitly deselected. It includes CSS embedding,
physical shape digesters and ordinary standalone controls. The full actual
trajectory browser entry also passes with the original requested width 650,
including state-file recovery and canvas-popup geometry/frame checks. These
scopes are recorded in the [shared receipt](../trajectory_plot_precision_receiving_20261107.json).
Reviewed integration, consolidated acceptance and closeout remain pending.

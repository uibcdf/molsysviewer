---
summary: Trajectory plot pixel dimensions are digested as CSS and fail in the public API.
issue: uibcdf/molsysviewer#322
status: partial
opened: 2026-11-07
closed:
severity: medium
verification: reproduced
area: [public-api, trajectory-plot, argdigest]
guard: tests/test_trajectory_plot.py
normative:
blocked_by: []
supersedes: []
---

# Pixel dimensions of trajectory plot cards

**Reproduced; correction and receiving in progress.** The #321 precision
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

---
summary: Observe plot authority replies through the delivered widget stream.
issue: uibcdf/molsysviewer#391
status: partial
opened: 2026-11-14
closed:
severity: medium
verification: reproduced
area: [testing, plots, jupyter, synchronization]
guard: molsysviewer/js/tests/e2e/trajectory-plot.e2e.ts
normative:
blocked_by: []
supersedes: []
---

# Plot authority inspection — receiving correction in progress

Source run [43646263694](https://github.com/uibcdf/molsysviewer/actions/runs/43646263694)
fails in the first authority inspection of core entry 54, `trajectory-plot`,
on MolSysViewer `eae573467c71e14b7f8e7216ca71d7e6b9b562c2` and scientific
provider `aee7aa65da56e896d1cb2d655bf73736f6453a43`. The preceding 53 core
entries, all 25 notebooks and the three Python source-host steps pass. The
complete core result remains failed; its prefix does not qualify the plot or
the remaining Movie entries.

`mountCanvasPopupFixture` installs the bridge's widget-message receiver.
`PythonFixtureBridge` delivers synchronous replies through that receiver,
empties the response message list and resolves after delivery. The old plot
inspector searches that consumed list and reports no current-state observation
before reaching any navigation assertion. This establishes a test receiving
defect, not missing scientific state or a rendering failure.

The correction observes the source widget's actual `msg:custom` delivery with
a request-scoped listener. It retains one state observation, requires exactly
one delivery and removes its listener in `finally`. The bridge and production
runtime remain unchanged; no packet is replayed. The original Python, SVG,
coordinate, callback, precision/Decimal, popup and static-independence assertions
and deadlines remain applicable. Both authority and precision inspections use
the owning source widget.

Receive the complete `trajectory-plot.e2e.ts` guard, then the required complete
current core lane. Keep #314's product intent routing and #321/#322's precision
and dimensions separate: this failure occurs before those assertions. Source
receiving, installed artifacts and postponed human acceptance remain distinct.

**Scoped receiving — 2026-11-14:** profile `plot-stream-source-836` passes
the complete plot entry, including the 15 Decimal/binary64 controls, actual
Python callbacks and coordinates, state files, source/canvas/card popups and
independent static HTML. The unchanged-input supervisor exits zero in 124.04
seconds, with no resource stop or surviving owned processes. The
[followup receipt](../molstar_qualification_followup_20261114.json) retains
source/native hashes and the earlier local npm-launcher setup failure.
Complete current core receiving remains required; this scoped result does
not turn the original hosted run green.

**Covering source receiving is terminal failure:** [43654425383](https://github.com/uibcdf/molsysviewer/actions/runs/43654425383)
on `2947c2fd` passes 4,732 Python cases with 42 explicit skips and all 25
notebooks. The previous reply-inspector assertion passes, followed by genuine
Python/source/popup navigation. Entry 54 then times out after 30 seconds while
waiting for the independent exported static page's controller. That is a later
phase, not evidence that the consumed-reply correction failed. The original
static console/bootstrap state was not archived; the cause remains unknown.
The [terminal receipt](../source_core_terminal_receiving_20261114.json)
retains both original ZIPs with verified GitHub hashes and the complete log.
Keep #391 partial while receiving the static bootstrap and complete current
core gate. The 53-entry prefix and local nine-Movie suffix are not that gate;
no deadline change or duplicate dispatch is justified by this observation.

**Diagnostic receiving implemented:** retain a bounded snapshot of the independent
page's console/page/network failures and explicit bootstrap state before its
owner retires it. Keep the original 30-second ready deadline and positive
Python/geometry/static assertions. A second real export deliberately names an
unavailable local runtime; receive its native file-load error and visible
failure through the same observer, before page closure. That is a receiver
control, not a reproduction or explanation of the older hosted failure.

The [diagnostic receipt](../static_bootstrap_diagnostic_receiving_20261114.json)
receives the complete entry in profile `860`, including the actual unavailable
runtime control, all original scientific/independent static assertions and
15 precision controls. The initial new negative-control expectation fails in
`857`; directed probe `858` identifies native CORS refusal (`ERR_FAILED`), not
a missing-file error. That receiver expectation is corrected without changing
the product, original deadline or asserted successful outcomes. All 22 owned
processes retire; scoped receiving does not explain or clear the hosted failure.

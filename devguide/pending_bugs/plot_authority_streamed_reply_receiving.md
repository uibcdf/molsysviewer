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

---
summary: Present independent addon result Views in Jupyter and Qt.
issue: uibcdf/molsysviewer#301
status: partial
opened: 2026-11-05
closed:
verification: reproduced
area: [addons, jupyter, standalone]
guard: tests/test_view_presentations.py
normative: docs/content/developer/addons.md
blocked_by: []
supersedes: []
---

# Independent result View presentation

## What

The maintainer approves an explicit destination after calculation: Show in
notebook or Open in new window in Jupyter; a new native window in Qt. Native
addon extraction/copy keeps returning molecular data. `view.extract` returns a
View with its existing scene-transfer semantics. No scientific wrapper displays
implicitly. Publication and tags remain paused.

## How

Viewer owns a per-source presentation service at
`view.addons.manager.presentations`. `prepare(initializer, title=...)` constructs
the correct host transport, initializes it without displaying and returns a
handle. `get(handle)` recovers the independent View. `records()` reports live
presentation metadata; `close(handle)` releases it. Providers discard unused
prepared Views when their panel unmounts. Presented Views outlive source-panel
navigation and source closure; they still depend on their kernel/application.

The notebook display surface contains the source canvas and independent results
below it. External results reuse their own View's authenticated canvas-popup
transport, with an offscreen, explicitly sized authority. The fresh destination
click reserves the browser window. Actual browser completion is acknowledged;
failure keeps the prepared View available for retry without recalculation.
Qt reuses QApplication and creates a new transported window without `exec()`.

## Why

An invisible Python View is not a successful presentation. In particular,
fullscreen, canvas-popup and detached-Studio workflows need an explicit visible
destination. The first consumer is MolSysMT Extract subset / Copy system in
uibcdf/molsysmt#421 and PR #543. Viewer owns this reusable host boundary.

## What was refuted

The ordinary canvas popup mirrors one existing View; it cannot itself create an
independent molecular result. Tabs do not release hidden molecular arrays and
add a session-management layer. Calling display() inside a generic addon does
not qualify remote notebook output or native Qt windows. The initial source
probe confirmed that ordinary new_view(native_result) makes another independent
coordinate copy; no zero-copy or large-trajectory RAM bound is promised here.

## Validation

Source implementation passes 359 host boundary cases (including the eight
presentation ownership cases), 44 public API checks, the JavaScript unit lane
and the separate nine-case ownership run with real native Qt windows. These
are overlapping scopes, not an additive scientific case count. The addon System
file passes 47 cases on its recorded native e614ba367 basis. The public API
inventory deliberately increases from 732 to 736 digested callables and 446 to
448 digesters, without missing digesters or undigested functions.

Actual Jupyter/ipykernel/AnyWidget comms and real Mol* pass the existing six-step
removal/popup receiving and the result scenario: ordered extraction,
notebook output, an independent window, opening/closing from detached Studio,
Python recovery and source-close independence. The known JupyterLab debugger
error also occurs in a plain-notebook control and is retained separately; no new
page-error fingerprint is accepted. A first result-window attempt exposed the
AnyWidget outer/inner element distinction; the host now waits for the actual
inner presentation/canvas entrypoint before opening it. The result is retained
on failure.

The destination refinement also reuses one View through rapid window/notebook
cycles, isolates delivery/acknowledgements by rendered output, makes closing a
handle idempotent and reports when notebook delivery is hidden by fullscreen.
Runtime bootstrap caching compares the served bundle digest and binds popup
source to the resolved module's own source; a stale tab cache is not silently
reused for a new presentation entrypoint. Final targeted receiving follows
these refinements rather than inheriting an earlier runtime's verdict.

Final receiving on code commit `42234de8` passes the seven-step result browser
guard and nine presentation/native-window ownership cases. The
[receiving record](../independent_view_presentation_receiving_20261105.json)
retains exact source hashes, earlier scopes, the repaired test-harness failures,
the plain Jupyter control diagnostic and the native ed09f6453 receiving basis.
The CI receptor reports run 42168035122 pending with eight queued test jobs;
there is no hosted passing claim. The owner contribution now pins this exact
Viewer code, with scientific returns unchanged. Owner #583/#584 repairs are
received and the duplicate consumer reports archived rather than left open.

Hosted exact-head CI and owner integration remain in progress;
visible human Jupyter/Qt review is still explicitly postponed. Native offscreen
window ownership does not certify rendered Qt/GPU behavior.
Unrelated human scratch files and all sibling worktrees are preserved. The suite
state refresh reports missing PeptideMT and unrelated ahead/behind/dirty clones;
none is merged or installed for this work.

## Source CI correction and Geometry receiving — 2026-11-06

Old run 42168035122 failed the same three assertions on all four Linux minors:
a stale capability audit, direct access to a private popup window, and the
obsolete mocked MIME expectation. The audit is regenerated, window reuse stays
inside its manager, and real-widget representation/cleanup replaces the obsolete
expectation. The complete qualified local core selection passes 3,464 cases
with 21 justified skips and 15 deselected Qt-runtime cases. The initial sandbox
full run and all original hosted failures are retained as failed observations.

The shared consumer now adds Geometry / Translate, with explicit units, structures
and update/result effects. All three actual-Jupyter scenarios pass (20 browser
checks) alongside 83 System/Geometry, 142 overlapping geometry/native-transform
and 36 distribution/smoke controls. #302/#303 close their host source defects;
owner integration, hosted exact-head, human and installed gates stay separate.
The [receiving record](../molsysmt_geometry_receiving_20261106.json) keeps exact
source hashes, complete outcomes, initial failures and the plain Jupyter control.

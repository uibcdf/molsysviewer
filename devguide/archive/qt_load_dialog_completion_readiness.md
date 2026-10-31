---
summary: Observe readiness and completion of native Qt file-dialog actions in CI
issue: uibcdf/molsysviewer#287
status: resolved
opened: 2026-10-30
closed: 2026-10-31
verification: reproduced
severity: medium
area: [qt, tests, loading]
guard: tests/test_qt_live_workbench.py::test_qt_live_workbench_full_render_gpu
normative: devguide/studio_interaction_contract.md
blocked_by: []
supersedes: []
---

# Qt Load dialog completion receiving

Hosted Qt run 41144414471 on Viewer 191419cc times out at the second
QFileDialog.getOpenFileNames call. Cancellation completed; the accept path stays
inside the modal dialog until the 180-second child limit. The original qt-render
JUnit preserves the full faulthandler stack, which console rendering truncates.
The first local Xvfb/SwiftShader control passes 1/1 in 37.82 s; prior native
Wayland receiving remains valid within its scope. The hosted failure is not
reproduced deterministically locally and is not attributed to molecular loading.

The current helper calls selectFile and immediately clicks Open when it first
sees any QFileDialog. It records the requested action as answered immediately
after that click, without observing dialog completion. It does not check the
expected title, exposure, target visibility/size or actual selected filename
before accepting. Investigate these timing/identity boundaries; do not call a
hypothesis proven merely because a local control passed.

Use real input once the intended widget and selection are ready, observe its
finished result, and retain bounded diagnostics/cleanup if it does not complete.
Do not add acceptance retries, hidden DOM activation or larger global timeouts.
Qualify the exact corrected source under hosted Xvfb and native Wayland; retain
source/general Pandas4Warning failures under MolSysMT#431 independently. No tag,
package, release or new Qt admission is authorized.

## Local correction receiving — 2026-10-30

The corrected helper binds only the expected visible dialog, selects the file
once, waits for exposure, enabled/nonzero button geometry and the requested
filename, then issues exactly one real mouse click. It observes finished codes
and checks rejected/accepted outcomes. A bounded observer records pending/modal
state and rejects only to clean up an already failed test. Acceptance is not
retried. Diagnostics are now included in the hosted artifact. The full local
Xvfb/SwiftShader guard passes 1/1 in 36.38 seconds; eight workflow checks pass.
The nondeterministic hosted root cause remains unproven until exact-source
qualification; this correction removes the test's unobserved-completion claim.

The same corrected full guard also passes natively on Wayland in 30.74 seconds,
with exactly two clicks and actual finished codes 0/1. This is additional local
receiving, not a substitute for the pending hosted qualification.

## Hosted selection counterexample — 2026-10-31

Run 41148560185 on 132b408c fails within the bounded dialog observer, without
the old 180-second hang. Its preserved diagnostics show Cancel returning 0,
then an accept dialog with no selected files and no attempted Open click.
Therefore selectFile() did not establish the assumed selection in that hosted
case. The exact reason for its nonapplication is not claimed. Local baseline
controls do not reproduce it reliably. Failure cleanup also revealed duplicate
rejection of the same modal; cleanup now excludes the owner from child rejection.

The helper now verifies that the fixture exists, focuses the real filename
editor and types the path with QTest, then observes selectedFiles and the actual
finished code. It still clicks only once, never uses synthetic DOM activation
or acceptance retries, and preserves diagnostics. This matches the user flow
more closely than a programmatic selectFile assumption. The corrected local
Xvfb/SwiftShader full guard passes 1/1 in 38.39 seconds. Native and exact-hosted
receiving remain due for this revision.

The typed native guard also passes on Wayland, 1/1 in 32.74 seconds. For this
guard-only iteration, the authorized internal checkpoint route uses a skipped
interim commit and a single exact-source Qt workflow_dispatch. The Viewer
runtime/scientific code is unchanged from 191419cc; the existing full/source
CI backlog is retained, not cleared or represented as passing. Scoped Ruff,
record and workflow checks remain due. This is not release qualification.

## Exact-source qualification in progress

A single workflow_dispatch, 41149452645, targets exactly
62508cfd54b1899d06a8d98c4ad12521f8d1feca with staging disabled. No duplicate
dispatch was created. The maintainer explicitly defers the Jupyter/Qt visual
smoke until later; no human acceptance is inferred from automated results.

## Resolution — 2026-10-31 UTC

Exact-source hosted run 41149452645 succeeds on
62508cfd54b1899d06a8d98c4ad12521f8d1feca. All required steps pass. Its original
JUnit files contain 1 window, 2 render and 11 probe cases: 14/14, zero failures,
errors or skips. The original native report confirms the visible Load route,
Cancel finished with 0, typed-file Open finished with 1, exactly two dialog
clicks, ten alternating 22/62-atom replacements and no failed deliveries.
Original JUnit/report digests are retained in the source receiving receipt.

The guard now waits for the intended exposed dialog and enabled button, uses
genuine filename input and observes actual completion. Diagnostic failure
cleanup is bounded and cannot manufacture a successful result. No acceptance
retry, extra global timeout, product rendering workaround or scientific change
was introduced. The precise Qt-internal reason selectFile did not establish the
hosted selection is not claimed; the corrected guard tests the user path.

The full browser gate 41144414475 passed on 191419cc; no Viewer runtime files
changed through the qualified guard source. Local native/SwiftShader evidence
remains separate. The maintainer explicitly defers the human Jupyter/Qt Load
smoke. Automatic receiving is complete; no human acceptance, full-scientific CI
clearance, new artifact qualification, tag or publication is inferred.

The final evidence-only closure changes no test, workflow or runtime bytes
relative to the qualified source. Scoped record/contract checks apply; completed
results are retained for unchanged inputs rather than repeated as a release gate.

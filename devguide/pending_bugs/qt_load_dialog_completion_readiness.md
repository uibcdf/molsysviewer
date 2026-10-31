---
summary: Observe readiness and completion of native Qt file-dialog actions in CI
issue: uibcdf/molsysviewer#287
status: active
opened: 2026-10-30
closed:
verification: reproduced
severity: medium
area: [qt, tests, loading]
guard:
normative:
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

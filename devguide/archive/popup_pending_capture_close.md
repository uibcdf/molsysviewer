---
summary: Diagnose pending capture cleanup after an actual popup closes.
issue: uibcdf/molsysviewer#378
status: resolved
opened: 2026-11-13
closed: 2026-11-13
severity: high
verification: reproduced
area: [capture, lifecycle, popup]
guard: molsysviewer/js/tests/e2e/moving-capture-lifecycle.e2e.ts
normative:
blocked_by: []
supersedes: []
---

# Resolved: pending capture after closing its actual popup

Resolved in source and native-browser receiving: early owner-bound `pagehide`
observation retires the exact endpoint before expensive native teardown, with
polling retained and no late source injection. Covering host/installed acceptance
remains separate under #372.

During #372 receiving, `707` completes box/trajectory and moving state/session/
annotation controls, then fails the `moving-capture-lifecycle` entry's existing
five-second closed-owner assertion. Isolated `709` reproduces the failure after
all six hidden/display/detached destination-preserving refusal controls pass.
Neither run stops for resources; inputs are unchanged and own-process cleanup
leaves no survivor or error.

The `709` diagnostic identifies the real canvas popup as both save owner and
capture renderer. After Playwright closes it, the Python authority still has its
registered endpoint, one pending Studio save and one pending capture, with
three genuine withheld scientific replies. No `popup_endpoint_closed` event
reaches the observed authority and no popup page error is recorded. The cause
and its relationship to the engine update remain unestablished; this is not an
upstream Mol* defect claim.

Inspect the native closed-window reference, closure monitor and authenticated
event route before changing an assertion or timeout. The correction must retain
exact owner/renderer cancellation, destination preservation, no late revival
and independent primary behavior. The existing actual-browser entry is the
behavioral guard; Python registry tests alone cannot receive window closure.

The complete all-state inventory has four pages/348 issues before this report;
related closed #319/#344 scopes do not record this focused failure. Original
logs and terminal receipts remain private with the #372 evidence. Native
host/installed/full-core qualification is still pending.

The native observer in `710` sees the closed window and a late one-second
monitor callback. The minimal Chrome control `711` receives `pagehide` for
both driver closure and native `window.close()` (the latter also receives
`beforeunload`). It changes neither molecular data nor production replies.
The source adds an owner-bound `pagehide` retirement listener, retains polling
as fallback and releases both observers on explicit closure/replacement. Host
and native closure share exactly-once endpoint notification. Actual types,
runtime/harness/entry builds and all 474 units pass in `712`. The unchanged
real-browser closure/cancellation guard remains the next required receiving.

The 4 CPU/4 GiB run `715` receives actual canvas-owner retirement with the
unchanged five-second post-close assertion. Its later panel click succeeds but
Playwright waits 30 seconds for scheduled owner navigation, before the explicit
new-panel receiving can run. Preserve that incomplete run. The test now opts
out of this implicit navigation wait only for the separate-window button,
retains explicit popup/loading and pending-capture assertions and additionally
requires the originating molecular controller/structure to survive unchanged.
The panel and full lifecycle exits were still pending at that point. `713` was rejected before
execution by the shared-CPU preflight; `714` is an operator driver-path error
before browser launch, not a product result.

## Resolution

Canonical `725` passes the entire registered lifecycle entry without a timeout
override: unavailable hidden/detached canvases refuse without replacing the
destination; recovery succeeds; closing the actual canvas and detached Studio
owners clears genuine pending saves/captures within the original five-second
assertion; released late scientific replies cannot recreate a file. The entry
also receives real transport-loss cancellation/autonomous expiry, cross-frame
static freezing and pending Python View closure. The originating molecular
controller survives opening detached Studio.

Native browser execution takes 161 seconds, with terminal exit 0 and unchanged
inputs; the bounded owner records 3,466.6 MiB peak summed process RSS, no resource
stop, no cleanup error and no surviving owned process. All 475 canonical units
and native project/runtime/harness/entry builds pass separately in `723`,
including exactly-once host/native closure and close-before-source resolution.
The original failures and diagnostic ablations remain preserved; none is
reclassified as a passing covering gate. The consolidated #372 receipt retains
their exact inputs and outcomes.

---
summary: Harden DataCard popup recovery, host bounds, keyboard navigation and disposal.
issue: uibcdf/molsysviewer#345
status: resolved
opened: 2026-11-08
closed: 2026-11-08
severity: medium
verification: reproduced
area: [plot, ui, accessibility, lifecycle]
guard: molsysviewer/js/tests/e2e/datacard-lifecycle.e2e.ts
normative: devguide/scene_contracts.md
blocked_by: []
supersedes: []
---

# DataCard lifecycle, bounds and keyboard access

**Resolved in source:** #315 B3.1–B3.5; later consolidated/installed/human
acceptance remains distinct. The [receiving record](../datacard_lifecycle_receiving_20261108.json)
retains exact inputs, native outcomes and private custody.

**Before correction:** A real pentalanine/Chromium before-control
reproduces retained active drag/resize listeners, a 450×210 card exceeding a
260×180 host, missing keyboard structure selection and silent popup blocking.
It exits 1 in 16.15 seconds with fixed inputs and all fifteen owned processes
closed. This does not measure a universal memory leak. The source is
`14ca8c83117f6e6b918371d3bddfaf9022c3f370`; the frozen scientific provider is
`42f5ed3bc8f02c979b3351212554e588243de0a5`.

The complete four-page issue inventory contains 315 issues. Closed #143 owns
canonical retention/hide/clear, #150 numeric axes and A3 literal title safety;
none receives the remaining B3 lifecycle/accessibility work. Preserve their
contracts and guards. B3.6 styling is an undecided recommendation, not part of
this correction.

## Accepted implementation and receiving

The card owns its gestures, observer, window and close fallback. Hide ends
active gestures and closes the popup, retaining the hidden card and its observer.
Clear/dispose also disconnect the observer without affecting another View.
The controller now disposes its plot overlay; it previously omitted that owner. Popup creation
publishes the detached state only after initialization succeeds; blocked and
bootstrap failures retain the source body and show a retry/dismiss notice.
Receive a real sandbox popup block and an independent native bootstrap-policy
failure, rather than replacing `window.open` or combining their coverage.

Constrain the card to the actual positive host bounds, preserve requested
sizes for later expansion and keep small content reachable through scrolling.
Receive source resize/fullscreen, popup resize/return, updates while detached,
current titles before the first popup and independent restoration. Preserve
the existing style and scientific observations.

Keyboard structure selection uses the existing trajectory-authority callback.
Complete raw current values remain accessible with their declared labels;
duplicate/nonmonotonic x coordinates must not collapse structure identity.
Receive actual input, Python agreement and native molecular coordinates through
the existing real-provider fixture. No new scientific calculation, implicit
preparation, Python parameter or dependency is introduced.

## Evidence boundaries

The private working directory retains original before observations, resource
and input manifests. Local receiving uses the qualified Python 3.14 environment,
at most eight logical CPUs/six GiB, swap disabled and a two-GiB globally
available reserve. Hosted, installed and human receiving retain separate scope;
A5/background behavior and Movie #320 remain required. The five original B3 leaves now have
locally verified source outcomes. This does not establish final release acceptance.

## Causal controls and guard refinement

The native sandbox before-control leaves the source graph available but reports
no blocked-window status. An independent policy installed after initialization
rejects native `Document.write`, leaving a blank child window with no source
notice. That second control executes the original compiled harness identified
by its manifest; the working TypeScript already contained changes. It is not a
clean-source original cohort or a claim of full Trusted Types compatibility.
Both policies now preserve the graph and report typed retry/dismiss notices;
partial child windows close. Restoring a minimized card uses native DOM icons.

Intermediate receiving failures are retained. The original total-observer
failure has no sufficient owner trace for attribution. A later total-timer
failure is traced to an unrelated 127 ms RxJS canvas timer: zero global
resources was an invalid oracle for a live molecular canvas. The final guard
positively observes a real card's observer/popup poll registration and their
release, while preserving unrelated input. That stronger check subsequently
finds a real omitted controller-dispose call; its native popup-close timeout is
retained before the correction. No failure is silently converted to a pass.

Final native receiving passes the complete DataCard guard, the existing
trajectory/precision/state/title entry with added real Python keyboard cases,
428 canonical Node tests and 503 affected Python checks (overlapping boundary
scopes, not one combined suite). Exact timings, later reporting-only checks and
all original campaign statuses are in the receipt. Browser screenshots are
supplemental visual inspection, not the postponed human Jupyter/Qt trial.

The durable contract is the DataCard clause in `scene_contracts.md`. B3.6
styling remains undecided; existing opacity, grays and blur are unchanged.

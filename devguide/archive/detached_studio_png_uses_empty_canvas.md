---
summary: Route detached Studio PNG export to its associated molecular canvas.
issue: uibcdf/molsysviewer#380
status: resolved
opened: 2026-11-13
closed: 2026-11-13
severity: medium
verification: measured
area: [export, studio, popup]
guard: molsysviewer/js/tests/e2e/studio-image-export.e2e.ts
normative:
blocked_by: []
supersedes: []
---

# Resolved: detached Studio PNG uses its associated canvas

**Resolved 2026-11-13.** The initial investigation below retains its original
scope; the Resolution section names the current correction and receiving.

Before 1.0, route the panel's PNG request to its associated visible molecular
canvas, retaining figure settings, requester-only delivery and bounded failure
on renderer/owner disappearance. The panel intentionally has no molecular
geometry; it must not silently capture another endpoint or claim success with
an empty image. Preserve the existing Python export contract and check widget,
exported-page and native Qt transport applicability, including Studio detached
from a canvas popup and independent Views.

During #372, the real persistent Python/widget/popup diagnostic `728` loads
pentalanine: the primary has 62 atoms, five representations and an 850 × 600
drawing buffer; the detached panel has zero atoms/representations and a 1 × 1
buffer. Clicking the actual Download PNG Image button with transparent
background downloads a **2 × 2 PNG with no nonzero-alpha pixels**, while the
panel reports `PNG download started.` Its source handles `download_image`
through its local `downloadViewportImage()` and `getImageDataUri()`.
The same observation records `panelAfter.animating=True`: the local native
screenshot helper also restarts the initially stopped panel render loop.
Delegation must preserve that panel's stopped loop, not only fix image pixels;
#379 remains partial until this path is received.

Native exit is 0, selected inputs are unchanged, the owner records 2,162.2 MiB
peak summed RSS, and there is no resource stop, cleanup error or surviving
owned process. These are successful reproduction facts, not export acceptance.
The diagnosis is MolSysViewer ownership/routing; no upstream regression or
causal relation to the Mol* version change is established. #379's unused-loop
correction remains separately scoped. The main-canvas PNG guard passes.

The complete pre-report all-state inventory contains four pages/350 issues,
excluding PRs; no equivalent focused report was identified. Raw downloaded
bytes, source identities and terminal evidence remain private with #372.
Receive actual output dimensions/pixels, selected renderer/figure settings,
owner isolation and close/cancel/late-reply semantics before closure.

## Implementation receiving

The widget host now binds a detached panel's private PNG request to the canvas
recorded at detachment. It owns the correlation, cancellation and deadline;
request payloads cannot choose another renderer or recipient. Panel-only image
rendering is refused defensively. The panel retains normal native screenshot
settings and exposes cancellation while waiting.

Project types, runtime/harness/entry builds and all 486 canonical unit cases
pass in controlled profile 743. The new mandatory core entry preserves actual
downloaded pixels and independent native references. Initial attempts expose
test preparation defects (a second browser context and duplicate bootstrap
instrumentation), corrected without changing product behavior. Profiles 748
and 750 then download an 850 x 600 molecular PNG but fail exact decoded-pixel
comparison with a subsequent native export. Profile 750 preserves both PNGs
and shows identical camera/background before, between and after captures.
Keep the discrepancy open while comparing repeated native exports; neither
the routing nor #379's final PNG lifecycle exit is declared accepted yet.

## Resolution

The host owns each panel's associated renderer, private correlation and
requester-only PNG delivery. Cancel, timeout, retirement and late replies
cannot redirect a capture to another canvas. Source identity and figure
settings are retained; the hidden panel renderer refuses image work and stays
stopped. Static HTML/Qt retain their existing canvas PNG paths and do not
advertise Python-widget panel detachment; no unsupported capability is added.

Current canonical guard 762 passes the complete real Python/widget/Mol*
workflow in 160 seconds (164 seconds supervised): three downloaded images,
both canvas origins, transparent/opaque settings, exact decoded native
reference pixels, preserved cameras/backgrounds, independent Views,
genuine rendered-reply cancellation/recovery, and closed-origin refusal.
Current panel/Movie regression 763 also passes. Source types/builds and all
490 canonical unit cases pass in 761. No resource stop, input mutation,
cleanup error or surviving owned process is recorded.

The original blank PNG remains reproduction evidence. The later first/repeated
pixel difference is independently native and separately resolved under #382;
it is not misreported as a routing or dependency-version regression. The
bounded entry now has a 240-second whole-workflow budget after the observed
172-second eight-image workflow; every operation deadline and quality choice
is unchanged. Full-core/platform/installed/human qualification stays separate.

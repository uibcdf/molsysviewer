---
summary: Route detached Studio PNG export to its associated molecular canvas.
issue: uibcdf/molsysviewer#380
status: open
opened: 2026-11-13
closed:
severity: medium
verification: reproduced
area: [export, studio, popup]
guard:
normative:
blocked_by: []
supersedes: []
---

# Detached Studio exports its empty local canvas

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

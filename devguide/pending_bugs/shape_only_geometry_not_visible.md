---
summary: Shape-only live Jupyter Render creates geometry that remains invisible
issue: uibcdf/molsysviewer#257
status: partial
opened: 2026-10-21
closed:
severity: high
verification: reproduced
area: [shapes, camera, notebook, addons]
guard: molsysviewer/js/tests/e2e/panel-popup-welcome.e2e.ts
normative:
blocked_by: []
supersedes: []
---

# Shape-only geometry is registered but not visible

**Reported:** Diego's real PharmacophoreMT/Jupyter smoke on 2026-10-21,
Viewer 7b3bec46 / runtime d126c5a1 and provider f0d96ae0.

## What

The empty canvas and Welcome appear. After preparing the unrelated sphere and
clicking Render, neither that sphere nor the two pharmacophore sites is visible.
The saved notebook's Render assertions pass: Python has both owned tags and the
caller sphere. Its subsequent Clear assertion fails; whether Clear was clicked
is not established and this is not yet a separate action-routing diagnosis.

## How

The native probe reproduces an existing sphere, camera radius zero and an empty
GPU pick. Camera authority disables Mol*'s automatic first framing. In Mol*
5.4.1, the Canvas3D sphere objects retain cached zero bounds until an operation
evaluates the scene's lazy bounds. The first attempted correction waited for
that cached radius before requesting a reset, so the new GPU-pick guard still
failed. Committing the new renderables and unconditionally requesting the first
reset removes that wait. Subsequent additions frame only while there is no
molecular system and no deliberate viewpoint; explicit views remain preserved.

#240's Welcome obstruction and #245's independent endpoint lifetime guards did
not prove visible geometry. The shape-only guard now requires an on-screen GPU
pick for the initial sphere and coexisting addon/caller geometry in both
canvases, through actual Python/widget/Chromium rendering. A distant addition
must preserve an explicitly chosen camera. Render/Clear, remount and both popup
types remain covered.

## Why

A native shape-only workspace must draw and frame its initial content without a
dummy molecular system or recovery click. Preserve chosen camera viewpoints and
ordinary popup behavior. Consumer context: uibcdf/pharmacophoremt#58.

## Evidence

The user-edited notebook is retained; no outputs are overwritten. Diagnostic
work belongs to `/tmp/msv-shape-only-review-20261021/`. The previous exact-source
CI success keeps its tested scope and does not certify this human observation.

## Source correction and remaining human receiving

The strengthened shape-only guard and scene contracts pass. Actual isolated
PharmacophoreMT f0d96ae0 Python helpers render and clear two sites while retaining
the caller sphere and no MolSys. This is not a browser observation of that
specific provider. The source correction is delivered; the report remains
partial until Diego confirms the live PHMT/Jupyter visual retest. His previous
view was closed before the separate Studio-occlusion question could be checked.

The notebook now requests compact controls under #258. Its original human
outputs are preserved in the working notebook and backed up under the evidence
directory. Reload the notebook page and restart the kernel before retesting so
the page-level runtime cache cannot retain the preceding bundle. After Render,
close Studio to inspect the entire scene, then reopen it for Clear and the
independent-window steps. No automatic panel closing is added.

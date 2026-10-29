---
summary: Local Qt shell mounts an export-only workbench and drops live product events.
issue: uibcdf/molsysviewer#270
status: resolved
opened: 2026-10-29
closed: 2026-10-29
severity: high
verification: measured
area: [standalone, qt, runtime]
guard: tests/test_qt_live_workbench.py::test_qt_live_workbench_full_render_gpu
normative:
blocked_by: []
supersedes: []
---

# Local Qt shell mounts an export-only workbench

## What

The local Qt shell owns a persistent MolSysView and QtViewChannel but mounts
its frontend with hasAuthority=false. Product events are handled as export-only
commands instead of reaching the Python owner. Studio actions, live camera
requests and addon tasks cannot use that authority. application.py additionally
installs an obsolete Reset-only native context menu.

## How

At 8903f065, create_standalone_qt0_window selects host_event_transport=url-scheme.
index.ts uses that switch only for readiness and message acknowledgements,
not controller product events. Its missing-authority path still owns those.
QtViewChannel also stores synchronized UI traits as inert plain attributes,
so Python and browser canvas/addon preferences can diverge.

## Why

The local standalone is another host of the same live scene and core tools.
Static HTML remains authority-free; changing an exported page into an implicit
Python client is not acceptable. Reuse the existing bridge and controller;
retain independent #35 reload, #36 movie and #51 popup acceptance criteria.

## Evidence and limits

A baseline real native-GPU window on Linux/Python 3.14, official PySide6/Qt
6.11.2 and NVIDIA Quadro M2000 reaches Ready and renders dialanine. Only that
app window is captured. This disproves a universal startup/render failure, not
the inspected missing-authority defect. Hosted historical Qt failures include
a smoke test explicitly disabling the GPU needed to create its WebGL canvas.
No D-Bus workaround, package upgrade or software-render certificate is inferred.

## Acceptance

Real Qt frontend actions create/revise Python-owned regions and annotations;
Studio and addon events reach their existing handlers; camera requests return;
canvas preferences synchronize in both directions with validated traits.
Shared context controls replace the native Reset-only override. Static HTML
keeps its existing no-session behavior. Test native rendering and repeated
loading separately from offscreen transport probes.

## Resolution — 2026-10-29

The local connector now supplies live Python authority to the shared controller.
Qt preferences reuse widget validators and synchronize in both directions;
static HTML retains its authority-free path. The obsolete Reset-only native
context override is removed. A native QAction no longer steals Escape; shared
canvas handlers precede the Qt fullscreen fallback.

The native guard creates a Python-owned region from the shared context form,
receives camera/PNG replies and verifies Python-to-browser Cinema and
browser-to-Python Standard preferences. Addon event routing is shared, but
notebook-widget addon rendering is not universally qualified by this test.

Native Linux source evidence: canonical PySide6/Qt 6.11.2, Python 3.14.7,
NVIDIA Quadro M2000. The guard passes with the frozen MolSysMT runtime matching
71fbe4f4. See [the review](../standalone_review_20261029.md) for scope and
retained failed attempts. This does not qualify a published artifact, other
native platforms or the standalone 1.0 support promise.

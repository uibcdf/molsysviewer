---
summary: Independent local Qt hosts share the default profile and retain the first transport handlers.
issue: uibcdf/molsysviewer#271
status: resolved
opened: 2026-10-29
closed: 2026-10-29
severity: high
verification: measured
area: [standalone, qt, lifecycle]
guard: tests/test_qt_live_workbench.py::test_qt_live_workbench_full_render_gpu
normative:
blocked_by: []
supersedes: []
---

# Independent local Qt hosts share their transport profile

## What

Creating and closing one local host, then creating another in the same Qt
application leaves the second waiting for readiness. Two simultaneous hosts
also install their bridge-specific handlers into the same global profile.

## How

The first real-window probe passes after respecting WebGL and showing its
window. The following full-render probe fails, with explicit stderr messages
that handlers already exist for molsysviewer and molsysviewer-payload.
_install_qt_message_bridge uses QWebEnginePage(webview), whose default profile
outlives the local window. Scheme handlers are profile-scoped and cannot use
two independent bridge payload stores simultaneously.

## Why

A local host owns one Python scene, bridge, page, URL handlers and private
WebEngine profile. Closing it must stop its bridge and scene and dispose its
page before its profile. Implicit shell HTML belongs to that lifetime; explicit
caller outputs must remain intact. A second host must not affect the first.
The resource exception under #109 and popup work under #51 remain distinct.

## Acceptance

Create two real native windows in one QApplication; both become ready with
independent scenes and profiles. Close one and continue using the other.
Reopening also succeeds. Owned temporary HTML is removed after page disposal;
explicit shell outputs remain. Late bridge sends fail visibly after closure.

## Resolution — 2026-10-29

Each local host now owns its own off-the-record profile and scheme handlers.
Normal closure cancels downloads, closes its view/bridge, disposes its page
before its profile and removes owned implicit HTML after page destruction.
Explicit outputs survive. Late sends raise a diagnosed error.

The native guard operates two simultaneous, ready windows with distinct
profiles, closes the second, verifies its closed view and removed implicit
HTML, then successfully requests the first window's camera. The older native
probe sequence also passes repeated host creation in one QApplication.
The broader #109 initialization/image-export exception remains open.

Native Linux source evidence: canonical PySide6/Qt 6.11.2, Python 3.14.7,
NVIDIA Quadro M2000. The guard passes with the frozen MolSysMT runtime matching
71fbe4f4. See [the review](../standalone_review_20261029.md) for scope and
retained failed attempts. This does not qualify a published artifact, other
native platforms or the standalone 1.0 support promise.

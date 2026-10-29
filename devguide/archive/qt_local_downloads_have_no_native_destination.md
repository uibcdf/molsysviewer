---
summary: Local Qt Studio downloads have no native destination handler.
issue: uibcdf/molsysviewer#272
status: resolved
opened: 2026-10-29
closed: 2026-10-29
severity: medium
verification: measured
area: [standalone, qt, export]
guard: tests/test_qt_live_workbench.py::test_qt_live_workbench_full_render_gpu
normative:
blocked_by: []
supersedes: []
---

# Local Qt downloads have no destination handler

## What

The live local Studio creates browser downloads but its WebEngine profile has
no downloadRequested slot. The remote Qt shell already owns a destination dialog
and acceptance path; the local native Export menu is a distinct working route.

## How

The local application installs bridge handlers and menus. Only the remote chrome
connects the download signal. Static exports and browser downloads under #181
retain their separate guards; they did not qualify this native integration.

## Why

The same Studio file workflows should work in a local native window. Reuse the
existing host integration instead of recreating export logic or scientific data.
The user chooses an explicit destination; cancelling must leave it untouched.
Completion and interruption must produce different status messages.

## Acceptance

An actual Qt download opens a real destination dialog, writes the expected
bytes when accepted and leaves no destination after cancellation. Exercise the
shared Studio HTML output and the existing remote-host contract. Profile/window
ownership stays with #271; remote previews remain outside the 1.0 promise.

## Resolution — 2026-10-29

Local and remote hosts reuse the native destination integration. The user
chooses the destination; cancellation creates no file. Status distinguishes
completion, cancellation and interruption. Native menu exports use the current
persistent scene, and HTML uses the canonical self-contained writer rather
than exporting the live shell connector.

The real Qt guard accepts a shared Studio HTML download, confirms its newly
created region, cancels a second download without a destination, then exports
the same current scene from the native menu. Pure local/remote integration
contracts remain covered in test_standalone.py.

Native Linux source evidence: canonical PySide6/Qt 6.11.2, Python 3.14.7,
NVIDIA Quadro M2000. The guard passes with the frozen MolSysMT runtime matching
71fbe4f4. See [the review](../standalone_review_20261029.md) for scope and
retained failed attempts. This does not qualify a published artifact, other
native platforms or the standalone 1.0 support promise.

---
summary: Qt Studio-loading guard activates a hidden form instead of visible Load controls
issue: uibcdf/molsysviewer#287
status: resolved
opened: 2026-10-30
closed: 2026-10-30
verification: reproduced
severity: medium
area: [qt, tests, loading]
guard: tests/test_qt_live_workbench.py::test_qt_live_workbench_full_render_gpu
normative: devguide/studio_interaction_contract.md
blocked_by: []
supersedes: []
---

# Visible Qt Studio loading guard

The current helper opens System, then queries the now-hidden Load form globally,
assigns input values and invokes JavaScript button.click(). Run 41139611271 on
531f3814 passes. This proves dispatch but cannot prove visible user access.

Update the native helper to navigate to Load, verify geometry/hit targets and use
real QTest WebEngine input for the source and primary action. Exercise native
file selection/cancellation as #286 is implemented. Retain authority, binary
projection, ten replacements/pixels, fullscreen, download/movie and cleanup
assertions. Hosted Xvfb/SwiftShader remains software diagnostic evidence; genuine
native observations retain their own provenance and no human acceptance is
inferred. No product failure is asserted solely from the old test weakness.

## Resolution — 2026-10-30

The real native helper opens Studio with its shortcut and selects the visible
Load tab. It checks element geometry and hit targets, synchronizes WebEngine
painting before native clicks, and uses QTest input rather than assigning DOM
values or calling button.click(). It cancels and accepts actual Qt file dialogs,
proves that choosing a path alone leaves the atom count unchanged, types the
path, selects Replace and activates the visible primary action. The expected
62-atom system loads and System becomes current. The unchanged authority,
binary projection, ten replacement/pixel, fullscreen, export/movie, independent
host and cleanup checks still pass. The second host clears its picker callback.

Final native Linux / Wayland execution passes 1/1 full guard in 30.63 s with
PySide6/Qt 6.11.2 and provider 9fb77c3583b44dda31c0466348369de137301df9. Dialogs
are real Qt widgets with AA_DontUseNativeDialogs for deterministic automation;
this does not certify every desktop portal. Runtime screenshots were inspected.
Earlier failed development runs and their tracebacks remain separate evidence:
the initial button callback was corrected, and immediate prepaint QTest clicks
were replaced with paint-synchronized hit checks. No retries or weakened
assertions are part of the passing guard. Hosted Xvfb/SwiftShader, installed
packages and human acceptance retain independent scopes.

See studio_load_polish_receiving_20261030.json and the maintained Studio contract.

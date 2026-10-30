---
summary: Expose native Qt shortcuts in shared Help and clarify source restoration.
issue: uibcdf/molsysviewer#281
status: resolved
opened: 2026-10-30
closed: 2026-10-30
verification: inspected
area: [standalone, qt, usability]
guard: tests/test_qt_live_workbench.py::test_qt_live_workbench_full_render_gpu
normative:
blocked_by: []
supersedes: []
---

# Discoverable Qt shortcuts in shared Help

## What

Retiring the window menu left native shortcuts outside visible Help. Bare
Ctrl+R restored a previous source rather than performing an ordinary reload.

## How

The live Qt transport supplies a bounded Desktop window shortcut section to
the shared Help renderer. These capabilities are not widget preferences or
portable scene state. Restoring a recorded source is now Ctrl+Shift+R;
Ctrl+Shift+D reads/copies the last status. Notebook and exported-page Help
retain their existing keyboard vocabulary; no replacement native menu appears.

## Why and receiving

The same Help entry should explain the host actually being used, without
advertising unavailable native operations elsewhere. The real Qt/WebEngine
child opens shared Help and verifies its native rows; window QActions retain
actual native export delivery. Headless channel receiving checks that host
capabilities stay outside portable export snapshots and validated preferences.
The shared JS units and browser gates retain their own recorded outcomes in
the [receipt](../standalone_window_polish_receiving_20261030.json).

## Resolution — 2026-10-30

Implemented in `7900263691cd96fcf74840357cc2e7ca8ef62914`. The live Qt/WebEngine guard opens actual shared Help, checks native shortcut rows and registered actions and exercises a real export key. The headless UI/export test preserves the separation between host capabilities, validated preferences and portable scene content.

Local regression covers 3,318 distinct passing cases across the original run
and directed test-provenance recovery, with 21 skips retained; 332 JS units
and 44 core browser suites pass. This is not one clean full pytest run.
Hosted CI and the postponed maintainer visual review retain their own states
in the receiving record. Qt remains experimental; no publication follows.

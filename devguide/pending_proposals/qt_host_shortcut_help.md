---
summary: Expose native Qt shortcuts in shared Help and clarify source restoration.
issue: uibcdf/molsysviewer#281
status: active
opened: 2026-10-30
closed:
verification: inspected
area: [standalone, qt, usability]
guard:
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
